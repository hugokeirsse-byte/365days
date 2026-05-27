# 📐 CAHIER DES CHARGES — Empire de production automatisée

**Version** : 2026-05-20 · **Porteur** : Hugo · **Repo** : `hugokeirsse-byte/365days`

> Ce document est **autonome** : il explique l'objectif, les marchés, le système d'agents,
> la boucle de production et les règles, pour pouvoir être lu par Hugo **et audité par une
> autre IA**. Documents de détail liés : `MAP_BUSINESS_ET_AGENTS.md`, `NOUVELLES_IDEES.md`,
> `LIBRARIES_AND_REPOS.md`, `CLAUDE_TOOLS.md`, `SECURITE_ET_LEGAL.md`, `INSCRIPTIONS_HUGO.md`,
> schémas dans `data/schemas/`.

---

## 1. VISION & OBJECTIF

Construire une **usine de production de contenu numérique et physique**, la **mieux organisée
possible**, qui tourne de façon largement autonome et **pluri-marché**. Des IA spécialisées
détectent les opportunités, produisent des produits **finis « clé en main »**, les auto-corrigent
jusqu'à aboutissement, puis les présentent à Hugo. **Hugo ne fait que valider et publier**
(et injecter parfois ses propres idées).

**Objectif chiffré du modèle** : volume **à qualité constante**, coût d'infrastructure ≈ **0 €**
(outils gratuits en rotation), revenus diversifiés sur de **nombreuses plateformes**.

**Principe fondateur** : *« On ne code/crée jamais à partir d'une page blanche. Pour chaque
besoin, on cherche d'abord un outil/repo/asset open-source mature à réutiliser ou combiner. »*

---

## 2. PRINCIPES DIRECTEURS (doctrine)

1. **Qualité > volume** : beaucoup de produits, mais **chacun fini et soigné** ; certains en
   qualité supérieure. Jamais « 2000 produits médiocres » — les plateformes le sanctionnent.
2. **Gratuit & durable** : on s'appuie sur des fournisseurs **gratuits** (pas sur des crédits
   d'essai de 1-5 $, gardés en réserve ponctuelle). On **multiplie les fournisseurs**, jamais
   les comptes d'un même fournisseur (= bannissement assuré).
3. **Multi-provider en rotation** : Gemini / Groq / Mistral / Cohere / HF… ; si un quota tombe,
   on bascule (`data/config/llm_routing.json`).
4. **Cascade temporelle** : les agents de fond sont **espacés dans le temps** pour rester sous
   les quotas gratuits. « Perpétuel » = *capable de tourner en boucle quand on l'allume*, **pas**
   *allumé en permanence*.
5. **Réutilisation maximale (MIX)** : forker/combiner des morceaux de plusieurs repos
   open-source compatibles (licences MIT/Apache/BSD/CC0 ; jamais GPL/AGPL/CC-BY-NC en prod).
6. **Anti-dérive** : chaque agent reçoit des **rappels permanents de son rôle** + un contrat
   précis, pour ne pas dériver.
7. **Diffusion semi-manuelle (anti-ban)** : pas d'upload 100 % automatique. La machine prépare
   tout (kit de publication) ; **Hugo colle et publie** → action humaine = indétectable.
8. **Focus marché anglais** par défaut (US/UK = plus gros marché) ; **adaptation** si l'analyse
   détecte un gros marché national (ex. France, Inde…).
9. **Légal & sûr** : domaine public vérifié (filtre pré-1929 US), licences contrôlées, secrets
   chiffrés (GitHub Secrets), W-8BEN, URSSAF avant 1ère vente. Cf. `SECURITE_ET_LEGAL.md`.

---

## 3. LES MARCHÉS / BUSINESS

Multi-business, multi-plateforme. Familles actives + en réserve :

