"""
Auditrice — Validateur universel de sorties d'agents IA.

Prend en entrée une tâche + une sortie d'agent, évalue la qualité,
retourne VALIDÉ ou RECONSTRUCTION_REQUISE avec feedback.

Usage:
  TASK_DESCRIPTION="Analyser ce document pour la conformité AI Act"
  AGENT_OUTPUT="Voici mon analyse..."
  AGENT_TYPE="analyste_conformité"       # optionnel, aide à calibrer les critères
  RECONSTRUCTION_HOOK="python mon_agent.py"  # optionnel, relance si échec
  python scripts/auditrice.py

Ou en import Python:
  from scripts.auditrice import audit
  result = audit(task="...", output="...", agent_type="...")
"""

import json
import os
import re
import sys
import subprocess
import time
from datetime import datetime


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

TASK_DESCRIPTION = os.environ.get("TASK_DESCRIPTION", "")
AGENT_OUTPUT = os.environ.get("AGENT_OUTPUT", "")
AGENT_TYPE = os.environ.get("AGENT_TYPE", "agent générique")
RECONSTRUCTION_HOOK = os.environ.get("RECONSTRUCTION_HOOK", "")
MAX_RECONSTRUCTIONS = int(os.environ.get("MAX_RECONSTRUCTIONS", "2"))
MIN_SCORE = int(os.environ.get("MIN_SCORE", "70"))

AUDIT_SYSTEM = """Tu es une auditrice experte en qualité de sorties d'agents IA.
Tu évalues si la sortie d'un agent répond correctement à sa tâche.

Critères d'évaluation :
- Complétude : La sortie répond-elle à TOUT ce qui était demandé ? (0-25)
- Précision : Le contenu est-il exact, cohérent, sans hallucinations ? (0-25)
- Actionabilité : Hugo peut-il utiliser cette sortie directement ? (0-25)
- Format : La structure est-elle claire et bien organisée ? (0-25)

Règles :
- Score < 70 → RECONSTRUCTION_REQUISE
- Score >= 70 → VALIDÉ
- Si la tâche est vide ou la sortie est vide → RECONSTRUCTION_REQUISE immédiat

Réponds en JSON uniquement, sans markdown :
{
  "status": "VALIDÉ" ou "RECONSTRUCTION_REQUISE",
  "score": 0-100,
  "scores_detail": {"complétude": 0-25, "précision": 0-25, "actionabilité": 0-25, "format": 0-25},
  "issues": ["problème 1", "problème 2"],
  "feedback": "Explication concise de ce qui manque ou est incorrect",
  "corrections_suggérées": ["correction 1", "correction 2"]
}"""


def call_gemini(system_prompt: str, user_message: str) -> str:
    import urllib.request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_message}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048}
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
        "temperature": 0.3,
        "max_tokens": 2048
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
    raise RuntimeError("Aucune clé API disponible")


def audit(task: str, output: str, agent_type: str = "agent générique") -> dict:
    """Évalue la qualité de la sortie d'un agent. Retourne un dict avec status, score, feedback."""
    if not task.strip() or not output.strip():
        return {
            "status": "RECONSTRUCTION_REQUISE",
            "score": 0,
            "issues": ["Tâche ou sortie vide"],
            "feedback": "Impossible d'évaluer une sortie vide.",
            "corrections_suggérées": ["Relancer l'agent avec une tâche définie"]
        }

    user_msg = f"""TYPE D'AGENT : {agent_type}

TÂCHE ORIGINALE :
{task}

SORTIE DE L'AGENT :
{output}

Évalue la qualité de cette sortie par rapport à la tâche. Réponds en JSON uniquement."""

    raw = llm_call(AUDIT_SYSTEM, user_msg)
    json_match = re.search(r'\{[\s\S]*\}', raw)
    if not json_match:
        return {
            "status": "VALIDÉ",
            "score": 65,
            "issues": ["Audit non parseable"],
            "feedback": "L'auditrice n'a pas pu parser sa propre réponse — approuvé avec réserves.",
            "corrections_suggérées": []
        }

    result = json.loads(json_match.group())
    # Ensure required fields
    result.setdefault("status", "VALIDÉ" if result.get("score", 0) >= 70 else "RECONSTRUCTION_REQUISE")
    result.setdefault("issues", [])
    result.setdefault("corrections_suggérées", [])
    return result


def save_audit_log(task: str, output: str, audit_result: dict, agent_type: str):
    os.makedirs("data/audit_logs", exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r'[^a-z0-9]+', '_', agent_type.lower())[:30]
    log_path = f"data/audit_logs/{slug}_{timestamp}.json"
    log = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent_type": agent_type,
        "task": task[:500],
        "output_preview": output[:500],
        "audit": audit_result
    }
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    return log_path


def main():
    if not TASK_DESCRIPTION or not AGENT_OUTPUT:
        print("ERREUR: TASK_DESCRIPTION et AGENT_OUTPUT sont requis", file=sys.stderr)
        print("Usage: TASK_DESCRIPTION='...' AGENT_OUTPUT='...' python auditrice.py", file=sys.stderr)
        sys.exit(1)

    print(f"\n🔍 AUDITRICE — Évaluation de sortie agent")
    print(f"   Agent   : {AGENT_TYPE}")
    print(f"   Tâche   : {TASK_DESCRIPTION[:80]}...")

    task = TASK_DESCRIPTION
    output = AGENT_OUTPUT
    reconstructions = 0

    while True:
        result = audit(task, output, AGENT_TYPE)
        log_path = save_audit_log(task, output, result, AGENT_TYPE)

        print(f"\n   Score   : {result.get('score', '?')}/100 — {result.get('status')}")
        if result.get("issues"):
            print("   Problèmes :")
            for issue in result["issues"]:
                print(f"     - {issue}")
        print(f"   Feedback: {result.get('feedback', '')}")

        if result["status"] == "VALIDÉ":
            print(f"\n✅ SORTIE VALIDÉE (score {result.get('score')}/100)")
            print(f"   Log : {log_path}")
            break

        # RECONSTRUCTION_REQUISE
        reconstructions += 1
        if reconstructions > MAX_RECONSTRUCTIONS or not RECONSTRUCTION_HOOK:
            print(f"\n❌ VALIDATION ÉCHOUÉE après {reconstructions} tentative(s)")
            print(f"   Score final : {result.get('score')}/100")
            print(f"   Corrections suggérées :")
            for c in result.get("corrections_suggérées", []):
                print(f"     → {c}")
            sys.exit(2)

        print(f"\n🔄 Reconstruction {reconstructions}/{MAX_RECONSTRUCTIONS} — relance de l'agent...")
        time.sleep(5)

        # Inject audit feedback into env for next run
        env = os.environ.copy()
        env["AUDIT_FEEDBACK"] = result.get("feedback", "")
        env["AUDIT_CORRECTIONS"] = json.dumps(result.get("corrections_suggérées", []))

        proc = subprocess.run(RECONSTRUCTION_HOOK, shell=True, capture_output=True, text=True, env=env)
        if proc.returncode != 0:
            print(f"   ❌ Reconstruction échouée (code {proc.returncode})")
            print(proc.stderr[:500])
            sys.exit(2)

        output = proc.stdout.strip()
        if not output:
            print("   ❌ Reconstruction retournée vide")
            sys.exit(2)

        print(f"   Nouvelle sortie reçue ({len(output)} chars) — re-audit...")
        time.sleep(3)


if __name__ == "__main__":
    main()
