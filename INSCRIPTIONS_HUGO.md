# 📋 INSCRIPTIONS HUGO — version 20/05/2026 (Empire Perpétuel, 100% gratuit à l'inscription)

> ## ✅ ÉTAT AU 20/05/2026 (déclaré par Hugo)
> Hugo a rempli les inscriptions **jusqu'à la clé Hugging Face**.
> - **FAIT** : Redbubble · KDP (+ W-8BEN) · clés LLM **gratuites** : Gemini, Groq, Mistral, OpenRouter, Cohere, HF, **Civitai** (`CIVITAI_API_KEY`).
> - **SKIPPÉ volontairement** (payant ou crédit limité — on veut du **100 % gratuit durable**) : Together (2.4), Replicate (2.9), Perplexity (2.10). Couverts par les gratuits + **Pollinations** (génération images **sans clé**) + post-traitement local sans clé.
> - **PAS ENCORE FAIT (priorité)** : **URSSAF** (obligatoire avant la 1ère vente) · **Bitwarden** (Hugo utilise déjà le gestionnaire de mots de passe intégré de son téléphone) · **tout le reste des Vagues 3 → 8**.
> - **Priorité convenue** : les **clés API** d'abord (fait jusqu'à HF). Action débloquante = poser `HF_API_KEY` + `GEMINI_API_KEY` dans les **GitHub Secrets** → ça lance la production.
> - ⚠️ *Les lignes individuelles ci-dessous ne sont pas toutes confirmées une par une : si une case est cochée à tort, signale-le.*

