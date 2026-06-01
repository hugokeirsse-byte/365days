"""
Producteur de rapports d'audit EU AI Act.

Prend en entrée un questionnaire client rempli (JSON) et génère :
- Un rapport PDF complet (25-30 pages)
- Un résumé exécutif (1 page)
- Un plan d'action priorisé (30j/90j/6mois)

Usage:
  INPUT_FILE=data/ai_act/questionnaires/client_xyz.json
  OUTPUT_DIR=data/ai_act/rapports/
  python scripts/produce_ai_act_audit.py

Format questionnaire (data/ai_act/questionnaires/template.json) :
  Voir produce_ai_act_questionnaire.py
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

INPUT_FILE = os.environ.get("INPUT_FILE", "")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "data/ai_act/rapports")
CLIENT_NAME = os.environ.get("CLIENT_NAME", "")
AUDIT_TYPE = os.environ.get("AUDIT_TYPE", "full")  # full | mini | template

# System prompt expert AI Act
EXPERT_SYSTEM = """Tu es un expert juridique et technique en conformité EU AI Act (Règlement IA européen 2024/1689).
Tu as une connaissance approfondie de :
- Les 4 niveaux de risque (inacceptable, haut risque, risque limité, risque minimal)
- L'Annexe III (systèmes IA à haut risque)
- Les obligations par catégorie : données (art.10), documentation (art.11), transparence (art.13), supervision humaine (art.14), précision (art.15), conformité (art.43-49)
- Le calendrier d'application : interdictions depuis février 2025, haut risque Annexe III depuis août 2026
- Les sanctions : jusqu'à 3% CA mondial pour non-conformité, 6% pour pratiques interdites

Tu analyses la situation d'une entreprise et produis des rapports clairs, actionnables, et sans jargon inutile.
Tu distingues toujours ce qui EST requis de ce qui est RECOMMANDÉ.
Tu priorises par urgence et impact business."""


def llm_call(system: str, user: str, temperature: float = 0.3) -> str:
    import urllib.request

    for attempt in range(3):
        try:
            if GEMINI_API_KEY:
                url = ("https://generativelanguage.googleapis.com/v1beta/models/"
                       "gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY)
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": user}]}],
                    "systemInstruction": {"parts": [{"text": system}]},
                    "generationConfig": {"temperature": temperature, "maxOutputTokens": 8192}
                }
                data = json.dumps(payload).encode()
                req = urllib.request.Request(url, data=data,
                                              headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=90) as resp:
                    result = json.loads(resp.read())
                return result["candidates"][0]["content"]["parts"][0]["text"].strip()

            elif GROQ_API_KEY:
                url = "https://api.groq.com/openai/v1/chat/completions"
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ],
                    "temperature": temperature,
                    "max_tokens": 8192
                }
                data = json.dumps(payload).encode()
                req = urllib.request.Request(url, data=data, headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {GROQ_API_KEY}"
                }, method="POST")
                with urllib.request.urlopen(req, timeout=90) as resp:
                    result = json.loads(resp.read())
                return result["choices"][0]["message"]["content"].strip()

        except Exception as e:
            if attempt < 2:
                wait = (attempt + 1) * 10
                print(f"   ⚠️  API error ({e}) — retry in {wait}s...")
                time.sleep(wait)
            else:
                raise

    raise RuntimeError("Toutes les tentatives API ont échoué")


def classify_risk(questionnaire: dict) -> dict:
    """Classifie le niveau de risque AI Act du système décrit."""
    user = f"""Voici la description du système IA d'une entreprise :

{json.dumps(questionnaire, ensure_ascii=False, indent=2)}

Classifie ce système selon l'EU AI Act :
1. Niveau de risque (inacceptable / haut risque Annexe III / risque limité / risque minimal)
2. Article ou Annexe applicable
3. Justification en 2-3 phrases
4. Obligations principales déclenchées

Réponds en JSON :
{{
  "niveau_risque": "haut risque|risque limité|risque minimal|inacceptable",
  "annexe_applicable": "Annexe III catégorie X" ou "N/A",
  "justification": "...",
  "obligations_principales": ["obligation 1", "obligation 2", "..."]
}}"""

    raw = llm_call(EXPERT_SYSTEM, user)
    match = re.search(r'\{[\s\S]*\}', raw)
    if match:
        return json.loads(match.group())
    return {"niveau_risque": "à déterminer", "justification": raw[:300],
            "obligations_principales": [], "annexe_applicable": "N/A"}


def generate_gap_analysis(questionnaire: dict, classification: dict) -> str:
    """Génère l'analyse des écarts de conformité."""
    user = f"""Entreprise et système IA :
{json.dumps(questionnaire, ensure_ascii=False, indent=2)}

Classification AI Act :
{json.dumps(classification, ensure_ascii=False, indent=2)}

Produis une analyse complète des écarts de conformité EU AI Act.
Pour chaque obligation applicable, indique :
- Ce qui est REQUIS par la loi
- Ce que l'entreprise a ACTUELLEMENT (selon le questionnaire)
- L'ÉCART (ce qui manque)
- La PRIORITÉ (CRITIQUE / IMPORTANT / RECOMMANDÉ)

Structure en sections claires. Sois précis et actionnable."""

    return llm_call(EXPERT_SYSTEM, user, temperature=0.3)


