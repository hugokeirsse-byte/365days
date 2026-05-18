# 🎯 STRATEGY — document unique de référence stratégique

**Mise à jour** : 2026-05-18
Consolide : EMPIRE_HUGO + BRIEFING_18MAI + LECONS_DU_WEB + AUDIT_SYSTEME + MASTER_LOOP + BRAND_IDENTITY + NOUVELLES_IDEES (archivés dans `archive/`).

---

## 🏛️ VISION

**Empire d'édition multi-pipeline 100% gratuit à l'inscription, depuis un téléphone Android, budget 0€.**

- Objectif réaliste 12 mois : 500-2000 €/mois passifs
- Objectif réaliste 24 mois : 2000-6000 €/mois passifs
- Système qui s'auto-alimente : scan trends → produire → uploader → mesurer → itérer

---

## 🎯 LES 4 PILIERS DE LA STRATÉGIE FINALE (post-audit)

Après audit honnête (cf. archive/LECONS_DU_WEB.md), on concentre sur 4 piliers gratuits :

### Pilier 1 : 🎲 JEUX DE CARTES POD (The Game Crafter / BoardGamesMaker)
- **Mécanique non protégée** par copyright (seul nom et identité visuelle le sont)
- Décline 1 mécanique (« Cliché Maximum ») × 10-20 niches ultra-spécifiques
- **5 decks codés** : DevOps, Pompiers, Profs, Pêche, Nurses
- Prix : 19.99$/deck, marge ~12-15$
- Pipeline : `produce_card_game.py`

### Pilier 2 : 📚 LOW-CONTENT KDP (Amazon)
- 100% offline (PIL + ReportLab), zéro IA image
- **Qualité parfaite garantie** (texte vectoriel TTF)
- **10 livres codés** : fishing_log, bird_watching, crochet_tracker, pet_health, sourdough_log, dnd_campaign, garden_planner, climbing_log, vinyl_collection, brewing_log
- Format : 6×9 inches paperback 100 pages
- Prix : 7.99$/livre, marge ~3$
- Pipeline : `produce_lowcontent_kdp.py`

### Pilier 3 : 📐 STL CULTS3D / PRINTABLES
- **80% royalties** sur Cults3D (le meilleur split du marché)
- Objets paramétriques génériques + objets fonctionnels nichés
- **Pipeline actuel** : bookmark, keychain, coaster, door_plate × 6 templates
- **À étendre** : organisateurs, supports tél, OEM replacement parts
- Pipeline : `produce_stl_parametric.py`

### Pilier 4 : 🎨 POD PHYSIQUE (Redbubble + TeePublic + Zazzle + Society6)
- T-shirts, posters, stickers, mugs, marque-pages
- 0€ à l'inscription, marge fixée par nous
- Pipelines : `produce_iheart_v3/v4`, `produce_viral_formats_v2`, `produce_quotes_minimal`, `produce_bible_verses_v2`, `produce_cultural_arbitrage_v2`, `produce_literal_idioms_v2`, `produce_wedding_stationery`, `produce_tumbler_wraps`

---

## 🧠 ARCHITECTURE EN 4 COUCHES

```
┌─ COUCHE 1 — DÉTECTION (5 agents Reddit/Etsy/Google) ────────┐
│ agent_trend_explosion  (Voie A : ce qui explose)            │
│ agent_niche_gap        (Voie B : demandes non comblées)     │
│ agent_trend_design_matcher (Etsy bestsellers structures)    │
│ agent_external_trends  (Google + TikTok + Pinterest)        │
│ seasonal_calendar      (events 12 semaines)                 │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─ COUCHE 2 — DÉCISION ───────────────────────────────────────┐
│ agent_opportunity_hunter   (croise tout)                    │
│ agent_ideator_offline      (brainstorm 200 idées)           │
│ agent_orchestrator         (1 trigger/run anti-spam)        │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─ COUCHE 3 — PRODUCTION (16+ pipelines) ─────────────────────┐
│ Cartes : produce_card_game                                  │
│ KDP : produce_lowcontent_kdp, produce_coloring_book,        │
│       produce_chess_book, produce_kdp_cover                 │
│ STL : produce_stl_parametric                                │
│ POD : produce_iheart_v3, v4, produce_viral_formats_v2,      │
│       produce_quotes_minimal, produce_bible_verses_v2,      │
│       produce_cultural_arbitrage_v2, produce_literal_idioms_v2,│
│       produce_wedding_stationery, produce_tumbler_wraps,    │
│       produce_cope_pack, produce_svg_pack                   │
│ Compositeur : scripts/lib/design_composer.py (réutilisable) │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─ COUCHE 4 — QC + APPRENTISSAGE ─────────────────────────────┐
│ agent_visual_audit        (heuristique sans clé)            │
│ agent_gemini_quality_check (Gemini Vision — besoin clé)     │
│ agent_auto_regen          (supprime rejected + retrigger)   │
│ agent_winner_amplifier    (multiplie ce qui vend)           │
└─────────────────────────────────────────────────────────────┘
```

