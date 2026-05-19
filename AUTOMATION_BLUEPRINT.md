# ⚙️ AUTOMATION BLUEPRINT — Qui fait quoi quand (économie tokens Claude)

**Date** : 2026-05-19
**Objectif** : minimiser les appels Claude Code à **< 10% du travail total**.
Le reste est délégué à des **LLM-minions gratuits** (vague 2 des inscriptions),
à des **GitHub Actions** déterministes, et à des **scripts Termux** locaux.

---

## 🎯 1. PRINCIPE DE ROUTAGE — la cascade par coût

Avant chaque tâche, le système se pose 4 questions dans cet ordre :

```
1. Peut-on faire ça en code Python pur (déterministe) ?
   → OUI : pas d'IA du tout. (image processing, PDF assembly, scraping)
   → NON : passer à 2

2. Un LLM gratuit illimité-en-pratique (Gemini/Groq/Mistral) peut-il faire ça ?
   → OUI : routage vers le minion approprié
   → NON : passer à 3

3. Un LLM gratuit avec quota peut-il faire ça (HF, Replicate trial) ?
   → OUI : routage avec gestion quota + fallback OpenRouter
   → NON : passer à 4

4. Faut-il vraiment Claude Code (assemblage, arbitrage, debug architecture) ?
   → OUI : appel Claude avec contexte resserré (jamais le repo entier)
   → NON : alerte au patron via Telegram pour décision
```

**Règle d'or** : Claude Code n'écrit **jamais** une rédaction longue, une traduction
mécanique, ou un résumé. Ces tâches sont systématiquement déléguées.

---

## 🧠 2. MATRICE DE ROUTAGE — qui fait quoi par type de tâche

| Tâche | 1er choix | Fallback | Quota typique | Claude appelé ? |
|---|---|---|---|---|
| **Détection tendances Reddit/Pinterest/TikTok** | Python + PRAW + scrapers | — | illimité (HTTP) | Non |
| **Résumé d'un thread Reddit (frustrations users)** | Mistral `small-latest` | Gemini Flash | ~1M tokens gratuits/mois | Non |
| **Brainstorm 200 idées de produits** | Gemini 2.x (1500/jour) | Groq Llama 3.1 70B | 1500 req/j | Non |
| **Rédaction d'un chapitre de livre (1500 mots)** | Groq Llama 3.1 70B (vitesse) | Gemini si stylé | quasi illimité (rate-limited à 30 req/min) | Non |
| **Traduction FR↔EN d'une description produit** | Mistral `small` | Gemini | gros quota | Non |
| **Traduction vers 10+ langues** | Gemini (long contexte) | Mistral en boucle | 1500/j | Non |
| **SEO keyword extraction des bestsellers KDP** | Cohere `command-r` | Mistral | trial 5$ + 1000 req/mois free | Non |
| **Génération image stylée (coloriage, mockup)** | HF Inference (SDXL/FLUX) | Replicate | 30k req HF, 5$ Replicate | Non |
| **Line-art ControlNet pour coloriage** | HF (ControlNet endpoint) | Replicate | idem | Non |
| **Upscaling 4K image** | Replicate (Real-ESRGAN) | HF | 5$ | Non |
| **Colorisation noir & blanc → couleur** | Replicate (DeOldify) | local CPU si Termux costaud | 5$ | Non |
| **Détourage automatique (rembg)** | Python `rembg` local | Replicate | illimité local | Non |
| **Critique anti-slop d'un produit (relecture)** | Gemini (vision multimodale) | Groq texte seul | 1500/j | Non |
| **Génération de prompt à partir d'une tendance** | Mistral | Gemini | gros quota | Non |
| **Veille web ciblée (top 10 articles sur X)** | Perplexity Sonar | OpenRouter "search" | 5$ trial | Non |
| **Routage automatique LLM (failover)** | OpenRouter | — | 1$ trial | Non |
| **Code Python standard (CRUD, scraping, PDF)** | Squelette GitHub + patch local | Mistral si patch trivial | — | Non |
| **Code Python architecture complexe** | **Claude Code** | — | — | **Oui** (rare) |
| **Debug d'une erreur GitHub Actions inconnue** | Gemini d'abord (avec log) | **Claude** si Gemini bloqué | — | **Oui** seulement si fallback |
| **Décision stratégique cross-modules** | **Claude Code** | — | — | **Oui** |
| **Arbitrage cross-canal (vague KDP→Merch→Jeu)** | **Claude Code** | — | — | **Oui** |
| **Validation finale avant publication** | **Hugo (humain)** via bot Telegram | — | — | Non |

