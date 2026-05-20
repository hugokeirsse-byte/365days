# 🗺️ MAP — Business × Agents IA perpétuels

**Date** : 2026-05-19
**Doctrine** : *« Aucune IA ne tourne en continu. Tout est en cron espacé pour rester sous quotas gratuits. »*

Ce document est la **carte mentale unique** : quels business on lance, quels agents les alimentent, à quelle fréquence, avec quel LLM.

---

## 📜 PRINCIPE DE LA CASCADE TEMPORELLE

Au lieu d'IA en continu (impossible à 0€), on **espace les appels** dans le temps pour rester sous les quotas gratuits qui se renouvellent :

```
Gemini   : 1500 req/jour gratuit → on cible 50-200 req/jour pour tout le système
Groq     : ~30 req/min          → on plafonne à 10/min volontairement
Mistral  : ~5 req/min           → on cible 200 req/jour
Cohere   : 1000 req/mois free   → 30/jour
HuggingFace : 30k req/mois free → 1000/jour
Replicate : 5$ trial            → utilisé sporadiquement pour upscale/colorisation
Perplexity : 5$ trial           → veille hebdo ciblée
```

**Effet** : chaque rôle d'agent dort entre 2 réveils. Le système est *perpétuel* dans le sens où il **tourne pour toujours**, pas dans le sens où il est *continu*.

**À éviter** : créer plusieurs comptes chez un même provider → ban assuré.
**Solution propre** : multi-provider en rotation via `llm_routing.json`.

---

## 🏢 PARTIE 1 — LES 13 BUSINESS À LANCER

### 🟢 Top 8 (à allumer dès Vagues 0+1+2 finies)

| # | Business | Brand | Plateformes | Module(s) | Score /40 |
|---|---|---|---|---|---|
| 1 | **Coloriages historiques vintage** (Köhler, Audubon, Vésale, Haeckel) | Heritage Coloring | KDP, Redbubble (posters), Gumroad | U + D | **40/40** |
| 2 | **Merch cross-canal** (1 design × 7 supports) | toutes brands | Redbubble, TeePublic, Zazzle, Society6, Spring, Amazon Merch | B | 38.5 |
| 3 | **Coloriages stylés modernes** (cottagecore, mushrooms, witch) | Modern Cozy | KDP, Gumroad | L | 37.5 |
| 4 | **Restauration vintage** (upscale + colorisation archives) | Heritage Coloring | Redbubble posters, KDP collector | P | 38.0 |
| 5 | **Jeux de cartes humour métier** (DevOps, Pompiers, Profs, Nurses, Pêche) | Pocket Decks | TGC, BGM, Gumroad print-and-play | A | 31.0 |
| 6 | **Bébés crossover super-héros PD** (Stardust×Phantom, Heap×Captain Wonder…) | Iconic Offspring | Redbubble stickers, KDP coloring, mini-books | W | 30.5 |
| 7 | **Mashups culturels** (expressions intraduisibles + visuel) | Modern Cozy | Redbubble, KDP, mug | V | 32.5 |
| 8 | **Coloring KDP low-content** (journaux, planners, gratitude) | Modern Cozy | KDP exclusif | D | 35.0 |

### 🟡 Middle tier (Vague 3+)

| # | Business | Quand | Module |
|---|---|---|---|
| 9 | **Fictions courtes KDP** (contes cozy, dark academia) | Vague 2+3 | K |
| 10 | **AR filters TikTok/Spark** (cape héros, transition vintage) | Vague 4 | Q |
| 11 | **Vidéos faceless YouTube** (process coloring, lore PD) | Vague 4 | C |
| 12 | **STL paramétriques** (Cults3D, Printables, MyMiniFactory) | Vague 5 | M2 |
| 13 | **Jeux mobiles casual** (squelettes Godot/Phaser GitHub + assets Kenney/OpenGameArt) | Vague 5 | S |
| 14 | **Affiliation 15 marchés M1→M15** | Vague 6 | dédié |

### 🔴 Reportés (revenus lents)
- Micro-services API (E), Synthèses rapports (R), Mods (H), Audio packs (I), Open data (J)

### ❌ Abandonnés
- Sites SEO AdSense (F), Extensions navigateur (G), ChatDev multi-agents (O)

---

## 🤖 PARTIE 2 — LES 27 RÔLES D'IA PERPÉTUELS