def generate_action_plan(gap_analysis: str, classification: dict) -> str:
    """Génère le plan d'action priorisé 30j/90j/6mois."""
    user = f"""Sur la base de cette analyse des écarts AI Act :

{gap_analysis}

Classification : {classification.get('niveau_risque')}

Génère un plan d'action priorisé en 3 phases :

**PHASE 1 — 30 jours (URGENT)** : Ce qui doit être fait immédiatement pour éviter les sanctions
**PHASE 2 — 90 jours** : Ce qui consolide la conformité
**PHASE 3 — 6 mois** : Ce qui optimise et documente durablement

Pour chaque action :
- Description claire (sans jargon)
- Responsable suggéré (DPO / DSI / Juridique / CEO)
- Temps estimé
- Documents à produire

Commence chaque action par un verbe d'action."""

    return llm_call(EXPERT_SYSTEM, user, temperature=0.3)


def generate_executive_summary(questionnaire: dict, classification: dict,
                                 gap_analysis: str, action_plan: str) -> str:
    """Génère le résumé exécutif d'une page."""
    company = questionnaire.get("entreprise", {}).get("nom", "Votre entreprise")
    user = f"""Rédige un résumé exécutif d'une page (maximum 400 mots) pour le dirigeant de {company}.

Contexte :
- Classification : {classification.get('niveau_risque')}
- Obligations : {', '.join(classification.get('obligations_principales', [])[:3])}

Points essentiels de l'analyse : {gap_analysis[:500]}...
Premières actions : {action_plan[:300]}...

Le résumé doit :
1. Commencer par le verdict global (CONFORME / PARTIELLEMENT CONFORME / NON CONFORME)
2. Expliquer les 2-3 risques principaux en langage clair (pas de jargon juridique)
3. Donner les 3 actions les plus urgentes
4. Terminer par la prochaine étape recommandée

Ton professionnel mais accessible pour un non-juriste."""

    return llm_call(EXPERT_SYSTEM, user, temperature=0.4)


