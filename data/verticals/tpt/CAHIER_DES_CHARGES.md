# CAHIER DES CHARGES — VERTICAL TPT (Teachers Pay Teachers)

> **Statut** : VERTICAL ACTIF — premier vertical text-first du système 365days
> **Type** : produit numérique passif (Couche 2). Aucune génération d'image payante requise.
> **Mis à jour** : 2026-06-02
> **Règle d'or du vertical** : *le contenu pédagogique doit être 100% correct, garanti par génération procédurale — jamais par hallucination LLM.*

---

## 0. POURQUOI CE VERTICAL EN PREMIER

| Critère | TPT | Raison |
|---|---|---|
| Génération d'image | **Aucune** (décoratif procédural ReportLab) | Pas de coût Fal.ai, pas de gibberish Pollinations |
| Correction du contenu | **Garantie** (maths/grilles générées par code) | Zéro risque d'hallucination = zéro mauvaise review |
| Automatisation | ★★★★★ | Un thème → N variantes en 1 run CI |
| Récurrence | Forte | Une fiche se vend des années, saisonnalité réexploitable |
| Marché | 253 M$ versés aux créateurs | Demande réelle, prouvée |
| Vitesse 1er € | 2-4 semaines | Rapide pour du passif |

**Décision** : TPT est le banc d'essai de toute l'architecture text-first. Ce qu'on valide ici (moteur de layout, boucle scan→CdC→prod→audit) se réplique ensuite sur Anki (#17), cheat sheets dev (#72), low-content KDP (#46), templates Notion (#60).

---

## 1. CE QU'ON VEND EXACTEMENT

### 1.1 Définition d'un livrable TPT

Un **produit TPT** = un **pack** (pas une fiche isolée) contenant :

