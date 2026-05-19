# 🛡️ SÉCURITÉ & CADRE LÉGAL — la pérennité avant la vitesse

**Date** : 2026-05-19
**Doctrine** : *« Une boutique bannie tue 6 mois de travail. Un compte fiscal mal réglé tue l'entreprise. »*
Aucune optimisation de vitesse ne vaut un seul ban Amazon, Google ou Stripe.

---

## 🎯 1. LES 5 RISQUES MAJEURS À COUVRIR

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| **R1 — Ban POD pour spam / contenu IA mal labellisé** | élevée | catastrophique | Throttling + filtre anti-slop + validation humaine staging |
| **R2 — Strike copyright (Disney, DC, Marvel, succession Doyle…)** | moyenne | grave | Liste blanche stricte + Progeny Engine + lien date >100ans |
| **R3 — Fiscalité (URSSAF, W-8BEN, TVA OSS)** | certaine si on vend | catastrophique | URSSAF Vague 1 + W-8BEN J1 + OSS quand >10k€/an |
| **R4 — Fuite de clés API / vol de prompts maîtres** | moyenne | grave | Termux privé + Secrets GitHub + jamais de clé en clair |
| **R5 — Compte unique = perte unique** | élevée à 12 mois | grave | Diversification plateformes + email maître protégé 2FA |

---

## 🔒 2. R1 — ANTI-BAN POD / KDP / MOBILE STORES

### 2.1 Throttling : le rythme « humain »

| Plateforme | Limite stricte recommandée | Limite officielle | Explication |
|---|---|---|---|
| **Amazon KDP** | ≤ 5 livres/jour, ≤ 30/semaine | aucune publique | au-delà = review manuelle prolongée |
| **Amazon Merch on Demand** | ≤ 5 designs/jour | tier-dépendant | 1ère tier = 25 designs total, monter lent |
| **Redbubble** | ≤ 20 designs/jour | aucune | mais 30+ déclenche review |
| **TeePublic** | ≤ 20 designs/jour | aucune | idem |
| **Etsy** (reporté) | ≤ 5 listings/jour | aucune | sensible à la nouveauté du compte |
| **Cults3D** | ≤ 10 STL/jour | aucune | OK plus généreux |
| **Gumroad** | illimité techniquement | — | mais pic = soupçon, lisser |
| **Google Play** | ≤ 1 app/semaine | aucune | strike facile en mobile |
| **YouTube Shorts** | ≤ 3 vidéos/jour | aucune | spam-detection algo agressive |

**Implémentation** : tous les uploads passent par une **queue locale Termux**
qui libère 1 produit toutes les X minutes (X variable aléatoire entre 45 et 180).
Cf. `AUTOMATION_BLUEPRINT.md` §6 (bot Telegram = validation manuelle).

### 2.2 Filtre anti-slop (zéro tolérance qualité IA visible)

Chaque asset passe **3 contrôles** avant d'atteindre staging :

1. **Contrôle technique automatique** (Python déterministe, 0 token) :
   - PDF : pages > 300 DPI ? bleed correct ? police embedded ?
   - PNG : dimension exacte ? CMJN si KDP couverture ? alpha si transparent ?
   - APK : signature valide ? permissions minimales ? SDK target récent ?
   - **Échec → poubelle automatique, pas même staging**

2. **Contrôle vision** (Gemini Vision, ~1 req par asset) :
   - "Cette image trahit-elle une production IA ? (mains à 6 doigts, texte gibberish, perspective cassée)"
   - "Si on retire le nom de la marque, est-ce qu'un acheteur Etsy paierait 15€ ?"
   - Score < 7/10 → boucle de correction (max 3 tentatives)

3. **Contrôle humain** (Hugo, bot Telegram) :
   - Le seul à publier. Aucune publication automatique.
   - Boutons ✅ / ❌ / 🔍 voir détails.

### 2.3 Métadonnées : pas de "ChatGPT-isms" qui trahissent

Mots/structures **interdits dans titres/descriptions** (signature LLM courante) :
- "Unleash" / "Embrace" / "Dive into" / "Discover the" / "In the realm of"
- "tapestry" / "rich tapestry" / "whimsical journey"
- "Let me know if you'd like..." (oubli copier-coller — fatal)
- Em-dash (—) en excès, virgule d'Oxford forcée
- Pluriels "the X and the Y" trop balancés