def save_as_markdown(content: dict, output_path: str):
    """Sauvegarde le rapport en Markdown (convertible en PDF)."""
    company = content["questionnaire"].get("entreprise", {}).get("nom", "Client")
    date_str = datetime.utcnow().strftime("%d/%m/%Y")

    md = f"""# Rapport d'Audit EU AI Act
## {company}

> **Date** : {date_str}
> **Type d'audit** : {content.get('audit_type', 'Audit Express')}
> **Auditeur** : 365days AI Compliance

---

## 1. RÉSUMÉ EXÉCUTIF

{content['executive_summary']}

---

## 2. CLASSIFICATION DU SYSTÈME IA

| Critère | Résultat |
|---------|---------|
| **Niveau de risque** | {content['classification']['niveau_risque'].upper()} |
| **Annexe applicable** | {content['classification'].get('annexe_applicable', 'N/A')} |

**Justification** : {content['classification']['justification']}

**Obligations principales déclenchées** :
{chr(10).join(f"- {o}" for o in content['classification'].get('obligations_principales', []))}

---

## 3. ANALYSE DES ÉCARTS DE CONFORMITÉ

{content['gap_analysis']}

---

## 4. PLAN D'ACTION PRIORISÉ

{content['action_plan']}

---

## 5. PROCHAINES ÉTAPES

Pour toute question sur ce rapport ou pour démarrer la mise en conformité :
- Email : [votre email]
- Audit de suivi disponible dans 90 jours

*Rapport généré le {date_str} — Ce rapport est basé sur les informations fournies via questionnaire.*
*Il ne constitue pas un avis juridique. Consultez un avocat pour les décisions réglementaires critiques.*
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)


def try_generate_pdf(md_path: str, pdf_path: str) -> bool:
    """Tente de générer un PDF depuis le Markdown. Retourne True si succès."""
    try:
        import subprocess
        # Try markdown to PDF via pandoc if available
        result = subprocess.run(
            ["pandoc", md_path, "-o", pdf_path, "--pdf-engine=wkhtmltopdf"],
            capture_output=True, timeout=30
        )
        if result.returncode == 0:
            return True
    except Exception:
        pass

    try:
        # Fallback: fpdf2
        from fpdf import FPDF

        with open(md_path, encoding="utf-8") as f:
            text = f.read()

        # Strip markdown formatting
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        text = re.sub(r'\|.+\|', '', text)  # Remove tables
        text = re.sub(r'\n{3,}', '\n\n', text)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=10)
        pdf.set_auto_page_break(auto=True, margin=15)

        for line in text.split('\n'):
            line = line.strip()
            if not line:
                pdf.ln(3)
                continue
            if len(line) > 2 and line == line.upper() and len(line) < 60:
                pdf.set_font("Helvetica", 'B', 12)
                pdf.multi_cell(0, 6, line)
                pdf.set_font("Helvetica", size=10)
            else:
                pdf.multi_cell(0, 5, line)

        pdf.output(pdf_path)
        return True
    except Exception as e:
        print(f"   ⚠️  PDF non généré ({e}) — rapport Markdown disponible")
        return False


def main():
    print(f"\n{'='*60}")
    print("  PRODUCTEUR AUDIT EU AI ACT")
    print(f"{'='*60}\n")

    # Load questionnaire
    if INPUT_FILE and os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, encoding="utf-8") as f:
            questionnaire = json.load(f)
    else:
        # Demo mode avec questionnaire exemple
        print("   Mode démo — questionnaire exemple")
        questionnaire = {
            "entreprise": {
                "nom": "TechCorp SAS",
                "secteur": "Ressources Humaines / Recrutement",
                "taille": "50 salariés",
                "pays": "France"
            },
            "systeme_ia": {
                "description": "Outil de tri automatique de CV pour identifier les candidats les plus pertinents",
                "fournisseur": "Développé en interne",
                "donnees_traitees": "CV, lettres de motivation, profils LinkedIn",
                "decisions_automatisees": "Score de pertinence 0-100 — RH voit uniquement les scores > 60",
                "supervision_humaine": "Partielle — RH peut outrepasser mais suit généralement le score",
                "documentation_existante": "Aucune documentation technique formelle"
            },
            "usage": {
                "depuis": "2024",
                "nombre_decisions_mois": "~200 CV traités/mois",
                "impact_personne": "Accès ou refus d'entretien d'embauche"
            }
        }

    company_name = questionnaire.get("entreprise", {}).get("nom", "Client")
    slug = re.sub(r'[^a-z0-9]+', '_', company_name.lower())[:30]
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step 1: Classification
    print("1/4 Classification du système IA...")
    classification = classify_risk(questionnaire)
    risk_level = classification.get("niveau_risque", "?")
    print(f"   → Niveau de risque : {risk_level.upper()}")
    time.sleep(3)

    # Step 2: Gap analysis
    print("2/4 Analyse des écarts de conformité...")
    gap_analysis = generate_gap_analysis(questionnaire, classification)
    print(f"   → {len(gap_analysis)} caractères générés")
    time.sleep(3)

    # Step 3: Action plan
    print("3/4 Plan d'action priorisé...")
    action_plan = generate_action_plan(gap_analysis, classification)
    print(f"   → {len(action_plan)} caractères générés")
    time.sleep(3)

    # Step 4: Executive summary
    print("4/4 Résumé exécutif...")
    executive_summary = generate_executive_summary(
        questionnaire, classification, gap_analysis, action_plan)
    print(f"   → {len(executive_summary)} caractères générés")

    # Assemble report
    report = {
        "questionnaire": questionnaire,
        "classification": classification,
        "gap_analysis": gap_analysis,
        "action_plan": action_plan,
        "executive_summary": executive_summary,
        "audit_type": "Audit Express 48h",
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }

    # Save
    md_path = os.path.join(OUTPUT_DIR, f"audit_{slug}_{timestamp}.md")
    json_path = os.path.join(OUTPUT_DIR, f"audit_{slug}_{timestamp}.json")
    pdf_path = os.path.join(OUTPUT_DIR, f"audit_{slug}_{timestamp}.pdf")

    save_as_markdown(report, md_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    pdf_ok = try_generate_pdf(md_path, pdf_path)

    print(f"\n{'='*60}")
    print(f"  RAPPORT GÉNÉRÉ — {company_name}")
    print(f"  Risque : {risk_level.upper()}")
    print(f"  Markdown : {md_path}")
    if pdf_ok:
        print(f"  PDF     : {pdf_path}")
    print(f"{'='*60}\n")

    # Print executive summary for quick review
    print("--- RÉSUMÉ EXÉCUTIF ---")
    print(executive_summary[:800])
    print("...")


if __name__ == "__main__":
    main()
