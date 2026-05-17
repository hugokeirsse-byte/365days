# 365days — Empire d'édition multi-pipeline Hugo Keirsse

**Mission** : système 100% automatisé, 100% légal, 100% gratuit (à l'inscription) qui détecte les opportunités du marché digital et produit en masse des designs / livres / STL prêts à uploader.

**Objectif** : 1500-5000 €/mois passifs à 12 mois, 4000-10 000 €/mois à 24 mois.

---

## 🧠 Architecture en 3 couches

```
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 1 — DÉTECTION (agents qui scannent le marché)      │
│  - agent_trend_explosion     (Voie A : ce qui explose)     │
│  - agent_niche_gap           (Voie B : demandes non comblées)│
│  - agent_trend_design_matcher (structures phrases Etsy)    │
│  - agent_external_trends     (Google/TikTok/Pinterest)     │
│  - seasonal_calendar         (events 12 semaines)          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 2 — DÉCISION (cerveau qui croise)                  │
│  - agent_opportunity_hunter  (croise tout)                 │
│  - agent_ideator_offline     (brainstorm 200 idées)        │
│  - agent_orchestrator        (auto-trigger pipelines)      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 3 — PRODUCTION (15+ pipelines)                     │
│  - produce_viral_formats     (65 formats × 25 niches)      │
│  - produce_iheart_v2         (scène DANS le cœur)          │
│  - produce_cultural_arbitrage (mots intraduisibles)        │
│  - produce_literal_idioms    (humour polyglotte)           │
│  - produce_bible_verses      (christian wall art US)       │
│  - produce_tumbler_wraps     (Etsy sublimation)            │
│  - produce_cope_pack         (multi-format COPE)           │
│  - produce_svg_pack          (Cricut/Silhouette)           │
│  - produce_coloring_book     (KDP-ready PDF)               │
│  - produce_kdp_cover         (cover auto)                  │
│  - produce_chess_book        (Mirabilia premium)           │
│  - produce_stl_parametric    (Cults3D + Printables)        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 4 — APPRENTISSAGE (boucle de feedback)             │
│  - agent_winner_amplifier    (multiplie ce qui vend)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 Documents stratégiques (lecture obligatoire)

| Fichier | Quand le lire |
|---|---|
| `INSCRIPTIONS_HUGO.md` | DEMAIN — séquence J1 d'inscription (30 min) |
| `UPLOAD_GUIDE.md` | Quand un compte Etsy/KDP est validé |
| `EMPIRE_HUGO.md` | Vue d'ensemble opérationnelle |
| `BRAND_IDENTITY.md` | Recherche format viral propriétaire (15 candidats) |
| `MASTER_LOOP.md` | Comment le système s'auto-évolue |
| `AUDIT_SYSTEME.md` | Forces / faiblesses / optimisations |
| `NOUVELLES_IDEES.md` | 8 nouveaux gisements + 20 plateformes additionnelles |
| `TARGETS_2026.md` | Recherche niches 2026 |
| `CULTURAL_ARBITRAGE_MERCH.md` | Bibliothèque 80 expressions intraduisibles |

---

## 🚀 Démarrage rapide (5 min)

### Sur ton tél, depuis n'importe où

1. **Voir l'inventaire** :
   ```
   python scripts/inventory_dashboard.py
   ```
   Te dit ce qui est prêt à uploader sur Etsy/KDP/Cults3D.

2. **Lancer une production** (depuis GitHub Actions UI sur mobile) :
   - Va sur https://github.com/hugokeirsse-byte/365days/actions
   - Choisis un workflow `Produce ...`
   - Run workflow → paramètres → Run

3. **Générer les listings Etsy** pour les designs produits :
   ```
   python scripts/etsy_listings_builder.py
   ```
   Crée `listing_etsy.txt` dans chaque dossier design.

4. **Générer les pins Pinterest** :
   ```
   python scripts/pinterest_descriptions_builder.py
   ```

---

## 🤖 Crons automatiques actifs (sur main)

| Quand | Quoi |
|---|---|
| Lundi 4h UTC | `agent_niche_gap` |
| Lundi 6h UTC | `agent_trend_explosion` + `seasonal_calendar` |
| Lundi 8h UTC | `agent_opportunity_hunter` (croise tout) |
| Mardi 4h UTC | `agent_external_trends` (Google+TikTok+Pinterest) |
| Mardi 5h UTC | `agent_trend_design_matcher` (Etsy bestsellers) |
| Mercredi 6h UTC | `agent_ideator_offline` (brainstorm 200 idées) |
| Jeudi 7h UTC | `agent_orchestrator` (auto-trigger productions) |
| Dimanche 22h UTC | `agent_winner_amplifier` (analyse ventes) |
| Toutes les 6h | `agent_trend_explosion` (data fraîche continue) |

---

## 💰 Stack de monétisation 100% gratuite à l'inscription

| Plateforme | Type | Marge | Inscription |
|---|---|---|---|
| Etsy Seller | Digital + POD | 70-85% | 5 min |
| Printful | POD physique | -coûts impression | 5 min |
| Redbubble | POD secondaire | 20% | 5 min |
| Society6 | Poster premium | 10% | 5 min |
| KDP | Livres papier | ~30% prix vente | 10 min |
| Cults3D | STL 3D | **80%** | 10 min |
| Printables | STL alt | trafic | 5 min |
| Pinterest Business | Trafic gratuit | - | 5 min |
| Spotify Podcasters | Audio | ~70% (1000 listeners) | 10 min |

---

## 🛡️ Engagements éthiques et légaux

- ✅ **100% légal** : sources publiques uniquement (Reddit JSON, Etsy HTML, Google Trends RSS, TikTok page publique)
- ✅ **Pas de bypass** : aucun captcha, aucun anti-fingerprint, aucun fake account
- ✅ **Pas de scraping login-required** : seulement les pages publiques affichées sans connexion
- ✅ **Domaine public uniquement** pour les textes (Bible KJV, idiomes traditionnels)
- ✅ **Pas de plagiat** : nos formats sont nos créations ou inspirés de structures publiques (proverbes, citations)
- ✅ **Conformité plateformes** : respect des TOS Etsy/Printful/KDP/Cults3D

---

## 📞 Quand contacter Claude

- **Nouveau pipeline / niche** → décris-moi, je code
- **Workflow plante** → screenshot du log Actions, j'analyse
- **Tu vois un bestseller concurrent** → URL + screenshot, je propose une réplique
- **Tu as une idée bizarre** → propose, on évalue
- **Tu veux pivoter** (abandonner Etsy, attaquer Cults3D…) → on en parle

---

**Le système est conçu pour fonctionner sans toi pendant 1 mois.** Au-delà tu auras juste du stock à uploader au retour.