> ## 🎨 GÉNÉRATEURS D'IMAGES — RÉALITÉ AU 21/05 (priorité actuelle)
> État **réel testé depuis GitHub Actions** (c'est notre infra : un service qui marche sur ton tél ne marche pas forcément sur un serveur datacenter).
> - ❌ **Hugging Face** : ne sert **plus** FLUX/SDXL gratuitement (CPU-only depuis mi-2025). Inutile pour l'image.
> - ❌ **Gemini** : **texte uniquement** sur notre clé (le modèle image renvoie HTTP 429 / facturation requise). Gemini reste notre **cerveau texte** (décision, prompts, SEO) — PAS un générateur d'image.
> - ❌ **AI Horde** : testé → **HTTP 403** (derrière Cloudflare anti-bot, qui bloque les IP des serveurs GitHub Actions). Inutilisable depuis notre infra.
> - 🏆 **Together AI** — **À FAIRE (priorité #1, GRATUIT)** : `https://api.together.xyz` → compte → **API key**. **$25 de crédits offerts** + endpoint **FLUX-schnell gratuit** (60 req/min) + **img2img**. Secret GitHub : `TOGETHER_API_KEY`.
> - 🏆 **Cloudflare Workers AI** — **À FAIRE (priorité #2, GRATUIT)** : `https://dash.cloudflare.com` → AI → Workers AI → **API Token** + **Account ID**. Gratuit **10 000 neurons/jour** (~centaines d'images/j, FLUX-schnell + SD img2img). Secrets : `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID`.
> - 💶 **Backup ≤10€/mois** (si on veut + de volume ou la « référence de style ») : **Runware** (FLUX **$0.0006/img** → ~16 000 imgs/mois pour 10€ → `RUNWARE_API_KEY`) · **SiliconFlow** (FLUX **Kontext** = édition guidée par image de référence, **$0.015/img** → `SILICONFLOW_API_KEY`).
> - 🟡 **Pollinations** : gratuit illimité, sans clé, mais brut (dépannage/volume).

**Refonte majeure** : intègre tous les flux ajoutés depuis le 18/05
(Modules A→W, Progeny Engine, arbitrage cross-canal, 15 marchés d'affiliation,
LLM-minions anti-tokens, sécurité Termux/GitHub hybride, bot de validation).

**Règles transversales** :
- 📧 **Email unique** : utilise toujours ton email KDP partout (cohérence reset password)
- 🔐 **Mots de passe** : tous dans **Bitwarden** (vague 0)
- 🛡️ **2FA** : actif partout où possible (priorité : KDP, Google, GitHub, banques)
- 💳 **Aucune CB requise** pour les vagues 0 → 5 (toutes les plateformes payantes
  sont reportées en bas de fichier, section 🔴)
- ⚖️ **Légal** : URSSAF auto-entrepreneur **obligatoire avant 1ère vente**
  (sinon impossible d'encaisser légalement). Coût = 0€ tant que tu ne vends rien.

---

## 🗺️ CARTE DES VAGUES (ordre exact)

| Vague | Quand | Quoi | Pourquoi |
|---|---|---|---|
| **0** | J-0 (immédiat) | Coffre-fort : Bitwarden + Termux + 2FA | rien ne se fait sans |
| **1** | J+1 (15 min) | Légal + 3 premières ventes possibles | URSSAF, Cults3D, Redbubble |
| **2** | J+1 → J+3 | **Stack LLM-minions gratuit** ⭐ | économise 90% de mes tokens |
| **3** | Semaine 1 | POD multi-canal + KDP + Digital direct | saturation revenus passifs |
| **4** | Semaine 1-2 | Trafic organique (Pinterest, TikTok, YT, Reddit) | acquisition gratuite |
| **5** | Semaine 2 | Mobile / Game Dev / API monetization | piliers long terme |
| **6** | Semaine 2-3 | **Affiliation 15 marchés** (sourcing robot) | revenus complémentaires |
| **7** | Semaine 3+ | Domaine public + archives + datasets | matière première gratuite |
| **8** | Semaine 3+ | Bot validation + alertes + dashboards | délégation décision |
| 🔴 | Cash flow ≥ 200€/mois | Payant (Etsy, Printful Pro, Play Console, etc.) | seulement quand ça rentre |

---

# 🧱 VAGUE 0 — LE COFFRE-FORT (J-0, 20 min)

> Avant toute autre inscription. Sans ces 4 outils, le reste fuite ou se perd.

### 0.1 Bitwarden — gestionnaire mots de passe (3 min) ⭐
🔗 https://bitwarden.com
- Inscription gratuite illimitée
- Installe l'app Android **avant** toutes les autres inscriptions
- Sauve chaque login que tu crées ensuite

### 0.2 Aegis Authenticator (2FA via F-Droid) (3 min) ⭐
🔗 https://github.com/beemdevelopment/Aegis (via F-Droid, pas le Play Store)
- 2FA local, exportable, chiffré
- Évite Google Authenticator (lié à un seul compte, perte = catastrophe)
- Alternative : **Ente Auth** (cloud chiffré, gratuit)

### 0.3 Termux + F-Droid (10 min) ⭐⭐ — TON COFFRE-FORT PRIVÉ
🔗 https://f-droid.org/packages/com.termux/ (jamais la version Play Store, obsolète)
- Installe via F-Droid (pas le Play Store : la version Play est figée)
- Packages à installer (`pkg install <nom>`) :
  - `openssh` (push GitHub sécurisé), `git`, `python`, `nodejs-lts`
  - `imagemagick`, `ffmpeg` (traitement images / vidéos local)
  - `termux-api` (notifications Android natives, sans bot tiers)
  - `cronie` ou `at` (planification locale)
  - `tmux` (sessions persistantes, ne perd rien si écran tué)
- **Ce qui RESTE dans Termux (privé) :**
  - Clés API maîtresses (jamais dans le repo)
  - Prompts stratégiques (notre "sauce")
  - Bases SQLite des opportunités détectées
  - Images HD brutes
  - Algorithmes Progeny Engine
- **Ce qui SORT vers GitHub (public) :**
  - Code générique (moteurs de jeux, assemblage PDF)
  - Workflows GitHub Actions
  - Secrets injectés au build (jamais en clair dans le code)

### 0.4 GitHub Mobile + clé SSH Termux (4 min)
🔗 https://github.com/mobile
- Génère une clé SSH dans Termux : `ssh-keygen -t ed25519`
- Ajoute la clé publique sur https://github.com/settings/keys
- Permet le push depuis Termux **sans entrer ton mot de passe** à chaque fois

---

# ⚖️ VAGUE 1 — LÉGAL + 3 PREMIÈRES VENTES (J+1, 25 min)

### 1.1 URSSAF Auto-entrepreneur (10 min) ⭐⭐ INDISPENSABLE
🔗 https://autoentrepreneur.urssaf.fr
- Inscription gratuite
- Activité : **« Vente de produits digitaux et imprimés à la demande »**
- BIC : commerce électronique
- 0€ de cotisation tant que tu n'as pas vendu
- **Indispensable pour encaisser légalement** (sinon Amazon/Redbubble/Stripe peuvent geler les fonds)

### 1.2 Cults3D — STL 3D 80% royalties (3 min)
🔗 https://cults3d.com
- Inscription gratuite, onglet vendeur
- 50+ produits STL paramétriques déjà prêts dans `products/stl_parametric/`

### 1.3 Redbubble — POD t-shirts/posters/stickers (3 min)
🔗 https://www.redbubble.com
- Inscription gratuite (créateur)
- Marge fixée par toi (20-40%)

### 1.4 W-8BEN (formulaire fiscal US, fait en ligne lors de l'inscription KDP/Redbubble)
- À remplir dès le premier compte US (Amazon KDP, Gumroad si > 10$/mois)
- Évite la retenue à la source US de 30% sur tes royalties
- France ↔ US = convention fiscale : 0% retenue avec W-8BEN correctement rempli

---

# 🧠 VAGUE 2 — STACK LLM-MINIONS GRATUIT (J+1 → J+3, 30 min) ⭐⭐⭐

> **OBJECTIF #1** : que **90% du travail rédactionnel / scripts / analyses** soit fait
> par des LLM gratuits, et que je n'intervienne qu'en chef d'orchestre. Inscris-toi
> à TOUS ceux-ci — chacun a un quota distinct, on les fait tourner en rotation.

### 2.1 Google AI Studio (Gemini) ⭐⭐ CRITIQUE
🔗 https://aistudio.google.com/app/apikey
- Gratuit : **1500 requêtes/jour** sur Gemini 2.x (et accès Gemini 3 Flash quand dispo)
- Active : 5 brains perpétuels, QC visuel, rédaction de masse, vision multimodale
- → Secret GitHub : `GEMINI_API_KEY`

### 2.2 Groq Cloud ⭐ (le plus rapide du marché)
🔗 https://console.groq.com
- Gratuit, quota généreux, **latence < 1s** sur Llama 3.x, Mixtral, Gemma
- Idéal pour : rédaction itérative de chapitres (Module K), critique anti-slop
- → Secret GitHub : `GROQ_API_KEY`

### 2.3 Mistral La Plateforme ⭐
🔗 https://console.mistral.ai
- Tier gratuit "Experiment" : suffisant pour scraping/résumé/traduction FR↔EN
- Modèles `mistral-small-latest` et `open-mixtral-8x7b` performants
- → Secret GitHub : `MISTRAL_API_KEY`

### 2.4 Together AI
🔗 https://api.together.xyz
- 1$ de crédit gratuit à l'inscription + tier "Lite" pour modèles open
- Accès Llama 3.x, Qwen, DeepSeek, FLUX image gen
- → Secret GitHub : `TOGETHER_API_KEY`

### 2.5 OpenRouter (méta-routeur)
🔗 https://openrouter.ai
- 1$ de crédit gratuit + modèles "free" routés (Llama 3, Gemma, Mistral free)
- Permet de **basculer automatiquement** entre providers quand un quota tombe
- → Secret GitHub : `OPENROUTER_API_KEY`

### 2.6 Cohere Trial
🔗 https://dashboard.cohere.com
- Trial gratuit, modèles `command-r` excellents pour résumés/RAG/SEO
- → Secret GitHub : `COHERE_API_KEY`

### 2.7 Hugging Face Token ⭐ (images + line-art)
🔗 https://huggingface.co/settings/tokens (type "Read")
- Inference API gratuite sur SDXL, FLUX, ControlNet, IP-Adapter, Real-ESRGAN
- Indispensable pour : coloring books, mashups, Progeny Engine, restoration
- → Secret GitHub : `HF_API_KEY`

### 2.8 Civitai (optionnel mais utile)
🔗 https://civitai.com
- Compte gratuit pour télécharger LoRA spécialisés (line-art, pixel art, styles vintage)
- À combiner avec HF Inference

### 2.9 Replicate (image/vidéo, micro-pay-as-you-go)
🔗 https://replicate.com
- Compte gratuit, 5$ d'essai en s'inscrivant via GitHub
- Accès DeOldify, Real-ESRGAN, Rembg, FLUX, ControlNet hébergés
- Permet de tester un pipeline lourd sans serveur perso
- → Secret GitHub : `REPLICATE_API_TOKEN`

### 2.10 Perplexity Sonar API (essai)
🔗 https://docs.perplexity.ai
- 5$ de crédit free, idéal pour le **scraping intelligent de tendances** (web + sources)
- → Secret GitHub : `PERPLEXITY_API_KEY`

> 📘 **Tuto pour les secrets GitHub** : voir [`SECRETS_GITHUB.md`](./SECRETS_GITHUB.md)
> Toutes les clés vont dans `Settings → Secrets and variables → Actions → New secret`
> Ne JAMAIS coller une clé en clair dans le code (toujours via `os.environ[...]`).

**🎯 Effet de cette vague** : on a 8-10 cerveaux gratuits en parallèle.
Stratégie de routage : tâches lourdes → Gemini/Groq ; tâches courtes/rapides → Mistral ;
images → HF/Replicate ; veille web → Perplexity. Moi (Claude Code) je ne suis appelé que
pour assembler / arbitrer / corriger les pannes.

---

# 🏭 VAGUE 3 — POD MULTI-CANAL + KDP + DIGITAL (Semaine 1, ~50 min)

### POD physique (compléter Redbubble)
- [ ] **3.1 TeePublic** — https://www.teepublic.com (5 min) — mêmes designs, double expo
- [ ] **3.2 Zazzle Designer** — https://www.zazzle.com/sell (5 min) — multi-objets, royalty 5-99%
- [ ] **3.3 Society6 Artist** — https://society6.com/create-store (5 min) — art prints premium
- [ ] **3.4 Printify** — https://printify.com (5 min) — catalogue énorme, marges souvent meilleures
- [ ] **3.5 Prodigi** — https://www.prodigi.com (5 min) — UK premium, gravure laser (utile Château Local)
- [ ] **3.6 Spring (ex-Teespring)** — https://www.spring.shop/sell (5 min) — POD US, paie en €
- [ ] **3.7 Displate** — https://displate.com/displateartist (5 min) — posters métal, niche pop-culture

### Jeux POD (forte marge, vrai pilier)
- [ ] **3.8 The Game Crafter (TGC)** — https://www.thegamecrafter.com (5 min)
- [ ] **3.9 BoardGamesMaker (BGM)** — https://www.boardgamesmaker.com (5 min)
- [ ] **3.10 MakePlayingCards (MPC)** — https://www.makeplayingcards.com (5 min) — paquets pros

### Livres KDP + distribution étendue
- [ ] **3.11 Amazon KDP** — https://kdp.amazon.com (10 min) — W-8BEN à remplir
- [ ] **3.12 Lulu** — https://www.lulu.com (5 min) — hardcover/couverture rigide premium
- [ ] **3.13 IngramSpark** (gratuit depuis 2023) — https://www.ingramspark.com (10 min)
      — distribution physique libraires + bibliothèques mondiales
- [ ] **3.14 Draft2Digital** — https://www.draft2digital.com (10 min) — Apple Books, Kobo, B&N
- [ ] **3.15 Smashwords** — https://www.smashwords.com (5 min) — alt D2D

### Digital direct (sans commission ou minime)
- [ ] **3.16 Gumroad** — https://gumroad.com (5 min) — 10% commission, parfait MVP
- [ ] **3.17 Payhip** — https://payhip.com (5 min) — 5% commission, mieux pour gros prix
- [ ] **3.18 Ko-fi** — https://ko-fi.com (5 min) — 0% commission + tip jar
- [ ] **3.19 Sellfy** — https://sellfy.com (5 min) — alt directe, free tier

### Assets créatifs / SVG / Templates
- [ ] **3.20 Creative Market** — https://creativemarket.com/sell (10 min) — 70% royalty
- [ ] **3.21 CreativeFabrica** — https://www.creativefabrica.com (5 min) — SVG, 70%
- [ ] **3.22 DesignBundles** — https://www.designbundles.net (10 min) — alt CreativeFabrica
- [ ] **3.23 Etsy ⏸️** — **REPORTÉ** (0,20$/listing, voir section 🔴)

### 3D / STL étendu
- [ ] **3.24 Printables (Prusa)** — https://www.printables.com (5 min) — gros trafic
- [ ] **3.25 MyMiniFactory** — https://www.myminifactory.com (5 min) — premium STL
- [ ] **3.26 Thangs** — https://thangs.com (5 min) — moteur recherche STL + monétisation

---

# 📣 VAGUE 4 — TRAFIC ORGANIQUE (Semaine 1-2, ~40 min)

> Le trafic = l'oxygène. Sans audience, pas de ventes même avec 1000 produits uploadés.

### Pinterest (priorité absolue — meilleur ROI organique 2026)
- [ ] **4.1 Pinterest Business** — https://business.pinterest.com (5 min)
  - Active **Rich Pins**
  - Lie au site/Gumroad/Redbubble (vérification domaine)
- [ ] **4.2 Pinterest Developer Platform** — https://developers.pinterest.com (15 min)
  - Token pour auto-publication (Sprint Pinterest Bot)

### TikTok (filtres AR + Reels)
- [ ] **4.3 TikTok Creator** — https://www.tiktok.com (5 min)
- [ ] **4.4 TikTok Effect House** — https://effecthouse.tiktok.com (10 min)
  — création de filtres AR gratuite ; programme créateur rémunère les filtres viraux
- [ ] **4.5 TikTok Shop** ⏸️ (réservé EU/US selon disponibilité)

### Instagram + Meta
- [ ] **4.6 Instagram Business** — https://business.instagram.com (5 min)
- [ ] **4.7 Meta Spark AR / Meta Effects** — https://spark.meta.com (10 min)
  — filtres AR Instagram/Facebook

### YouTube (faceless videos)
- [ ] **4.8 YouTube Studio** (compte Google) — https://studio.youtube.com (5 min)
  — chaîne dédiée par niche
- [ ] **4.9 YouTube Data API** — https://console.cloud.google.com (15 min)
  — uploads automatisés en mode "private" puis tu valides

### Reddit
- [ ] **4.10 Reddit** — compte avec ton vrai pseudo (vraies subreddits ciblées)
- [ ] **4.11 Reddit Developer** — https://www.reddit.com/prefs/apps (5 min)
  — PRAW pour scraping légal des frustrations utilisateurs

### Newsletter / propre liste email
- [ ] **4.12 Beehiiv** — https://beehiiv.com (5 min) — free 2500 abos
- [ ] **4.13 Substack** — https://substack.com (5 min) — alt Beehiiv
- [ ] **4.14 MailerLite** — https://mailerlite.com (5 min) — free 1000 abos + auto

### Image stock gratuites (pour vidéos faceless + visuels)
- [ ] **4.15 Pexels API** — https://www.pexels.com/api (3 min) — clés gratuites
- [ ] **4.16 Pixabay API** — https://pixabay.com/api/docs (3 min)
- [ ] **4.17 Unsplash Developers** — https://unsplash.com/developers (3 min)

---

# 🎮 VAGUE 5 — MOBILE / GAMEDEV / API MONETIZATION (Semaine 2, ~60 min)

### Game Asset Marketplaces (Module H, Module S retombées)
- [ ] **5.1 itch.io** — https://itch.io/register (5 min) ⭐ — assets indie, communauté massive
- [ ] **5.2 Unity Publisher** — https://publisher.unity.com (15 min) — 30% commission
- [ ] **5.3 Fab Marketplace (Epic)** — https://www.fab.com (10 min) — **12% commission, meilleur du marché**
- [ ] **5.4 GameDev Market** — https://www.gamedevmarket.net (5 min)
- [ ] **5.5 OpenGameArt** — https://opengameart.org (5 min) — CC, build réputation
- [ ] **5.6 GitHub Pages + Gumroad** pour vente directe assets ZIP (déjà couvert)

### Modding (Module H)
- [ ] **5.7 CurseForge** — https://www.curseforge.com (10 min) — Minecraft/WoW/Sims, partage revenus pub
- [ ] **5.8 Modrinth** — https://modrinth.com (5 min) — alt CurseForge, communauté Minecraft
- [ ] **5.9 NexusMods Author** — https://www.nexusmods.com (5 min) — Skyrim/FO4/jeux PC majeurs

### Mobile / Android (Module N, Module S)
- [ ] **5.10 Google Play Console** ⏸️ — **REPORTÉ** (25$ one-time, voir 🔴)
- [ ] **5.11 Amazon Appstore Developer** — https://developer.amazon.com (10 min)
      — **GRATUIT** (alternative à Play Store le temps que cash flow rentre)
- [ ] **5.12 F-Droid Repo** — https://f-droid.org/docs/Submitting_to_F-Droid (15 min)
      — distribution open-source gratuite, audience tech
- [ ] **5.13 Google AdMob** — https://admob.google.com (10 min)
      — gratuit, monétisation pub dans apps Android
- [ ] **5.14 AppLovin MAX** — https://www.applovin.com (10 min)
      — alt AdMob, eCPM souvent supérieur

### API monetization (Module E, Module J)
- [ ] **5.15 RapidAPI Provider** — https://rapidapi.com/provider (15 min)
      — publication d'APIs payantes, RapidAPI gère facturation
- [ ] **5.16 Render** — https://render.com (5 min) — free tier, héberge tes APIs FastAPI
- [ ] **5.17 Vercel** — https://vercel.com (5 min) — free tier serverless
- [ ] **5.18 Netlify** — https://www.netlify.com (5 min) — free static hosting
- [ ] **5.19 Cloudflare Workers** — https://workers.cloudflare.com (10 min)
      — free tier 100k req/jour, idéal proxy/scraping/CDN

### Audio packs (Module I, Module Q ASMR)
- [ ] **5.20 BandLab Sounds Marketplace** — https://www.bandlab.com (10 min) — gratuit
- [ ] **5.21 LANDR Samples** — https://samples.landr.com (10 min)
- [ ] **5.22 Pond5 Contributor** — https://www.pond5.com (15 min) — premium SFX/music
- [ ] **5.23 AudioJungle (Envato)** ⏸️ — frais d'auteur (reporté)

---

# 💰 VAGUE 6 — AFFILIATION 15 MARCHÉS (Semaine 2-3, ~90 min)

> Cf. ta matrice M1→M15. Inscris-toi aux **programmes d'affiliation** correspondants.
> Le script génère le lien, tu valides et postes manuellement (anti-ban).

| # | Programme | Lien | Commission typique | Activation |
|---|---|---|---|---|
| M1a | **Amazon Associates FR** | https://partenaires.amazon.fr | 1–10% | 3 ventes en 180j sinon coupé |
| M1b | **Amazon Associates US** | https://affiliate-program.amazon.com | 1–10% | idem |
| M1c | **eBay Partner Network** | https://partnernetwork.ebay.com | 1–6% | gratuit |
| M2a | **Hostinger Affiliate** | https://www.hostinger.com/affiliates | 60% / vente | gros prix |
| M2b | **Shopify Affiliate** | https://www.shopify.com/affiliates | 100$ par parrainage | sélectif |
| M2c | **Brevo Partner** | https://www.brevo.com/partners | 5€/lead + 25%/vente | facile |
| M3 | **Awin** (régie globale) | https://www.awin.com (5$ frais déposés, remboursés à 1ère vente) | varie | accès Booking/Skyscanner/etc. |
| M3b | **CJ Affiliate** | https://www.cj.com | varie | accès grosses marques |
| M3c | **Impact** | https://impact.com | varie | accès Envato/Canva/AirBnB |
| M3d | **TimeOne / Effiliation** (FR) | https://www.timeonegroup.com | varie | accès FNAC/Cdiscount/SNCF |
| M4 | **ThemeForest/Envato** (via Impact) | https://elements.envato.com/affiliate | 30% | via Impact |
| M5 | (couvert par Amazon Associates) | — | — | — |
| M6 | (scraping interne, pas d'inscription) | — | — | — |
| M7a | **KDP** (déjà fait) + **Udemy Affiliate** | https://www.udemy.com/affiliate | 15% | via Impact |
| M7b | **Coursera Partner** | https://www.coursera.org/about/partners | 20–45% | via Impact |
| M8 | **Amazon Business** | — | — | via Amazon Associates |
| M9a | **MyProtein Affiliate** | https://www.myprotein.com/affiliate.list | 8% | via Awin |
| M9b | **Bulk Affiliate** | https://www.bulk.com/affiliates | 8% | direct |
| M10a | **Booking.com Affiliate** | https://www.booking.com/affiliate-program | 25–40% du fee | via Awin |
| M10b | **Skyscanner Partners** | https://www.partners.skyscanner.net | variable | via Awin/direct |
| M10c | **GetYourGuide Partner** | https://partner.getyourguide.com | 8% | direct |
| M11 | (couvert eBay + Amazon) | — | — | — |
| M12a | **BoursoBank parrainage** | (app perso, lien unique) | 80€/parrainage | dans l'app |
| M12b | **Revolut parrainage** | (app perso) | 10–50€ | dans l'app |
| M12c | **N26 parrainage** | (app perso) | variable | dans l'app |
| M13 | (couvert Amazon) | — | — | — |
| M14a | **HeyGen Affiliate** | https://www.heygen.com/affiliate | 30% récurrent | direct |
| M14b | **ElevenLabs Affiliate** | https://elevenlabs.io/affiliates | 25% | direct |
| M14c | **Jasper, Notion, etc.** | via Impact/Partnerstack | varie | recurring |
| M15a | **NordVPN Affiliate** | https://nordvpn.com/affiliate | 30–100% | via CJ |
| M15b | **CyberGhost Affiliate** | https://www.cyberghostvpn.com/affiliates | 100% 1ère vente | via Awin |
| M15c | **Surfshark Affiliate** | https://surfshark.com/affiliates | 40–100% | direct |

**⚖️ Légal obligatoire** : chaque post / commentaire affilié doit inclure
la mention `"En tant que partenaire, je touche une commission..."` ou équivalent
(directive ARPP/DGCCRF en France, FTC aux USA).

---

# 📚 VAGUE 7 — SOURCES DU DOMAINE PUBLIC (Semaine 3+, 0 à 30 min)

> La plupart **ne demandent pas d'inscription** (juste un compte API parfois).
> Matière première gratuite pour Modules U, V, M, M2, P, W (Progeny).

### Texte (Module K, M)
- [ ] **7.1 Project Gutenberg** — https://www.gutenberg.org — pas d'inscription, scraping libre
- [ ] **7.2 Internet Archive** — https://archive.org/account/signup — compte gratuit pour uploads/téléch.
- [ ] **7.3 Wikisource** — pas d'inscription pour lire ; API libre
- [ ] **7.4 HathiTrust** — accès limité hors UE, alternative Internet Archive

### Image / Art (Modules U, V, W)
- [ ] **7.5 Smithsonian Open Access** — https://www.si.edu/openaccess — CC0, 4.5M assets
- [ ] **7.6 Met Museum Open Access** — https://www.metmuseum.org/art/collection/open-access — CC0
- [ ] **7.7 Rijksmuseum API** — https://data.rijksmuseum.nl (clé API gratuite)
- [ ] **7.8 New York Public Library Digital Collections** — https://digitalcollections.nypl.org
- [ ] **7.9 Library of Congress** — https://www.loc.gov — API publique
- [ ] **7.10 British Library Flickr** — https://www.flickr.com/photos/britishlibrary — CC0
- [ ] **7.11 Europeana** — https://pro.europeana.eu/page/apis (clé API gratuite)
- [ ] **7.12 BHL (Biodiversity Heritage Library)** — https://www.biodiversitylibrary.org/api2/docs

### Audio (Module I, Q)
- [ ] **7.13 Freesound** — https://freesound.org/apiv2/apply (clé API gratuite, CC/CC0)
- [ ] **7.14 Free Music Archive** — https://freemusicarchive.org
- [ ] **7.15 Musopen** — https://musopen.org (classique domaine public)

### Code / Datasets (Module M2, J)
- [ ] **7.16 GitHub Search API** (déjà accès via token GitHub) — `stale-repos`, license MIT scanning
- [ ] **7.17 data.gouv.fr** — pas d'inscription pour la plupart
- [ ] **7.18 Kaggle Datasets** — https://www.kaggle.com (compte gratuit, API)
- [ ] **7.19 Hugging Face Datasets** — déjà couvert (compte HF)

**⚖️ Vigilance copyright** :
- "Domaine public" varie par pays. Steamboat Willie : public US depuis 2024,
  mais **les versions modernes de Mickey restent sous copyright**.
- Sherlock Holmes : public US (4 dernières nouvelles tombent en 2027).
  En UE, déjà public depuis 2000.
- Règle interne : **filtrer par date < 1929 (US) + < 1924 (UE)** pour être safe.
- Le **Progeny Engine** (Module W) crée une œuvre dérivée nouvelle = PI propre
  → sortie du périmètre de Disney/Doyle Estate, à condition que la composition
  hybride soit substantiellement transformative (jurisprudence "transformative use").

---

# 🤖 VAGUE 8 — BOT VALIDATION + ALERTES + DASHBOARDS (Semaine 3+, 30 min)

> Délégation de la décision : tu valides en 1 clic depuis ton téléphone, pas en codant.

### 8.1 Telegram Bot (5 min) ⭐
🔗 https://t.me/BotFather — `/newbot`
- Gratuit, instantané, pas d'inscription tierce
- Sauve le `BOT_TOKEN` dans Bitwarden + secret GitHub `TELEGRAM_BOT_TOKEN`
- Crée un canal privé "Empire Control" → ajoute le bot admin
- Récupère `chat_id` → secret GitHub `TELEGRAM_CHAT_ID`
- Le bot t'envoie : aperçus de produits, alertes de tendances, boutons OUI/NON

### 8.2 Discord Webhook (3 min)
🔗 Serveur Discord perso → channel → Webhook
- Plus visuel que Telegram pour les rapports de prod (embeds, images)
- URL secret GitHub `DISCORD_WEBHOOK_URL`

### 8.3 ntfy.sh (0 min, sans inscription)
🔗 https://ntfy.sh
- Notifs push Android sur un topic privé (ex: `ntfy.sh/empire-hugo-XXXX`)
- Aucune inscription, aucun token, parfait pour alertes simples (CI fail, vente, etc.)

### 8.4 Termux:API (déjà installé en vague 0)
- Notifications Android natives sans serveur tiers
- Commande : `termux-notification --title "..." --content "..."`

### 8.5 GitHub Issues comme "centre de commande" (0 inscription)
- Le robot crée des Issues étiquetées `validation-required`, `opportunity`, `bug`
- Tu valides en commentant `/approve` ou `/reject` → un workflow réagit
- Avantage : audit log permanent, accessible depuis l'app GitHub mobile

### 8.6 UptimeRobot (5 min) — monitoring gratuit
🔗 https://uptimerobot.com
- 50 monitors gratuits, alerte si une API perso (Render/Vercel) tombe

---

# 🔴 REPORTÉS (cash flow ≥ 200€/mois)

| Plateforme | Coût | Quand activer |
|---|---|---|
| **Etsy Seller** | 0,20$/listing × 200 = 40$ initial | mois 2-3 |
| **Google Play Console** | 25$ one-time | dès qu'un APK est prêt + 200€/mois |
| **Printful Pro** | 25$/mois | inutile, free tier OK |
| **eRank Etsy SEO** | 10$/mois | seulement si Etsy actif |
| **Canva Pro** | 12€/mois | Photopea/GIMP/Krita gratuits suffisent |
| **DistroKid / TuneCore** | 19$/an | AI Music = mauvaise idée 2026 (cf. LECONS_DU_WEB.md) |
| **AudioJungle (Envato)** | frais auteur | seulement si pack audio rentable validé |
| **Apple Developer** | 99$/an | iOS uniquement quand revenu Android prouvé |
| **GitHub Pro** | 4$/mois | **inutile** : Actions illimitées sur repo public |
| **Termux:Boot premium** | 2,99€ | utile pour startup auto, à voir |
| **Claude Pro / Max** | 18€ → 200€+/mois | **upgrade quand tu génères au moins 3× le coût** |

---

# 📊 RÉCAP : ce qu'on débloque à fin de Semaine 2

| Domaine | Plateformes actives |
|---|---|
| **Coffre-fort** | Bitwarden, Aegis, Termux, GitHub SSH |
| **Légal** | URSSAF, W-8BEN |
| **LLM minions** | Gemini, Groq, Mistral, Together, OpenRouter, Cohere, HF, Civitai, Replicate, Perplexity (10) |
| **POD physique** | Redbubble, TeePublic, Zazzle, Society6, Printify, Prodigi, Spring, Displate (8) |
| **POD jeux** | TGC, BGM, MPC (3) |
| **STL 3D** | Cults3D, Printables, MyMiniFactory, Thangs (4) |
| **Livres** | KDP, Lulu, IngramSpark, D2D, Smashwords (5) |
| **Digital direct** | Gumroad, Payhip, Ko-fi, Sellfy (4) |
| **Assets créatifs** | Creative Market, CreativeFabrica, DesignBundles (3) |
| **Game/Mod** | itch.io, Unity, Fab, GameDev Market, OpenGameArt, CurseForge, Modrinth, NexusMods (8) |
| **Mobile/API** | Amazon Appstore, F-Droid Repo, AdMob, AppLovin, RapidAPI, Render, Vercel, Netlify, Cloudflare (9) |
| **Trafic** | Pinterest + Dev, TikTok + EffectHouse, Instagram + Spark, YouTube + API, Reddit + Dev, Beehiiv, Substack, MailerLite (12) |
| **Stock libre** | Pexels, Pixabay, Unsplash, Freesound, FMA, Musopen (6) |
| **Domaine public** | Gutenberg, Archive.org, Smithsonian, Met, Rijksmuseum, NYPL, LoC, BL, Europeana, BHL, Kaggle (11) |
| **Affiliation** | 15 marchés (M1–M15), majorité via Awin/CJ/Impact (≈25 programmes) |
| **Notif/contrôle** | Telegram Bot, Discord Webhook, ntfy.sh, Termux:API, UptimeRobot |

**Total à dépenser** : 0,00 € (Awin nécessite 5$ déposés, remboursés à la 1ère vente).

---

# 🎯 PROCHAINE ACTION HUGO (à faire avant qu'on continue)

**Coffre-fort (Vague 0)** :
1. Bitwarden ❌ PAS FAIT (Hugo utilise le gestionnaire de mdp intégré du téléphone)
2. Aegis (F-Droid) — à confirmer
3. Termux (F-Droid) — installé mais **pas encore utilisé** (utilité expliquée par Claude ; pas indispensable tant qu'on tourne via GitHub Actions)
4. GitHub Mobile ✅

**Légal + 1ères ventes (Vague 1)** :
5. URSSAF ❌ PAS FAIT — **à faire avant la 1ère vente**
6. Cults3D — à confirmer
7. Redbubble ✅

**LLM-minions (Vague 2)** :
8–13. Gemini ✅ · Groq ✅ · Mistral ✅ · OpenRouter ✅ · Cohere ✅ · HF ✅
14. Civitai ✅ (`CIVITAI_API_KEY`)
❌ **Skippés (payants / crédit limité)** : Together (2.4) · Replicate (2.9) · Perplexity (2.10) → remplacés par les gratuits + Pollinations (sans clé)
\+ **KDP** ✅ (Vague 3.11, fait en avance) · **W-8BEN** ✅

**RESTE À FAIRE** : URSSAF · Bitwarden (optionnel) · Vagues 3 → 8.
**ACTION DÉBLOQUANTE** : poser `HF_API_KEY` + `GEMINI_API_KEY` dans les GitHub Secrets → lance la production.

---

# 🔐 SECRETS GITHUB À CONFIGURER (au fil des inscriptions)

🔗 https://github.com/hugokeirsse-byte/365days/settings/secrets/actions

| Secret | Source | Utilisé par |
|---|---|---|
| `GEMINI_API_KEY` | Google AI Studio | 5 brains + QC + rédaction de masse |
| `GROQ_API_KEY` | Groq Console | rédaction itérative rapide |
| `MISTRAL_API_KEY` | Mistral Console | traduction FR↔EN, résumés |
| `TOGETHER_API_KEY` | Together AI | Llama/FLUX |
| `OPENROUTER_API_KEY` | OpenRouter | fallback multi-LLM |
| `COHERE_API_KEY` | Cohere | résumé/RAG/SEO |
| `HF_API_KEY` | Hugging Face | SDXL, ControlNet, IP-Adapter, Real-ESRGAN |
| `REPLICATE_API_TOKEN` | Replicate | DeOldify, Rembg, FLUX |
| `PERPLEXITY_API_KEY` | Perplexity | scraping intelligent tendances |
| `PINTEREST_API_KEY` | Pinterest Dev | auto-publication pins |
| `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` | Reddit Dev | PRAW scraping |
| `YOUTUBE_API_KEY` + OAuth | Google Cloud | upload faceless videos |
| `PEXELS_API_KEY` / `PIXABAY_API_KEY` / `UNSPLASH_API_KEY` | (idem) | stock images |
| `RAPIDAPI_PROVIDER_KEY` | RapidAPI | publication APIs |
| `ADMOB_APP_ID` | AdMob | injection SDK dans APKs |
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | BotFather | bot validation |
| `DISCORD_WEBHOOK_URL` | Discord channel | rapports prod |
| `AMAZON_ASSOCIATES_TAG_FR` / `_US` | Associates | affiliation M1 |
| `AWIN_API_TOKEN` | Awin | accès Booking/MyProtein/etc. |

📘 Tuto détaillé : [`SECRETS_GITHUB.md`](./SECRETS_GITHUB.md)

---

# 🆘 EN CAS DE BLOCAGE

| Symptôme | Cause probable | Action |
|---|---|---|
| « Compte Amazon Associates suspendu après 180j » | pas atteint 3 ventes | recréer, revenir avec trafic Pinterest |
| « KDP refuse W-8BEN » | identité non validée | scan passeport via dashboard KDP |
| « Awin demande 5$ pour ouvrir » | normal | dépôt remboursé à la 1ère commission |
| « Quota Gemini épuisé » | 1500/jour dépassé | router vers Groq/Mistral via OpenRouter |
| « GitHub Actions 2000 min/mois épuisées » | repo passé en privé ? | **garder le repo public** : minutes illimitées |
| « TikTok rejette mon filtre AR » | review manuelle requise | normal, 24-48h d'attente |
