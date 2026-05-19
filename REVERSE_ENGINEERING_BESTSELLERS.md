# 🔎 REVERSE ENGINEERING BESTSELLERS — recopier en mieux + cross-polliniser

**Date** : 2026-05-19
**Doctrine** :
> *« On n'invente pas la demande. On la trouve, on extrait la formule gagnante,
> on enlève ce qui a déçu les acheteurs (commentaires 1-3★), et on décline sur
> tous nos canaux pour que la pluie tombe de partout. »*

---

## 🎯 1. LES 3 MOTEURS D'ASPIRATION (les "antennes")

| Moteur | Source de signal | Ce qu'on extrait | Volume estimé |
|---|---|---|---|
| **A. Bestsellers Direct** | Amazon KDP, Etsy, Redbubble, Cults3D, Play Store charts | structure gagnante (TOC, tags, titres, prix) | 50-200 produits/jour |
| **B. Reviews Negatives (1-3★)** | mêmes plateformes, sections commentaires | défauts récurrents = opportunité d'amélioration | 20-50 douleurs identifiées/semaine |
| **C. Trend Spotting Précoce** | TikTok, Pinterest, Google Trends, BuzzSumo, Reddit | esthétiques émergentes (ex: cottagecore, dark academia, cute baby crossover) | 5-15 tendances qualifiées/semaine |

→ La combinaison **A × B × C** = le filtre Hugo.
- A seul = on imite (sans valeur ajoutée)
- A × B = on imite **en mieux** (valeur)
- A × B × C = on imite en mieux **avec un angle moderne** = best of breed

---

## 🧰 2. SOURCES DE CODE & TEMPLATES — pas que GitHub

L'**erreur** serait de ne piocher que dans GitHub. Carte complète des dépôts publics
exploitables pour ne **jamais coder à partir d'une page blanche** :

### 2.1 Code source

| Source | Spécialité | Note |
|---|---|---|
| **GitHub** | tout | search par `license:mit`, `stars:>100`, `pushed:<2 ans` |
| **GitLab.com** public projects | DevOps, Python lib | souvent CI/CD propres |
| **Codeberg** | éthique / FLOSS | mirrors d'orgs européennes |
| **SourceForge** | legacy Linux/Windows tools | trésors anciens encore utiles |
| **Bitbucket public** | rare mais existant | scripts data scientists |
| **HuggingFace Spaces** | démos ML clé en main | code Gradio prêt à forker |
| **Replit Community** | mini-projets web/JS | bug rapidement mais inspiration |
| **Glitch.com** projets remixables | webapps légères Node | bon pour APIs Express |
| **Awesome Lists** (`awesome-*`) | curation thématique | porte d'entrée vers le bon repo |
| **PyPI / npm / crates.io** | bibliothèques | parfois plus utile qu'un repo |

### 2.2 Templates de livres (KDP)

| Source | Quoi extraire |
|---|---|
| Page bestsellers KDP par catégorie | TOC visible via "Look inside", tags, sous-titre |
| **OpenLibrary** | métadonnées bibliographiques mondiales |
| **Project Gutenberg** | textes domaine public directement utilisables |
| **Wattpad** | romans niche populaires (style, structure, dialogues) |
| **AO3 / FanFiction.net** | structures qui prennent (sans copier le contenu protégé) |
| **Goodreads listopia** | listes "best of niche" + scores |

### 2.3 Templates de Merch (t-shirts, posters, stickers)

| Source | Quoi extraire |
|---|---|
| Redbubble "Trending" par catégorie | titres + tags + prix + nombre de ventes implicite (étoiles) |
| TeePublic "Best Sellers" hebdo | idem |
| Amazon Merch on Demand "Movers & Shakers" | quoi monte cette semaine |
| **Etsy listings actifs** (`?sort=most_relevant&filter=top_seller`) | structures de titres SEO |
| **Pinterest Trends** (FR + US + UK) | esthétiques qui montent |

### 2.4 Templates de Jeux (mobile, cartes)

| Source | Quoi extraire |
|---|---|
| Play Store "Top Free Casual" | mécanique de base, structure des reviews |
| itch.io trending | mécanique indé qui marche |
| **BoardGameGeek hot list** | mécaniques de jeux de cartes émergentes |
| **GitHub `awesome-godot` / `awesome-phaser`** | moteurs forkables |
| **OpenGameArt + Kenney.nl** | assets libres prêts à l'emploi |