### 🔭 Antennes (détection) — 6 rôles

| # | Rôle | Fréquence | LLM utilisé | Coût |
|---|---|---|---|---|
| 1 | **Éclaireur Bestsellers** — scrape top-ventes KDP/Etsy/Redbubble/Cults3D | daily 1h UTC | Python pur (HTTP) | 0 |
| 2 | **Critique de Plaintes** — extrait pain points reviews 1-3★ | daily 2h | Mistral small | gratuit |
| 3 | **Tendanceur** — veille TikTok/Pinterest/Google Trends | 4×/jour (toutes 6h) | Gemini Flash | gratuit (~30 req/j) |
| 4 | **Saisonnier** — events calendaires 12 semaines à l'avance | weekly lundi | Python pur | 0 |
| 5 | **Archéologue PD** — refresh Smithsonian, Met, Rijks, BHL, NYPL | weekly samedi | Python pur | 0 |
| 6 | **Affiliate Hunter** — scan X/Reddit pour intentions d'achat | 2×/jour | Mistral small | gratuit |

### 🧠 Cerveaux (synthèse) — 5 rôles

| # | Rôle | Fréquence | LLM utilisé |
|---|---|---|---|
| 7 | **Synthétiseur** — fusion bestsellers + pain points + trends → winning_formula.json | daily 3h | Gemini Flash |
| 8 | **Opportunist** — applique scoring_matrix.json, trie les niches | daily 3h30 | Python + Mistral |
| 9 | **Brainstormer** — 200 idées/semaine sur niches non servies | weekly | Gemini Flash (1 grosse req) |
| 10 | **Arbitragiste Cross-canal** — décide cascade modules quand signal arrive | event-driven | Python + Mistral |
| 11 | **Méta-Critique hebdo** — audit modules profitables vs gouffres | weekly dim 22h | Gemini Flash |

### 🎨 Producteurs (création) — 8 rôles

| # | Rôle | Fréquence | LLM utilisé |
|---|---|---|---|
| 12 | **Coloriste Heritage** — line-art coloring depuis PD HD | lundi 4h | HF SDXL+ControlNet |
| 13 | **Engendreur Progeny** — fusion 2 parents PD → bébé crossover | jeudi 4h | HF FLUX + Gemini prompts |
| 14 | **Marchandiseur Cross-canal** — décline 1 design en 7 supports | event-driven | Python pur (resize/mockup) |
| 15 | **Restaurateur Vintage** — upscale + colorisation + nettoyage | vendredi 4h | Replicate Real-ESRGAN+DeOldify |
| 16 | **Card Game Designer** — decks thématiques humour métier | mardi 4h | Gemini + Pollinations |
| 17 | **Conteur Cozy** — fictions courtes branded | mercredi 4h | Groq Llama 70B |
| 18 | **Vidéaste Faceless** — shorts YouTube/TikTok | dimanche 4h | Groq + Gemini Vision |
| 18b | **Game Builder (semi-auto)** — fork squelette + swap assets Kenney/OpenGameArt + build APK. ⚠️ GATE DÉCISION HUGO EN AMONT : les bots proposent type+squelette, Hugo choisit, PUIS build | déclenché par décision Hugo (pas cron auto) | Gemini code-patch + Mistral codestral |

### 🛡️ Filtres (qualité) — 4 rôles

| # | Rôle | Quand | LLM utilisé |
|---|---|---|---|
| 19 | **Censeur Copyright** — check blacklist/whitelist sur chaque output | inline | Python regex |
| 20 | **Anti-Slop Textuel** — détecte ChatGPT-isms | inline | Python pur |
| 21 | **Anti-Slop Visuel** — relecture critique | inline | Gemini Vision |
| 22 | **Validateur Schéma** — conformité JSON contracts | CI sur PR | Python jsonschema |

### 📱 Interface humaine — 2 rôles

| # | Rôle | Quand | Tech |
|---|---|---|---|
| 23 | **Messager Telegram** — notifs avec boutons inline, reçoit verdict | event-driven | Python + Telegram Bot API |
| 24 | **Rapporteur Hebdo** — résumé dimanche : produits/validés/rejetés/revenu projeté | weekly dim 23h | Python + Gemini Flash |

### 🔒 Garde-fous (sécurité) — 3 rôles

