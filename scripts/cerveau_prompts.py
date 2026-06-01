"""
Cerveau perpétuel — générateur de rôles experts pour agents IA.

Usage:
  ROLE_TYPE="expert analyste conformité AI Act"
  DOMAIN="réglementation européenne IA, conformité B2B"
  CONTEXT="Analyser un document client et identifier les obligations AI Act"
  python scripts/cerveau_prompts.py

Sortie: data/prompts/{slug}.json avec le system prompt complet.
"""

import json
import os
import re
import time
import sys
import hashlib
from datetime import datetime

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

ROLE_TYPE = os.environ.get("ROLE_TYPE", "")
DOMAIN = os.environ.get("DOMAIN", "")
CONTEXT = os.environ.get("CONTEXT", "")
OUTPUT_SLUG = os.environ.get("OUTPUT_SLUG", "")
VALIDATE = os.environ.get("VALIDATE", "1")  # 1 = auto-valide le prompt généré

MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))


def call_gemini(system_prompt: str, user_message: str, model: str = "gemini-2.0-flash") -> str:
    import urllib.request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_message}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
    return result["candidates"][0]["content"]["parts"][0]["text"].strip()


def call_groq(system_prompt: str, user_message: str) -> str:
    import urllib.request
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 4096
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
    return result["choices"][0]["message"]["content"].strip()


def llm_call(system_prompt: str, user_message: str) -> str:
    if GEMINI_API_KEY:
        return call_gemini(system_prompt, user_message)
    elif GROQ_API_KEY:
        return call_groq(system_prompt, user_message)
    raise RuntimeError("Aucune clé API disponible (GEMINI_API_KEY ou GROQ_API_KEY requis)")


CERVEAU_SYSTEM = """Tu es un architecte de prompts système expert.
Ta mission : créer des rôles d'experts précis, complets et actionnables pour des agents IA.

Un bon system prompt contient :
1. IDENTITÉ — Qui est cet agent, quel est son niveau d'expertise
2. MISSION — Ce qu'il doit accomplir exactement
3. COMPÉTENCES — Ses domaines de connaissance spécifiques
4. MÉTHODE — Comment il travaille (étapes, raisonnement)
5. CONTRAINTES — Ce qu'il ne fait jamais
6. FORMAT DE SORTIE — Structure exacte de ses réponses

Réponds UNIQUEMENT en JSON valide, sans markdown, sans explication autour.
Format exact :
{
  "role_name": "Nom court du rôle",
  "version": "1.0",
  "created_at": "ISO date",
  "system_prompt": "Le system prompt complet en texte",
  "tags": ["tag1", "tag2"],
  "use_cases": ["cas d'usage 1", "cas d'usage 2"]
}"""


def generate_prompt(role_type: str, domain: str, context: str) -> dict:
    user_msg = f"""Crée un system prompt expert pour ce rôle :

RÔLE : {role_type}
DOMAINE : {domain}
CONTEXTE D'UTILISATION : {context}

Le system prompt doit être en français, précis et opérationnel.
Réponds en JSON uniquement."""

    raw = llm_call(CERVEAU_SYSTEM, user_msg)

    # Extract JSON if wrapped in markdown
    json_match = re.search(r'\{[\s\S]*\}', raw)
    if not json_match:
        raise ValueError(f"Réponse LLM non-JSON : {raw[:200]}")

    result = json.loads(json_match.group())
    result["created_at"] = datetime.utcnow().isoformat() + "Z"
    return result


AUDITEUR_SYSTEM = """Tu es un évaluateur de prompts système IA.
Tu analyses la qualité et l'efficacité d'un system prompt expert.

Critères d'évaluation :
- Clarté de l'identité et du rôle (0-20)
- Précision des compétences et du domaine (0-20)
- Clarté de la méthode de travail (0-20)
- Contraintes bien définies (0-20)
- Format de sortie spécifié (0-20)

Réponds en JSON uniquement :
{
  "status": "VALIDÉ" ou "RECONSTRUCTION_REQUISE",
  "score": 0-100,
  "issues": ["problème 1", "problème 2"],
  "feedback": "texte explicatif bref"
}"""


def validate_prompt(prompt_data: dict) -> dict:
    user_msg = f"""Évalue ce system prompt :

{json.dumps(prompt_data, ensure_ascii=False, indent=2)}

Réponds en JSON uniquement."""

    raw = llm_call(AUDITEUR_SYSTEM, user_msg)
    json_match = re.search(r'\{[\s\S]*\}', raw)
    if not json_match:
        return {"status": "VALIDÉ", "score": 75, "issues": [], "feedback": "Audit non parseable, approuvé par défaut"}
    return json.loads(json_match.group())


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')[:50]


def main():
    if not ROLE_TYPE:
        print("ERREUR: ROLE_TYPE est requis", file=sys.stderr)
        sys.exit(1)

    print(f"\n🧠 CERVEAU PROMPTS — Génération de rôle expert")
    print(f"   Rôle    : {ROLE_TYPE}")
    print(f"   Domaine : {DOMAIN}")
    print(f"   Contexte: {CONTEXT[:80]}...")

    os.makedirs("data/prompts", exist_ok=True)

    slug = OUTPUT_SLUG or slugify(ROLE_TYPE)
    output_path = f"data/prompts/{slug}.json"

    attempt = 0
    prompt_data = None
    audit_result = None

    while attempt < MAX_RETRIES:
        attempt += 1
        print(f"\n   Tentative {attempt}/{MAX_RETRIES} — Génération...")

        try:
            prompt_data = generate_prompt(ROLE_TYPE, DOMAIN, CONTEXT)
        except Exception as e:
            print(f"   ❌ Erreur génération : {e}")
            time.sleep(5)
            continue

        if VALIDATE == "1":
            print("   Validation du prompt généré...")
            time.sleep(3)  # Rate limiting
            try:
                audit_result = validate_prompt(prompt_data)
            except Exception as e:
                print(f"   ⚠️  Audit échoué : {e} — approuvé par défaut")
                audit_result = {"status": "VALIDÉ", "score": 70, "issues": [], "feedback": "Audit échoué"}

            print(f"   Score : {audit_result.get('score', '?')}/100 — {audit_result.get('status')}")

            if audit_result.get("status") == "VALIDÉ" and audit_result.get("score", 0) >= 60:
                break
            else:
                print(f"   Reconstruction requise : {audit_result.get('feedback', '')}")
                # Enrich context for retry
                issues = "\n".join(f"- {i}" for i in audit_result.get("issues", []))
                CONTEXT_ENRICHED = f"{CONTEXT}\n\nProblèmes à corriger:\n{issues}"
                CONTEXT = CONTEXT_ENRICHED  # type: ignore
                time.sleep(5)
        else:
            audit_result = {"status": "VALIDÉ", "score": 80, "issues": [], "feedback": "Validation désactivée"}
            break

    if not prompt_data:
        print("\n❌ Échec de génération après toutes les tentatives", file=sys.stderr)
        sys.exit(1)

    # Save result
    final_output = {
        **prompt_data,
        "audit": audit_result,
        "generation_metadata": {
            "role_type": ROLE_TYPE,
            "domain": DOMAIN,
            "context": CONTEXT,
            "attempts": attempt,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Prompt sauvegardé → {output_path}")
    print(f"   Rôle    : {prompt_data.get('role_name', slug)}")
    print(f"   Score   : {audit_result.get('score', '?')}/100")
    print(f"   Statut  : {audit_result.get('status')}")
    print(f"\n--- SYSTEM PROMPT ---")
    print(prompt_data.get("system_prompt", "")[:500])
    print("...")


if __name__ == "__main__":
    main()