### 2.5 Templates AR Filters

| Source | Quoi extraire |
|---|---|
| TikTok "Top Effects" hebdo | mécaniques qui prennent (jeu visage, esthétique, transition) |
| Effect House Trends | concours hebdo créateurs |
| Snapchat Lens Studio examples | inspiration UI/UX |

---

## 🔧 3. PIPELINE D'EXTRACTION ET D'AMÉLIORATION — protocole "Best Of Breed"

Pour chaque niche détectée comme rentable, on déroule **6 étapes**, dont les
4 premières sont 100% automatisées (zéro Claude) :

```
[ÉTAPE 1] SCAN BESTSELLERS (script Python, 0 token)
└── Scrape les 20 produits top-vente sur la plateforme cible
└── Extrait : titre, sous-titre, tags, prix, # reviews, # ★ moyenne
└── Stocke dans data/bestsellers/<niche>.json

[ÉTAPE 2] SCAN REVIEWS NÉGATIVES (script Python + Mistral, ~0.5 req/produit)
└── Pour chaque produit top : récupère reviews 1-3★
└── Mistral résume en 3-5 "pain points" récurrents
└── Stocke dans data/pain_points/<niche>.json
└── Exemple sortie :
    {
      "niche": "mystical_mushrooms_coloring",
      "pain_points": [
        "papier trop fin (encre traverse)",   # 47% des avis
        "trop de pages dupliquées",            # 31%
        "lignes pas fermées (peinture déborde)" # 22%
      ]
    }

[ÉTAPE 3] SCAN TENDANCES MODERNES (Perplexity ou Gemini, 1-2 req)
└── "Quelles esthétiques montent sur TikTok/Pinterest cette semaine pour <niche> ?"
└── Filtre les signaux faibles vs forts
└── Stocke dans data/modern_angles/<niche>.json

[ÉTAPE 4] SYNTHÈSE = formule gagnante (Gemini, 1 req structurée)
└── Input : bestsellers + pain_points + modern_angles
└── Output : data/winning_formula/<niche>.json
    {
      "structure_basée_sur": "top_3_bestsellers_avg_TOC",
      "ameliorations_obligatoires": ["papier épais déclaré", "0 duplicate (hash check)", "lignes fermées (ControlNet)"],
      "angle_moderne": "bébé crossover cute style cottagecore",
      "titre_template": "{Niche} Coloring Book for {Audience} — {AngleModerne}",
      "prix_optimal": 8.99,  # médiane des top vendeurs
      "page_count": 100,     # mediane
      "format": "8.5x11 portrait"
    }

[ÉTAPE 5] PRODUCTION (pipelines existants)
└── Le module de production (Coloring, KDP, Merch...) lit winning_formula/<niche>.json
└── et applique strictement la formule sans inventer
└── Output : staging/<niche>/<asset>

[ÉTAPE 6] VALIDATION (Hugo via bot Telegram)
└── Hugo approuve → upload manuel sur la plateforme cible
```

**Effet** : on a un produit qui :
- a la **structure** des best-sellers (donc demande prouvée)
- corrige **explicitement** les défauts (donc 4-5★ probable)
- a un **angle moderne** (donc shareable sur TikTok/Pinterest)

---

## 🌐 4. CROSS-POLLINISATION — l'unité du système

> *« On crosse tous nos systèmes pour faire une grosse unité. »*

Chaque actif gagnant doit se décliner sur **N supports en parallèle**. Le tableau
ci-dessous montre comment un signal détecté sur **1 canal** doit déclencher la
production sur **tous les autres compatibles** :

### 4.1 Matrice de réplication cross-canal

