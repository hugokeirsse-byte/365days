# Briefing 10 — agent_app_code_scout.py

## OBJECTIF
Créer `scripts/agent_app_code_scout.py` — recherche des projets open-source sur GitHub
pouvant servir de base technique pour une application mobile ou un jeu.
Strategie : assembler des briques existantes plutôt que coder de zéro.

## PHILOSOPHIE
Pour chaque app/jeu mobile, Gemini identifie :
1. Le moteur / framework le plus adapté parmi ceux disponibles open-source
2. Les repos GitHub existants utilisables comme point de départ (licence permissive)
3. Les assets libres de droits utilisables
4. Le minimum de code original à écrire pour assembler le tout

Gemini joue le rôle d'architecte : il assemble des briques pré-existantes.
Claude ne code rien de l'app directement.

## ENTRÉES
- `GEMINI_API_KEY` (env)
- `APP_CONCEPT` (env) : description libre de l'app/jeu (ex: "puzzle game with falling blocks, casual, monetized with ads")
- `APP_PLATEFORME` (env, optionnel) : `android`, `ios`, `both`, `web` (défaut: both)
- `APP_MONETISATION` (env, optionnel) : `ads`, `freemium`, `paid`, `iap` (défaut: ads)
- `GITHUB_TOKEN` (env, optionnel) : pour API GitHub (rate limit sans token: 60 req/h)

## PROCESSUS EN 3 ÉTAPES

### Étape 1 — Analyse du concept par Gemini
Prompt système :
```
Tu es un architecte technique expert en apps mobiles open-source.
Tu dois identifier les meilleures briques existantes pour construire cette app sans partir de zéro.
Tu connais les frameworks: Flutter, React Native, Godot, Unity (gratuit), Pygame, Phaser.js, LibGDX.
Tu connais les règles de licence: MIT, Apache 2.0 = utilisables commercialement. GPL = à éviter.
```
Prompt utilisateur :
```
Concept d'app: [APP_CONCEPT]
Plateforme: [APP_PLATEFORME]
Monétisation: [APP_MONETISATION]

Retourne un JSON avec:
- framework_recommande: (nom + raison en 1 phrase)
- github_queries: [liste de 5-10 requêtes de recherche GitHub]
- mots_cles_assets: [mots-clés pour chercher assets libres]
- architecture_proposee: (description en 3-5 points)
- mvp_features: [liste des features indispensables pour la v1]
- nice_to_have: [features pour v2]
Réponse en JSON pur entre ```json et ```.
```

### Étape 2 — Recherche GitHub automatique
Pour chaque query de la liste `github_queries` :
- Appeler l'API GitHub Search : `https://api.github.com/search/repositories?q=<query>&sort=stars&per_page=5`
- Filtrer: stars >= 100, licence MIT ou Apache-2.0, mis à jour depuis < 2 ans
- Garder les 3 meilleurs résultats par query
- Header: `User-Agent: 365days-AppScout/1.0 (hugo.keirsse@gmail.com)`

### Étape 3 — Synthèse Gemini
Passer à Gemini la liste des repos trouvés :
```
Voici les repos open-source trouvés pour l'app "[APP_CONCEPT]":
[liste des repos avec nom, stars, description, licence]

Sélectionne les 3-5 plus utiles et explique comment les combiner.
Propose un plan d'implémentation en 5 étapes maximum.
Identifie ce qu'il faudra coder de zéro (minimum possible).
Retourne un JSON de synthèse.
```

## SORTIES
Dossier : `products/apps/<APP_ID>/`

### `TECH_STACK.md` (lisible par Hugo)
```markdown
# STACK TECHNIQUE — [NOM APP]

## Framework retenu
...

## Repos à utiliser comme base
| Repo | Stars | Licence | Utilité | Lien |
|---|---|---|---|---|

## Plan d'implémentation
1. ...
2. ...

## Ce qu'on code de zéro (minimum)
- ...

## Assets libres identifiés
- ...

## Estimation effort
- MVP : X semaines CI
- V2 : Y semaines supplémentaires
```

### `tech_stack.json` (pour les étapes suivantes)

## WORKFLOW CI
Créer `.github/workflows/app_code_scout.yml` :
- Trigger: `.triggers/app_code_scout`
- Inputs: `app_concept`, `plateforme`, `monetisation`
- Commit dans `products/apps/<APP_ID>/`

## STDLIB ONLY + EXIT 0 TOUJOURS
Use `urllib.request` pour toutes les API (GitHub + Gemini).
Pas de `requests`, `httpx`, `aiohttp`.
