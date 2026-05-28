"""
Shared utilities for all brain agents (B1 Stratège, Prospecteur, Architecte, CdC).
Multi-provider LLM routing, angle rotation, report memory, quota logging.
"""
import json
import os
import urllib.request
import urllib.error
from datetime import date, datetime
from pathlib import Path

# --------------------------------------------------------------------------- #
# Routing config
# --------------------------------------------------------------------------- #
DEFAULT_ROUTING = {
    "prospecteur": {"primary": "gemini", "fallback": ["groq", "mistral"]},
    "architecte": {"primary": "mistral", "fallback": ["gemini", "groq"]},
    "stratege": {"primary": "gemini", "fallback": ["mistral", "groq"]},
    "roman_planner": {"primary": "gemini", "fallback": ["groq"]},
    "roman_writer": {"primary": "groq", "fallback": ["gemini", "mistral"]},
    "cdc_generator": {"primary": "gemini", "fallback": ["mistral"]},
    "conseil": {"primary": "gemini", "fallback": ["mistral"]},
    "stl_trends": {"primary": "gemini", "fallback": ["groq", "mistral"]},
    "stl_cdc": {"primary": "gemini", "fallback": ["groq", "mistral"]},
}

def _load_routing():
    cfg_path = Path("data/config/llm_routing.json")
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text())
        except Exception:
            pass
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(DEFAULT_ROUTING, ensure_ascii=False, indent=2))
    return DEFAULT_ROUTING