---

## 🔄 3. WORKFLOW TYPE — exemple complet : "Publier 1 livre de coloriage"

```
[1] Cron GitHub Actions, lundi 6h
    └── déclenche workflow `produce_coloring_book.yml`

[2] Script Python (déterministe, 0 token)
    └── lit `data/niche_gap.json` → choisit une niche cible "Mystical Mushrooms"

[3] Appel Gemini (1 req, ~3000 tokens output)
    └── génère 30 prompts d'illustration (1 par page)

[4] Boucle Python → 30 appels HF Inference (SDXL line-art)
    └── 30 images PNG line-art 300 DPI

[5] Script Python OpenCV (déterministe)
    └── seuillage binaire → noir & blanc parfait, nettoyage micro-pixels

[6] Script Python ReportLab (déterministe)
    └── assemble PDF KDP-ready (couverture + pages + marges KDP)

[7] Appel Gemini Vision (1 req, vision multimodale)
    └── relecture critique : "ces 30 pages ont-elles le niveau d'un best-seller KDP ?"
    └── retourne JSON : { "verdict": "PASS"|"FAIL", "fautes": [...], "suggestions": [...] }

[8] Si verdict = FAIL :
    └── boucle au pas [3] avec correctifs
    └── max 3 itérations sinon Claude est appelé pour arbitrage

[9] Si verdict = PASS :
    └── PDF copié dans `staging/coloring/mystical_mushrooms_2026-05-19.pdf`
    └── notif Telegram : aperçu PDF + boutons "✅ Publier" / "❌ Rejeter"

[10] Hugo reçoit la notif sur son téléphone
     └── clique ✅ → workflow `publish_kdp.yml` se déclenche (upload via API ou guide manuel)
     └── clique ❌ → le produit va dans `archive/rejected/`

INTERVENTION CLAUDE = 0 SAUF SI étape [8] échoue 3 fois.
INTERVENTION HUGO = 1 clic à l'étape [10].
```

---

## 📅 4. TOPOLOGIE GITHUB ACTIONS — qui tourne quand

```
.github/workflows/
├── agent_brain_meta.yml          [existant]    cron */4h, 5 brains
├── produce_coloring_book.yml     [à créer]     cron lundi 4h
├── produce_card_game.yml         [existant]    cron mardi 4h
├── produce_kdp_book.yml          [à créer]     cron mercredi 4h (séquentiel par chapitre)
├── produce_progeny_pack.yml      [à créer]     cron jeudi 4h (Module W)
├── produce_vintage_restoration.yml [à créer]   cron vendredi 4h (Modules U+P)
├── produce_merch_batch.yml       [à créer]     cron samedi 4h
├── produce_video_faceless.yml    [à créer]     cron dimanche 4h
│
├── sourcing_bestsellers.yml      [à créer]     cron daily 1h, scrape KDP/Etsy/Amazon
├── sourcing_reviews_weakness.yml [à créer]     cron daily 2h, scrape 1-3★ reviews
├── sourcing_domain_public.yml    [à créer]     cron weekly, refresh Gutenberg/Met/Smithsonian
├── sourcing_affiliate_intents.yml [à créer]    cron */2h, scan X/Reddit pour intentions d'achat
│
├── llm_router.yml                [à créer]     reusable workflow appelé par tous les producers
├── quality_check_vision.yml      [à créer]     reusable workflow, appel Gemini Vision
├── publish_staging.yml           [à créer]     reusable, push to staging/ + notif Telegram
└── claude_arbitrage.yml          [à créer]     dispatché manuellement quand fallback chain échoue
```

**Règle de séparation** :
- Tout ce qui produit → cron nocturne (3h-6h UTC, fenêtre calme)
- Tout ce qui veille (sourcing) → cron diurne (intervalles courts)
- Tout ce qui publie → déclenché par Hugo (jamais auto)

---