1. **Worksheet(s)** — les fiches d'exercices, prêtes à imprimer (8.5×11", US Letter)
2. **Answer Key** — le corrigé complet (argument de vente #1 chez les profs)
3. **Cover / Thumbnail** — la 1ère image vue sur TPT (générée procéduralement, voir §5.4)
4. **Terms of Use** — page légale standard (1 page, template fixe)
5. **Credits page** — attribution polices/ressources (légal)

> Un pack TPT qui ne contient PAS de corrigé se vend 3-5× moins. Le corrigé est NON négociable.

### 1.2 Taxonomie des produits (par difficulté de production)

| Tier | Type | Contenu généré par | Image ? | Priorité |
|---|---|---|---|---|
| **A** | Maths (opérations, fractions, valeur de position, horloge, monnaie) | **Code procédural** (correct par construction) | Non | **1 — on commence ici** |
| **A** | Grilles/puzzles (sudoku enfant, mots mêlés, mots croisés, labyrinthes) | **Code procédural** | Non | 2 |
| **B** | Langue (vocabulaire, conjugaison, compréhension, phonics) | **LLM + validation** | Non | 3 |
| **B** | Sciences/QCM (quiz, vrai-faux, appariement) | **LLM + validation** | Non | 4 |
| **C** | Activités illustrées (coloriage pédagogique, flashcards imagées) | LLM + image | Oui (plus tard) | Reporté |

**On démarre exclusivement par le Tier A maths** : contenu généré par code = correction mathématiquement garantie = zéro mauvaise review possible sur le fond.

### 1.3 Le moat : différenciation vs les 1M+ de fiches existantes

Une fiche de maths générique ne se vend pas. Ce qui fait vendre :

1. **Thématisation saisonnière** — la MÊME fiche de multiplication déclinée Halloween / Noël / Saint-Valentin / Pâques / rentrée. Le prof cherche "multiplication Halloween worksheet" → SEO long-tail peu concurrencé.
2. **Différenciation par niveau** — 3 niveaux (support / on-level / challenge) dans le même pack. Les profs ADORENT car ils gèrent des classes hétérogènes.
3. **Corrigé impeccable** — toujours inclus, mis en page proprement.
4. **Mise en page pro** — marges propres, police lisible enfant (pas de Times), zones de réponse claires, pas d'encombrement.
5. **Auto-checking** — variantes "self-correcting" (code couleur, QR vers corrigé) = premium.

---

## 2. ARCHITECTURE DU SYSTÈME (A → Z)

```
┌─────────────────────────────────────────────────────────────────┐
│  COUCHE SCAN — détecte QUOI produire (2 sources)                  │
│                                                                   │
│  (A) SCAN TENDANCE     → ce qui se cherche/vend sur TPT & Google  │
│      scripts/tpt/scan_demand.py                                   │
│      sources : Google Trends (RSS/CSV), TPT search suggest,       │
│                calendrier scolaire US (saisonnalité)              │
│      sortie  : data/verticals/tpt/opportunities.json             │
│                                                                   │
│  (B) SCAN DEMANDE      → quelqu'un veut une fiche précise         │
│      (mutualisé avec le scanner global de services, voir §8)     │
│      sortie  : injecte une opportunité "on-demand" prioritaire   │
└───────────────────────────────┬───────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  COUCHE CdC — décide le pack précis à produire                    │
│  scripts/tpt/agent_tpt_cdc.py                                     │
│  prend la meilleure opportunité → génère product CdC (gate=pending)│
│  sortie : products/tpt/<id>/CAHIER_DES_CHARGES.md + cdc.json      │
└───────────────────────────────┬───────────────────────────────────┘
                                ↓  [GATE 1 — Hugo approuve en 30s]
┌─────────────────────────────────────────────────────────────────┐
│  COUCHE PRODUCTION — fabrique les PDF                             │
│  scripts/tpt/generate_worksheet.py  (moteur principal)            │
│  → worksheet.pdf + answer_key.pdf + cover.pdf + terms.pdf         │
│  → bundle ZIP prêt à uploader                                    │
│  Contenu maths = procédural (correct). Layout = ReportLab.        │
└───────────────────────────────┬───────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  COUCHE AUDIT — vérifie AVANT présentation                       │
│  scripts/tpt/audit_worksheet.py                                   │
│  checks : corrigé cohérent avec fiche, 0 réponse fausse,          │
│           densité OK (pas trop/pas assez), marges print-safe,     │
│           lisibilité (taille police mini), pages = attendu        │
└───────────────────────────────┬───────────────────────────────────┘
                                ↓  [GATE 2 — Hugo voit le PDF fini]
┌─────────────────────────────────────────────────────────────────┐
│  COUCHE PUBLICATION — Hugo uploade sur TPT (manuel, 5 min)        │
│  listing.md fournit : titre SEO, description, tags, prix          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. COUCHE SCAN — quoi produire

### 3.1 Scan tendance (`scan_demand.py`)

**Objectif** : sortir une liste classée d'opportunités `{skill, grade, theme, season, score}`.

**Sources gratuites, sans clé** :
- **Calendrier scolaire US** (procédural) : génère les fenêtres saisonnières 8-10 semaines à l'avance (Back to School août, Halloween oct, Thanksgiving nov, Christmas déc, Valentine fév, St Patrick mars, Easter avr, End of Year mai, Summer juin). C'est la source #1 : la saisonnalité TPT est ultra-prévisible.
- **TPT search autosuggest** : l'endpoint public de suggestion de recherche TPT renvoie les complétions populaires (ex. "multiplication" → "multiplication worksheets, multiplication color by number, multiplication facts"). Scrape léger, respectueux (1 req/skill, cache 7j).
- **Google Trends** (pytrends optionnel, ou CSV manuel) : valide qu'un terme monte.

**Scoring d'une opportunité** :
```
score = demande(0-40) + saisonnalité(0-30) + faible_concurrence(0-20) + facilité_prod(0-10)
```
- `demande` : volume de recherche relatif
- `saisonnalité` : proximité d'un event (pic = +30, hors-saison = 0)
- `faible_concurrence` : long-tail (3+ mots) = bonus
- `facilité_prod` : Tier A = 10, Tier B = 5, Tier C = 2

**Sortie** : `data/verticals/tpt/opportunities.json` (10-20 opportunités triées).

### 3.2 Scan demande on-demand (mutualisé §8)

Si le scanner global de services détecte une demande explicite ("I need a 3rd grade fractions worksheet pack"), il injecte une opportunité avec `source: "on_demand"` et `score: 100` (priorité absolue) dans le même `opportunities.json`.

---

## 4. COUCHE CdC — le contrat de production

### 4.1 Fichier `cdc.json` (par produit)

Champs **bloquants** que l'audit vérifie :

```json
{
  "id": "tpt_2026-06-02_multiplication_halloween_g3",
  "created_at": "2026-06-02T08:00:00Z",
  "vertical": "tpt",
  "source": "trend",              // trend | on_demand
  "skill": "multiplication",      // compétence pédagogique
  "skill_params": {               // paramètres procéduraux EXACTS
    "operation": "mul",
    "factor_min": 2, "factor_max": 12,
    "problems_per_page": 25,
    "levels": ["support", "on_level", "challenge"]
  },
  "grade": "3",                   // niveau scolaire US (K-12)
  "theme": "halloween",           // habillage visuel/lexical
  "season_window": "2026-10-01..2026-10-31",
  "pack_contents": ["worksheet", "answer_key", "cover", "terms"],
  "pages_expected": { "worksheet": 3, "answer_key": 3 },
  "title_seo": "Halloween Multiplication Worksheets 3rd Grade — Differentiated 3 Levels",
  "tags": ["halloween", "multiplication", "3rd grade", "differentiated", "no prep", "math facts"],
  "price_usd": 3.50,
  "audit_criteria": [
    { "criterion": "answer_key matches worksheet 100%", "blocking": true },
    { "criterion": "0 réponse mathématiquement fausse", "blocking": true },
    { "criterion": "marges print-safe >= 0.5in", "blocking": true },
    { "criterion": "police corps >= 14pt (lisibilité enfant)", "blocking": true },
    { "criterion": "pages produites == pages_expected", "blocking": true },
    { "criterion": "thème appliqué (titre + déco + lexique)", "blocking": false }
  ],
  "human_gates": { "gate_start": "pending", "gate_end": "not_reached" }
}
```

### 4.2 `CAHIER_DES_CHARGES.md` (par produit)

Document lisible par Hugo en 30s pour le GATE 1 : promesse, aperçu du contenu, mise en page, prix, mots-clés. Généré par `agent_tpt_cdc.py`.

---

## 5. COUCHE PRODUCTION — le moteur

### 5.1 Principe : contenu procédural, layout ReportLab

- **Le contenu maths est généré par du code Python pur** → chaque problème a sa réponse calculée par la même fonction → le corrigé est correct par construction. Impossible d'avoir une réponse fausse.
- **Le layout est fait en ReportLab** (vectoriel, 300 DPI implicite, print-ready).
- **Aucune image générée** : la décoration (bordures thématiques, icônes citrouille/sapin, séparateurs) est dessinée procéduralement (formes ReportLab) ou via un petit jeu d'icônes SVG/police symboles libres de droits.

### 5.2 Générateurs de compétences (Tier A — le cœur)

Chaque "skill" est un module qui expose `generate(params, seed) -> (problems, answers)` :

| Skill | Paramètres | Garantie |
|---|---|---|
| `arithmetic` | operation (add/sub/mul/div), plages, retenue oui/non | réponses calculées |
| `fractions` | add/sub/simplify/compare, dénominateurs | réponses calculées |
| `place_value` | nb de chiffres, forme (expanded/standard/word) | réponses calculées |
| `telling_time` | pas (heure/demie/quart/5min) | réponses calculées |
| `money` | devise, opération (rendu monnaie, total) | réponses calculées |
| `word_problems` | template + valeurs procédurales | énoncé LLM, **chiffres et réponse par code** |
| `number_grids` | suites, nombres manquants | réponses calculées |

> **Word problems** : le LLM écrit UNIQUEMENT l'habillage narratif ("Sarah a X citrouilles…"), mais X et la réponse sont injectés par le code. Le LLM ne calcule jamais.

### 5.3 Différenciation (3 niveaux dans 1 pack)

- **support** : plage réduite, moins de problèmes, indices visuels
- **on_level** : standard du grade
- **challenge** : plage étendue, problèmes mixtes, bonus

### 5.4 Cover / thumbnail procédurale

Page 1 du pack = vignette TPT. Générée en ReportLab :
- Bandeau couleur thème (orange Halloween, rouge Noël…)
- Titre gros, sous-titre, niveau, "3 Levels Included", "Answer Keys Included", "No Prep — Just Print"
- Cadre décoratif thématique (formes procédurales)
- Pas de génération IA → cohérent, lisible, gratuit.

### 5.5 Sortie

```
products/tpt/<id>/
├── worksheet.pdf        # les fiches élève
├── answer_key.pdf       # corrigés
├── cover.pdf            # thumbnail/cover TPT
├── terms.pdf            # terms of use (template)
├── bundle.zip           # tout regroupé, prêt upload
├── listing.md           # titre SEO + description + tags + prix
├── cdc.json             # le contrat
└── audit.json           # résultat audit
```

---

## 6. COUCHE AUDIT (`audit_worksheet.py`)

Vérifie AVANT de présenter à Hugo. Tous bloquants sauf mention :

1. **Cohérence corrigé** : re-génère les réponses depuis le seed + params, compare au PDF corrigé. 100% match obligatoire.
2. **Marges print-safe** : ≥ 0.5in tous bords (sinon coupe à l'impression).
3. **Lisibilité** : police corps ≥ 14pt (enfants).
4. **Densité** : entre 15 et 30 problèmes/page (ni vide ni surchargé).
5. **Comptage pages** : == `pages_expected`.
6. **Thème** (non bloquant) : titre + couleur + lexique appliqués.

Sortie `audit.json` : `{ "passed": true/false, "checks": [...] }`. Si échec bloquant → STOP, alerte Hugo, ne publie pas.

---

## 7. COUCHE PUBLICATION (Hugo, manuel ~5 min)

`listing.md` fournit clé-en-main :
- **Titre SEO** (≤ ~80 car, mots-clés en tête)
- **Description** (structure TPT : accroche, ce qui est inclus, niveaux, "no prep", standards CCSS visés)
- **Tags** (TPT en demande 4-8)
- **Prix** conseillé (voir §9)
- **Standards alignés** (Common Core ex. `3.OA.C.7`)

Hugo : upload sur TPT, copie-colle, publie. Plus tard : semi-auto si API/CSV TPT.

---

## 8. INTÉGRATION AU SYSTÈME GLOBAL (scan demande + tendance)

Le vertical TPT ne réinvente pas le scanner. Il branche sur le **moteur de scan unique** du système 365days :

```
scripts/scan/scan_engine.py   (moteur générique, à construire — sert TOUS les verticaux)
   ├── source: trends      → alimente opportunities.json de chaque vertical
   └── source: on_demand   → détecte une demande explicite (Upwork/Reddit/Malt/email)
                             classe par vertical, injecte en priorité 100
```

- **Mode tendance** : pousse proactivement des opportunités (vitrine passive).
- **Mode demande** : si quelqu'un demande explicitement une fiche → on répond (service). Même moteur, sortie routée vers le bon vertical.

> Le scanner TPT (`scan_demand.py`) est la **première implémentation concrète** du mode tendance. Le mode demande global se construit juste après, en réutilisant la même structure d'`opportunity`.

---

## 9. ÉCONOMIE DU VERTICAL

| Poste | Valeur |
|---|---|
| Coût production / pack | **0 €** (CI GitHub gratuit, pas d'IA payante) |
| Temps Hugo / pack | ~5 min (gates + upload) |
| Prix de vente unitaire | 2.50 – 5.00 $ (pack simple), 6 – 12 $ (bundle saisonnier) |
| Commission TPT | 20% (vendeur basique) ou 15% (Premium 60$/an) |
| Net / vente | ~2 – 4 $ |
| Volume cible an 1 | 100 – 300 packs en catalogue |
| Revenu réaliste | 500 – 5000 $/mois (vendeur établi, cf. catalogue #11) |

**Stratégie volume** : 1 thème de compétence × 5 saisons × 3 grades = 15 packs depuis UNE base de générateur. Le moteur amortit l'effort.

---

## 10. ROADMAP DU VERTICAL

| Étape | Livrable | Statut |
|---|---|---|
| 0 | Ce CdC | ✅ |
| 1 | Moteur `generate_worksheet.py` (skill arithmetic) + sample PDF | 🔨 en cours |
| 2 | Audit `audit_worksheet.py` | à faire |
| 3 | CdC generator `agent_tpt_cdc.py` + workflow CI | à faire |
| 4 | Scanner `scan_demand.py` (saisonnier + TPT suggest) | à faire |
| 5 | Skills additionnels (fractions, place_value, time, money) | à faire |
| 6 | 1er pack publié sur TPT par Hugo | GATE Hugo |
| 7 | Réplication du pattern au vertical suivant (Anki #17) | après livrable |

---

## 11. RÈGLES NON-NÉGOCIABLES DU VERTICAL

- ❌ Jamais de réponse calculée par LLM (hallucination = mauvaise review = mort sur TPT).
- ❌ Jamais publier sans corrigé.
- ❌ Jamais de police < 14pt pour le corps élève.
- ✅ Toujours 3 niveaux de différenciation quand la compétence le permet.
- ✅ Toujours print-safe (marges ≥ 0.5in, US Letter).
- ✅ Toujours créditer polices/ressources (page credits).
- ✅ Contenu généré par code pour tout ce qui est calculable.
