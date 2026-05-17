# 🔁 MASTER LOOP — le cycle d'évolution continue du système

**Objectif** : un système qui **s'auto-alimente, s'auto-corrige, s'auto-améliore** sans intervention manuelle (sauf publication finale par Hugo).

---

## ⏰ Le cycle hebdomadaire automatique

```
┌─────────────────────────────────────────────────────────────────┐
│  LUNDI    00h  cron : seasonal_calendar.py                       │
│  LUNDI    06h  cron : agent_trend_explosion (Voie A)             │
│  LUNDI    04h  cron : agent_niche_gap (Voie B)                   │
│  LUNDI    08h  cron : opportunity_hunter (croise A+B)            │
│  ─────────────────────────────────────────                       │
│  MARDI    05h  cron : trend_design_matcher (scrape Etsy)         │
│  ─────────────────────────────────────────                       │
│  MERCREDI 06h  cron : ideator_offline (brainstorm 200 idées)     │
│  ─────────────────────────────────────────                       │
│  JEUDI    Hugo : check dashboard, choisit 3-5 productions        │
│  ─────────────────────────────────────────                       │
│  VEND.    Production : Hugo trigger les pipelines choisis        │
│  ─────────────────────────────────────────                       │
│  SAM.     Hugo uploads sur les plateformes (Etsy, Printful…)     │
│  ─────────────────────────────────────────                       │
│  DIM.     Hugo entre les ventes de la semaine                    │
│           → cycle recommence Lundi avec nouvelles données        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧬 Les 3 boucles d'auto-amélioration

### Boucle 1 : DÉCOUVERTE (input → opportunités)

```
Reddit r/Etsy + r/PrintOnDemand   ──┐
                                     ├──> opportunity_hunter
Reddit r/passionate_niches        ──┤      │
Etsy bestsellers (HTML public)    ──┤      │
Seasonal events calendar          ──┘      ▼
                                     opportunities.json
                                           │
                                           ▼
                                    Hugo décide
```

**Quoi évolue** : nouvelles structures de phrases découvertes chaque semaine via `trend_design_matcher`.

### Boucle 2 : PRODUCTION (opportunités → assets)

```
opportunities.json                    ──┐
ideas_brainstorm.json                 ──┤
trend_design_matches.json (structures)  ├──> Hugo trigger
                                         │      │
                                         ▼      ▼
                              produce_viral_formats / iheart / etc.
                                         │
                                         ▼
                              products/<pipeline>/ assets
                                         │
                                         ▼
                              etsy_listings_builder.py
                              pinterest_descriptions_builder.py
                                         │
                                         ▼
                              listing_etsy.txt + pinterest_pin.txt
                                         │
                                         ▼
                                    Hugo upload
```

**Quoi évolue** : on multiplie ce qui marche, on supprime ce qui flop.

### Boucle 3 : APPRENTISSAGE (ventes → corrections)

```
Hugo entre ventes ──> data/sales_feedback.csv
                              │
                              ▼
                  agent_winner_amplifier (à coder)
                              │
                              ├──> Designs qui vendent : 10 variantes
                              │
                              └──> Niches qui flop 60j : descore -2
                                              │
                                              ▼
                              prochaine opportunity_hunter run
                              prend en compte les ajustements
```

**Quoi évolue** : la liste des niches actives, les scores, les priorités.

---

## 📂 Format `data/sales_feedback.csv` (à remplir par Hugo)

```csv
date,platform,design_id,niche,format_family,units_sold,revenue_eur,notes
2026-05-25,etsy,iheart_v2_fishing_vintage_engraving,fishing,iheart_v2,3,13.50,"décollage rapide"
2026-05-25,etsy,viral_diagnosed_terminal_cats_v0,cats,medical,5,19.95,"explosion sur TikTok"
2026-05-26,kdp,coloring_mystical_mushrooms,mushroom,coloring_book,2,15.98,
2026-05-27,redbubble,iheart_v2_reading_watercolor_modern,reading,iheart_v2,1,3.20,
```

**Pas besoin d'être exhaustif** : 5 minutes/dimanche suffisent. Le système s'occupe du reste.

---

## 🤖 Les rôles précis de chaque agent

| Agent | Fréquence | Output | Consommé par |
|---|---|---|---|
| `agent_trend_explosion` | 6h | `data/trend_explosion.json` | opportunity_hunter, ideator |
| `agent_niche_gap` | 1j | `data/niche_gap.json` | opportunity_hunter, ideator |
| `agent_trend_design_matcher` | 1 sem (mardi) | `data/trend_design_matches.json` | viral_formats injector |
| `seasonal_calendar` | 1j | `data/upcoming_events.json` | opportunity_hunter, ideator |
| `agent_ideator_offline` | 1 sem (merc) | `data/ideas_brainstorm.json` | Hugo (lecture) |
| `agent_opportunity_hunter` | 1 sem (lundi) | `data/opportunities.json` | Hugo (décision) |
| `agent_auditor` | manuel | qualité visuelle | Hugo (revue) |
| `agent_winner_amplifier` (à coder) | 1 sem | tâches `produce_*` ré-priorisées | Hugo (ou auto-trigger) |

---

## 🔮 Quand le système atteindra sa vitesse de croisière

**Cible : mois 3**

- 10+ pipelines actifs, alimentés par 5+ agents en cascade
- 500+ designs/livres produits par semaine en automatique
- Hugo : 20 min/jour upload + 30 min/dimanche analyse
- Sales feedback alimentant la boucle 3 → optimisation continue
- Nouveaux formats viraux découverts toutes les 2 semaines via Trend Design Matcher
- 1 nouvelle plateforme exploitée par mois (Creative Market, Society6, Spotify, etc.)

**Indicateur de succès** : revenus mensuels × 2 toutes les 4-8 semaines pendant les 6 premiers mois.

---

## 🛟 Plan de récupération en cas de problème

### Si Pollinations bloque
→ Switch backup HuggingFace SDXL (à activer dès clé HF dispo)

### Si Etsy ferme la boutique
→ Diversification déjà en place (Redbubble, Society6, Cults3D, KDP)
→ Re-publier sur shop secondaire en 24h

### Si Hugo part en vacances 1 mois
→ Les agents continuent à scanner et produire
→ Stock accumulé prêt à uploader au retour
→ Aucun impact si crons sur main

### Si GitHub Actions atteint la limite
→ Réduire `MAX_DESIGNS` par run
→ Prioriser top 10 opportunités au lieu de top 30
→ Passer le repo en public (Actions illimitées)

### Si un format propriétaire flop
→ Les 64 autres formats viraux + les pipelines I❤️v2, cultural arbitrage, idioms continuent
→ Aucun SPOF (Single Point Of Failure)

---

## 🎯 La règle d'or

**"Run, measure, double down on what works, kill what doesn't, repeat."**

Pas d'attachement émotionnel aux niches/formats qui flop. La data décide.