| Famille | Exemples de produits | Plateformes |
|---|---|---|
| **Coloriages** (historiques PD + modernes mignons) | coloring books KDP, cartes line-art | KDP, Gumroad, Redbubble |
| **KDP low-content** | journaux, planners, gratitude, trackers | KDP |
| **Merch POD** (1 design × N supports) | t-shirt, mug, poster, sticker | Redbubble, TeePublic, Zazzle, Society6… |
| **Cartes / jeux POD** | decks humour métier | TGC, BGM, MPC |
| **Restauration vintage** | upscale + colorisation d'archives PD | Redbubble posters, KDP collector |
| **Fictions / romans courts** | contes cozy, dark academia | KDP, D2D |
| **Jeux** (script narratif d'abord) | fiction interactive à choix | itch.io, Amazon Appstore, Play (reporté) |
| **Apps** | assemblage d'outils gratuits clé en main | stores mobiles |
| **3D / STL** | modèles à imprimer | Cults3D, Printables, MyMiniFactory |
| **Vidéo faceless** | shorts process / lore | YouTube, TikTok |
| **Affiliation** | 15 marchés (liens + messages pré-rédigés) | Amazon, Awin, CJ, Impact… |

**Produits mixtes** (créneau à fort potentiel) : combiner les formats — ex. *coloriage + explications
du sujet*, *livre d'horreur + illustrations à colorier*, *image qui marche en merch → déclinée en
livre*. La règle : un produit peut **hybrider** deux formats qui marchent.

---

## 4. LE MOTEUR DE DÉCISION (« quoi produire »)

Avant toute production, le **Stratège** choisit **la meilleure opportunité à l'instant T**
(potentiel × faisabilité × fraîcheur). Ses 4 stratégies :

1. **Mono-trend** — exploiter une trend forte.
2. **Cross-trend** — croiser 2+ trends (ex. *cute × super-héros*).
3. **Original** — idée innovante propre (parfois on **crée** la trend).
4. **Refonte/amélioration** — reprendre un **bestseller mal noté** et corriger ses défauts.

**Trends × Niches** : on ne fait pas qu'exploiter les trends — on les **croise avec des niches
sous-exploitées** (ex. *coloriage mignon × pêche au carnassier*) et avec le **domaine public**
(ex. *planches Köhler × psaumes de la Bible* si c'est la trend). On met **les bons mots-clés**
pour capter l'audience.

**Déclinaisons multiples** (jamais un seul pari par trend) :
- Pour une trend, on produit **plusieurs variations** pour maximiser les chances qu'une touche.
- **Designs/merch** : N variations visuelles du thème.
- **Livres** : pas le même livre — des variations qui reprennent/croisent les mots hypés.
- **Non-clones** : les déclinaisons ne doivent **pas réutiliser les mêmes images** ni se
  ressembler ; on s'inspire d'un sujet, on varie par mix (trend × niche × original).
  *Exception* : extension d'une **collection** d'un produit qui a marché (cohérence voulue).
- **Allocation proportionnelle** : si une trend est **dominante**, on lui consacre beaucoup
  plus de produits.

**3 sources d'idées** :
1. **Auto** — l'IA lance directement la production sur ses meilleures opportunités.
2. **Semi-originale** — une IA génère un **dossier d'idées innovantes** ; Hugo le lit à son
   rythme et coche « celle-là, on la lance ».
3. **Hugo** — ses propres idées, injectées comme commandes prioritaires.

Contrat machine : `data/schemas/product_brief.schema.json` (stratégie, force de trend,
nb de déclinaisons, style + images de référence, format, ton, signature, collection).

---

## 5. LA BOUCLE DE PRODUCTION AUTONOME

```
[Détection]  Scout Marché + Radar/Émergence + niches → signaux
      ↓
[Décision]   Stratège choisit l'opportunité + génère le BRIEF PRODUIT précis
      ↓
[Production] Producteur génère (plusieurs déclinaisons), en parallèle si léger
      ↓
[Audit]      Juge Qualité note POINT PAR POINT contre le Brief
      ├─ défaut CORRIGEABLE → route vers l'outil de réparation (upscale, fermer
      │     les lignes, texture, redressement, inpainting) → re-audite
      ├─ pas abouti → corrige et reboucle (bornée)
      ├─ bloqué insoluble → STOP + alerte Hugo (jamais de boucle infinie)
      └─ ABOUTI (clé en main) → STOCK → enchaîne le produit suivant
      ↓
[Validation] HUGO dépile le stock : publie / non (retour boucle, motif)
```

**Définition « clé en main »** : produit **100 % publiable**, rien à retoucher. Ex. coloring book =
titre + sous-titre pensés **en collection** + déclinaison prévue + couverture + **mise en page KDP
sans erreur** + métadonnées de listing prêtes.

**Visuel obligatoire** : un produit « juste du texte » ne vend pas. Règle = **un visuel sympa**
(fond illustré) **OU** une écriture vraiment marrante/piquante (pour t-shirt/mug). Sinon → rejet.

**Texte dans les images** : les modèles d'image gèrent mal le texte → on **génère le visuel sans
texte** (HF) puis on **incruste le texte avec Pillow** (police nette, multilingue). Image et texte
**séparés puis assemblés**.

**Minimiser les retours d'audit** : plus le **brief amont** est précis et orienté, moins l'audit
renvoie en correction. On investit dans la qualité du brief d'entrée.

---

## 6. RÈGLES QUALITÉ & LIGNES DIRECTRICES PAR PRODUIT

Chaque type de produit a une **ligne directrice** : *acceptable / inacceptable / indispensable*
(stockée dans `data/quality_rules.json`, vérifiée par le Juge Qualité). Exemple coloriage :
- **Indispensable** : traits **épais et bien délimités**, lignes fermées, cohérence stylistique
  de toute la série, couverture, format KDP exact.
- **Inacceptable** : incohérences de génération IA, **zones grises**, détails infimes
  inimprimables, texte/watermark parasite, pages qui ne se ressemblent pas entre elles.

Filtres transverses : **Censeur Copyright**, **Anti-Slop** (textuel + visuel), **Validateur Schéma**.

---

## 7. LES AGENTS (33 rôles → 13 agents consolidés)

| Agent | Fonction |
|---|---|
| **A1 Scout Marché** | top-ventes + reviews + analyse jeux ; détecte les « bestsellers mal notés » |
| **A2 Radar & Émergence** | trends, calendrier saisonnier, sources PD, **business émergents** |
| **A3 Affiliate Hunter** | intentions d'achat → leads + message + lien (Hugo envoie) |
| **B1 Stratège** | choix d'opportunité + Brief Produit + déclinaisons + dossier d'idées |
| **B2 Auditeur** | audit rentabilité **+** architecture (auto-amélioration du système) |
| **C1 Atelier Image** | coloriage, fusion PD, merch, restauration/upscale |
| **C2 Plume** | romans, scripts de jeux, fictions (fil conducteur, anti-répétition) |
| **C3 Card Designer** | decks POD |
| **C4 Vidéaste** | shorts faceless |
| **C5 Game Builder** | jeux (séquentiel, gate Hugo) |
| **D1 Scout Technique** | cherche **en continu** outils/repos gratuits pour **toute l'usine** |
| **E1 Juge Qualité** | audit point-par-point + routage réparation + critère d'arrêt |
| **F1 Ops & Interface** | Telegram, rapports, secrets, backup, **ordonnanceur de quotas** |

Détail des 33 sous-rôles : `MAP_BUSINESS_ET_AGENTS.md`.

---

## 8. RÉGIMES D'EXÉCUTION

- **Agents de fond** (détection, stratégie, qualité, ops) : **cron espacé**, tournent en continu léger.
- **Agents-projet** (Plume, Game Builder, etc.) : **déclenchés à la demande**, boucle bornée
  (minuterie `/loop` + seuil qualité), s'arrêtent une fois le produit livré.
- **Production parallèle** pour produits **légers** (plusieurs du même business en même temps).
- **Jeux = séquentiel** : un seul à la fois, poussé jusqu'au clé-en-main, **gate Hugo** dédié.

---

## 9. INFRASTRUCTURE & OUTILS

- **Exécution** : GitHub Actions (gratuit, repo public) ; Termux (téléphone) **optionnel**.
- **LLM gratuits** : Gemini (1500/j), Groq, Mistral, Cohere, HF (images) ; trials en réserve.
- **Images** : HF (SDXL/FLUX/ControlNet/IP-Adapter) + post-traitement **open-source sans clé**
  (opencv, rembg, Pillow, Real-ESRGAN). Référence de style via **image d'un produit exemple**
  de la trend (IP-Adapter / img2img).
- **Secrets** : GitHub Secrets chiffrés (`GEMINI_API_KEY`, `HF_API_KEY`, …) ; jamais en clair.
- **Recherche d'outils** : le **Scout Technique** cherche en permanence de nouveaux outils
  gratuits raccordables → plus on a d'outils, plus on peut **basculer** quand un quota tombe.
- **Diffusion** : kit de publication pré-rempli → **Hugo publie à la main** (anti-ban).
- **Validation** : Telegram (boutons), file de produits priorisée.

---

## 10. RÔLE DE L'HUMAIN (HUGO)

- **Valide / publie** le stock fini (oui → publie, non → retour boucle avec motif).
- **Injecte** ses propres idées quand il veut.
- **Fixe le quota hebdomadaire** (ex. « X coloriages + Y low-content + 3 romans + 1 jeu »).
- Tout le reste est automatisé. Objectif : Hugo peut s'absenter sans que le système s'arrête.

---

## 11. CAPACITÉ DE PRODUCTION ESTIMÉE (régime établi, gratuit)

| Produit | Machine / semaine |
|---|---|
| Merch / designs (× supports) | 30-80 designs |
| Low-content | 10-30 |
| Coloring books | 3-6 (goulot = quota images HF) |
| Romans / fiction | 2-5 |
| Decks de cartes | 1-3 |
| Jeu de script | ~1 toutes 1-2 semaines |

**Vrai goulot = Hugo** (validation + upload manuel) : ~**15-40 produits publiés/semaine** selon
le temps consacré et le mix. Démarrage volontairement bas (calibrage qualité), montée ensuite.

---

## 12. STATUT ACTUEL & PRÉREQUIS POUR DÉMARRER

**Fait** : architecture complète, schémas, 37 tests verts, brains de veille déjà actifs sur
`main`, téléchargeur de sources PD codé, outillage Claude Code installé.

**Prérequis pour passer au réel** :
1. **`HF_API_KEY`** + **`GEMINI_API_KEY`** dans les GitHub Secrets (HF = qualité image = bloquant).
2. **Réseau ouvert** (PC/Termux ou GitHub Actions) pour télécharger les sources PD (les API
   tierces sont bloquées dans l'environnement de dev actuel).
3. **URSSAF** avant la 1ère vente.

**Premier business à lancer** (meilleur ratio faisabilité × rentabilité) : **Coloriages / KDP**.
**Premier jeu** : **fiction interactive à choix** (game03), thème fantasy/dragon, simple.

---

## 13. CE QUI RESTE À CONSTRUIRE (backlog priorisé)

1. Brancher la **clé HF** → activer la génération d'images réelle.
2. Coder le **workflow « jusqu'à prêt-à-uploader »** (produit fini → `staging/` → notif).
3. Implémenter l'**Auditeur Produit (E1)** avec grilles par type + routage réparation.
4. Implémenter le **Stratège (B1)** : briefs + déclinaisons + dossier d'idées.
5. Étendre le **Scout Technique** (recherche continue d'outils gratuits).
6. Prototype **jeu de script** (moteur narratif + UI + visuels HF).
7. Pipeline **image+texte séparés** (Pillow) pour designs « visuel + écriture ».
8. (plus tard) Mécanisme pour **solliciter Claude ponctuellement** quand inutilisé (les tokens
   ne s'accumulent pas → autant les employer sur des sujets utiles).

---

---

## 14. AJUSTEMENTS SUITE À L'AUDIT EXTERNE (Gemini, 20/05)

Audit globalement positif. Décisions retenues :

- ✅ **Boucle de rétroaction ventes (data-driven)** — ADOPTÉ. Un `data/sales_feedback.csv`
  (déjà amorcé) + un futur `data/analytics.json` alimentent le **Stratège (B1)** : la production
  **dérive vers ce qui se vend réellement**, pas seulement vers les trends. C'est le signal aval
  qui manquait (les trends = signal amont).
- ✅ **Étalement SEO des publications** — ADOPTÉ. L'**ordonnanceur (F1)** prépare un **calendrier
  de publication étalé** (régularité quotidienne), pas un dump hebdomadaire. KDP/Redbubble
  récompensent la régularité ; bonus : ça lisse aussi la charge de validation de Hugo.
- 🟡 **Mémoire de style / signature** — ADOPTÉ AVEC GARDE-FOU. Une **bibliothèque de styles-
  signature** réutilisables (cohérence de marque) MAIS sans cloner : la variété du sujet/contenu
  reste imposée (cf. déclinaisons non-clones). Signature reconnaissable ≠ produits identiques.
- 🟡 **Robustesse des forks** — ADOPTÉ. On **vendorise/épingle** les repos forkés (version figée),
  pour qu'une mise à jour upstream ne casse pas une chaîne.
- 🟡 **Arrêt impitoyable des boucles** — RENFORCÉ. En plus de `loop_policy`, un **budget d'appels
  API par produit** (dépassé → stop + alerte Hugo).
- ❌ **Mode dégradé via modèle local sur Termux** — REJETÉ (irréaliste : un téléphone ne peut pas
  faire tourner un modèle d'image type SDXL/FLUX). On garde l'**objectif** (résilience) mais le
  **failsafe réaliste** = **Pollinations** en secours (gratuit, sans clé) + rotation multi-provider
  + **cache** des générations réussies.
- ✅ **Déployer 1 seul produit d'abord** — CONFIRMÉ : coloriages d'abord, chaîne bout-en-bout
  validée, puis scaling.

---

---

## 15. ÉVOLUTIONS & DIRECTIVES COMPLÉMENTAIRES (20/05, soir)

### 15.1 Production par ÉLÉMENTS / micro-blocs (compositing) ⭐
Quand générer un produit fini « d'un coup » est trop dur, on **génère des unités fiables** puis on
les **assemble** — même logique que « visuel sans texte + texte en overlay Pillow » :
- **Coloriage** : générer plein d'**éléments uniques** (créatures, objets, potions…) puis les
  **placer sur la page via des patrons d'emplacements** (comme on insère des sprites dans un jeu —
  en plus simple, car statique). Un élément raté = on regénère **juste l'élément**, pas la page.
- **Livres** : écrire par **micro-blocs (300-500 mots)** cohérents entre eux (mémoire de contexte),
  pas des chapitres entiers → concentration maximale, moins de répétition.
- Avantage : fiabilité, réparation locale, parallélisation.

### 15.2 Édition CIBLÉE plutôt que régénération totale
Sur un défaut **localisé**, ne pas tout refaire : modifier/supprimer **uniquement l'élément
problématique** via **inpainting** (`IOPaint`, Apache-2.0) ou retouche `opencv` — un « Photoshop
piloté par le code ». Combiné au compositing (15.1), on remplace juste l'unité fautive.

### 15.3 Génération multi-source (gratuit, illimité)
- **Pollinations** (sans clé, illimité) pour le **volume** / les éléments / les brouillons.
- **HF** (clé Hugo) pour la **qualité finale** + l'upscale.
- Post-traitement **local sans clé** (opencv, rembg, Pillow, Real-ESRGAN).
- *Skippés volontairement* (payants/crédit limité) : Together, Replicate, Perplexity.

### 15.4 Coloriages « intelligents » — 11 systèmes de valeur (catalogue)
Au lieu d'images aléatoires, structurer les coloring books par **logique de valeur** :
enquête à énigmes · pixel-art par numéro · architecture/plans · anatomie didactique · cartes de
mondes · typographie/calligraphie · illusions de perspective (Escher) · journaling visuel ·
mode/stylisme · blackout (réserve blanche) · tessellation/pavage. Règle d'or : **sobriété, clarté
des tracés, utilité réelle** (relaxation/apprentissage). → Se combine avec les produits mixtes (§3).

### 15.5 Livres « indétectables » (human-centric)
Doctrine intégrée dans `data/quality_rules.json > fiction_novel` : `style_guide` (blacklist de mots
IA, rythme de phrases alterné, ton émotionnel, imperfection contrôlée) + **3 passes d'audit**
(structure / rythme / humanisation) + **test de l'oreille** (TTS + LLM « critique sévère »). La force
n'est pas le modèle, c'est la **sévérité de la boucle d'audit**.

### 15.6 Nouvel agent #35 — Chasseur de Viral
Cherche **le hit** (potentiel viral/explosif) dans chaque domaine, en boucle (cf. MAP).

### 15.7 Trajectoire d'évolution (vision long terme)
| Étape | Mode | Rôle d'Hugo |
|---|---|---|
| **1. Artisanat automatisé** *(actuel)* | B2C : on produit & publie (KDP/Redbubble) | opérateur + validateur |
| **2. Agence de prestation** | B2B : vendre le **service** (assets sur mesure, ghostwriting…) | chef de projet / commercial |
| **3. Plateforme SaaS** | le client utilise notre interface, le système génère pour lui | gestionnaire produit |
| **4. Écosystème de marque** | univers propres → audience, pub, dérivés | directeur artistique |
| **5. Infrastructure de données** | revendre la **prédiction de tendances** / licences du moteur | stratège |

> **On reste focalisé sur l'Étape 1** (prouver la chaîne sur les coloriages). Les étapes 2-5 sont
> le cap, pas le présent.

### 15.8 Business B2B « services » (Étape 2, plus tard)
Quand un domaine atteint l'**excellence**, vendre la **production sur mesure** (ex. « je vous
produis 100 assets de jeu dans telle ambiance », ghostwriting, couvertures KDP pour autres auteurs,
restauration de photos…). Client décrit → la machine produit → Hugo traite le mail + livre le
dossier fini. **Clé** : on vend l'**output fini** (valeur livrée), pas une recette (≠ packs de
prompts, qui échouent car trop faciles à reproduire soi-même). À déclencher **après** la preuve
de qualité, pas avant.

---

### 15.9 Scaling spécifique sur un HIT (Hugo 21/05)
Deux niveaux de scaling :
- **Niveau domaine** (branches principales) : on scale globalement (plus de business, plus de volume).
- **Niveau produit, DANS un domaine** : dès qu'un produit **explose** (signal `sales_feedback`), on
  **ne stoppe pas** la production diverse normale (exploration), mais on lance **EN PLUS** une
  **vague de scaling ciblée** sur le gagnant (exploitation) :
  - **Tomes** : Vol. 2, 3, 4… de la collection ;
  - **Dérivés** : variations un peu différentes (sous-thèmes, cross avec d'autres trends/niches) ;
  - **Version améliorée** : corrige ses faiblesses (issues des reviews).
- Donc production = **base diverse** (on cherche le hit) **+ sur-pondération massive du hit** (on
  l'exploite). C'est l'allocation proportionnelle (§4) **déclenchée par le signal ventes** (§14),
  appliquée au niveau **collection**.

---

---

## 16. DÉCISIONS STRUCTURANTES — 27/05/2026

### 16.1 Fournisseur images : Runware remplace HuggingFace

HuggingFace ne sert plus FLUX/SDXL gratuitement depuis mi-2025 (CPU-only). Décision :

| Rôle | Fournisseur | Clé | Coût |
|------|------------|-----|------|
| Volume / brouillons | **Pollinations** | Aucune | Gratuit illimité |
| Qualité finale | **Runware** | `RUNWARE_API_KEY` | ~$0.002-0.006/image |
| Upscale 2× | **PIL LANCZOS** | Aucune | Gratuit local |

La section 15.3 est mise à jour en conséquence (HF → Runware).

**Résolution minimum pour coloriages KDP** : les images doivent sortir à ≥2550px (300 DPI pour 8.5×11"). Le pipeline `produce_coloring_book.py` inclut désormais un upscale 2× PIL automatique après téléchargement Pollinations.

### 16.2 Processus CdC obligatoire avant production

**Règle absolue** : aucun produit ne part en production sans CdC validé par Hugo.

Workflow :
1. Trigger → `agent_cdc_<type>.py` génère un CdC complet dans `products/<type>/<id>/`
2. `cdc.json` contient `gate_cdc: "pending"`
3. Hugo ouvre `CAHIER_DES_CHARGES.md` + `cdc.json` du produit, lit, valide ou rejette
4. Si validé : Hugo change `gate_cdc` → `"approved"` et push → production démarre automatiquement
5. Si rejeté : Hugo note les raisons → le CdC est régénéré avec de nouvelles contraintes

**Ce que contient un CdC ultra-complet** :
- Identité commerciale (nom de plume UNIQUE par livre, bio, style signature)
- Concept (titre, logline, genre, sous-genre, langue, longueur)
- Public cible (persona, tranche d'âge, douleur résolue)
- Analyse marché (5 concurrents avec ASIN, note, ce qui manque, notre angle)
- Description Amazon + mots-clés KDP (7 slots utilisés)
- Pour les romans : plan de 38 chapitres COMPLET + guide de style + tropes
- Pour les low-content : spec ReportLab page par page (layout précis au mm)
- Calendrier de production + critères de validation

### 16.3 Système d'audit v3 — par type de produit

L'auditeur (`scripts/agent_visual_audit.py`) évalue maintenant chaque type selon ce qui compte pour les consommateurs de la plateforme cible :

| Type | Critères principaux | Seuil REJECT |
|------|--------------------|----|
| Coloring KDP | Résolution ≥1400px, lignes pures, style cohérent, ≥30 pages | score < 45 |
| Low-content KDP | ≥100 pages, PDF valide, 7 keywords, format standard | score < 45 |
| STL Cults3D | Fichiers valides, dimensions ≤250mm, metadata listing | score < 45 |
| Card game | ≥50 cartes, fichier règles OBLIGATOIRE, résolution cartes | score < 45 |
| Roman | ≥50 000 mots, <30 phrases-tics IA, faible répétition | score < 45 |

**Règle** : s'il y a UN problème bloquant (`issues[]` non vide) → maximum REVIEW, jamais APPROVE.  
**APPROVE = prêt à uploader sans aucune réserve.**

### 16.4 Stack LLM multi-provider (brain_utils.py)

Tous les agents brain utilisent `scripts/lib/brain_utils.py` :

| Fonction | Détail |
|----------|--------|
| `llm_call(agent_type, system, user)` | Tente provider primaire, bascule sur fallbacks automatiquement |
| `get_angle(agent_type)` | Angle rotatif semaine par semaine (12 angles Prospecteur, 7 Architecte, 6 Stratège) |
| `get_previous_propositions(dir, type)` | Lit 4 derniers rapports, injecte "INTERDIT de répéter" |
| `get_temperature(agent_type)` | Température variable par semaine (stimulation créative) |
| `log_api_call(...)` | Log `data/logs/quota.jsonl` pour contrôle budget |
| `check_daily_budget(provider)` | Vérifie quota avant appel |

Routing par agent :

| Agent | Provider primaire | Fallback |
|-------|-----------------|---------|
| Prospecteur, Stratège, CdC | Gemini Flash | Groq → Mistral |
| Architecte Système | Mistral Small | Gemini → Groq |
| Roman Writer | Groq Llama 3.3 70B | Gemini → Mistral |

### 16.5 Cerveaux branchés (27/05/2026)

| Agent | Script | Workflow CI | Cron | Statut |
|-------|--------|------------|------|--------|
| B1 Stratège | `agent_b1_stratege.py` | `b1_stratege.yml` | Lundi 06h UTC | ✅ branché |
| Prospecteur d'Émergence | `agent_prospecteur_emergence.py` | `prospecteur_emergence.yml` | Jeudi 05h UTC | ✅ branché |
| Architecte Système | `agent_architecte_systeme.py` | `architecte_systeme.yml` | Dimanche 04h UTC | ✅ branché |
| CdC Roman | `agent_cdc_roman.py` | `cdc_roman.yml` | Sur trigger | ✅ branché |
| CdC Low-content | `agent_cdc_lowcontent.py` | `cdc_lowcontent.yml` | Sur trigger | ✅ branché |
| Rapporteur Hebdo | `agent_rapporteur_hebdo.py` | `rapporteur_hebdo.yml` | Dimanche 20h UTC | ✅ branché |
| Éclaireur Bestsellers | `agent_eclaireur_bestsellers.py` | `agent_eclaireur.yml` | Mardi 03h UTC | ✅ branché |
| Saisonnier | `agent_saisonnier.py` | `seasonal_planner.yml` | Lundi 06h UTC | ✅ branché |

Cerveaux du MAP non encore implémentés (backlog) :
- **#5 Archéologue PD** — scrape musées (Smithsonian, Met, Rijks) pour images domaine public
- **#6 Affiliate Hunter** — scanne Reddit/X pour intentions d'achat
- **#24 Rapporteur Hebdo** → implémenté (voir ci-dessus)
- **#35 Chasseur de Viral** — cherche le potentiel viral dans chaque domaine

### 16.6 Asset packs gamedev — nouveau domaine

Ajout au catalogue (section 3) : **vente de packs d'assets pour développeurs de jeux**.

- Plateformes : **itch.io**, **GameDevMarket**, Gumroad
- Contenu : sprite sheets, textures, UI kits, tilesets (pixel art, fantasy, sci-fi…)
- Production : Gemini génère les specs + descriptions, Pollinations/Runware génère les visuels
- Prix : $5-$25 par pack, revenus passifs (téléchargements illimités)
- Script existant : `produce_gamedev_asset_pack.py`
- Workflow existant : `produce_gamedev_asset_pack.yml`

### 16.7 Produits uploadables maintenant (27/05/2026)

| Produit | Type | Audit | Plateforme | Action Hugo |
|---------|------|-------|------------|-------------|
| 10 journaux low-content | Low-content KDP | APPROVE 92-100/100 | KDP | Upload manuel |
| 194 fichiers STL (4 types) | STL | APPROVE 100/100 | Cults3D | S'inscrire + upload |
| 5 jeux de cartes | Card game | REVIEW (pas de règles) | Etsy/TGC | Ajouter règles d'abord |
| Mystical Mushrooms | Coloring | REJECT 40/100 | — | Ne pas uploader, régénérer |
| Mystical Creatures | Coloring | REJECT 0/100 | — | Ne pas uploader, régénérer |

---

*Ce cahier des charges est vivant : il est mis à jour à chaque décision structurante.*