---

## ⏰ CYCLE HEBDOMADAIRE AUTOMATIQUE (crons sur main)

| Quand | Quoi |
|---|---|
| Lundi 4h UTC | `agent_niche_gap` |
| Lundi 6h UTC | `agent_trend_explosion` + `seasonal_calendar` |
| Lundi 8h UTC | `agent_opportunity_hunter` |
| Lundi 0h30 | `agent_auto_regen` (cleanup rejected) |
| Mardi 4h UTC | `agent_external_trends` |
| Mardi 5h UTC | `agent_trend_design_matcher` |
| Mercredi 6h UTC | `agent_ideator_offline` |
| Jeudi 7h UTC | `agent_orchestrator` (trigger productions) |
| Dimanche 22h UTC | `agent_winner_amplifier` |
| Tous les jours 23h | `agent_visual_audit` |
| Tous les jours 0h | `agent_gemini_quality_check` (si clé) |
| Toutes les 6h | `agent_trend_explosion` (data fraîche) |

---

## 🛡️ RÈGLES NON-NÉGOCIABLES

### Légal / éthique
- ✅ Sources publiques uniquement (Reddit JSON, Etsy HTML, Google Trends RSS)
- ✅ Pollinations.ai (open-source, pas de SynthID)
- ✅ Domaine public pour textes (Bible KJV, idiomes traditionnels)
- ✅ Mécaniques de jeu (non protégées par copyright)
- ❌ Pas de copie de noms/visuels protégés (« Blanc Manger Coco » = marque déposée)
- ❌ Pas de captcha bypass, fake accounts, anti-fingerprint
- ❌ Pas de scraping login-required

### Etsy 2025-2026 (anti-ban)
- ✅ **Disclosure AI** auto dans chaque listing (variante random)
- ✅ Coche « Designed by » pas « Made by »
- ✅ Max 5 listings/jour, jamais batch automatique
- ✅ Variation forte de descriptions (anti-pattern)
- ❌ Pas de templates fixes identiques (règle juin 2025)

---

## 📈 LES 3 BOUCLES D'AUTO-AMÉLIORATION

### Boucle DÉCOUVERTE
Reddit → Etsy bestsellers → Google/TikTok → opportunity_hunter → opportunities.json

### Boucle PRODUCTION
opportunities.json → orchestrator → trigger pipelines → audit → upload Hugo

### Boucle APPRENTISSAGE (besoin Hugo)
Hugo entre ventes hebdo dans `data/sales_feedback.csv` → `winner_amplifier` → multiplie ce qui marche, descore ce qui flop

---

## 💀 PROBLÈME ACTUEL & LIMITES TECHNIQUES

### Limite Pollinations Flux (gratuit)
- **Texte généré = gibberish** → on bypass avec overlay Pillow (V2/V3/V4)
- Illustrations : mains tordues, anatomie approximative, sujets pas toujours fidèles au prompt
- **Pollinations IGNORE souvent les contraintes négatives** : « no heart symbols » → met un cœur quand même
- **Anatomie cassée fréquente** : double chien sur iheart_v4 my_dog, double cœur sur iheart_v3 fishing
- 70% des designs sont vendables, 30% à filtrer via audit
- **Solution réelle** : HF SDXL + ControlNet/InstantID/IP-Adapter (besoin clé HF gratuite)

### Pipelines EN PAUSE (production bloquée jusqu'à inscriptions Hugo)
- ⏸ `produce_iheart_v3` (cadre cœur + scène) — double cœur fréquent
- ⏸ `produce_iheart_v4` (mask cœur) — anatomie sujet cassée
- ⏸ `produce_coloring_book` — sujets off-topic, traits trop fins
- **Réactivation** : dès que `HF_API_KEY` est dispo, on active `produce_iheart_hf.py` qui utilise SDXL + ControlNet pour vrai contrôle

### Limite QC heuristique (sans Gemini)
- Détecte le texte gibberish, pas les défauts d'illustration
- **Solution** : `agent_gemini_quality_check` s'active dès clé Gemini dispo

### Limite layouts (corrigée le 18/05)
- Cœur paramétrique mathématique (équation x=16sin³t, y=13cost-5cos2t...) → cœur PROPRE
- Auto-sizing typo
- Décoratifs Pillow garantis nets

---

## 🎰 STACK 100% GRATUIT (cf. INSCRIPTIONS_HUGO.md)

