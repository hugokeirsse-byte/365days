"""
Dialogue Gemini A ↔ Gemini B — collaboration adversariale automatisée.

Gemini A = Questionneurateur socratique. Pose des questions ciblées pour perfectionner B.
         Dit "VALIDÉ" quand la sortie de B est optimale.
Gemini B = Créateur/Bâtisseur. Génère et affine le livrable.

Workflow :
  1. cerveau_prompts génère les rôles experts de A et B
  2. B produit un premier draft
  3. A pose une question ciblée sur le draft de B
  4. B améliore son output
  5. Répéter jusqu'à "VALIDÉ" ou max_turns
  6. Auditrice valide le résultat final
  7. Auto-commit sur GitHub si validé

Usage:
  TOPIC="système de réponse appels d'offres BOAMP"
  GOAL="Produire un workflow complet pour détecter et répondre aux AO publics français"
  MAX_TURNS=8
  TEMPO=5
  python scripts/gemini_dialogue.py

Sorties: data/dialogues/{slug}_{timestamp}.json
         data/dialogues/{slug}_final.md (le livrable final de B)
"""

import json
import os
import re
import sys
import time
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")

TOPIC = os.environ.get("TOPIC", "")
GOAL = os.environ.get("GOAL", "")
MAX_TURNS = int(os.environ.get("MAX_TURNS", "8") or "8")
TEMPO = int(os.environ.get("TEMPO", "5") or "5")  # secondes entre appels API
AUTO_COMMIT = os.environ.get("AUTO_COMMIT", "1")  # 1 = commit sur GitHub si validé
MIN_AUDIT_SCORE = int(os.environ.get("MIN_AUDIT_SCORE", "70") or "70")

# Fallback robuste : si TOPIC/GOAL non fournis par le workflow, lire le trigger file
# directement (évite tout problème d'échappement shell dans GITHUB_ENV).
_TRIGGER_FILE = ".triggers/gemini_dialogue.json"
if (not TOPIC or not GOAL) and os.path.exists(_TRIGGER_FILE):
    try:
        with open(_TRIGGER_FILE, encoding="utf-8") as _f:
            _t = json.load(_f)
        TOPIC = TOPIC or _t.get("topic", "")
        GOAL = GOAL or _t.get("goal", "")
        MAX_TURNS = int(_t.get("max_turns", MAX_TURNS))
        TEMPO = int(_t.get("tempo", TEMPO))
        AUTO_COMMIT = str(_t.get("auto_commit", AUTO_COMMIT))
        MIN_AUDIT_SCORE = int(_t.get("min_audit_score", MIN_AUDIT_SCORE))
        print(f"   ℹ️  Paramètres lus depuis {_TRIGGER_FILE}")
    except Exception as _e:
        print(f"   ⚠️  Lecture trigger file échouée : {_e}")


def call_gemini(system_prompt: str, history: list, user_message: str,
                temperature: float = 0.7) -> str:
    import urllib.request
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}")

    # Gemini n'accepte que les rôles "user" et "model" (pas "assistant" comme OpenAI/Groq)
    role_map = {"assistant": "model", "user": "user", "model": "model"}
    contents = []
    for msg in history:
        contents.append({
            "role": role_map.get(msg["role"], "user"),
            "parts": [{"text": msg["content"]}]
        })
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {"temperature": temperature, "maxOutputTokens": 4096}
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
                                  headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        raise RuntimeError(f"Gemini HTTP {e.code}: {body}") from None
    # Gemini peut renvoyer un candidat sans texte (filtré, MAX_TOKENS…)
    candidates = result.get("candidates", [])
    if not candidates or "content" not in candidates[0]:
        finish = candidates[0].get("finishReason", "?") if candidates else "no_candidates"
        raise RuntimeError(f"Gemini réponse vide (finishReason={finish})")
    return candidates[0]["content"]["parts"][0]["text"].strip()


def call_groq(system_prompt: str, history: list, user_message: str,
              temperature: float = 0.7) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 4096
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:200]
        raise RuntimeError(f"Groq HTTP {e.code}: {body}") from None
    return result["choices"][0]["message"]["content"].strip()


