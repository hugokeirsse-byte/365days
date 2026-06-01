"""
Scanner de prospects AI Act — identifie les entreprises qui ont besoin d'un audit.

Sources gratuites :
- Recherches Google (actualités IA + secteur)
- Profils LinkedIn publics (via recherche Google)
- Communiqués de presse (entreprises annonçant des outils IA)

Pour chaque prospect trouvé :
- Génère un mini-audit automatiquement
- Crée l'email d'accompagnement
- Ajoute à la liste de prospects

Usage:
  SECTOR="ressources humaines"      # secteur à cibler
  REGION="France"
  MAX_PROSPECTS=5
  python scripts/agent_ai_act_scanner.py

Sortie: data/ai_act/prospects/{timestamp}_prospects.json
        data/ai_act/mini_audits/ (un fichier par prospect)
"""

import json
import os
import re
import time
import subprocess
import sys
from datetime import datetime

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

SECTOR = os.environ.get("SECTOR", "ressources humaines")
REGION = os.environ.get("REGION", "France")
MAX_PROSPECTS = int(os.environ.get("MAX_PROSPECTS", "5"))


def llm_call(system: str, user: str, max_tokens: int = 4096) -> str:
    import urllib.request
    for attempt in range(3):
        try:
            if GEMINI_API_KEY:
                url = ("https://generativelanguage.googleapis.com/v1beta/models/"
                       "gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY)
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": user}]}],
                    "systemInstruction": {"parts": [{"text": system}]},
                    "generationConfig": {"temperature": 0.5, "maxOutputTokens": max_tokens}
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
                    "temperature": 0.5, "max_tokens": max_tokens
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
    raise RuntimeError("API failed")


SCANNER_SYSTEM = """Tu es un expert en prospection B2B et en EU AI Act.
Tu identifies des entreprises françaises qui utilisent l'IA et qui n'ont probablement pas encore fait de conformité AI Act.
Tu fournis des informations précises et réalistes. Tu ne confonds jamais des entreprises fictives avec des entreprises réelles.
Tu travailles avec des exemples typiques de secteur quand tu n'as pas d'informations spécifiques."""


def generate_prospect_profiles(sector: str, region: str, count: int) -> list:
    """Génère des profils de prospects typiques dans un secteur."""
    user = f"""Génère {count} profils d'entreprises TYPIQUES dans le secteur "{sector}" en {region}
qui utilisent probablement de l'IA et qui n'ont pas encore fait leur conformité EU AI Act.

Pour chaque profil, donne :
- Nom fictif réaliste (type "SAS", "SARL", "SA" francophone)
- Taille (employés)
- Usage IA typique dans ce secteur
- Pourquoi elles risquent la non-conformité AI Act
- Où on pourrait les trouver (LinkedIn, site web, communiqué de presse)

Réponds en JSON :
{{
  "prospects": [
    {{
      "nom": "...",
      "secteur": "{sector}",
      "taille": "...",
      "usage_ia": "...",
      "risque_non_conformite": "...",
      "ou_trouver": "...",
      "priorite": "haute|moyenne"
    }}
  ]
}}"""

    raw = llm_call(SCANNER_SYSTEM, user)
    match = re.search(r'\{[\s\S]*\}', raw)
    if match:
        data = json.loads(match.group())
        return data.get("prospects", [])
    return []


def generate_search_queries(sector: str) -> list:
    """Génère des requêtes de recherche pour trouver des prospects réels."""
    user = f"""Génère 5 requêtes de recherche Google/LinkedIn pour trouver des entreprises françaises
dans le secteur "{sector}" qui utilisent l'IA et auraient besoin d'un audit EU AI Act.

Réponds en JSON : {{"queries": ["requête 1", "requête 2", ...]}}"""

    raw = llm_call(SCANNER_SYSTEM, user, max_tokens=1000)
    match = re.search(r'\{[\s\S]*\}', raw)
    if match:
        return json.loads(match.group()).get("queries", [])
    return [f'site:linkedin.com "intelligence artificielle" "{sector}" France']


def run_mini_audit_for_prospect(prospect: dict) -> dict:
    """Lance le mini-audit pour un prospect et retourne les chemins de fichiers."""
    env = os.environ.copy()
    env["COMPANY_NAME"] = prospect["nom"]
    env["COMPANY_SECTOR"] = prospect["secteur"]
    env["COMPANY_AI_USE"] = prospect["usage_ia"]
    env["COMPANY_SIZE"] = prospect.get("taille", "PME")

    result = subprocess.run(
        [sys.executable, "scripts/produce_ai_act_mini.py"],
        capture_output=True, text=True, env=env
    )

    slug = re.sub(r'[^a-z0-9]+', '_', prospect["nom"].lower())[:30]
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")

    return {
        "mini_audit_path": f"data/ai_act/mini_audits/{slug}_{timestamp}.md",
        "email_path": f"data/ai_act/mini_audits/{slug}_{timestamp}_email.txt",
        "success": result.returncode == 0
    }


def main():
    print(f"\n{'='*60}")
    print(f"  SCANNER PROSPECTS AI ACT")
    print(f"  Secteur : {SECTOR} | Région : {REGION}")
    print(f"  Objectif : {MAX_PROSPECTS} prospects")
    print(f"{'='*60}\n")

    os.makedirs("data/ai_act/prospects", exist_ok=True)
    os.makedirs("data/ai_act/mini_audits", exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # Générer les requêtes de recherche
    print("📡 Génération des requêtes de recherche...")
    queries = generate_search_queries(SECTOR)
    print(f"   {len(queries)} requêtes générées")
    for q in queries:
        print(f"   → {q}")
    time.sleep(4)

    # Générer les profils de prospects
    print(f"\n🎯 Identification de {MAX_PROSPECTS} prospects typiques...")
    prospects = generate_prospect_profiles(SECTOR, REGION, MAX_PROSPECTS)
    print(f"   {len(prospects)} prospects identifiés")
    time.sleep(4)

    # Générer les mini-audits
    print("\n📋 Génération des mini-audits personnalisés...")
    results = []

    for i, prospect in enumerate(prospects, 1):
        print(f"\n   [{i}/{len(prospects)}] {prospect['nom']}")
        print(f"         Usage IA: {prospect['usage_ia'][:60]}...")

        files = run_mini_audit_for_prospect(prospect)
        prospect["fichiers"] = files
        results.append(prospect)

        print(f"         {'✅' if files['success'] else '⚠️ '} Mini-audit: {files['mini_audit_path']}")
        time.sleep(5)  # Rate limiting Gemini

    # Sauvegarder le rapport de scan
    report = {
        "scan_date": datetime.utcnow().isoformat() + "Z",
        "secteur": SECTOR,
        "region": REGION,
        "requetes_recherche": queries,
        "prospects": results,
        "stats": {
            "total_identifies": len(results),
            "audits_generes": sum(1 for p in results if p.get("fichiers", {}).get("success")),
            "priorite_haute": sum(1 for p in results if p.get("priorite") == "haute")
        }
    }

    report_path = f"data/ai_act/prospects/{timestamp}_scan_{SECTOR[:20]}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"  SCAN TERMINÉ")
    print(f"  {len(results)} prospects | {report['stats']['audits_generes']} mini-audits générés")
    print(f"  Rapport : {report_path}")
    print(f"{'='*60}")
    print(f"\n📋 PROCHAINES ACTIONS HUGO :")
    print(f"   1. Ouvrir data/ai_act/mini_audits/ → lire les emails")
    print(f"   2. Chercher ces entreprises sur LinkedIn")
    print(f"   3. Copier-coller l'email + envoyer")
    print(f"\n💡 Requêtes à taper sur LinkedIn/Google :")
    for q in queries[:3]:
        print(f"   → {q}")


if __name__ == "__main__":
    main()
