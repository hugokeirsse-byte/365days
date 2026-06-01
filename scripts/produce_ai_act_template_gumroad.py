"""
Générateur du template d'auto-audit AI Act — produit Gumroad à €49.

Produit un document complet (Markdown → PDF) que le client remplit seul
pour évaluer sa propre conformité EU AI Act.

Ce produit EST le lead magnet : le client achète €49 → découvre qu'il n'est pas conforme
→ contacte Hugo pour l'audit complet à €990.

Usage:
  python scripts/produce_ai_act_template_gumroad.py

Sortie: data/ai_act/produits/template_autoaudit_ai_act_v1.md
"""

import json
import os
import re
import time
from datetime import datetime

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


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
                    "generationConfig": {"temperature": 0.4, "maxOutputTokens": 8192}
                }
                req = urllib.request.Request(
                    url, json.dumps(payload).encode(),
                    {"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=90) as resp:
                    return json.loads(resp.read())["candidates"][0]["content"]["parts"][0]["text"].strip()
            elif GROQ_API_KEY:
                url = "https://api.groq.com/openai/v1/chat/completions"
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "system", "content": system},
                                 {"role": "user", "content": user}],
                    "temperature": 0.4, "max_tokens": 8192
                }
                req = urllib.request.Request(
                    url, json.dumps(payload).encode(),
                    {"Content-Type": "application/json",
                     "Authorization": f"Bearer {GROQ_API_KEY}"}, method="POST")
                with urllib.request.urlopen(req, timeout=90) as resp:
                    return json.loads(resp.read())["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt < 2:
                time.sleep((attempt + 1) * 10)
            else:
                raise
    raise RuntimeError("API failed")


EXPERT_SYSTEM = """Tu es un expert EU AI Act (Règlement 2024/1689) spécialisé dans la création d'outils pratiques pour les entreprises.
Tu écris des documents clairs, professionnels, sans jargon inutile.
Tes documents sont directement utilisables par un responsable non-juriste."""


def generate_template() -> str:
    user = """Crée un template complet d'auto-audit EU AI Act pour les entreprises françaises.

Ce document sera vendu €49 sur Gumroad comme outil de conformité autonome.

Structure requise :

# Template d'Auto-Audit EU AI Act
## Comment utiliser ce document
## PARTIE 1 — Comprendre l'EU AI Act en 5 minutes (résumé exécutif sans jargon)
## PARTIE 2 — Identifier votre système IA (questions + cases à cocher)
## PARTIE 3 — Classifier votre niveau de risque (arbre de décision simple)
## PARTIE 4 — Checklist de conformité par niveau de risque
   - Niveau minimal (liste simple)
   - Niveau limité (liste courte)
   - Niveau haut risque (liste complète avec explications)
## PARTIE 5 — Votre score de conformité (tableau d'auto-évaluation)
## PARTIE 6 — Plan d'action personnel (template à compléter)
## PARTIE 7 — Documents à produire (liste avec templates simples)
## RESSOURCES ET PROCHAINES ÉTAPES

Important :
- Chaque section doit avoir des cases à cocher [ ] que le client remplit
- Utiliser des exemples concrets (RH, finance, santé, marketing)
- Inclure les dates clés de l'AI Act
- À la fin : invitation subtile à contacter un expert pour l'audit complet

Sois exhaustif — ce document doit valoir ses €49."""

    return llm_call(EXPERT_SYSTEM, user)


def generate_gumroad_description() -> str:
    """Génère la description du produit pour la page Gumroad."""
    user = """Écris la description de vente pour ce produit Gumroad :

PRODUIT : Template d'Auto-Audit EU AI Act
PRIX : €49
FORMAT : PDF/Word (template à remplir)
POUR : Dirigeants et DPO de PME françaises utilisant l'IA

La description doit :
- Titre percutant (ex: "EU AI Act : Êtes-vous en conformité ?")
- Résumer le problème (enforcement commence août 2026)
- Ce qu'ils obtiennent (liste bullet points)
- Pour qui c'est fait
- Ce que ça leur évite
- Garantie satisfaction
- Call-to-action

Maximum 300 mots. Ton : professionnel mais direct."""

    return llm_call(EXPERT_SYSTEM, user)


def main():
    print("\n🏗️  GÉNÉRATION TEMPLATE GUMROAD — Auto-audit EU AI Act")

    os.makedirs("data/ai_act/produits", exist_ok=True)

    print("   Génération du template (25-30 pages)...")
    template_content = generate_template()
    time.sleep(4)

    print("   Génération de la description Gumroad...")
    gumroad_desc = generate_gumroad_description()

    # Save
    template_path = "data/ai_act/produits/template_autoaudit_ai_act_v1.md"
    gumroad_path = "data/ai_act/produits/gumroad_description.md"

    with open(template_path, "w", encoding="utf-8") as f:
        f.write(f"---\n")
        f.write(f"Généré le : {datetime.utcnow().strftime('%Y-%m-%d')}\n")
        f.write(f"Version : 1.0\n")
        f.write(f"---\n\n")
        f.write(template_content)

    with open(gumroad_path, "w", encoding="utf-8") as f:
        f.write("# Description Gumroad — Template Auto-Audit AI Act\n\n")
        f.write(gumroad_desc)

    print(f"\n✅ Template → {template_path}")
    print(f"✅ Description Gumroad → {gumroad_path}")
    print(f"\n📋 PROCHAINES ACTIONS HUGO :")
    print(f"   1. Lire le template (vérifier qualité)")
    print(f"   2. Convertir en PDF (Google Docs → Télécharger en PDF)")
    print(f"   3. Créer le produit sur Gumroad.com à €49")
    print(f"   4. Copier la description depuis {gumroad_path}")
    print(f"\n--- DESCRIPTION GUMROAD ---")
    print(gumroad_desc)


if __name__ == "__main__":
    main()
