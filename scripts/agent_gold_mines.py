#!/usr/bin/env python3
"""
Agent Gold Mines — Détecteur de business modèles ÉMERGENTS.

Ce n'est PAS un explorateur de niches (ça, c'est niches_explorer).
Ce n'est PAS un détecteur de tendances produit (ça, c'est opportunity_hunter).

C'est un radar sur les NOUVEAUX TYPES DE BUSINESS qui émergent et qui
pourraient être adaptés au système 365days (Hugo + Claude + GitHub + Gemini
+ outils gratuits en ligne).

Exemples de ce qu'il détecte :
- "Les NFT numismatiques sont morts, mais les 'digital collectibles' sur Farcaster
  marchent maintenant avec des artistes indépendants"
- "La demande en 'AI-generated personalized children's books' explose sur
  des plateformes comme Lulu.com avec des marges ×5 vs KDP classique"
- "Micro-SaaS de personalisation de PDFs sur Gumroad — 0 code, pipeline
  Claude + templates = $200-2000/mois passif"

Angle de rotation hebdomadaire pour couvrir les vecteurs d'émergence.

Output :
  data/brain/gold_mines_YYYY-MM-DD.json
  data/brain/gold_mines_latest.json
  data/reports/rapport_gold_mines_YYYY-MM-DD.md

Env :
  GOLD_ANGLE    override de l'angle (optionnel)
  GEMINI_API_KEY
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, extract_json, get_previous_propositions, get_temperature

BRAIN_DIR   = Path("data/brain")
REPORTS_DIR = Path("data/reports")

# Angles de rotation — chacun ouvre un vecteur d'émergence différent
GOLD_ANGLES = [
    "new_platform_launches",          # Nouvelles plateformes qui paient les créateurs
    "ai_tools_monetization",          # Nouveaux modèles de monétisation de l'IA
    "micro_saas_no_code",             # Micro-SaaS sans code, avec Claude + GitHub
    "digital_physical_hybrid",        # Produits hybrides digital+physique (POD évolutif)
    "community_monetization",         # Nouvelles façons de monétiser une communauté
    "regulatory_opportunity",         # Lois/régulations créant de nouveaux marchés
    "platform_exodus_opportunity",    # Utilisateurs qui fuient une plateforme → opportunité
    "subscription_fatigue_pivot",     # Fatigue des abonnements → modèles alternatifs
    "generative_ai_content_markets",  # Marchés pour du contenu entièrement généré par IA
    "longevity_wellness_market",      # Boom du marché longévité/santé → sous-niches
]


def _get_angle() -> str:
    override = os.environ.get("GOLD_ANGLE", "").strip()
    if override:
        return override
    week = date.today().isocalendar()[1]
    return GOLD_ANGLES[week % len(GOLD_ANGLES)]


def run_gold_mines():
    today = date.today().isoformat()
    angle = _get_angle()

    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    previous = get_previous_propositions("data/brain", "gold_mines")

    print(f"[Gold Mines] Date: {today} | Angle: {angle}")
    if previous:
        print(f"[Gold Mines] Mémoire chargée — interdit de répéter.")

    system_prompt = f"""Tu es un expert en détection d'opportunités business émergentes pour créateurs solo.

TON RÔLE : Identifier des TYPES DE BUSINESS nouveaux ou en train d'émerger qui peuvent être
exploités par UN SEUL créateur avec : Claude AI, GitHub Actions, Gemini API, Python, outils gratuits.
PAS de serveurs. PAS d'investissement. Zéro coût fixe autant que possible.

PROFIL DE HUGO (propriétaire du système) :
- Entrepreneur solo en France
- Système automatisé : GitHub Actions + Gemini + Claude + scripts Python
- Verticaux actuels : livres de coloriage KDP, STL 3D print, low-content KDP, romans,
  jeux de société, merch design (t-shirts/mugs), assets Godot, jeux mobiles, apps mobiles,
  packs SVG, illustrations domaine public
- Budget: minimal, outils gratuits ou freemium
- Objectif: revenus passifs/semi-passifs, maximum ROI par heure

CE QUE TU CHERCHES (angle du jour : {angle}) :
Des business modèles émergents qui :
1. N'existaient pas ou étaient marginaux il y a 2 ans
2. Peuvent être lancés SANS équipe et SANS budget significatif
3. S'automatisent avec nos outils actuels (Claude, Gemini, GitHub, Python)
4. Ont un potentiel de revenu mesurable ($100-$5000/mois dans les 6 mois)
5. Sont 100% légaux et éthiques

