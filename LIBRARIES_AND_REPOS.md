# 📚 LIBRARIES & REPOS — code open-source réutilisable par module

**Date** : 2026-05-20
**Doctrine** :
> *« On ne code jamais à partir d'une page blanche. Pour chaque besoin, on cherche
> d'abord un repo open-source mature, perfectionné, optimisé. On forke / vendorise /
> dépend / s'inspire. Coder from scratch est le DERNIER recours. »*

C'est l'application de la doctrine reverse-engineering au **code lui-même**.

---

## 🔬 PROTOCOLE DE SÉLECTION — avant de coder quoi que ce soit

Pour tout nouveau besoin technique, dérouler ces 5 étapes :

```
[1] Chercher dans CE document (besoin déjà cartographié ?)
[2] Si absent : WebSearch + GitHub search
    - "license:mit stars:>500 pushed:>2025-01-01 <besoin>"
    - awesome-lists du domaine
[3] Évaluer chaque candidat sur 6 critères (grille ci-dessous)
[4] Décider le mode d'intégration : depend / vendor / fork / inspire
[5] Documenter le choix dans ce fichier (entrée nouvelle)
```

### Grille d'évaluation (6 critères, /18)

| Critère | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| **License** | GPL/AGPL (viral, risqué pour commercial) | LGPL | Apache-2.0 | MIT / BSD / CC0 |
| **Maintenance** | abandonné >2 ans | dernier commit >1 an | <1 an | <3 mois |
| **Popularité** | <100 ⭐ | 100-1k | 1k-10k | >10k |
| **Qualité code** | pas de tests, illisible | tests partiels | tests + CI | tests + CI + docs + types |
| **Fit besoin** | détourné | adaptation lourde | adaptation légère | drop-in exact |
| **Légèreté/déps** | déps lourdes conflictuelles | déps lourdes | déps modérées | minimal/pure-python |

**Seuil d'adoption** : ≥ 12/18. En dessous, chercher une alternative ou coder soi-même.

### ⚠️ Vigilance licence (CRITIQUE pour usage commercial)

| License | Usage commercial | Obligation | Notre verdict |
|---|---|---|---|
| **MIT / BSD / Apache-2.0** | ✅ libre | attribution | **PRÉFÉRÉ** |
| **CC0 / Unlicense** | ✅ libre | aucune | **PRÉFÉRÉ** (assets) |
| **LGPL** | ✅ si lié dynamiquement | publier modifs de la lib | OK avec prudence |
| **GPL / AGPL** | ⚠️ contamine notre code | publier TOUT notre code | **ÉVITER** sauf outil isolé en subprocess |
| **CC-BY-NC** | ❌ non-commercial | — | **INTERDIT** pour la prod |
| **"Research only" / custom** | ❌ | — | **INTERDIT** |

> **Piège classique** : beaucoup de modèles IA (Stable Diffusion, certains LoRA,
> certains checkpoints) ont des licences restrictives (CreativeML Open RAIL-M,
> Stability Community License avec seuil de revenu). **Toujours vérifier la
> licence du modèle ET du code.** Cf. note par module ci-dessous.

---

## 🎨 MODULE 12 — Coloriste Heritage (line-art coloring book)

**Besoin** : convertir une image (PD ou générée) en line-art propre pour coloriage,
lignes fermées, niveau de détail réglable.

