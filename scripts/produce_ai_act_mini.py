"""
Générateur de mini-audit AI Act GRATUIT — outil d'acquisition client.

Génère un aperçu de conformité personnalisé (1-2 pages) pour une entreprise cible.
Hugo envoie ce mini-audit à un prospect pour démontrer la valeur.
Le prospect voit ce qu'il rate → veut le rapport complet → paie €990.

Usage:
  COMPANY_NAME="Acme SAS"
  COMPANY_SECTOR="Ressources Humaines"
  COMPANY_AI_USE="Outil de scoring de CV automatisé"
  python scripts/produce_ai_act_mini.py

Sortie: data/ai_act/mini_audits/{slug}_{timestamp}.md
"""

import json
import os
import re
import sys
import time
from datetime import datetime

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

COMPANY_NAME = os.environ.get("COMPANY_NAME", "")
COMPANY_SECTOR = os.environ.get("COMPANY_SECTOR", "")
COMPANY_AI_USE = os.environ.get("COMPANY_AI_USE", "")
COMPANY_SIZE = os.environ.get("COMPANY_SIZE", "PME")


def llm_call(system: str, user: str) -> str:
    import urllib.request
    for attempt in range(3):
        try:
            if GEMINI_API_KEY:
                url = ("https://generativelanguage.googleapis.com/v1beta/models/"
                       "gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY)
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": user}]}],
                    "systemInstruction": {"parts": [{"text": system}]},
                    "generationConfig": {"temperature": 0.4, "maxOutputTokens": 3000}
                }
                req = urllib.request.Request(
                    url, json.dumps(payload).encode(),
                    {"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=60) as resp:
                    return json.loads(resp.read())["candidates"][0]["content"]["parts"][0]["text"].strip()
            elif GROQ_API_KEY:
                url = "https://api.groq.com/openai/v1/chat/completions"
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "system", "content": system},
                                 {"role": "user", "content": user}],
                    "temperature": 0.4, "max_tokens": 3000
                }
                req = urllib.request.Request(
                    url, json.dumps(payload).encode(),
                    {"Content-Type": "application/json",
                     "Authorization": f"Bearer {GROQ_API_KEY}"}, method="POST")
                with urllib.request.urlopen(req, timeout=60) as resp:
                    return json.loads(resp.read())["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt < 2:
                time.sleep((attempt + 1) * 8)
            else:
                raise
    raise RuntimeError("API calls failed")


EXPERT_SYSTEM = """Tu es un expert EU AI Act (Règlement 2024/1689).
Tu écris des analyses courtes, percutantes et sans jargon inutile.
Ton objectif : montrer à un dirigeant d'entreprise CE QU'IL RISQUE concrètement.
Utilise des exemples réels et des chiffres de sanctions précis quand c'est pertinent."""


def generate_mini_audit(company_name: str, sector: str, ai_use: str, size: str) -> str:
    user = f"""Génère un mini-audit EU AI Act GRATUIT pour cette entreprise.

**Entreprise** : {company_name}
**Secteur** : {sector}
**Utilisation IA** : {ai_use}
**Taille** : {size}

Ce mini-audit doit :
1. Identifier le niveau de risque probable (sans questionnaire complet, sur la base des infos)
2. Citer 2-3 obligations AI Act spécifiques qui s'appliquent probablement
3. Pointer 1-2 risques concrets (avec montant de sanction potentielle)
4. Se terminer par une accroche vers l'audit complet

Format : document professionnel, 300-400 mots, avec sections claires.
Commence par : "Analyse préliminaire EU AI Act — {company_name}"

Sois percutant. Ce document doit faire prendre conscience du risque, pas faire peur inutilement."""

    return llm_call(EXPERT_SYSTEM, user)


def generate_outreach_email(company_name: str, mini_audit: str, sector: str) -> str:
    """Génère l'email d'accompagnement que Hugo copie-colle."""
    user = f"""Génère l'email d'accompagnement que Hugo envoie avec ce mini-audit AI Act.

Destinataire : décideur de {company_name} (secteur {sector})
Mini-audit joint : ci-dessous

Email doit :
- Sujet accrocheur (max 60 caractères)
- Corps de 80-100 mots maximum
- Personnalisé pour {company_name}
- Proposer l'audit complet à €990 avec délai 48h
- Call-to-action clair (pas de lien, juste "répondez à cet email")
- Ton professionnel mais humain (pas de corporate speak)

Commencer par "Sujet: " puis une ligne vide puis le corps.

Mini-audit :
{mini_audit[:500]}"""

    return llm_call(EXPERT_SYSTEM, user)


def main():
    if not COMPANY_NAME:
        # Demo mode
        global COMPANY_NAME, COMPANY_SECTOR, COMPANY_AI_USE, COMPANY_SIZE
        COMPANY_NAME = "Exemple Corp SAS"
        COMPANY_SECTOR = "Finance / Crédit"
        COMPANY_AI_USE = "Score automatique d'octroi de crédit pour clients PME"
        COMPANY_SIZE = "80 employés"
        print("   Mode démo — entreprise exemple")

    print(f"\n🔍 MINI-AUDIT AI ACT — {COMPANY_NAME}")
    print(f"   Secteur : {COMPANY_SECTOR}")
    print(f"   Usage IA: {COMPANY_AI_USE}")

    os.makedirs("data/ai_act/mini_audits", exist_ok=True)
    slug = re.sub(r'[^a-z0-9]+', '_', COMPANY_NAME.lower())[:30]
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")

    print("\n   Génération du mini-audit...")
    mini_audit = generate_mini_audit(COMPANY_NAME, COMPANY_SECTOR, COMPANY_AI_USE, COMPANY_SIZE)
    time.sleep(4)

    print("   Génération de l'email d'accompagnement...")
    email_text = generate_outreach_email(COMPANY_NAME, mini_audit, COMPANY_SECTOR)

    # Save
    output_path = f"data/ai_act/mini_audits/{slug}_{timestamp}.md"
    email_path = f"data/ai_act/mini_audits/{slug}_{timestamp}_email.txt"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Mini-Audit EU AI Act — {COMPANY_NAME}\n\n")
        f.write(f"> Généré le {datetime.utcnow().strftime('%Y-%m-%d')}\n\n")
        f.write("---\n\n")
        f.write(mini_audit)

    with open(email_path, "w", encoding="utf-8") as f:
        f.write(f"# Email d'accompagnement — {COMPANY_NAME}\n\n")
        f.write(email_text)

    print(f"\n✅ Mini-audit → {output_path}")
    print(f"✅ Email      → {email_path}")
    print("\n" + "="*50)
    print("À FAIRE PAR HUGO :")
    print("1. Lire le mini-audit (vérifier 2 min)")
    print("2. Copier l'email + joindre le PDF")
    print("3. Envoyer à [décideur @entreprise]")
    print("="*50)
    print("\n--- EMAIL À COPIER ---")
    print(email_text)


if __name__ == "__main__":
    main()