CE QUE TU NE CHERCHES PAS :
- Des niches dans des marchés existants (Etsy, KDP coloring, etc.) — c'est le rôle de niches_explorer
- Des tendances de produit — c'est le rôle de opportunity_hunter
- Des idées théoriques sans chemin d'exécution concret

EXEMPLES DE CE QUI EST DANS TA ZONE :
✓ "Les 'AI legal document templates' personnalisables sur Gumroad explosent —
   Claude peut générer 50 templates juridiques localisés par pays en 1h, Gumroad = 0€ fixe"
✓ "Automatiser des 'AI-voiceover audiobooks' pour domaine public sur ACX/Spotify —
   TTS gratuit + Python + 0 droits d'auteur = revenu long tail"
✓ "Micro-SaaS 'AI-powered Etsy description writer' sur Gumroad (paiement unique) —
   Claude API + interface web statique GitHub Pages = infrastructure ~0€"
✗ "T-shirts avec des citations de films" (c'est une niche, pas un business modèle)
✗ "Coloriage de mandala" (déjà dans nos verticaux)

{previous}

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "date_analyse": "{today}",
  "angle": "{angle}",
  "agent": "gold_mines",

  "opportunites_emergentes": [
    {{
      "nom": "Nom court du business modèle",
      "type_business": "digital_product|saas|service_automatise|contenu|marketplace|autre",
      "description_concrete": "Ce que c'est concrètement en 2-3 phrases, sans jargon",
      "pourquoi_maintenant": "Qu'est-ce qui vient de changer pour que ça soit possible/rentable NOW",
      "signal_detectable": "Où Hugo peut vérifier que ça marche (Reddit, Product Hunt, Twitter, revenu public, etc.)",
      "outils_necessaires": ["Claude", "GitHub Actions", "Gemini", "autre outil gratuit"],
      "investissement_requis": "0€|<50€|50-200€|>200€",
      "temps_premier_revenu": "1 semaine|2-4 semaines|1-3 mois|3-6 mois",
      "revenu_potentiel_mensuel": "100-500€|500-2000€|2000-10000€|>10000€",
      "risque_principal": "Description du risque principal",
      "score_adaptabilite_365days": 8,
      "etape_1_pour_tester": "Première action concrète à faire en moins de 2 heures pour valider"
    }}
  ],

  "business_modeles_mourants": [
    {{
      "modele": "Business modèle en déclin",
      "pourquoi": "Raison du déclin",
      "pivot_possible": "Comment transformer en opportunité"
    }}
  ],

  "technologie_enabler": {{
    "technologie": "Technologie/changement qui ouvre des possibilités",
    "opportunites_qu_elle_cree": ["opportunité 1", "opportunité 2"],
    "delai_avant_saturation": "3 mois|6 mois|1 an|2 ans+"
  }},

  "top_pick_semaine": {{
    "opportunite": "Nom de la meilleure opportunité",
    "justification": "Pourquoi c'est le top pick cette semaine",
    "action_immediate": "Ce que Hugo peut faire AUJOURD'HUI en 30 minutes"
  }}
}}
JSON uniquement, sans markdown ni texte autour."""

    user_prompt = f"""Détecte les opportunités business émergentes pour la semaine du {today}.

Angle : {angle}

Identifie exactement 5 opportunités RÉELLES et CONCRÈTES, pas des tendances vagues.
Pour chacune : un signal vérifiable, des outils disponibles, et une première étape en 2h max.

1 business mourant avec son pivot possible.
1 technologie enabler avec ses délais.
1 top pick de la semaine avec action immédiate.