# --------------------------------------------------------------------------- #
# Provider implementations (stdlib urllib only)
# --------------------------------------------------------------------------- #
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def _call_gemini(system: str, user: str, temperature: float, max_tokens: int,
                 json_mode: bool = True) -> tuple[str, int, int]:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY not set")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"
    gen_config = {"temperature": temperature, "maxOutputTokens": max_tokens}
    body = {
        "contents": [{"role": "user", "parts": [{"text": f"{system}\n\n{user}"}]}],
        "generationConfig": gen_config,
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        result = json.loads(resp.read())
    candidate = result["candidates"][0]
    finish = candidate.get("finishReason", "STOP")
    if finish not in ("STOP", "MAX_TOKENS", "FINISH_REASON_STOP"):
        print(f"[brain_utils] Gemini finishReason={finish} (non bloquant)")
    text = candidate["content"]["parts"][0]["text"]
    usage = result.get("usageMetadata", {})
    return text, usage.get("promptTokenCount", 0), usage.get("candidatesTokenCount", 0)


def _call_openai_compat(base_url: str, model: str, api_key: str,
                         system: str, user: str, temperature: float, max_tokens: int) -> tuple[str, int, int]:
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        base_url,
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
    text = result["choices"][0]["message"]["content"]
    usage = result.get("usage", {})
    return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def _call_groq(system: str, user: str, temperature: float, max_tokens: int) -> tuple[str, int, int]:
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        raise ValueError("GROQ_API_KEY not set")
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    return _call_openai_compat(
        "https://api.groq.com/openai/v1/chat/completions",
        model, key, system, user, temperature, max_tokens
    )


def _call_mistral(system: str, user: str, temperature: float, max_tokens: int) -> tuple[str, int, int]:
    key = os.environ.get("MISTRAL_API_KEY", "")
    if not key:
        raise ValueError("MISTRAL_API_KEY not set")
    model = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")
    return _call_openai_compat(
        "https://api.mistral.ai/v1/chat/completions",
        model, key, system, user, temperature, min(max_tokens, 8192)
    )


PROVIDERS = {
    "gemini": _call_gemini,
    "groq": _call_groq,
    "mistral": _call_mistral,
}


# --------------------------------------------------------------------------- #
# Main LLM call
# --------------------------------------------------------------------------- #
def llm_call(agent_type: str, system: str, user: str,
             temperature: float = 0.7, max_tokens: int = 4000,
             json_mode: bool = True) -> str:
    """Try primary provider then fallbacks. Returns text or empty string.
    json_mode=True (default): Gemini uses responseMimeType application/json — prevents truncation.
    Set json_mode=False for free-text outputs (novel chapters, etc.).
    """
    routing = _load_routing()
    config = routing.get(agent_type, DEFAULT_ROUTING.get(agent_type, {"primary": "gemini", "fallback": []}))
    providers = [config["primary"]] + config.get("fallback", [])

    for provider in providers:
        fn = PROVIDERS.get(provider)
        if fn is None:
            continue
        for attempt in range(2):
            try:
                print(f"[brain_utils] {agent_type} → {provider} (attempt {attempt+1})")
                if provider == "gemini":
                    text, tokens_in, tokens_out = fn(system, user, temperature, max_tokens, json_mode)
                else:
                    text, tokens_in, tokens_out = fn(system, user, temperature, max_tokens)
                log_api_call(agent_type, provider, tokens_in, tokens_out, True)
                return text
            except (urllib.error.URLError, TimeoutError) as e:
                print(f"[brain_utils] {provider} timeout/network: {e}")
                if attempt == 0:
                    continue
            except Exception as e:
                print(f"[brain_utils] {provider} error: {e}")
                break
        log_api_call(agent_type, provider, 0, 0, False)

    print(f"[brain_utils] All providers failed for {agent_type}")
    return ""


def extract_json(text: str) -> str:
    """Extract JSON from LLM response, stripping markdown fences or surrounding prose."""
    t = text.strip()
    # Try direct parse first
    if t.startswith("{") or t.startswith("["):
        return t
    # Strip ```json ... ``` or ``` ... ```
    if "```" in t:
        parts = t.split("```")
        for part in parts[1::2]:  # odd parts are inside fences
            inner = part.strip()
            if inner.startswith("json"):
                inner = inner[4:].strip()
            if inner.startswith("{") or inner.startswith("["):
                return inner
    # Last resort: find first { or [
    for ch, end in [("{", "}"), ("[", "]")]:
        start = t.find(ch)
        if start != -1:
            last = t.rfind(end)
            if last > start:
                return t[start:last + 1]
    return t


# --------------------------------------------------------------------------- #
# Angle Rotator
# --------------------------------------------------------------------------- #
ANGLES = {
    "prospecteur": [
        "Explore UNIQUEMENT les marchés B2B : vendre nos capacités à d'autres créateurs/entreprises, pas directement au consommateur final.",
        "Explore UNIQUEMENT les niches ultra-spécialisées que les grandes plateformes ignorent : trop petites pour elles, parfaites pour nous.",
        "Pense comme un investisseur qui cherche le x10 : qu'est-ce qui n'existe pas encore mais sera évident dans 12 mois ?",
        "Explore UNIQUEMENT les formats apparus ou explosés après 2024. Nouveaux formats, nouvelles plateformes, nouveaux comportements d'achat.",
        "Cherche les business qu'UNE SEULE personne fait discrètement et gagne bien. Invisible aux algorithmes, visible aux observateurs attentifs.",
        "Explore les opportunités de TRADUCTION ou d'ADAPTATION culturelle : un produit qui marche en anglais et qui n'existe pas dans d'autres langues.",
        "Challenge nos certitudes : qu'est-ce qu'on croit impossible ou hors de portée mais qui en réalité ne l'est pas avec notre stack actuelle ?",
        "Explore UNIQUEMENT les marchés à forte saisonnalité : rentrée, Noël, Saint-Valentin, été. Comment les anticiper 3 mois en avance ?",
        "Pense en HYBRIDES : croise deux de nos domaines existants pour créer quelque chose qu'aucun concurrent ne fait.",
        "Explore les marchés DISGRÂCIÉS : domaines que tout le monde évite en ce moment parce qu'il y a eu trop de spammeurs, mais qui ont encore une demande réelle.",
        "Explore ce qu'on peut faire avec SEULEMENT du texte et du code, zéro image. Marchés entièrement pilotables par LLM.",
        "Pense à l'AFFILIATION avancée : pas juste des liens, mais des systèmes de recommandation automatisés ultra-ciblés.",
    ],
    "architecte": [
        "Perspective du client final qui reçoit notre produit : qu'est-ce qui lui semble médiocre ou incomplet ?",
        "Perspective de l'ingénieur DevOps : où est le risque de crash silencieux ? Qu'est-ce qui peut tomber sans qu'on le sache ?",
        "Perspective de la scalabilité : qu'est-ce qui casse ou se dégrade si on multiplie le volume par 10 ?",
        "Perspective du CFO : où perdons-nous de l'argent ou du temps sans le savoir ? Quelles inefficiences coûtent cher ?",
        "Perspective de quelqu'un qui reprend le système dans 6 mois sans documentation : où se perd-il ?",
        "Perspective de la sécurité et de la résilience : comment ce système pourrait-il être dégradé ou bloqué (ban plateformes, API morte, repo corrompu) ?",
        "Perspective de l'automatisation maximale : quelles actions Hugo fait encore manuellement qui pourraient être automatisées sans risque ?",
    ],
    "stratege": [
        "Maximise le potentiel de revenu à court terme (1-3 mois) avec ce qu'on peut produire AUJOURD'HUI sans clé image.",
        "Maximise la diversification : propose des produits dans des catégories qu'on n'a pas encore testées.",
        "Cherche l'angle COLLECTION : quel produit, s'il explose, ouvre une série de 10+ volumes ?",
        "Cherche le REFONTE gagnante : quel bestseller est mal noté pour une raison simple à corriger ?",
        "Maximise la VITESSE : quel produit peut être en vente dans 48h avec notre stack actuelle ?",
        "Cherche le CROSS-TREND : deux tendances qui ne se sont pas encore croisées mais dont le croisement ferait sens.",
    ],
}


def get_angle(agent_type: str) -> str:
    """Returns this week's angle for the given agent type."""
    week = date.today().isocalendar()[1]
    angles = ANGLES.get(agent_type, ["Explore de nouveaux angles."])
    return angles[week % len(angles)]


# --------------------------------------------------------------------------- #
# Report Memory
# --------------------------------------------------------------------------- #
def get_previous_propositions(reports_dir: str, agent_type: str, max_reports: int = 4) -> str:
    """
    Reads last N reports for this agent, extracts proposal names.
    Returns an injection string forbidding repetition.
    """
    rdir = Path(reports_dir)
    if not rdir.exists():
        return ""

    pattern = f"rapport_{agent_type}_"
    files = sorted(
        [f for f in rdir.glob(f"*{agent_type}*") if f.suffix in (".json", ".md")],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[:max_reports]

    propositions = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
            if f.suffix == ".json":
                data = json.loads(content)
                for item in data if isinstance(data, list) else data.get("propositions", []):
                    if isinstance(item, dict):
                        name = item.get("titre") or item.get("name") or item.get("title") or ""
                        if name:
                            propositions.append(name)
            else:
                for line in content.splitlines():
                    if line.startswith("## ") or line.startswith("### "):
                        propositions.append(line.lstrip("#").strip())
        except Exception:
            pass

    if not propositions:
        return ""

    unique = list(dict.fromkeys(propositions))[:30]
    joined = "\n".join(f"- {p}" for p in unique)
    return f"INTERDIT de répéter ou paraphraser ces propositions déjà faites :\n{joined}\n\nApporte des idées ENTIÈREMENT nouvelles."


# --------------------------------------------------------------------------- #
# Temperature Schedule
# --------------------------------------------------------------------------- #
TEMPERATURE_SCHEDULE = {
    "prospecteur": lambda week: [0.9, 1.0, 0.85, 0.95, 1.0, 0.8][week % 6],
    "architecte": lambda week: [0.6, 0.7, 0.65, 0.75][week % 4],
    "stratege": lambda week: [0.7, 0.8, 0.75, 0.85][week % 4],
    "roman_writer": lambda week: 0.92,
}


def get_temperature(agent_type: str) -> float:
    week = date.today().isocalendar()[1]
    fn = TEMPERATURE_SCHEDULE.get(agent_type, lambda w: 0.7)
    return fn(week)


# --------------------------------------------------------------------------- #
# Quota Logger
# --------------------------------------------------------------------------- #
def log_api_call(agent_type: str, provider: str, tokens_in: int, tokens_out: int, success: bool):
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "date": date.today().isoformat(),
        "agent": agent_type,
        "provider": provider,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "success": success,
    }
    with open(logs_dir / "quota.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def check_daily_budget(provider: str, max_calls_today: int = 200) -> bool:
    """Returns True if provider still has budget for today."""
    quota_file = Path("data/logs/quota.jsonl")
    if not quota_file.exists():
        return True
    today = date.today().isoformat()
    count = 0
    try:
        for line in quota_file.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            if entry.get("date") == today and entry.get("provider") == provider and entry.get("success"):
                count += 1
    except Exception:
        return True
    return count < max_calls_today