| Si signal détecté sur… | Alors lancer production sur… | Mécanique |
|---|---|---|
| **Bestseller KDP coloring "mystical mushrooms"** | Merch (t-shirt, sticker, poster), Mug, Coloring inversé, Mini-jeu mobile, Vidéo TikTok process | extraire les 5 visuels les plus iconiques du livre |
| **Bestseller t-shirt Redbubble "vintage botanical"** | Livre coloring planches botaniques, Carte postale set, Coussin, Coque téléphone, Wall art poster | extraire 30-50 variantes |
| **Trend Pinterest "cottagecore witch"** | Coloring book, Merch (sticker pack), Tarot deck, Carnet journal, Mug citation | générer pack complet niche-first |
| **Trend TikTok "bébé crossover super-héros"** | Sticker pack (priorité), Coloring book, Mini-livre illustré KDP, T-shirt, Mug, AR filter | exploit-fast, signal éphémère |
| **Best-seller jeu mobile niche (casual cozy)** | Pas de clone, mais : merch fan-art (légal si transformatif), guide stratégie KDP, soundtrack ASMR | dérivé éditorial |
| **Domaine public actif : planches médicinales anciennes** | Coloring book (Module U), poster vintage (Module B/U), mug botanique, carnet d'herboriste KDP, jeu de cartes éducatif TGC | full Module U + cross-canal |
| **Domaine public actif : super-héros Golden Age** | Sticker pack bébé crossover, coloring book bébé heroes, t-shirt collection vintage, mini-livre KDP "L'héritage oublié des héros", AR filter cape | Module W full pipeline |

### 4.2 Le "stock toujours plein"

Le système doit produire **en permanence** des assets dans `staging/`, **en avance**
sur les inscriptions. Pourquoi :
1. Quand tu valides une plateforme (ex: KDP), il y a déjà 20 livres prêts à uploader → tu sors gros volume d'un coup
2. Quand un signal explose, tu as déjà la matière première (juste à reformater)
3. Si une plateforme tombe, le stock va vers la suivante en quelques minutes