Pense comme un entrepreneur solo qui a 4h/semaine pour de nouveaux projets.
Réponds avec le JSON complet. Aucun texte en dehors du JSON."""

    temperature = get_temperature("prospecteur")
    print(f"[Gold Mines] Appel LLM (temperature={temperature:.2f})...")
    response = llm_call("stratege", system_prompt, user_prompt,
                        temperature=temperature, max_tokens=8000)

    if not response:
        print("[Gold Mines] Échec LLM.")
        sys.exit(1)

    clean = extract_json(response)

    try:
        data = json.loads(clean)
    except Exception as e:
        print(f"[Gold Mines] JSON invalide : {e}")
        debug = BRAIN_DIR / f"gold_mines_debug_{today}.txt"
        debug.write_text(response, encoding="utf-8")
        sys.exit(1)

    dated = BRAIN_DIR / f"gold_mines_{today}.json"
    dated.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Gold Mines] JSON → {dated}")

    latest = BRAIN_DIR / "gold_mines_latest.json"
    latest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Gold Mines] Latest → {latest}")

    md_lines = _build_md_report(data, today, angle)
    md_path = REPORTS_DIR / f"rapport_gold_mines_{today}.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[Gold Mines] Rapport → {md_path}")

    ops = data.get("opportunites_emergentes", [])
    top = data.get("top_pick_semaine", {})
    tech = data.get("technologie_enabler", {})

    print(f"\n[Gold Mines] === RÉSUMÉ ===")
    print(f"Angle  : {angle}")
    for i, op in enumerate(ops, 1):
        score = op.get("score_adaptabilite_365days", "?")
        print(f"#{i} [{score}/10] {op.get('nom','')} — {op.get('revenu_potentiel_mensuel','')} — {op.get('temps_premier_revenu','')}")
    print(f"\nTOP PICK : {top.get('opportunite','?')}")
    print(f"ACTION   : {top.get('action_immediate','?')[:100]}")
    print(f"TECH     : {tech.get('technologie','?')} (saturation dans {tech.get('delai_avant_saturation','?')})")


def _build_md_report(data: dict, today: str, angle: str) -> list[str]:
    ops     = data.get("opportunites_emergentes", [])
    mourants = data.get("business_modeles_mourants", [])
    tech    = data.get("technologie_enabler", {})
    top     = data.get("top_pick_semaine", {})

    lines = [
        f"# Gold Mines — Business Émergents — {today}",
        f"**Angle** : {angle}",
        f"**Agent** : gold_mines | Périmètre : NOUVEAUX business modèles, pas des niches",
        "",
        "---",
        "",
        f"## 🏆 TOP PICK DE LA SEMAINE",
        "",
        f"**{top.get('opportunite','')}**",
        "",
        f"{top.get('justification','')}",
        "",
        f"**Action immédiate** : {top.get('action_immediate','')}",
        "",
        "---",
        "",
        "## 💰 5 Opportunités Émergentes",
        "",
    ]

    for i, op in enumerate(ops, 1):
        score = op.get("score_adaptabilite_365days", "?")
        lines += [
            f"### #{i} — {op.get('nom','')} `[{score}/10]`",
            "",
            f"**Type** : {op.get('type_business','')} | "
            f"**Revenu estimé** : {op.get('revenu_potentiel_mensuel','')} | "
            f"**Délai 1er revenu** : {op.get('temps_premier_revenu','')}",
            f"**Investissement** : {op.get('investissement_requis','')}",
            "",
            op.get("description_concrete", ""),
            "",
            f"**Pourquoi maintenant** : {op.get('pourquoi_maintenant','')}",
            f"**Signal vérifiable** : {op.get('signal_detectable','')}",
            f"**Outils** : {', '.join(op.get('outils_necessaires',[]))}",
            f"**Risque principal** : {op.get('risque_principal','')}",
            "",
            f"> **Étape #1 (< 2h)** : {op.get('etape_1_pour_tester','')}",
            "",
        ]

    lines += [
        "---",
        "",
        "## ⚡ Technologie Enabler",
        "",
        f"**{tech.get('technologie','')}**",
        "",
        f"Opportunités qu'elle crée :",
    ]
    for opp in tech.get("opportunites_qu_elle_cree", []):
        lines.append(f"- {opp}")
    lines += [
        "",
        f"**Délai avant saturation** : {tech.get('delai_avant_saturation','')}",
        "",
        "---",
        "",
        "## ⬇️ Business en Déclin (à éviter ou pivoter)",
        "",
    ]
    for m in mourants:
        lines += [
            f"- **{m.get('modele','')}** : {m.get('pourquoi','')}",
            f"  → Pivot : {m.get('pivot_possible','')}",
        ]

    lines += [
        "",
        "---",
        "",
        f"*Rapport généré le {today} — Agent: gold_mines*",
    ]
    return lines


if __name__ == "__main__":
    run_gold_mines()