## 🏠 5. TERMUX (LOCAL) — ce qui ne va JAMAIS dans le cloud

Le téléphone Termux héberge un orchestrateur local qui :

```
~/empire/
├── secrets/
│   ├── api_keys.env          [permission 600, jamais push]
│   ├── prompts_master/       [notre "sauce", invariants, plans Progeny]
│   └── trade_secrets.sqlite  [scoring matrices, jeux gagnants identifiés]
│
├── orchestrator/
│   ├── cron_local.sh         [planifie via cronie : push d'images HD vers HF avant production]
│   ├── push_to_github.sh     [commit + push avec ssh-key, jamais en clair]
│   ├── pull_assets.sh        [récupère APK/PDF/PNG depuis GitHub releases]
│   └── notify.py             [proxy entre alertes locales et Telegram bot]
│
├── stage_local/              [images HD brutes téléchargées des musées, jamais push]
│   ├── domain_public/
│   └── progeny_inputs/
│
└── delivery/                 [APK/PDF/ZIP prêts à upload manuel sur stores]
    ├── kdp/
    ├── redbubble/
    ├── itch/
    └── cults3d/
```

**Pourquoi rien ne sort de Termux sauf via SSH chiffré** :
- Personne ne peut voler nos prompts maîtres (la "recette")
- Les clés API ne sont jamais dans le code (toujours `os.environ`)
- Les algorithmes Progeny Engine restent privés (la PI hybride)

---

## 🤖 6. LE BOT TELEGRAM — interface unique de décision

Toute la délégation décisionnelle passe par **un seul canal Telegram privé**.
Hugo a 4 types de messages possibles, chacun avec boutons inline :

| Type | Quand | Boutons | Action après clic |
|---|---|---|---|
| **🆕 Produit en staging** | Un PDF/PNG/APK est prêt | ✅ Publier · ❌ Rejeter · 🔍 Voir détails | publish workflow OU archive/ |
| **🚨 Alerte tendance** | Score d'opportunité > 8/10 | 🚀 Lancer prod · 📌 Mettre en file · ❌ Ignorer | trigger pipeline OU queue |
| **⚠️ Décision ambiguë** | LLM ne sait pas trancher | A · B · C · D · ❓ Demander Claude | applique le choix OU call Claude |
| **💔 Bug critique** | Workflow failed 3× | 🩹 Patcher (Gemini) · 🧠 Claude · ⏸️ Pause | trigger debug OU pause module |

Implémentation : **bot stateless** lancé en GitHub Actions (cron) qui poll les
nouvelles décisions Hugo et déclenche les workflows correspondants via
`workflow_dispatch`. Aucun serveur 24/7 nécessaire = 0€.

---

## 🪞 7. AUTO-CORRECTION — boucle de QA sans Claude

Avant d'appeler Claude pour un bug, le système passe par 3 niveaux :

```
NIVEAU 1 — Auto-retry (gratuit)
└── Si workflow Actions échoue, retry 3× avec backoff exponentiel
    └── 60% des bugs sont des flakes réseau, résolus ici

NIVEAU 2 — Gemini Code-Repair (gratuit, 1500/j)
└── Si toujours échec, télécharge le log d'erreur, dump le fichier source,
    et envoie à Gemini avec prompt :
    "Voici le code (fichier X). Voici l'erreur Y. Corrige le code."
└── Le diff est appliqué automatiquement, retry workflow.
    └── ~30% des bugs restants sont résolus ici

NIVEAU 3 — Claude Code (rare, dernier recours)
└── Notif Telegram : "Bug bloquant. Claude requis pour module Z."
└── Hugo clique 🧠 Claude → workflow `claude_arbitrage.yml` se déclenche
    → spawne une session Claude Code avec contexte resserré (1 module, pas le repo)
```

**Effet attendu** : Claude est appelé pour **< 10% des bugs**.

---

## 📊 8. BUDGET TOKENS — estimation par semaine