**Règle de stock cible** :
- Coloring books prêts : **30 min** (pour saturer KDP en 30 jours @ 1/jour)
- Merch designs prêts : **200** (pour 7 plateformes × ~25-30 designs initiaux)
- STL paramétriques : **100** (Cults3D + Printables + MyMiniFactory)
- Cartes de jeu : **5 decks** (TGC + BGM)
- APKs casual : **3** (Amazon Appstore d'abord)
- Vidéos YT shorts : **30** (1 mois d'avance, 1 par jour)
- AR filters : **10** (Effect House + Spark AR)

---

## 🩺 5. RÉHABILITATION DU DOMAINE PUBLIC — pilier dédié

C'est le pilier que tu identifies comme « ça marche pas mal » et il faut le formaliser
en **process répétable**. 5 étapes :

```
[1] CHOIX DE LA NICHE PD
   └── Liste blanche : whitelist_pd.json
   └── Critères : pré-1929 (US+UE) ET non-marqué moderne
   └── Exemples : plantes médicinales, anatomie XIXe, astronomie ancienne,
       contes populaires, super-héros Golden Age, estampes japonaises pré-1925

[2] ACQUISITION HAUTE DÉFINITION
   └── Sources : Smithsonian, Met, Rijksmuseum, BHL, Internet Archive, Gallica
   └── Tous CC0 ou PD → libre exploitation commerciale
   └── Termux télécharge en local dans stage_local/domain_public/<niche>/

[3] NETTOYAGE + UPSCALING (déterministe + Replicate)
   └── Real-ESRGAN x4 pour passer en 4K
   └── DeOldify si colorisation utile
   └── OpenCV pour seuillage binaire si coloring book
   └── Rembg pour détourage si poster ou Merch

[4] PROGENY OPTIONNEL (Module W)
   └── Si on veut un mashup : fusion 2 oeuvres PD compatibles
   └── ex: plante médicinale × anatomie victorienne = "Botanical Anatomy"

[5] DÉCLINAISON CROSS-CANAL
   └── Module B (Merch) + Module K (KDP) + Module U (Coloring) + Module C (Vidéo Process)
   └── La même matière produit 5-7 produits différents
```

### Exemples concrets validés (à shipper en pilote)

| Niche PD | Source | Déclinaisons |
|---|---|---|
| **Plantes médicinales Köhler (1887)** | BHL + Wikipedia Commons | Coloring book "Healing Herbs", poster set 8 plantes, mug botanique, carnet d'herboriste, mini-livre KDP "Old Remedies Rediscovered" |
| **Atlas anatomique Vésale (1543)** | Internet Archive | Coloring book "Renaissance Anatomy", t-shirt "skeletal mood", poster gothic, livre relié KDP collector |
| **Estampes Hokusai (vagues, fleurs, créatures)** | Met Open Access | Coloring book "Japanese Edo", set magnets, t-shirts collection, AR filter "vague" |
| **Audubon Birds of America (1827)** | NYPL Digital | Coloring book "Birds of Yesterday", set 12 posters, livre relié KDP, mug ornithologue |
| **Mythes Cthulhu / Lovecraft (pré-1929)** | Wikisource | Coloring book "Eldritch", t-shirt collection cute, AR filter tentacules, mini-jeu mobile cosmic horror |
| **Super-héros Golden Age (Stardust, Phantom Lady, Heap)** | Public Domain Super Heroes Wiki | Sticker pack bébé crossover (Module W), coloring book "Forgotten Heroes Babies", t-shirt collection, AR cape |
| **Cartes médiévales / portulans** | Library of Congress | Coloring book "Old Maps", poster mur, mug capitaine, carnet voyage |

---

## 🔄 6. WORKFLOW UNIFIÉ — un signal, N produits

Schéma final qui unifie tout :

```
                            ┌──────────────────────────────┐
                            │  ANTENNES (cron daily)       │
                            │  • Bestsellers KDP/Etsy/RB   │
                            │  • Reviews 1-3★ aggregator   │
                            │  • Pinterest/TikTok trends   │
                            │  • Domaine public refresh    │
                            └──────────────┬───────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────┐
                            │  SYNTHESE (Gemini, 1 req/niche)│
                            │  → winning_formula/<niche>.json│
                            └──────────────┬───────────────┘
                                           │ déclenche en parallèle
            ┌──────────────────┬───────────┼───────────┬──────────────┐
            ▼                  ▼           ▼           ▼              ▼
      ┌──────────┐       ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
      │ Coloring │       │ Merch    │ │ Mini-jeu │ │ Vidéo    │ │ AR Filter│
      │ book     │       │ pack     │ │ mobile   │ │ TikTok   │ │          │
      │ (Module L)│       │ (Module B)│ │ (Module S)│ │ (Module C)│ │ (Module Q)│
      └────┬─────┘       └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
           │                  │            │            │            │
           └──────────────────┴────────────┼────────────┴────────────┘
                                           ▼
                            ┌──────────────────────────────┐
                            │  STAGING + bot Telegram      │
                            │  Hugo valide en 1 clic       │
                            └──────────────┬───────────────┘
                                           ▼
                            ┌──────────────────────────────┐
                            │  Upload manuel par Hugo       │
                            │  sur les N plateformes        │
                            └──────────────────────────────┘
```

Une seule détection alimente 5-6 productions en parallèle → c'est l'unité du système.

---

## 📋 7. PRIORITÉS POUR LES 10 PREMIÈRES NICHES À TESTER

Quand Vagues 0+1+2 seront prêtes, on lance la machine sur ces 10 niches en parallèle.
Chaque niche = full pipeline cross-canal (5-7 produits déclinés).

| # | Niche | Type | Modules activés | Effort |
|---|---|---|---|---|
| 1 | **Mystical mushrooms cute** | trend moderne | L (coloring), B (merch), C (vidéo) | bas |
| 2 | **Bébé crossover super-héros PD** | trend + PD | W (Progeny), B, L, K | moyen |
| 3 | **Plantes médicinales Köhler** | PD réhab | U (vintage line-art), K, B | bas |
| 4 | **Anatomie Vésale renaissance** | PD réhab | U, K (collector), B | bas |
| 5 | **Birds of America Audubon** | PD réhab | U, B (posters), K | bas |
| 6 | **Cottagecore witch journal** | trend moderne | K, L, B | bas |
| 7 | **Vintage botanical Hokusai** | PD réhab cross-culture | U, V (mashup), B, L | moyen |
| 8 | **Forgotten Heroes Babies** | PD super-héros cute | W, L, B, K | moyen |
| 9 | **Dark Academia stationery** | trend moderne | K, B, L | bas |
| 10 | **Eldritch cute Cthulhu** | PD Lovecraft + cute | W, L, B, K | moyen |

→ **6 niches "bas effort"** se lancent dès Vagues 0+1+2 ok.
→ **4 niches "moyen effort"** activent le Module W (Progeny Engine) — lancées Vague 2+3 ok.

---

## ✅ 8. EN UNE PHRASE

> Nos **antennes** captent ce qui marche, nos **synthèses** extraient la formule,
> nos **modules** produisent la formule en mieux avec un angle moderne, **toi**
> tu valides en 1 clic, et chaque succès **se réplique sur 5-7 canaux** parce qu'on
> a pré-stocké la matière première. La pluie tombe de partout, tu fais que trier.
