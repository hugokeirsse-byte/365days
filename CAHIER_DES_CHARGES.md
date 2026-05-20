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

*Ce cahier des charges est vivant : il est mis à jour à chaque décision structurante.*