| Acteur | Tokens/semaine estimés | Coût |
|---|---|---|
| Gemini | ~5M tokens (10500 req à 500 tk/req) | 0€ (sous 1500/j) |
| Groq | ~10M tokens | 0€ (très généreux) |
| Mistral | ~2M tokens | 0€ (tier free) |
| HF Inference | ~500 générations images | 0€ (sous quota) |
| Replicate | ~50 générations Real-ESRGAN/DeOldify | 0€ (5$ trial étalé sur ~3 mois) |
| Perplexity | ~30 requêtes web search | 0€ (5$ trial étalé) |
| **Claude Code** | **~500k tokens** (arbitrage + debug niveau 3) | **estim. 1 plan Pro mensuel suffit** |

→ **Si revenu mensuel > 50€** : tu peux confortablement payer Claude Pro (~18€).
→ **Si revenu mensuel > 600€** : upgrade Claude Max (~200€), je peux tourner ~10× plus.

---

## 🔌 9. CONTRATS DE SORTIE — formats JSON canoniques

Tous les modules échangent via JSON normalisé pour qu'on puisse changer de LLM sans casser le pipeline.

```json
// Format "opportunity" produit par tout module de détection
{
  "id": "opp_2026-05-19_mystical_mushrooms",
  "type": "kdp_coloring | merch_design | mobile_game | api_service | ...",
  "niche": "mystical mushrooms",
  "score": 8.5,
  "evidence": {
    "search_volume": 8200,
    "competition_density": "low",
    "bestseller_review_pain_points": ["thin paper", "duplicates"],
    "trending_platform": "TikTok #cottagecore"
  },
  "next_action": "produce_coloring_book",
  "deadline": "2026-05-26"
}
```

```json
// Format "asset" produit par tout module de production
{
  "id": "asset_2026-05-19_mystical_mushrooms_v1",
  "opp_id": "opp_2026-05-19_mystical_mushrooms",
  "type": "pdf_book | png_design | apk | epub | zip",
  "path_in_repo": "staging/coloring/mystical_mushrooms.pdf",
  "qa_verdict": "PASS",
  "qa_score": 9.2,
  "qa_critic": "gemini-2.0-vision",
  "publish_targets": ["KDP", "Gumroad"],
  "metadata": {
    "title_en": "...",
    "keywords": [...],
    "bullets": [...]
  }
}
```

Ces 2 contrats sont le **seul couplage entre modules**. Tout le reste est libre.

---

## ✅ 10. CHECKLIST DE LANCEMENT — quand commencer chaque pipeline

| Pipeline | Pré-requis inscriptions | Pré-requis secrets GitHub | Prêt si |
|---|---|---|---|
| `produce_coloring_book` | KDP + Gumroad | `GEMINI_API_KEY` + `HF_API_KEY` | Vague 1+2 ok |
| `produce_card_game` | TGC + BGM | `GEMINI_API_KEY` | Vague 1+2 ok |
| `produce_kdp_book` | KDP + D2D | `GROQ_API_KEY` + `GEMINI_API_KEY` | Vague 1+2+3 ok |
| `produce_progeny_pack` | Redbubble + KDP + Gumroad | `HF_API_KEY` + `GEMINI_API_KEY` | Vague 2+3+7 ok |
| `produce_vintage_restoration` | Redbubble + KDP | `REPLICATE_API_TOKEN` + `HF_API_KEY` | Vague 2+3+7 ok |
| `produce_merch_batch` | Redbubble + TeePublic + Zazzle | `GEMINI_API_KEY` + `HF_API_KEY` | Vague 1+2+3 ok |
| `produce_video_faceless` | YouTube channel + Pexels | `YOUTUBE_API_KEY` + `PEXELS_API_KEY` + `GEMINI_API_KEY` | Vague 2+4 ok |
| `produce_mobile_game` | Amazon Appstore (ou Play 25$) + AdMob | `ADMOB_APP_ID` + `GEMINI_API_KEY` | Vague 2+5 ok |
| `produce_api_service` | Render/Vercel + RapidAPI | `RAPIDAPI_PROVIDER_KEY` | Vague 2+5 ok |
| `sourcing_bestsellers` | — | — | toujours prêt |
| `sourcing_affiliate_intents` | Awin + Amazon Associates | `AWIN_API_TOKEN` + `AMAZON_ASSOCIATES_TAG_FR` | Vague 6 ok |

**→ Dès que Vagues 0+1+2 sont faites, on peut allumer 3 pipelines** (coloring,
card game, merch). Le reste s'allume au fur et à mesure des autres vagues.
