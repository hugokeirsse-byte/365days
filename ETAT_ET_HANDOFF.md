# ÉTAT DU PROJET & PASSATION (lis-moi en premier)

> **But de ce fichier :** permettre à une NOUVELLE conversation Claude de reprendre le projet
> avec autant de contexte que la précédente, sans relire un historique géant.
> **Méthode :** lis ce fichier + les fichiers cités. Le **repo est la mémoire**, pas le chat.
> Auteur du projet : Hugo Keirsse. Rôles : **Hugo = chef**, **Claude = sous-chef/orchestrateur**,
> **Gemini + outils = employés**. On délègue un max, Claude code le moins possible.

---

## 1. VISION (recentrée)
Empire de produits numériques. **On se concentre 100 % sur les LIVRES** pour l'instant
(jeux vidéo/assets/merch = en pause, regroupés mais pas prioritaires).
Catégories de livres à décliner : **coloriages** (en cours), livres enfants, mangas, BD, romans, low-content.
Pour chaque genre = un **STUDIO séparé** (équipe d'IA = chef de projet, dessinateur, scénariste, designer, auditeur),
on **ne mélange pas** les studios. On reproduit une vraie maison de création, mais en IA.

**3 sources de création** (par studio) : (1) 100 % original IA, (2) idée de Hugo exécutée en auto,
(3) réutilisation de libre-de-droits commercial réadapté.

**2 GATES humains (Hugo intervient UNIQUEMENT au début et à la fin) :**
- **GATE 1** : l'IA propose un **cahier des charges complet** (concept, style, image(s) de réf candidate(s)
  à choisir, model sheets si persos, **nom d'auteur**, titre, format). Hugo lit → approuve / choisit la réf / corrige.
- **(milieu = 100 % autonome)** : production → audit → produit fini clé-en-main.
- **GATE 2** : produit fini présenté → Hugo décide la **publication**.

---

## 2. LA BOUCLE AUTONOME (4 briques — TOUTES câblées et testées à blanc)
```
Stratège → [GATE 1: Hugo] → Producteur → (génération CI) → Auditeur ⟲(boucle bornée) → [GATE 2: Hugo] → publication
```
| Brique | Fichier | Rôle | Statut |
|---|---|---|---|
| 1. Stratège | `scripts/agent_strategist.py` | lit trends → écrit le cahier des charges (file 10 max) | ✅ **prouvé avec Gemini en CI** |
| 2. Producteur | `scripts/produce_from_brief.py` | écrit 30 prompts distincts/cohérents, borné budget, **0 image** | ✅ testé |
| 3. Auditeur + boucle | `scripts/agent_brief_auditor.py` | audit point par point vs cahier ; corrige/contourne/**escalade Hugo** | ✅ testé (`--demo-loop`) |
| 4. GATE 2 | `scripts/agent_gate2.py` | présente si **abouti** ; enregistre décision publication | ✅ testé |
| Builder | `scripts/agent_builder.py` | **briefing.md → code via Gemini** (la machine qui construit l'usine) | ⚠️ écrit, **pas encore branché en CI** |

Workflows CI : `.github/workflows/strategist.yml`, `production_loop.yml`, `reference_candidates.yml`.
Déclenchés par push d'un fichier `.triggers/<nom>` (mécanisme existant) ou workflow_dispatch.

---

## 3. CAHIER DES CHARGES (le contrat = le gros du travail)
- **Schéma** : `data/schemas/product_brief.schema.json` (étendu : `image_budget`, `reference_selection`,
  `cover` avant/arrière, `collection.author` + unicité, `human_gates`, `book_structure`).
- **Briefs** : `data/briefs/brief_*.json`. Politique de file : `data/briefs/_queue_policy.json` (**max 10** AI-original en attente).
- **Brief lisible (humain)** : `products/coloring_books/_gate1/<id>/CAHIER_DES_CHARGES.md` + `ref_candidates/` + `production_plan.json` + `audit_vs_brief.json`.
- **En file actuellement :**
  - `brief_2026-05-22_coloring_kawaii_mushroom_hollow` — **GATE 1 approuvé**, réf **cand_4** verrouillée (fait à la main par Claude au départ).
  - `brief_2026-05-22_coloring_kawaii-cottagecore-dad` — **écrit par l'IA (Gemini)**, GATE 1 en attente (preuve que le Stratège marche).

---

## 4. STRATÉGIE IMAGES (important, nouvelle direction)
- **FLUX.1 schnell** = seul modèle à **licence commerciale** (Apache-2.0) → obligatoire pour vendre les images.
- **Runware** = fournisseur payant pour FLUX schnell (~0,0006 $/image), **vérifié compatible**, déjà intégré dans `scripts/lib/image_router.py` (provider en tête, dormant tant que `RUNWARE_API_KEY` absent). Filet **gratuit = Pollinations**.
- **PROBLÈME constaté par Hugo** : FLUX schnell fait de belles images mais de **mauvais coloriages**.
- **DÉCISION** : ne plus générer les coloriages directement. **Générer des images normales (ou réutiliser du libre-de-droits commercial) puis les CONVERTIR en line-art** par un code déterministe (contours, **épaisseur de trait réglable depuis le cahier des charges**). Double usage : l'image sert au **merch** ET, convertie, au **coloriage**.
- **À FAIRE (prochaine tâche déléguée)** : `scripts/lib/image_to_coloring.py` (Pillow/numpy, paramètres : épaisseur, seuil noir/blanc, format). → à faire écrire par **Gemini via le Builder** (briefing.md).

---

## 5. MODÈLE DE DÉLÉGATION (pour économiser Claude)
**Protocole d'orchestration :** Claude **ne code jamais sans avoir cherché un agent/outil capable de le faire**.
Pour toute tâche : Claude écrit un petit **`data/build_queue/<tâche>.md`** (ligne `TARGET: chemin`, + description/entrées/sorties/contraintes),
→ le **Builder** (`agent_builder.py`) le donne à **Gemini** qui écrit le code → Claude **relit/valide**, Hugo approuve.
Idem pour le contenu créatif (Stratège, prompts) : c'est **Gemini** qui rédige, pas Claude.

---

## 6. CONTRAINTES & PIÈGES (à savoir absolument)
- **Sandbox local de Claude = réseau bloqué (allowlist)** : pas d'accès à Gemini, Runware, Pollinations en local
  (`Host not in allowlist`, HTTP 403). → **TOUTE génération (images) et tout appel Gemini se font en CI (GitHub Actions)**, pas en local.
  En local, les agents tombent en mode déterministe/fallback (utile pour tester le câblage, PAS pour du vrai contenu).
- **Ne PAS faire la « danse git main-sync » en local** (checkout origin/main matérialise 1,6 Go → se fait tuer, laisse des locks).
  Pour porter sur **main**, utiliser **l'API GitHub** (`mcp__github__push_files` / `create_or_update_file`), pas le working tree.
- **Secrets GitHub** : `GEMINI_API_KEY` ✅ (présent, gratuit). `RUNWARE_API_KEY` = à ajouter quand on veut la qualité payante. `HF_API_KEY` optionnel.
- **products/** a été nettoyé/regroupé par business **sur la branche** (8 dossiers) ; **main a encore l'ancienne structure** (le gros push échouait — à refaire via API plus tard, non urgent).
- Branche de dev : `claude/review-project-briefing-galq7`. Modèle Gemini stable : `gemini-2.5-flash` (+ fallbacks `gemini-2.0-flash`, `gemini-flash-latest`). Anciens scripts qui utilisaient `gemini-2.0-flash-exp` (déprécié) ont été corrigés.

---

## 7. POURQUOI CLAUDE ATTEINT VITE SES LIMITES + COMMENT ÉCONOMISER
**Pourquoi :** une conversation très longue est **re-traitée en entier à chaque tour** (chaque message, chaque sortie d'outil
volumineuse — gros `ls`, `ps`, lectures d'images, dumps git — reste dans le contexte et coûte des tokens à répétition).
**Solutions (par ordre d'impact) :**
1. **Ouvrir une NOUVELLE conversation par phase/module.** Repartir propre, ce fichier = mémoire. ← le plus gros gain.
2. **Déléguer le code à Gemini** (Builder + briefing.md). Claude n'écrit que de petits briefings + valide.
3. **Éviter les grosses sorties** dans le chat (commandes ciblées, pas de dumps massifs ; ne pas relire des fichiers déjà connus).
4. **Décider par lots** (moins d'allers-retours). Utiliser **Haiku** pour le mécanique, **Opus** pour la conception.
5. Garder Claude en **orchestrateur** : il déclenche des workflows CI et rapporte, il ne fait pas le travail manuel constamment.

---

## 8. PROCHAINES ÉTAPES (priorité : construire l'usine, puis la faire tourner)
1. **Brancher le Builder en CI** (`builder.yml` + `.triggers/builder`) et lui faire écrire `image_to_coloring.py` (briefing à créer dans `data/build_queue/`).
2. Tester le convertisseur sur une image FLUX schnell réelle (en CI) → coloriage propre.
3. Brancher Producteur+Auditeur en CI = `production_loop.yml` (déjà créé) ; ajouter l'étape génération (gated) quand Hugo dit go + `RUNWARE_API_KEY`.
4. S'assurer que **les 5 cerveaux** (`agent_brain_meta.py`) tournent en CI (Gemini OK) ; éventuellement ajouter un cerveau « Architecte » qui rédige des briefings pour le Builder.
5. GATE 1 en attente : faire générer les **réfs candidates** du brief « Dads » (workflow `reference_candidates.yml`) pour que Hugo choisisse.

---

## 9. TON & RÈGLES DE TRAVAIL AVEC HUGO
- Répondre en **français**, points **courts et fréquents** (ne pas rester silencieux longtemps : il croit que ça bugge).
- **Zéro génération d'images sans le feu vert explicite de Hugo.** Simuler d'abord en gratuit, basculer payant après validation.
- Être **honnête** sur ce qui est réel vs simulé (ex. ne pas présenter un fallback déterministe comme « écrit par l'IA »).
- Actions risquées/irréversibles (suppressions, push main, force) : confirmer avant.
