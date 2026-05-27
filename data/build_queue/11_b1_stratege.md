# Briefing 11 — agent_b1_stratege.py

## IDENTITÉ
Agent **B1 Stratège** — le cerveau décisionnel de l'usine.
Il lit les données des agents Brain, évalue les opportunités, et produit
une liste priorisée de CdC à valider par Hugo. Rien ne part en production
sans qu'il ait d'abord décidé et que Hugo ait approuvé.

## ENTRÉES
- `GEMINI_API_KEY` (env)
- `data/reports/` : tous les fichiers JSON/MD des agents Brain
  - `trends_realtime_latest.json` (si existant)
  - `niches_explorer_latest.json` (si existant)
  - `money_maker_latest.json` (si existant)
  - `system_optimizer_latest.json` (si existant)
  - `tools_scout_latest.json` (si existant)
  - `trend_explosion_latest.json` (si existant)
  - `niche_gap_latest.json` (si existant)
- `data/sales_feedback.csv` (si existant) : ventes réelles
- `STRATEGE_MAX_PROPOSITIONS` (env, défaut: 5) : nb de CdC à proposer
- `STRATEGE_TYPES_ACTIFS` (env, défaut: `roman,lowcontent,stl,coloriage,assets_svg`)
  Types de produits que l'usine peut produire MAINTENANT

## PROCESSUS

### Étape 1 : Collecte des signaux
Lire tous les fichiers de `data/reports/` et en extraire :
- Top 10 des trends du moment
- Top 10 des niches sous-exploitées
- Signaux de ventes réelles si disponibles
- Outils/repos nouveaux disponibles

### Étape 2 : Appel Gemini — Décision stratégique
Système :
```
Tu es le Stratège d'une usine de production numérique automatique.
Ton seul but : choisir LES MEILLEURES opportunités de production
pour maximiser le revenu potentiel, en fonction des types de produits
disponibles et des signaux marché du moment.

Critères de scoring (total /100) :
- Potentiel revenu (BSR, demande, prix moyen) : 35 pts
- Frêléchéur (trend montante vs stable vs descendante) : 25 pts
- Faisabilité sans clé image (si applicable) : 20 pts
- Décalé des concurrents (pas juste copier) : 20 pts

Types de stratégie disponibles :
1. MONO-TREND : exploiter une seule trend forte telle quelle
2. CROSS-TREND : croiser 2+ trends (ex: dark academia × mushrooms)
3. ORIGINAL : idée innovante propre (créer la trend)
4. REFONTE : reprendre un bestseller mal noté et corriger ses défauts

Non-clones obligatoire : chaque proposition doit être distincte.
Pense en collections (Vol.1 ouvre une série scalable).
```

Utilisateur :
```
Signaux marché du [DATE] :
[CONTENU DES RAPPORTS BRAIN]

Types de produits disponibles maintenant : [STRATEGE_TYPES_ACTIFS]

Génère [STRATEGE_MAX_PROPOSITIONS] propositions de production priorisées.
Pour chaque proposition :
- type : roman|lowcontent|stl|coloriage|assets_svg|autre
- strategie : MONO-TREND|CROSS-TREND|ORIGINAL|REFONTE
- titre_propose : titre complet et accrocheur
- logline : 1 phrase
- score : /100
- pourquoi_maintenant : 2-3 phrases (urgence, timing)
- angle_differenciateur : ce qui le distingue des concurrents
- potentiel_collection : oui/non + description si oui
- estimation_revenu_mensuel : fourchette en $ après 3 mois
- effort_production : faible|moyen|eleve
- prochaine_action : "lancer_cdc"|"besoin_image_api"|"besoin_validation_concept"

Réponds en JSON pur entre ```json et ```.
```

### Étape 3 : Génération des mini-CdC
Pour chaque proposition avec `prochaine_action == "lancer_cdc"` :
- Générer un second appel Gemini pour produire un mini-CdC (500-800 mots)
- Structure : positionnement, audience, 5 concurrents, mots-clés KDP, description Amazon draft, nom de plume/auteur
- Sauvegarder dans `data/strategie/propositions/<type>_<slug>_miniCdC.md`

### Étape 4 : Rapport Hugo
Créer `data/strategie/rapport_stratege_YYYY-MM-DD.md` :
```markdown
# Rapport Stratège — [DATE]
**Signaux lus :** [liste des fichiers Brain lus]
**Propositions :** [N]

## 1. [TITRE] — Score : XX/100
**Type :** ... | **Stratégie :** ...
**Logline :** ...
**Pourquoi maintenant :** ...
**Revenu estimé :** ... | **Effort :** ...
✅ Mini-CdC disponible : `data/strategie/propositions/...`

---
## [SUITE]

## ✔️ VALIDATION
Édite `rapport_stratege_YYYY-MM-DD.json` et ajoute `"approved": true`
sur la proposition que tu veux lancer. Le CI déclenchera automatiquement
le générateur de CdC correspondant.
```

## WORKFLOW CI
Créer `.github/workflows/b1_stratege.yml` :
- **Cron** : tous les lundis 06h00 UTC (début de semaine)
- **Trigger manuel** : `.triggers/b1_stratege` ou `workflow_dispatch`
- Commit dans `data/strategie/`
- Pas de `sys.exit(1)` — exit 0 toujours

## LOGIQUE DE CONTINUATION
Si un rapport de la semaine précédente contient des propositions non-approuvées,
les inclure en tête du nouveau rapport avec mention "[REPORTÉ - non validé]".

## STDLIB ONLY
`urllib.request`, `json`, `pathlib`, `os`, `re`, `datetime`, `csv`