| Repo / Lib | Ce que ça fait | License | Verdict |
|---|---|---|---|
| **huggingface/diffusers** | pipeline SD/SDXL/FLUX standard | Apache-2.0 | ✅ socle, depend |
| **lllyasviel/ControlNet** | conditionnement (lineart, canny, scribble) | Apache-2.0 (code) | ✅ inspire / via diffusers |
| **patrickvonplaten/controlnet_aux** | preprocessors lineart/canny/hed clés en main | Apache-2.0 | ✅ depend (drop-in) |
| **Mikubill/sd-webui-controlnet** | UI ControlNet (référence d'implémentation) | GPL ⚠️ | inspire seulement (GPL) |
| **opencv-python** | seuillage binaire, fermeture morphologique des gaps | Apache-2.0 | ✅ depend (post-process) |
| **FLUX.1-schnell (black-forest-labs)** | génération rapide, bon texte | Apache-2.0 (schnell) | ✅ via HF/Replicate |

**⚠️ Licence modèles** : FLUX.1-**schnell** = Apache-2.0 (OK commercial). FLUX.1-**dev** =
non-commercial (INTERDIT prod). SDXL base = CreativeML OpenRAIL (OK commercial mais lire).

**Stack recommandée** : `diffusers` + `controlnet_aux` (preprocessor lineart) + FLUX.1-schnell
ou SDXL + ControlNet-lineart, puis post-process `opencv` (MORPH_CLOSE pour fermer les lignes).

---

## 🖼️ MODULE 15 — Restaurateur Vintage (upscale, colorisation, nettoyage)

| Repo / Lib | Ce que ça fait | License | Verdict |
|---|---|---|---|
| **xinntao/Real-ESRGAN** | upscale x2/x4, photo + dessin | BSD-3 | ✅ vendor / via Replicate |
| **jantic/DeOldify** | colorisation N&B → couleur | MIT | ✅ via Replicate |
| **TencentARC/GFPGAN** | restauration visages anciens | Apache-2.0 | ✅ depend |
| **sczhou/CodeFormer** | restauration visages (SOTA, > GFPGAN) | NTU S-Lab License ⚠️ | vérifier (research-ish) |
| **Sanster/IOPaint** (ex-Lama-Cleaner) | inpainting, retrait objets/taches | Apache-2.0 | ✅ depend |
| **Pillow / scikit-image** | nettoyage, dépoussiérage, niveaux | MIT/BSD | ✅ depend |

**Stack recommandée** : Real-ESRGAN (upscale) → DeOldify (colorisation si N&B) →
GFPGAN (visages si présents) → IOPaint (retrait taches/déchirures) → Pillow (finition).
Sur Replicate pour éviter d'héberger les poids.

**⚠️ CodeFormer** : license S-Lab restrictive — préférer GFPGAN (Apache) pour la prod.

---

## 🧬 MODULE 13 — Engendreur Progeny (fusion 2 parents PD → bébé crossover)

| Repo / Lib | Ce que ça fait | License | Verdict |
|---|---|---|---|
| **tencent-ailab/IP-Adapter** | conditionner par image (préserver style/identité d'un parent) | Apache-2.0 | ✅ depend |
| **InstantID/InstantID** | préserver traits faciaux d'une référence | Apache-2.0 (code) | ✅ utile pour cohérence visage bébé |
| **huggingface/diffusers** | socle pipeline | Apache-2.0 | ✅ depend |
| **continue-revolution/sd-forge-...** | implems récentes adapters | varié | inspire |

**Stack recommandée** : diffusers + 2× IP-Adapter (1 par parent) avec poids pondérés
pour le mashup, + prompt textuel cute/baby. InstantID si on veut un visage cohérent
sur toute une collection.

**⚠️ Rappel légal** : ne s'applique QU'AUX parents de `whitelist_pd.json`. Cf. SECURITE_ET_LEGAL.md §3.

---

## 🏭 MODULE 14 — Marchandiseur Cross-canal (mockups t-shirt/mug/poster)

| Repo / Lib | Ce que ça fait | License | Verdict |
|---|---|---|---|
| **python-pillow/Pillow** | composition, perspective, overlay design sur template | MIT-CMU | ✅ socle |
| **psd-tools** | lire templates PSD (smart objects) | MIT | ✅ depend si templates PSD |
| **opencv-python** | warp perspective réaliste (mug courbe, t-shirt plis) | Apache-2.0 | ✅ depend |
| **Kenney / placeit-like templates** | mockups de base | (chercher CC0) | sourcer CC0 |
| **rembg** | détourage automatique du design | MIT | ✅ depend |

**Stack recommandée** : Pillow + opencv (warp perspective + multiply blend pour les
ombres/plis) sur des templates de mockup CC0. Pas besoin de service payant type Placeit.

**À sourcer** : un set de templates de mockup CC0 (t-shirt blanc/noir, mug, poster
encadré, tote bag, sticker sheet). Chercher sur OpenGameArt, Pexels, ou créer 1 set maison.

---

## 🔭 MODULE 1 — Éclaireur Bestsellers (scraping / APIs marché)

| Repo / Lib | Ce que ça fait | License | Verdict |
|---|---|---|---|
| **python-amazon-paapi** | API officielle Amazon Product Advertising (via Associates) | MIT | ✅ depend (légal, propre) |
| **keepa/keepa-python** | historique prix/BSR Amazon (freemium) | — | optionnel (payant au-delà free) |
| **scrapy** | framework scraping robuste | BSD-3 | ✅ pour scraping structuré |
| **encode/httpx** | client HTTP/2 moderne | BSD-3 | ✅ depend (remplace requests) |
| **microsoft/playwright-python** | navigateur headless (pages JS lourdes) | Apache-2.0 | ✅ depend si JS nécessaire |
| **scrapfly/fake-useragent** | rotation UA pour scraping public | Apache-2.0 | ✅ depend |
| **trending-on-etsy / etsy scrapers communautaires** | top-ventes Etsy | varié | inspire / vérifier ToS |

**⚠️ Légal** : privilégier les **APIs officielles** (Amazon PA-API via Associates,
Pinterest API, future Etsy API) au scraping HTML. Le scraping public reste légal
sur pages affichées sans login, mais rate-limiter agressivement. Cf. SECURITE_ET_LEGAL.md §2.4.

---

## 📖 MODULE 17 — Conteur Cozy (fictions courtes KDP)

| Repo / Lib | Ce que ça fait | License | Verdict |
|---|---|---|---|
| **run-llama/llama_index** | gestion long contexte, mémoire chapitre par chapitre | MIT | ✅ depend |
| **jxnl/instructor** | sorties LLM structurées (JSON fiable) | MIT | ✅ depend (qualité output) |
| **EbookLib** | génération EPUB propre | AGPL ⚠️ | subprocess isolé OU alternative |
| **ReportLab** | génération PDF (intérieur livre) | BSD (open) | ✅ depend |
| **Pandoc** (via subprocess) | conversion markdown → EPUB/PDF | GPL (binaire externe) | ✅ OK en subprocess (pas linké) |

**⚠️ EbookLib AGPL** : si on l'importe, contamine. Solution : utiliser **Pandoc en
subprocess** (binaire externe, pas de linkage) pour markdown→EPUB. Légal et propre.

---

## 🎬 MODULE 18 — Vidéaste Faceless (shorts YouTube/TikTok)

| Repo / Lib | Ce que ça fait | License | Verdict |
|---|---|---|---|
| **Zulko/moviepy** | montage vidéo programmatique | MIT | ✅ socle |
| **ManimCommunity/manim** | animations mathématiques/explicatives | MIT | ✅ depend (vidéos éducatives) |
| **coqui-ai/TTS** ou **Piper** | voix off TTS gratuite | MPL-2.0 / MIT | ✅ depend (Piper léger) |
| **openai/whisper** ou **faster-whisper** | sous-titres auto | MIT | ✅ depend |
| **Stable Video Diffusion** | image → clip court | Stability Community ⚠️ | vérifier seuil revenu |

**Stack recommandée** : moviepy (assemblage) + Piper TTS (voix) + faster-whisper
(sous-titres) + assets vidéo Pexels/Pixabay (gratuit). SVD seulement si licence OK.

**⚠️ Musique** : utiliser uniquement bibliothèques libres (YouTube Audio Library,
Freesound CC0, Pixabay Music) — jamais de musique sous copyright.

---

## 🎲 MODULE 16 — Card Game Designer (decks POD)

| Repo / Lib | Ce que ça fait | License | Verdict |
|---|---|---|---|
| **Pillow + ReportLab** | layout cartes + planche PDF print-ready | MIT/BSD | ✅ socle (déjà utilisé) |
| **nanDECK** (legacy) | langage de description de cartes | freeware | inspire (logique) |
| **squib (Ruby)** | génération de cartes par script | MIT | inspire (port Python) |
| **CardConjurer** | éditeur de cartes web | varié | inspire |

**Note** : on a déjà `produce_card_game.py`. Surtout besoin d'inspiration pour le
gabarit (bleed 3mm, safe zone, dos de carte) — TGC et BGM fournissent leurs specs.

---

## 🎮 MODULE 18b — Game Builder Auto (jeux mobiles casual)

| Repo / Asset | Ce que ça fait | License | Verdict |
|---|---|---|---|
| **godotengine/godot-demo-projects** | squelettes de jeux Godot | MIT | ✅ fork |
| **photonstorm/phaser3-examples** | squelettes Phaser 3 (web/mobile) | MIT | ✅ fork |
| **libgdx/libgdx** | framework jeu Java (Android natif) | Apache-2.0 | ✅ depend |
| **Kenney.nl assets** | sprites/audio/3D CC0 | CC0 | ✅ drop-in |
| **OpenGameArt (filtre CC0)** | assets variés | CC0 | ✅ drop-in |
| **godotengine/godot** | moteur (export APK) | MIT | ✅ depend |

**Stack recommandée** : fork un squelette Godot 4 (export Android natif, gratuit),
swap les assets par du Kenney CC0, adapter la logique via Gemini code-patch.
Premier déploiement Amazon Appstore (gratuit), itch.io (web build), puis Play (25$ reporté).

Cf. `data/sources/domain_public_manifests.json > module_s_specific` (déjà documenté).

### ⚠️ EXCEPTION DE FLUX — décision humaine EN AMONT (règle Hugo 20/05)

Contrairement aux autres modules (production auto → validation finale), le Module S
garde **Hugo dans la boucle de décision en amont** :

```
[1] Bots de recherche (Tendanceur #3 + Éclaireur #1) scannent :
    - tendances jeux mobiles (Play Store charts, itch.io trending, TikTok gaming)
    - modes/mécaniques qui montent (cozy, idle, hyper-casual, color sort...)
    - reviews des top jeux de la niche (pain points #2)
[2] Les bots PROPOSENT à Hugo via Telegram :
    - le type de jeu détecté comme porteur
    - 2-3 squelettes GitHub candidats (avec stars, license, fit)
[3] >>> HUGO DÉCIDE <<< :
    - quel TYPE de jeu on crée
    - quel SQUELETTE de code on importe
[4] SEULEMENT APRÈS sa décision : le Game Builder (#18b) fork le squelette
    choisi, swap les assets, adapte la logique
[5] Validation finale Hugo avant publication (comme les autres modules)
```

→ Les bots ne lancent **jamais** la production d'un jeu sans le double GO de Hugo
(type + squelette). C'est le seul module avec gate de décision en amont.

---

## 📱 MODULE 23 — Messager Telegram (validation 1-clic)

| Repo / Lib | Ce que ça fait | License | Verdict |
|---|---|---|---|
| **python-telegram-bot** | framework bot complet, mature, boutons inline | LGPL-3 | ✅ depend (LGPL OK si non modifié) |
| **aiogram** | alternative async moderne | MIT | ✅ depend (préféré, MIT) |
| **pyTelegramBotAPI (telebot)** | simple, léger | GPL-2 ⚠️ | éviter (GPL) |

**Stack recommandée** : **aiogram** (MIT, async, callback_query natif pour les boutons).
Tourne en GitHub Actions long-polling OU webhook sur Render free tier.

---

## 🏛️ MODULE 5 — Archéologue PD (acquisition sources domaine public)

| Repo / Lib | Ce que ça fait | License | Verdict |
|---|---|---|---|
| **jjjake/internetarchive** | client officiel Internet Archive | AGPL ⚠️ | subprocess CLI (`ia` binaire) |
| **metmuseum API** (pas de lib, REST direct) | Met Open Access CC0 | API gratuite | ✅ httpx direct |
| **Smithsonian Open Access API** | CC0 | API gratuite | ✅ httpx direct |
| **pyEuropeana** | API Europeana | Apache-2.0 | ✅ depend |
| **biodiversity heritage library API** | BHL (Köhler, Haeckel) | API gratuite | ✅ httpx direct |

**Stack recommandée** : httpx direct sur les APIs muséales REST (Met, Smithsonian,
BHL, NYPL, Rijksmuseum, Europeana). Le `ia` CLI en subprocess pour Internet Archive
(évite la contamination AGPL).

---

## 🔧 INFRASTRUCTURE TRANSVERSALE (tous modules)

| Repo / Lib | Ce que ça fait | License | Verdict |
|---|---|---|---|
| **jd/tenacity** | retry avec backoff exponentiel | Apache-2.0 | ✅ depend (réseau) |
| **mjpieters/aiolimiter** | rate-limiter async (quotas LLM) | MIT | ✅ depend |
| **pydantic/pydantic** | validation données + schémas | MIT | ✅ depend (contrats JSON) |
| **python-jsonschema/jsonschema** | validation JSON Schema | MIT | ✅ depend (déjà utilisé) |
| **encode/httpx** | HTTP/2 client moderne | BSD-3 | ✅ depend |
| **tiangolo/typer** | CLI propre pour les scripts | MIT | ✅ depend (UX scripts) |
| **trufflesecurity/trufflehog** | scan secrets exposés | AGPL (binaire) | ✅ OK en GitHub Action |
| **astral-sh/ruff** | lint + format Python ultra-rapide | MIT | ✅ depend (qualité code) |
| **pydantic-settings** | config par env vars typée | MIT | ✅ depend (secrets propres) |

---

## 🗂️ AWESOME-LISTS À SURVEILLER (points d'entrée recherche)

| Liste | Domaine |
|---|---|
| `awesome-python` | tout Python |
| `awesome-godot` | Module 18b jeux |
| `awesome-stable-diffusion` | Modules 12, 13 image gen |
| `awesome-aigc` (AI generated content) | Modules image/vidéo |
| `awesome-public-datasets` | Module 5 sources |
| `awesome-scalability` / `awesome-cron` | infra |
| `awesome-selfhosted` | alternatives gratuites à services payants |

---

## 📋 TABLEAU RÉCAP — décisions d'intégration par module

| Module | Lib principale | Mode | License OK ? |
|---|---|---|---|
| 12 Coloriste | diffusers + controlnet_aux + opencv | depend | ✅ |
| 13 Progeny | diffusers + IP-Adapter | depend | ✅ |
| 14 Marchandiseur | Pillow + opencv + rembg | depend | ✅ |
| 15 Restaurateur | Real-ESRGAN + DeOldify + GFPGAN + IOPaint | via Replicate | ✅ |
| 1 Éclaireur | python-amazon-paapi + scrapy + httpx | depend | ✅ |
| 17 Conteur | llama_index + instructor + ReportLab + Pandoc(subprocess) | mixte | ✅ |
| 18 Vidéaste | moviepy + Piper + faster-whisper | depend | ✅ |
| 16 Card Designer | Pillow + ReportLab | depend (déjà) | ✅ |
| 18b Game Builder | Godot fork + Kenney CC0 | fork + assets | ✅ |
| 23 Messager | aiogram | depend | ✅ |
| 5 Archéologue | httpx + ia(subprocess) + pyEuropeana | mixte | ✅ |
| Infra | tenacity, aiolimiter, pydantic, httpx, ruff, typer | depend | ✅ |

---

## 🔄 PROCESS D'ENRICHISSEMENT CONTINU

Ce document est **vivant**. Chaque fois qu'on attaque un nouveau besoin :
1. Un agent (ou Claude) lance la recherche selon le protocole
2. Le candidat retenu est ajouté ici avec son score /18 et son mode d'intégration
3. Les choix obsolètes sont marqués `⚠️ DÉPRÉCIÉ — remplacé par X`

**À FAIRE (quota WebSearch était épuisé le 19/05)** : valider par recherche web
récente les SOTA 2026 pour : line-art coloring (FLUX vs SDXL+ControlNet),
upscaling (Real-ESRGAN vs nouveaux modèles), et character consistency
(IP-Adapter vs InstantID vs nouveautés). Mettre à jour les entrées concernées.