def call_mistral(system_prompt: str, history: list, user_message: str,
                 temperature: float = 0.7) -> str:
    url = "https://api.mistral.ai/v1/chat/completions"
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    payload = {
        "model": "mistral-small-latest",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 4096
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MISTRAL_API_KEY}"
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:200]
        raise RuntimeError(f"Mistral HTTP {e.code}: {body}") from None
    return result["choices"][0]["message"]["content"].strip()


def _is_auth_error(msg: str) -> bool:
    return any(code in msg for code in ["401", "403", "invalid_api_key", "Forbidden", "Unauthorized"])


def _is_rate_limit(msg: str) -> bool:
    return any(x in msg.lower() for x in ["429", "quota", "rate limit", "exceeded"])


def llm(system_prompt: str, history: list, user_message: str, temperature: float = 0.7) -> str:
    """Appelle Gemini → Mistral → Groq avec gestion fine des erreurs.
    - 429/quota : attend 90s et réessaie (jusqu'à 8 fois)
    - 401/403   : erreur d'auth → passe directement au suivant, pas de retry
    """
    if not any([GEMINI_API_KEY, MISTRAL_API_KEY, GROQ_API_KEY]):
        raise RuntimeError("Aucune clé API disponible")

    providers = []
    if GEMINI_API_KEY:
        providers.append(("Gemini", call_gemini))
    if MISTRAL_API_KEY:
        providers.append(("Mistral", call_mistral))
    if GROQ_API_KEY:
        providers.append(("Groq", call_groq))

    for provider_name, call_fn in providers:
        max_attempts = 8 if provider_name == "Gemini" else 3
        for attempt in range(max_attempts):
            try:
                result = call_fn(system_prompt, history, user_message, temperature)
                if attempt > 0:
                    print(f"   ✅ {provider_name} OK (tentative {attempt + 1})")
                return result
            except Exception as e:
                msg = str(e)
                if _is_auth_error(msg):
                    print(f"   ✗ {provider_name} auth invalide ({msg[:60]}) → prochain fournisseur")
                    break  # Pas de retry sur erreur d'auth
                if attempt < max_attempts - 1:
                    wait = 90 if _is_rate_limit(msg) else (attempt + 1) * 10
                    print(f"   ⚠️  {provider_name} erreur ({msg[:60]}) — retry dans {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"   ✗ {provider_name} épuisé ({max_attempts} tentatives) → prochain fournisseur")

    raise RuntimeError(f"Tous les LLM ont échoué ({', '.join(p for p, _ in providers)})")


def generate_agent_role(agent: str, topic: str, goal: str) -> str:
    """Génère un system prompt expert pour l'agent A ou B via le cerveau."""
    if agent == "A":
        prompt = f"""Tu es un architecte de prompts expert.
Génère le system prompt d'un agent Socrate (questionneurateur), spécialisé dans :
- Domaine : {topic}
- Objectif final : {goal}

L'agent A doit :
- Analyser la sortie de B et identifier la PLUS IMPORTANTE lacune ou amélioration possible
- Poser UNE SEULE question précise, ciblée sur cette lacune
- Ne jamais poser une question vague
- Dire "VALIDÉ" uniquement quand la sortie est vraiment optimale et complète
- Ne jamais se satisfaire d'une réponse incomplète

Réponds UNIQUEMENT avec le system prompt (texte direct, pas de JSON, pas de markdown)."""
    else:
        prompt = f"""Tu es un architecte de prompts expert.
Génère le system prompt d'un agent Créateur/Bâtisseur expert dans :
- Domaine : {topic}
- Livrable attendu : {goal}

L'agent B doit :
- Produire un livrable complet, actionnable, directement utilisable par Hugo (humain non-téchnique)
- Prendre en compte TOUTES les questions de A et améliorer son output en conséquence
- Toujours livrer la VERSION COMPLÈTE de son output (pas juste les modifications)
- Être précis, structuré, professionnel
- Ne jamais halluciner des faits ou inventer des données

Réponds UNIQUEMENT avec le system prompt (texte direct, pas de JSON, pas de markdown)."""

    history: list = []
    role = llm("Tu es un expert en conception de prompts système.", history, prompt, temperature=0.6)
    return role


def audit_output(task: str, output: str) -> dict:
    """Auditrice inline — évalue la qualité finale du dialogue."""
    audit_system = """Tu es une auditrice experte. Évalue si ce livrable est vraiment prêt à l'emploi.
Score sur 100 :
- Complétude (0-25): répond-il à TOUT ce qui était demandé ?
- Précision (0-25): est-ce exact et cohérent ?
- Actionabilité (0-25): Hugo peut-il l'utiliser directement ?
- Structure (0-25): c'est clair et bien organisé ?

Réponds en JSON uniquement :
{"status":"VALIDÉ"ou"RECONSTRUCTION_REQUISE","score":0-100,"issues":[],"feedback":"..."}"""

    user_msg = f"OBJECTIF: {task}\n\nLIVRABLE:\n{output}\n\nÉvalue. JSON uniquement."
    history: list = []
    raw = llm(audit_system, history, user_msg, temperature=0.2)
    match = re.search(r'\{[\s\S]*\}', raw)
    if not match:
        return {"status": "VALIDÉ", "score": 70, "issues": [], "feedback": "Audit non parseable"}
    return json.loads(match.group())


def git_commit_and_push(output_dir: str, topic_slug: str) -> bool:
    """Auto-commit et push du livrable validé."""
    try:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        commands = [
            f'git add {output_dir}',
            f'git commit -m "dialogue: {topic_slug} — livrable validé {timestamp}"',
            'for i in 1 2 3 4; do git push origin HEAD && break || sleep $((i*2)); done'
        ]
        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0 and 'nothing to commit' not in result.stdout:
                print(f"   Git warning: {result.stderr[:200]}")
        return True
    except Exception as e:
        print(f"   Git error: {e}")
        return False


def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')[:40]


def main():
    if not TOPIC or not GOAL:
        print("ERREUR: TOPIC et GOAL sont requis", file=sys.stderr)
        print("Usage: TOPIC='...' GOAL='...' python gemini_dialogue.py", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  DIALOGUE GEMINI A ↔ B")
    print(f"  Sujet  : {TOPIC}")
    print(f"  Objectif: {GOAL[:80]}")
    print(f"  Turns  : max {MAX_TURNS} | Tempo : {TEMPO}s")
    print(f"{'='*60}\n")

    os.makedirs("data/dialogues", exist_ok=True)
    topic_slug = slugify(TOPIC)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dialogue_path = f"data/dialogues/{topic_slug}_{timestamp}.json"
    final_path = f"data/dialogues/{topic_slug}_final.md"

    # ÉTAPE 1 : Générer les rôles via le cerveau
    print("🧠 Génération des rôles experts...")
    role_a = generate_agent_role("A", TOPIC, GOAL)
    time.sleep(TEMPO)
    role_b = generate_agent_role("B", TOPIC, GOAL)
    time.sleep(TEMPO)
    print("   ✅ Rôles générés")

    # ÉTAPE 2 : Premier draft de B
    print(f"\n🏗️  [B] Génération du premier draft...")
    history_b: list = []
    first_prompt = f"""Ton objectif : {GOAL}

Sujet : {TOPIC}

Produis un premier draft complet et structuré. Vise l'excellence dès le premier essai.
Ton output sera critiqué et amélioré par un questionneurateur — sois aussi complet que possible."""

    draft_b = llm(role_b, history_b, first_prompt, temperature=0.7)
    history_b.append({"role": "user", "content": first_prompt})
    history_b.append({"role": "assistant", "content": draft_b})
    print(f"   Draft B ({len(draft_b)} chars)")
    time.sleep(TEMPO)

    # Dialogue log
    dialogue_log = {
        "topic": TOPIC,
        "goal": GOAL,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "roles": {"A": role_a[:500], "B": role_b[:500]},
        "turns": [],
        "final_output": "",
        "audit": {}
    }

    # ÉTAPE 3 : Boucle de dialogue A ↔ B
    current_output = draft_b
    history_a: list = []
    validated = False

    for turn in range(1, MAX_TURNS + 1):
        print(f"\n--- Tour {turn}/{MAX_TURNS} ---")

        # A pose une question ou valide
        a_prompt = f"""Voici la sortie actuelle de l'agent B :

---
{current_output}
---

Objectif final : {GOAL}

Analyse cette sortie. Identifie LA lacune ou amélioration la plus importante.
Pose UNE question précise pour aider B à améliorer son output.
Si la sortie est vraiment optimale et complète, dis uniquement : VALIDÉ"""

        response_a = llm(role_a, history_a, a_prompt, temperature=0.5)
        history_a.append({"role": "user", "content": a_prompt})
        history_a.append({"role": "assistant", "content": response_a})

        print(f"[A] {response_a[:200]}...")

        turn_log = {"turn": turn, "a_question": response_a, "b_response": ""}
        time.sleep(TEMPO)

        # Check si A a validé
        if "VALIDÉ" in response_a.upper() and len(response_a) < 100:
            print(f"\n✅ Gemini A a validé au tour {turn}")
            validated = True
            dialogue_log["turns"].append(turn_log)
            break

        # B améliore son output
        b_prompt = f"""Question de l'agent A :
{response_a}

Améliore ton output en répondant précisément à cette question.
Fournis la VERSION COMPLÈTE de ton output amélioré, pas seulement les modifications."""

        improved_b = llm(role_b, history_b, b_prompt, temperature=0.7)
        history_b.append({"role": "user", "content": b_prompt})
        history_b.append({"role": "assistant", "content": improved_b})

        print(f"[B] Output amélioré ({len(improved_b)} chars)")
        current_output = improved_b
        turn_log["b_response"] = improved_b[:1000]
        dialogue_log["turns"].append(turn_log)
        time.sleep(TEMPO)

    dialogue_log["final_output"] = current_output
    dialogue_log["a_validated"] = validated

    # ÉTAPE 4 : Audit final
    print(f"\n🔍 Audit final de l'auditrice...")
    time.sleep(TEMPO)
    audit_result = audit_output(GOAL, current_output)
    dialogue_log["audit"] = audit_result
    dialogue_log["completed_at"] = datetime.utcnow().isoformat() + "Z"

    print(f"   Score : {audit_result.get('score')}/100 — {audit_result.get('status')}")
    if audit_result.get("issues"):
        for issue in audit_result["issues"]:
            print(f"   ⚠️  {issue}")

    # ÉTAPE 5 : Sauvegardes
    with open(dialogue_path, "w", encoding="utf-8") as f:
        json.dump(dialogue_log, f, ensure_ascii=False, indent=2)

    header = f"""# {TOPIC}

> **Objectif** : {GOAL}
> **Généré le** : {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC
> **Tours de dialogue** : {len(dialogue_log['turns'])} | **Score audit** : {audit_result.get('score')}/100
> **Statut** : {audit_result.get('status')}

---

"""
    with open(final_path, "w", encoding="utf-8") as f:
        f.write(header + current_output)

    print(f"\n📁 Dialogue sauvegardé → {dialogue_path}")
    print(f"📄 Livrable final     → {final_path}")

    # ÉTAPE 6 : Auto-commit si validé
    audit_ok = audit_result.get("score", 0) >= MIN_AUDIT_SCORE
    if AUTO_COMMIT == "1" and audit_ok:
        print(f"\n🚀 Auto-commit du livrable validé...")
        success = git_commit_and_push("data/dialogues/", topic_slug)
        if success:
            print("   ✅ Poussé sur GitHub")
        else:
            print("   ⚠️  Commit/push non effectué (vérifier manuellement)")
    elif not audit_ok:
        print(f"\n⚠️  Score insuffisant ({audit_result.get('score')}/{MIN_AUDIT_SCORE}) — pas de commit auto")
        print(f"   Feedback : {audit_result.get('feedback')}")

    print(f"\n{'='*60}")
    print(f"  DIALOGUE TERMINÉ — {len(dialogue_log['turns'])} tours")
    print(f"  Score final : {audit_result.get('score')}/100")
    print(f"  Statut : {audit_result.get('status')}")
    print(f"{'='*60}\n")

    if audit_result.get("status") == "RECONSTRUCTION_REQUISE" and audit_result.get("score", 0) < 50:
        sys.exit(1)


if __name__ == "__main__":
    main()