| # | Rôle | Quand | Tech |
|---|---|---|---|
| 25 | **Vigile Secrets** — truffleHog scan fuites clés | monthly | GitHub Action |
| 26 | **Archiviste Backup** — mirror Codeberg + carte SD Termux | quarterly | git mirror |
| 27 | **Comptable Quota** — tracke consommation tokens par provider + alerte | continu (sur chaque appel) | Python + JSON local |

### 🛠️ Méta-outils dev — 1 rôle

| # | Rôle | Quand | Tech |
|---|---|---|---|
| 28 | **Skeleton Scout** — on lui donne un cahier des charges (type de projet OU fonction à améliorer), il recherche/évalue/propose des repos GitHub squelettes selon la grille /18, recommande le mode (fork/mix/inspire) et le combo MIX. Pour Module S : présente à Hugo pour décision. | event-driven (sur CodeSearchBrief) | GitHub Search API + WebSearch + scoring déterministe (`scripts/lib/skeleton_scout.py`) |

> L'agent #28 implémente la vision Hugo (20/05) : *« on paramètre une IA qui
> recherche les codes squelettes selon les infos qu'on lui rend ; elle cherche
> aussi pour améliorer juste certaines fonctions. On lui entre le type de jeu et
> ce qu'on veut exactement. »* Contrats : `code_search_brief.schema.json` (entrée)
> et `skeleton_candidate.schema.json` (sortie).

---

## 🔗 PARTIE 3 — QUEL AGENT NOURRIT QUEL BUSINESS

```
                ┌─────────────────────────────────────────┐
                │  ANTENNES (1-6)                          │
                │  signaux marché bruts                    │
                └─────────────┬───────────────────────────┘
                              ↓
                ┌─────────────────────────────────────────┐
                │  CERVEAUX (7-11)                         │
                │  synthèse → winning_formula.json         │
                └─────────────┬───────────────────────────┘
                              ↓
       ┌──────────────────────┼──────────────────────┐
       ↓                      ↓                      ↓
 ┌──────────┐         ┌──────────┐            ┌──────────┐
 │ Producteurs│        │ Producteurs│           │ Producteurs│
 │ heritage   │        │ iconic_off │           │ modern_cozy│
 │ (12, 15)   │        │ (13)       │           │ (14, 16,17)│
 └─────┬──────┘        └─────┬──────┘           └─────┬──────┘
       │                     │                        │
       └─────────────────────┼────────────────────────┘
                             ↓
                ┌─────────────────────────────────────────┐
                │  FILTRES (19-22)                         │
                │  Copyright + Anti-Slop + Schémas         │
                └─────────────┬───────────────────────────┘
                              ↓
                ┌─────────────────────────────────────────┐
                │  INTERFACE (23)                          │
                │  Telegram avec preview + boutons         │
                └─────────────┬───────────────────────────┘
                              ↓
                ┌─────────────────────────────────────────┐
                │  HUGO valide en 1 clic                   │
                └─────────────────────────────────────────┘
```

### Mapping business → agents producteurs

| Business | Agents producteurs | Agents filtres |
|---|---|---|
| **Coloriages historiques (B1)** | Coloriste Heritage (12) + Archéologue PD (5) | 19, 20, 21, 22 |
| **Merch cross-canal (B2)** | Marchandiseur Cross-canal (14) | 19, 20, 21, 22 |
| **Coloriages stylés modernes (B3)** | Coloriste Heritage (12, mais autres prompts) | tous filtres |
| **Restauration vintage (B4)** | Restaurateur Vintage (15) + Archéologue PD (5) | tous filtres |
| **Jeux de cartes (B5)** | Card Game Designer (16) | 19, 20, 22 |
| **Bébés super-héros PD (B6)** | Engendreur Progeny (13) | 19, 20, 21, 22 |
| **Mashups culturels (B7)** | Coloriste + Marchandiseur (12, 14) | tous filtres |
| **Coloring KDP low-content (B8)** | Coloriste Heritage (12) avec mode "minimal" | 20, 22 |
| **Fictions courtes (B9)** | Conteur Cozy (17) | 19, 20, 22 |
| **AR filters (B10)** | Marchandiseur + assets visuels (14) | 19, 21 |
| **Vidéos faceless (B11)** | Vidéaste Faceless (18) | 19, 20, 21 |
| **STL paramétriques (B12)** | (à coder) | 19, 22 |
| **Affiliation (B13)** | Affiliate Hunter (6) + Conteur Cozy (17 pour content) | 19, 20 |