→ Implémentation : filtre regex post-LLM + reformulation Mistral si match.

### 2.4 Rotation User-Agents (pour scraping uniquement, pas upload)

```python
from fake_useragent import UserAgent
ua = UserAgent(browsers=['Chrome', 'Firefox', 'Safari', 'Edge'])
headers = {'User-Agent': ua.random}
```

Les **uploads** passent par les APIs officielles (KDP API, Pinterest Dev API, Amazon Associates, etc.) qui n'exigent pas de rotation UA, mais demandent un token. Pas de Selenium/Playwright sauf si pas d'API disponible.

---

## ⚖️ 3. R2 — COPYRIGHT : ZONE BLANCHE STRICTE

### 3.1 Tableau des dates clés (à mettre à jour chaque 1er janvier)

| Œuvre | Statut US (2026) | Statut UE (2026) | Utilisable ? |
|---|---|---|---|
| **Steamboat Willie (Mickey 1928)** | PD depuis 2024 | PD depuis 2024 | OUI (la version 1928 SEULEMENT, pas Mickey moderne) |
| **Tigger / Winnie l'Ourson** | PD depuis 2024 | mixte (selon édition) | OUI texte 1926, ATTENTION Tigger 1928 |
| **Sherlock Holmes (canon Doyle)** | PD intégral en 2027 (4 dernières en 2027) | PD depuis 2000 | OUI canon + nouvelles antérieures à 1930 |
| **Dracula (Stoker 1897)** | PD | PD | OUI |
| **Phantom of the Opera (Leroux 1910)** | PD | PD | OUI |
| **Tarzan (Burroughs 1912)** | PD depuis 2008 (US) | PD | OUI livres antérieurs à 1930 |
| **Old Maid card games** | PD anciennes éditions | PD | OUI |
| **Tom Swift / Nancy Drew premiers tomes** | PD pour tomes < 1929 | PD | OUI seulement tomes anciens |
| **Old superheroes Centaur/Fox/Holyoke (1938-1944)** | majoritairement PD | PD | OUI (voir liste 3.4) |
| **Superman (Action Comics #1, 1938)** | sous copyright DC jusqu'en 2034 | idem | **NON** |
| **Batman (1939)** | sous copyright DC jusqu'en 2035 | idem | **NON** |
| **Captain America (1941)** | Marvel | idem | **NON** |
| **H.P. Lovecraft (mort 1937)** | PD US (publication < 1929) | PD depuis 2008 (mort + 70) | OUI majorité |

### 3.2 Règle d'or interne : DOUBLE BARRIÈRE

Pour qu'une œuvre soit **utilisable** par nos modules :
1. **Date** : publication avant **1929** (zone safe US ET UE)
2. **Personnage spécifique** : confirmer qu'il n'a pas été "modernisé" par un titulaire récent
   - Mickey 1928 = OK ; Mickey 1990 = NON (modernisé sous copyright)

→ Si une œuvre passe la double barrière, elle entre dans `data/whitelist_pd.json`.

### 3.3 Le Progeny Engine — fair use transformatif

La méthode **Progeny Engine** (Module W) ajoute une couche de sécurité même
sur des œuvres récentes, via la **doctrine du fair use transformatif** (US) et
**l'exception de parodie/œuvre dérivée** (Code de la PI français, art. L. 122-5) :

1. **Sujet inédit** : on crée un personnage NOUVEAU (le "Progeny") fusionnant
   des attributs de plusieurs œuvres. Ce n'est ni l'un ni l'autre.
2. **Transformation substantielle** : on change le style (cute/baby/badass),
   le contexte narratif, l'âge, la pose.
3. **Non-substituable au marché original** : un bébé Sherlock Holmes-Golem
   n'entre pas en compétition avec les rééditions de Conan Doyle.

**MAIS** : le fair use est une défense, pas un permis. Donc même avec Progeny :
- On ne touche **jamais** aux franchises actives (Disney, DC, Marvel, Nintendo, Pokémon, Star Wars, Harry Potter, Mickey post-1929, Astro Boy, One Piece, etc.)
- Le Progeny Engine s'applique **uniquement** sur des couples dont les 2 parents passent la double barrière 3.2

### 3.4 Liste blanche des super-héros tombés dans le domaine public US

> Source canonique : **Public Domain Super Heroes Wiki** (publicdomainsuperheroes.com)
> et **Wikipédia** "List of public domain superheroes". À vérifier au cas par cas
> (date de publication, renouvellement de copyright omis).

**Compatible avec ton idée "cute crossover bébés super-héros"** :

| Héros | Éditeur | Date | Statut PD |
|---|---|---|---|
| **Stardust the Super Wizard** | Fox Feature (1939) | 1939 | PD (Fox a perdu droits) |
| **Captain Wonder** | Holyoke (1942) | 1942 | PD |
| **The Black Owl** | Prize Publications (1940) | 1940 | PD |
| **The Eye** | Centaur (1939) | 1939 | PD |
| **Doll Man** (premières apparitions Quality) | Quality (1939) | 1939 | mixte — vérifier au cas par cas |
| **Phantom Lady (Quality)** | Quality (1941) | 1941 | PD partiel |
| **The Heap** | Hillman (1942) | 1942 | PD |
| **Amazing-Man** | Centaur (1939) | 1939 | PD |
| **Black Terror** | Nedor (1941) | 1941 | PD |
| **The Fighting Yank** | Nedor (1941) | 1941 | PD |
| **Miss Masque** | Nedor (1946) | 1946 | PD |
| **Yankee Doodle Jones** | (1941) | 1941 | PD |
| **Skyman** | Columbia/Big Shot (1940) | 1940 | PD |
| **Daredevil** (Lev Gleason version, PAS Marvel) | Lev Gleason (1940) | 1940 | PD |
| **Mr. Justice** | MLJ (1940) | 1940 | PD |
| **Bulletman** (Fawcett) | Fawcett (1940) | 1940 | mixte — Fawcett racheté DC, vérifier |
| **The Green Lama** | Prize (1940) | 1940 | PD |
| **Cat-Man (Holyoke)** | Holyoke (1941) | 1941 | PD |
| **Silver Streak** | Lev Gleason (1939) | 1939 | PD |

**Concept "cute crossover bébés super-héros" — 5 combos à shipper en pilote** :
1. **Bébé Stardust × Bébé Phantom Lady** (cosmic + détective)
2. **Bébé Captain Wonder × Bébé The Heap** (force + nature)
3. **Bébé Black Terror × Bébé Miss Masque** (justice duo)
4. **Bébé The Eye × Bébé The Green Lama** (mystique duo)
5. **Bébé Stardust × Bébé Bulletman** (vitesse cosmique)

→ Chaque combo passe par : Progeny Engine → coloring book + sticker pack + t-shirt
+ poster + livre illustré court (KDP) → Module W full pipeline.

### 3.5 Quarantaine immédiate

Si une plateforme refuse un design pour copyright :
1. Retrait immédiat du compte
2. La niche concernée passe en `data/blacklist_copyright.json`
3. Le module producteur ne re-générera plus rien avec ce couple parent
4. Alerte Telegram à Hugo avec capture du refus

---

## 📜 4. R3 — FISCALITÉ ET COMPTABILITÉ

### 4.1 Auto-entrepreneur français — l'essentiel

- **Seuil 2026** : 77 700 € de chiffre d'affaires (services BIC) avant bascule
- **Cotisations** : ~22% du CA (URSSAF + impôt libératoire si choisi)
- **Déclaration** : mensuelle ou trimestrielle sur autoentrepreneur.urssaf.fr
- **Compte bancaire dédié** : obligatoire au-delà de 10k€/an de CA
  → Ouvrir un **2ème compte Boursorama / Revolut Business** (gratuit) en mois 2

### 4.2 W-8BEN — éviter la retenue US 30%

À remplir sur **chaque plateforme US** lors de la 1ère inscription ou dans les
paramètres fiscaux :
- KDP, Gumroad (si revenu > 10$), Redbubble US, TeePublic, Spring
- Identifiant : **TIN français = ton numéro fiscal de 13 chiffres** (sur ton avis d'imposition)
- Convention France-USA : **0% de retenue à la source** sur les royalties si W-8BEN correctement rempli

### 4.3 TVA OSS — quand on vend B2C dans l'UE > 10k€/an

- Sous 10k€/an UE : TVA française uniquement (régime franchise auto-entrepreneur)
- Au-delà : inscription au **guichet unique OSS** (impots.gouv.fr) pour reverser
  TVA dans chaque pays UE → géré par les plateformes (Amazon, Gumroad), pas par toi

### 4.4 Plateformes qui reversent automatiquement

| Plateforme | Retient & reverse TVA UE ? | Action Hugo |
|---|---|---|
| Amazon KDP | OUI | rien |
| Etsy (quand activé) | OUI (depuis 2021) | rien |
| Redbubble | OUI | rien |
| TeePublic | OUI | rien |
| Gumroad | OUI (depuis 2015) | rien |
| Cults3D | OUI | rien |
| **Direct (ton site Stripe)** | NON | **ne PAS faire avant 10k€/an** |

---

## 🔐 5. R4 — SÉCURITÉ DES CLÉS ET PROMPTS MAÎTRES

### 5.1 Architecture du coffre-fort (rappel Vague 0)

```
┌──────────────────────────────────────────┐
│ TERMUX (Android, privé, jamais en ligne) │
│ ~/empire/secrets/                        │
│ ├── api_keys.env (chmod 600)             │
│ ├── prompts_master/ (recettes)           │
│ └── ssh_keys/                            │
└──────────────────────────────────────────┘
                  ↓ ssh + push uniquement
┌──────────────────────────────────────────┐
│ GITHUB (public, code générique)          │
│ Secrets injectés au runtime              │
│ ├── GEMINI_API_KEY = ${{ secrets.X }}    │
│ └── jamais en clair dans le code         │
└──────────────────────────────────────────┘
```

### 5.2 Règles immuables

- ❌ **Jamais** une clé API dans un fichier `.py` commité (même en commentaire)
- ❌ **Jamais** un `.env` dans le repo (ajouter `.env` au `.gitignore` immédiatement)
- ✅ Toujours `os.environ.get("CLE_X")` avec fallback explicite si manquant
- ✅ Toujours **2FA obligatoire** sur les comptes maîtres (Gmail, GitHub, Amazon)
- ✅ Toujours **mot de passe unique fort** (Bitwarden génère 20+ caractères)
- ✅ Rotation annuelle des tokens (GitHub Personal Access Token, API keys)

### 5.3 Prompts maîtres = trade secret

Les prompts qui définissent **comment** nos modules produisent (Progeny Engine,
scoring matrices, style transfer instructions, anti-slop critic) :
- **Restent dans Termux**, dossier `prompts_master/`
- Sont **chargés au runtime** dans GitHub Actions via un **gist privé** ou
  un **secret GitHub** (`MASTER_PROMPTS_BASE64`) si moins de 64KB

**Ce qu'on accepte de mettre en public dans le repo** :
- Skeletons de prompts (templates avec `{{ variable }}` à remplir)
- Logique de routage (qui appelle quoi quand)
- Schémas JSON canoniques (contrats entre modules)

**Ce qu'on protège** :
- Les exemples spécifiques few-shot qui rendent un prompt performant
- Les seuils numériques exacts du scoring matrix (au-delà de 15/20 = validé, etc.)
- Les blacklists internes (mots-clés trahis comme IA, niches saturées)

### 5.4 Audit régulier des secrets exposés

Tous les 30 jours, lancer un scan automatique :
```bash
# truffleHog (gratuit, open-source) scanne l'historique git
trufflehog git file://. --only-verified
```
→ GitHub Action `secret_audit.yml` (cron mensuel). Aucune intervention.

---

## 🪪 6. R5 — DIVERSIFICATION POUR ÉVITER LA PERTE UNIQUE

### 6.1 Email maître

- **1 seul email** lié à tout (Bitwarden, Gmail, AWS, KDP, GitHub…)
- → si compromis = catastrophe
- **Mitigation** : 2FA Aegis (pas SMS) + **clé physique YubiKey** (~50€) dès cash flow > 200€/mois

### 6.2 Diversification revenus

| Pilier | Plateformes (objectif) | Pourcentage cible mois 12 |
|---|---|---|
| POD physique | Redbubble + TeePublic + Zazzle + Society6 + Spring | 25% |
| Livres KDP | KDP + D2D + IngramSpark | 25% |
| Digital direct | Gumroad + Payhip + Ko-fi | 15% |
| Jeux POD | TGC + BGM + MPC | 10% |
| 3D STL | Cults3D + Printables + MyMiniFactory | 5% |
| Mobile games | Amazon Appstore + F-Droid + plus tard Play | 10% |
| API monetization | RapidAPI | 5% |
| Affiliation | Amazon Associates + Awin + parrainages | 5% |

→ **Si une plateforme tombe = perd 5-25% du revenu, pas tout.**

### 6.3 Backup repo

- Repo principal GitHub (public)
- **Mirror automatique** vers Codeberg (gratuit, alternatif) via GitHub Action
- **Backup local** Termux : `git clone --mirror` mensuel sur la carte SD

---

## 🚨 7. PROTOCOLE D'INCIDENT — checklist en cas de drame

### 7.1 Ban d'un compte (KDP / Redbubble / Etsy)

1. **Ne pas paniquer**, ne pas recréer un compte sur le même email immédiatement
2. Lire le mail de notification → identifier la raison
3. Appel ticket support (réponse 7-21 jours selon plateforme)
4. **Pendant l'attente** : router le pipeline vers la plateforme alternative
   (TeePublic si Redbubble, Lulu si KDP, etc.)
5. Si refus définitif : nouvelle entité (associé / SARL → Vague 9 future) ou pivot

### 7.2 Strike copyright

1. **Retirer immédiatement** tous les produits utilisant l'œuvre concernée
2. La niche passe en `data/blacklist_copyright.json`
3. Si possible, **contester** (counter-notice DMCA si tu es certain du fair use) — mais
   privilégier le retrait silencieux
4. Notif Telegram à Hugo pour décision

### 7.3 Compte bancaire gelé

1. Stripe / banque demande des justificatifs → fournir attestation URSSAF + factures
2. Si bloqué > 30 jours → migration vers Wise / Revolut Business comme backup
3. Toujours avoir **2 comptes pro** dès cash flow > 500€/mois

### 7.4 Vol de clés / hack

1. Si suspicion de compromission **immédiatement** :
   - Révoquer la clé sur le dashboard provider
   - Régénérer
   - Mettre à jour Secret GitHub
   - Audit logs : qui s'est connecté ?
2. Si Bitwarden compromis : exporter, créer nouveau vault, changer tous les MDP

---

## ✅ 8. CHECKLIST DE LANCEMENT — avant d'allumer un module

Avant le premier upload d'un nouveau module, valider les 7 points :

- [ ] **L1** : la niche / personnage est dans `data/whitelist_pd.json` (si Module U/V/W/P)
- [ ] **L2** : la plateforme cible accepte le format (ex: KDP non-fiction vs low-content rules)
- [ ] **L3** : URSSAF active (1er upload payant uniquement)
- [ ] **L4** : W-8BEN rempli sur la plateforme US
- [ ] **L5** : compte bancaire dédié configuré (si > 10k€/an de CA prévu)
- [ ] **L6** : 2FA actif sur le compte plateforme
- [ ] **L7** : staging Telegram opérationnel (validation humaine prête)

Tant qu'un module n'a pas validé ces 7 cases, il reste en mode **dry-run** (génère mais ne publie pas).

---

## 📖 ANNEXES — sources légales

- **Code de la PI (France)** : art. L. 111-1 → L. 122-12 (droits d'auteur), art. L. 122-5 (exceptions parodie/dérivée)
- **US Copyright Office Circular 14** : œuvres dérivées et compilations
- **Convention de Berne** : durée minimale 50 ans post-mortem (UE applique 70 ans)
- **DMCA Title 17 §512** : safe harbor, counter-notice
- **RGPD** : on ne collecte aucune donnée client direct (les plateformes gèrent)
- **DGCCRF (France) sur affiliation** : mention obligatoire `« lien sponsorisé »` ou `« partenariat »`
- **FTC (US) Endorsement Guides** : disclosure obligatoire en marketing d'affiliation

> Ce document n'est pas un avis juridique. Pour les décisions à fort enjeu
> (entité SARL, conflit copyright sérieux), consulter un avocat IP spécialisé.