| Catégorie | Plateforme | Inscription |
|---|---|---|
| Légal | URSSAF | 0€ |
| Sécurité | Bitwarden | 0€ |
| POD physique | Redbubble + TeePublic + Zazzle + Society6 | 0€ |
| POD jeux | The Game Crafter + BoardGamesMaker | 0€ |
| STL 3D | Cults3D (80% royalty) + Printables | 0€ |
| Livres | KDP | 0€ |
| Digital direct | Gumroad + Payhip + Ko-fi | 0€ |
| Trafic | Pinterest + Reddit + TikTok + Instagram | 0€ |
| IA Stack | HF Token + Gemini API | 0€ |

**Etsy reporté quand cash flow ≥ 200€/mois** (0,20$/listing à l'inscription = ~40$ pour démarrer).

---

## 🔮 ROADMAP

### Sprint 1 (cette semaine — code prêt)
- ✅ design_composer.py refondu (cœur paramétrique + grille)
- ✅ 5 pipelines V2/V3/V4 + V5 (gibberish-proof)
- ✅ produce_card_game.py (5 decks Cliché Maximum)
- ✅ produce_lowcontent_kdp.py (10 journals)
- ✅ agent_auto_regen.py (cleanup automatique)
- Hugo inscrit Bitwarden + URSSAF + Cults3D + Redbubble + TGC + KDP

### Sprint 2 (semaine 2-3)
- Refondre `produce_iheart_v5.py` (sans "I", typo par niche, cœur paramétrique)
- 5 nouveaux decks card_game (gamers, alpinistes, wicca, agence comm, vanlife)
- 10 nouveaux journals KDP
- 50+ STL bookmarks/keychains/coasters/door_plates × 6 templates
- multi_platform_listings_builder (Redbubble + Zazzle + Cults3D)

### Sprint 3 (mois 2 — besoin HF + Gemini)
- Coloring books V2 via HF SDXL + ControlNet line-art
- Gemini Vision QC sur tous les designs
- Bot ideator LLM (Groq + Gemini pour nouvelles idées de cartes)
- Romance ebook KDP

### Sprint 4 (mois 3 — diversification)
- Newsletter Substack/Beehiiv niche tech
- Pinterest auto-publisher
- TikTok faceless niche

### Au-delà (mois 6+)
- Hardware (3D printer, graveur laser)
- App mobile (extension des jeux qui marchent)

---

## 📊 ESTIMATIONS HONNÊTES (sources : Reddit/Medium 2025-2026)

| Pilier | Production | ROI réaliste mois 3 | ROI réaliste mois 12 |
|---|---|---|---|
| Jeux cartes TGC | 5-10 decks | 50-200€/mois | 300-1500€/mois |
| KDP low-content | 10-30 livres | 30-100€/mois | 200-1000€/mois |
| STL Cults3D | 50-200 STL | 30-150€/mois | 200-2000€/mois |
| POD Redbubble/Zazzle | 100-500 designs | 20-100€/mois | 100-800€/mois |
| **TOTAL** | | **130-550€/mois** | **800-5300€/mois** |

**Médiane réaliste** : 250-400€/mois à 6 mois, 1500-3000€/mois à 18 mois.

---

## 🎓 PRINCIPES DE CROISSANCE

1. **Niche profonde > volume large** (corrigé après audit du 17/05)
2. **Pollinations gratuit > IA payante** (au moins en V1)
3. **Layout overlay Pillow > texte généré Flux** (qualité garantie)
4. **Cadencement humain > spam automatique** (Etsy ban-proof)
5. **2-3 boutiques par catégorie > 1 boutique tout** (anti-fragilité)
6. **Hugo uploade manuellement** (contrôle qualité humain + cohérence Etsy)
7. **Réinvestir 100% du chiffre les 6 premiers mois** (clés API HF/Gemini → meilleurs modèles)

---

## 📁 ARCHIVE

Anciens documents (toujours consultables) :
- `archive/EMPIRE_HUGO.md` — vision initiale
- `archive/BRIEFING_18MAI.md` — analyse 11 idées du 17/05
- `archive/LECONS_DU_WEB.md` — rapport entrepreneurs similaires
- `archive/AUDIT_SYSTEME.md` — audit forces/faiblesses
- `archive/MASTER_LOOP.md` — cycle auto-évolutif
- `archive/BRAND_IDENTITY.md` — recherche format propriétaire
- `archive/NOUVELLES_IDEES.md` — 8 idées + 20 plateformes
- `archive/TARGETS_2026.md` — recherche niches 2026
- `archive/CULTURAL_ARBITRAGE_MERCH.md` — 80 expressions intraduisibles

**Tu consultes en priorité** : README.md + STRATEGY.md (ce fichier) + INSCRIPTIONS_HUGO.md + UPLOAD_GUIDE.md + AUDIT_QUALITE.md.