### Mapping business → garde-fous communs
- Tous les business utilisent **Vigile Secrets (25)**, **Comptable Quota (27)** et **Archiviste Backup (26)** par défaut.

---

## 📊 PARTIE 4 — CADENCE GLOBALE HEBDOMADAIRE

```
┌─────────────────────────────────────────────────────────────────┐
│ LUNDI                                                            │
│  01h  Éclaireur Bestsellers (#1)                                 │
│  02h  Critique de Plaintes (#2)                                  │
│  03h  Synthétiseur (#7) + Opportunist (#8)                       │
│  04h  Coloriste Heritage (#12) — pipeline coloriages historiques │
│  06h  Saisonnier (#4)                                            │
│                                                                  │
│ MARDI                                                            │
│  01h  Éclaireur Bestsellers (#1)                                 │
│  02h  Critique de Plaintes (#2)                                  │
│  03h  Synthétiseur + Opportunist                                 │
│  04h  Card Game Designer (#16)                                   │
│  Tendanceur (#3) toutes les 6h                                   │
│                                                                  │
│ MERCREDI                                                         │
│  01h  Éclaireur + Critique                                       │
│  04h  Conteur Cozy (#17) — fictions                              │
│  Affiliate Hunter (#6) ×2                                        │
│                                                                  │
│ JEUDI                                                            │
│  01h  Éclaireur + Critique                                       │
│  04h  Engendreur Progeny (#13) — bébés crossover                 │
│                                                                  │
│ VENDREDI                                                         │
│  01h  Éclaireur + Critique                                       │
│  04h  Restaurateur Vintage (#15)                                 │
│  Brainstormer (#9) hebdo                                         │
│                                                                  │
│ SAMEDI                                                           │
│  03h  Archéologue PD (#5) — refresh musées                       │
│  04h  Marchandiseur Cross-canal (#14) — gros batch merch         │
│                                                                  │
│ DIMANCHE                                                         │
│  04h  Vidéaste Faceless (#18)                                    │
│  22h  Méta-Critique hebdo (#11)                                  │
│  23h  Rapporteur Hebdo (#24) → Telegram                          │
└─────────────────────────────────────────────────────────────────┘

PERMANENT (event-driven, à chaque génération) :
  Censeur Copyright (#19), Anti-Slop Textuel (#20),
  Anti-Slop Visuel (#21), Validateur Schéma (#22),
  Messager Telegram (#23), Comptable Quota (#27)

MENSUEL :
  Vigile Secrets (#25) — 1er jour du mois 2h UTC

TRIMESTRIEL :
  Archiviste Backup (#26) — 1er jour des trimestres
```

---

## 📈 PARTIE 5 — BUDGET TOKENS / JOUR PROJETÉ

| Provider | Tokens/jour | Tokens/mois | Sous quota gratuit ? |
|---|---|---|---|
| Gemini Flash | ~150 req × 2000 tk avg = 300k tokens | ~9M | Oui (1500 req/j = limite) |
| Groq Llama 70B | ~50 req × 3000 tk = 150k | ~4.5M | Oui (large marge) |
| Mistral small | ~100 req × 800 tk = 80k | ~2.4M | Oui |
| Cohere command-r | ~20 req × 1000 tk = 20k | ~600k | Oui (1000/mois) |
| HF Inference (images) | ~30 générations | ~900 | Oui (30k/mois) |
| Replicate | ~5 générations | ~150 | Oui (5$ trial étalé ~3 mois) |
| **Claude (moi)** | **~5k tokens** | **~150k** | Plan Pro mensuel ≈ 18€ |

**Total IA / mois : ~17M tokens cumulés, 0€ sauf Claude qui devient rentable à partir de ~50€/mois de revenu.**

---

## ✅ PARTIE 6 — STATUT ACTUEL DES 27 RÔLES

| Statut | Quantité | Détails |
|---|---|---|
| 🟢 Déjà codé partiellement | 5 | Tendanceur (≈ trend_explosion), Opportunist (≈ opportunity_hunter), Saisonnier (seasonal_calendar), Brainstormer (ideator_offline), Méta-Critique (winner_amplifier) |
| 🟡 Skeleton à coder | 22 | Reste, à coder en sprints Vague 2+ |

→ Cf. `EMPIRE_HUGO.md` pour les agents existants à brancher dans cette map.

---

## 🎯 RÉCAPITULATIF EN 3 PHRASES

1. **13 business** (8 top + 5 middle tier) qui couvrent POD physique, KDP digital, jeux, AR, vidéo, affiliation.
2. **27 agents IA perpétuels** (6 antennes + 5 cerveaux + 7 producteurs + 4 filtres + 2 interface + 3 garde-fous), tous en cron espacé pour rester gratuit.
3. **1 humain (toi)** qui valide en 1 clic Telegram, branché à un système qui pleut de partout grâce à la cross-pollinisation.

---

## 🆕 AJUSTEMENTS & NOUVEAUX RÔLES — directives Hugo 20/05

### Nouveaux agents à formaliser

| # | Rôle | Mission | Statut |
|---|---|---|---|
| **29** | **Veilleur d'Outils Gratuits** | Recherche perpétuelle d'outils/repos/APIs **gratuits** utilisables (libres de droits commercial) pour servir nos business. Extension du Skeleton Scout (#28) mais orientée *outillage* et pas seulement squelettes de code. Vérifie aussi que nos outils restent maintenus/à jour. | à coder |
| **30** | **Architecte Auto-Amélioration** | Réfléchit **en boucle** au système global : failles, points faibles, comment l'améliorer/perfectionner/étoffer. Va plus loin que la Méta-Critique (#11, qui audite la *rentabilité* des modules) : lui audite l'**architecture** elle-même. Propose à Hugo. | à coder |
| **31** | **Scénariste Maître** (moteur narratif) | Écrit des **scripts/récits entiers** à partir d'un sujet (jeux narratifs, livres, fictions) : fil conducteur solide, belle écriture, **zéro répétition**, boucle d'**auto-correction → re-correction**, suppression des **patterns d'IA** (anti-slop renforcé). Montée en puissance du Conteur Cozy (#17) couplé à l'Anti-Slop Textuel (#20). | à coder |
| **32** | **Analyste Marché Jeux** | Pour une catégorie donnée : top 10 des jeux qui marchent, leurs **forces** (à garder), **faiblesses** (à corriger), **demandes récurrentes des joueurs**, et **fonctionnement général**. Alimente la décision Hugo + le Skeleton Scout pour le MIX. Équivalent de l'Éclaireur/Critique appliqué aux jeux. | à coder |
| **33** | **Juge de Sortie** (analyste-qualité) | **Évalue l'output** d'un agent-en-boucle (script, design, chapitre…) selon des critères, et décide : **re-corriger** ou **stop, c'est bon**. C'est le **critère d'arrêt** des boucles d'auto-correction (notamment Scénariste #31). « Peut-être même créer une IA d'analyse » — Hugo 20/05. | à coder |
| **34** | **Prospecteur d'Émergence** | Recherche **constante** de **business/marchés en émergence**, MÊME hors de nos domaines actuels, dès lors qu'ils sont **applicables à notre usine** (production automatisée, faible coût, scalable). Distinct du Scout Marché (#1, qui creuse nos niches connues) : lui scanne LARGE (macro-tendances, nouveaux formats, plateformes naissantes) et évalue l'**applicabilité à notre système**. « une IA à la recherche constante d'un business en émergence » — Hugo 20/05. | à coder |

### Extensions de rôles existants

- **#1 Éclaireur Bestsellers — ÉLARGI** : ne plus se limiter aux coloring books. Couvrir **tous les business** (jeux de société, vêtements/merch, livres, jeux mobiles, 3D…) et **segmenter par catégorie** : « dans telle catégorie, ce qui explose c'est X ». Sortir un classement par domaine + le top toutes catégories.
- **#2 Critique de Plaintes → + détecteur "bestseller mal noté"** : repérer les produits à **fort volume de ventes MAIS mauvaise note**, surtout quand le défaut est **simple à corriger** (fait par flemme / pas refait car ça vendait déjà). = opportunités en or. Cf. nouvelle idée business (NOUVELLES_IDEES.md).
- **#6 Affiliate Hunter — workflow précisé** : sort des **leads** (gens en recherche active d'un produit) + un **message pré-rédigé** + le **lien d'affiliation**, le tout poussé à Hugo via Telegram. **Hugo envoie lui-même** (jamais d'envoi auto → anti-ban).
- **#28 Skeleton Scout — MIX par fonction confirmé** : assembler des morceaux de plusieurs repos commerciaux par *fonctionnalité* (ex. zoo : « terrain+emplacement » d'un repo, « capture de bêtes » d'un autre, « boutique de skins » d'un 3e, « régie pub » d'un 4e). Pas besoin d'un squelette parfait unique. Chercher aussi des **squelettes d'agents/IA perpétuels** existants (cf. wshobson/agents, ECC) à adapter plutôt que tout recoder.

### Doctrine renforcée

- **DEUX RÉGIMES D'EXÉCUTION (précision Hugo 20/05)** — « perpétuel » ≠ « en continu » :
  1. **Agents de fond** (Antennes, Cerveaux, certains Producteurs comme designs/coloriages) : utiles en permanence → **cron espacé** (cascade temporelle), tournent tranquillement en arrière-plan.
  2. **Agents-projet** (Scénariste #31, Game Builder #18b, Analyste Jeux #32…) : **déclenchés à la demande** quand un projet précis démarre. Ils tournent en **boucle intensive bornée** (minuterie / nombre d'itérations / seuil de qualité) **le temps de livrer**, puis **s'arrêtent**. On ne fait PAS mouliner le moteur narratif s'il n'y a rien à écrire à l'instant T.
  - **Mécanisme minuterie** : la skill Claude Code **`/loop`** (relance un prompt/commande à intervalle, ou en auto-pacing) sert exactement de minuterie de déclenchement. Boucle = générer → **Juge de Sortie (#33)** analyse → re-corriger → … → stop quand le seuil est atteint.
- **Anti-dérive (fiabilité)** : chaque agent doit recevoir des **rappels permanents de son rôle** dans son system-prompt (ancrage répété) pour ne pas dériver. Objectif : le système le plus fiable possible.
- **Qualité > volume** : beaucoup de produits, mais **chacun fini et soigné** (certains en qualité supérieure). Aucune plateforme ne doit nous voir comme « 2000 merdes ». Les filtres Anti-Slop (#20/#21) sont bloquants.
- **Diffusion semi-manuelle (anti-ban)** : pas d'upload 100 % auto pour l'instant. Modèle cible = le bot **pré-remplit** la fiche produit et envoie le lien à Hugo, **Hugo sélectionne et publie** (copier-coller). Automatisation seulement sur ce qui est *léger, contrôlable, indétectable*.

> Ces ajustements sont datés ; intégration fine dans les parties 1-6 au prochain tri d'architecture.

---

## 🧬 CONSOLIDATION — 33 rôles → 13 agents (directive Hugo 20/05)

**Pourquoi** : 33 rôles, c'est éclaté et redondant. Regrouper = plus clair **et** moins
d'appels API dupliqués (donc plus loin des limites). Les 33 fonctions subsistent comme
**sous-modes** de 13 agents.

> ⚠️ Rappel quota : le nombre d'agents n'impacte PAS les limites. Seul compte le **nombre
> d'appels/jour**, déjà bridé par cascade temporelle + multi-provider (`llm_routing.json`)
> + Comptable Quota. La consolidation réduit surtout les appels **redondants**.

| Agent consolidé | Cluster | Regroupe (rôles d'origine) |
|---|---|---|
| **A1 · Scout Marché** | détection | #1 Éclaireur + #2 Critique de Plaintes + #32 Analyste Marché Jeux (+ détecteur "bestseller mal noté") |
| **A2 · Radar Tendances, Sources & Émergence** | détection | #3 Tendanceur + #4 Saisonnier + #5 Archéologue PD + #34 Prospecteur d'Émergence (veille macro de business naissants applicables à l'usine) |
| **A3 · Affiliate Hunter** | détection | #6 |
| **B1 · Stratège** | cerveau | #7 Synthétiseur + #8 Opportunist + #9 Brainstormer + #10 Arbitragiste |
| **B2 · Auditeur** | cerveau | #11 Méta-Critique + #30 Architecte Auto-Amélioration |
| **C1 · Atelier Image** | production | #12 Coloriste + #13 Engendreur Progeny + #14 Marchandiseur + #15 Restaurateur |
| **C2 · Plume (narratif)** | production | #17 Conteur Cozy + #31 Scénariste Maître |
| **C3 · Card Designer** | production | #16 |
| **C4 · Vidéaste Faceless** | production | #18 |
| **C5 · Game Builder** | production | #18b (gate décision Hugo en amont) |
| **D1 · Scout Technique** | méta | #28 Skeleton Scout + #29 Veilleur d'Outils Gratuits — **portée = l'usine entière** (outils GitHub libres pour l'infra/le fonctionnement général, pas seulement par produit). Alimente B2 Auditeur en pistes d'amélioration du système. |
| **E1 · Juge Qualité** | qualité | #19 Copyright + #20 Anti-Slop Textuel + #21 Anti-Slop Visuel + #22 Schéma + #33 Juge de Sortie |
| **F1 · Ops & Interface** | infra | #23 Telegram + #24 Rapporteur + #25 Vigile Secrets + #26 Backup + #27 Comptable Quota |

**Régime d'exécution** (cf. doctrine ci-dessus) : A1/A2/B1/E1/F1 = **fond** (cron espacé) ;
C1-C5, C2, D1 = **projet à la demande** (boucle bornée + Juge Qualité comme critère d'arrêt).

**À renforcer** : F1 doit intégrer un vrai **ordonnanceur** (throttle/queue) pour le cas où
plusieurs agents-projet tournent en même temps → garantit qu'on reste sous les quotas.

---

## 🏭 LA BOUCLE PRODUIT AUTONOME — vision cible (Hugo 20/05)

**Objectif final** : une **usine** qui produit seule des **produits finis triés par priorité**,
Hugo ne fait que la **validation finale** (ok / ça repart). « Que tout se lance comme une
grosse machine, me donne des produits finis, et j'ai juste à dire ok ou non. »

```
Stratège (B1) choisit quoi produire (rentabilité × demande × saison)
        ↓
Producteur (C1-C5) génère le produit
        ↓
Juge Qualité (E1) AUDITE selon critères PROPRES AU TYPE de produit
   ex. coloring book : qualité du dessin, COHÉRENCE de la série,
       line-art fermé, zéro texte parasite, lisibilité
   ex. livre/script : fil conducteur, zéro répétition, anti-slop
   ex. merch : lisibilité du design sur le support, marges
        ↓
   ┌── PAS BON → diagnostic ("problèmes : X, Y, Z") → RELANCE AUTO la prod
   │                                                   avec corrections ciblées
   │        ↑________________ (boucle bornée) _________________↓
   └── BON → entre dans la FILE DE PRODUITS FINIS, classée par priorité de publication
        ↓
   HUGO valide en haut de pile : OK → publie / NON → repart en correction
```

### Implications concrètes
- **E1 Juge Qualité = "Auditeur Produit"** : grilles de critères **par type de produit**
  (étendre `data/quality_rules.json` par catégorie). C'est lui qui déclenche la régénération.
- **File priorisée** : F1/B1 maintiennent un **backlog de produits finis** trié (le plus
  rentable/demandé en haut). Hugo dépile.
- **Boucle bornée** : limite d'itérations / seuil de qualité pour ne pas tourner à l'infini
  (cf. doctrine 2 régimes). En attendant la clé HF, l'audit tournera en mode dégradé
  (Pollinations) — la vraie qualité viendra avec HF.
- **Injection manuelle** : Hugo peut aussi pousser sa propre idée/produit dans la file
  (« tiens, lance ça »), traitée comme une commande prioritaire.
- **Couverture** : la boucle doit s'appliquer à **TOUS les business**, y compris ceux en
  pause (à brancher au moment de leur réactivation).

### Cadence & verdicts (modèle opérationnel — Hugo 20/05)
- **Quota hebdomadaire paramétrable** : on fixe une commande par semaine (ex. « 100 coloriages
  + 100 livres low-content + 3 romans + 1 ébauche de jeu »). La machine produit **au maximum
  de ses capacités** sous ce quota.
- **Boucle d'aboutissement AUTONOME (correction Hugo 20/05)** : la machine ne renvoie PAS
  des brouillons à trier. Pour CHAQUE produit, elle **boucle seule** (générer → Juge Qualité
  #33 compare à la description cible : trends du moment + signature idéale + bon format) et
  **se corrige** jusqu'à la **version qu'elle juge la plus aboutie possible** avec notre
  système actuel. Quand c'est abouti → **mise en STOCK automatique** → elle **passe au produit
  suivant** sans attendre. « Elle fait au mieux qu'elle peut et quand c'est fait, boom, terminé. »
- **Production SIMULTANÉE** : plusieurs produits / plusieurs business **en parallèle** (ex. un
  livre de coloriage + un roman + une ébauche de jeu en même temps). À terme : **plusieurs
  produits d'un même business simultanément**. (Borné par l'ordonnanceur F1 pour les quotas.)
- **Hugo = validation du STOCK fini** : il ne voit que des produits **auto-jugés aboutis**,
  classés par priorité, et tranche OK → publier / NON → repart. (Il peut aussi injecter une
  commande prioritaire : « tiens, lance ça ».)
- **Scaling** : plus le système se perfectionne (meilleurs prompts, filtres, clé HF), plus le
  **quota hebdomadaire augmente** — montée en volume **À QUALITÉ CONSTANTE**.

### Définition d'un produit « CLÉ EN MAIN » (Hugo 20/05)
Un produit en stock doit être **100 % publiable**, rien à retoucher. Pour un **livre de
coloriage** par ex. :
- **Titre + sous-titre** accrocheurs, pensés **comme une collection** (Vol. 1…) ;
- **Déclinaison préparée** : si le produit explose, la suite de la collection est déjà cadrée ;
- **Couverture** générée ;
- **Mise en page complète au format KDP sans erreur** (trim 8.5×11, bleed 0.125", gutter 0.75", PDF/X) ;
- **Métadonnées de listing** (titre/description/tags) prêtes à coller.
→ Chaque type de produit a sa propre check-list « clé en main » (dans `data/quality_rules.json`).

### Le CHOIX EN AMONT = liberté décisionnelle du Stratège (Hugo 20/05)
**Pour tous les projets** (pas que les livres), avant de produire, le **Stratège (B1)** choisit
**la meilleure opportunité à l'instant T** (potentiel × faisabilité × fraîcheur) — c'est son
**idée personnelle**, ce qu'il juge le plus prometteur. Il dispose de 4 **stratégies** :
1. **Mono-trend** : exploiter **une seule** trend forte telle quelle.
2. **Cross-trend** : **croiser** 2+ trends qui marchent en ce moment (ex. cute × super-héros).
3. **Original** : sa **propre idée** innovante — parfois c'est nous qui **créons** la trend.
4. **Refonte/amélioration** : reprendre un produit **qui a bien vendu mais marche mal**
   (bestseller mal noté) et corriger ses défauts.
Il enchaîne : après un produit, il **rebascule** sur une autre trend, un autre cross, un original
ou une refonte — selon ce qui est le plus prometteur à ce moment-là.

### Le BRIEF PRODUIT = contrat anti-dérive (Hugo 20/05)
Une fois l'opportunité choisie, le **Stratège (B1)** génère un **Brief Produit précis**
→ contrat : `data/schemas/product_brief.schema.json` (avec la stratégie retenue et le pourquoi).
Exemple : *« coloring type Coco-Wyo × super-héros monte → produire ça, style cadré par images
de référence HF, format KDP, ton line-art, signature maison, pensé en collection »*.
- L'**Auditrice (E1)** a ce brief « dans ses données » et audite le produit **POINT PAR
  POINT** contre lui : cohérence stylistique entre toutes les pages, format KDP sans erreur,
  ton de couleur, zéro parasite, couverture, complétude clé-en-main. Chaque critère est
  **bloquant ou non** → un produit n'est « abouti » que si **tous les bloquants passent**.
- **Ligne de conduite ultra précise = ce brief + la grille de critères** → empêche la dérive
  (« pas de truc à moitié fait qui passe »).
- **Garde-fou anti-boucle-infinie** (`loop_policy`) : `max_iterations` ; si le **même critère**
  échoue plusieurs fois → tenter un **contournement** (autre approche/outil) ; si **insoluble**
  malgré tout → **STOP la production + ALERTER Hugo** (ne jamais tourner en boucle sur une
  erreur irrésolvable — ex. un blocage récurrent sur une ébauche de jeu).
- **Applicable à TOUS les produits** (coloring, romans, jeux, merch, 3D…), pas seulement les
  coloring books — l'exemple ci-dessus est générique.
