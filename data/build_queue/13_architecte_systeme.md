# Briefing 13 — agent_architecte_systeme.py

## IDENTITÉ
Agent **#30 Architecte Auto-Amélioration** — réfléchit en boucle
au système global de l'usine : failles, goulets, redondances, opportunités
d'amélioration durable. Va plus loin que la Méta-Critique (#11 qui évalue
la rentabilité) : lui audite l'ARCHITECTURE et propose des améliorations
structurelles concrètes, actionnables par le Builder.

## PHILOSOPHIE
Il lit l'état réel du système (pas ce qu'il devrait être).
Il compare au CAHIER_DES_CHARGES.md (vision cible).
Il identifie l'écart et propose les actions pour le combler.
Ses recommandations les plus implémentables génèrent automatiquement
des fichiers dans `data/build_queue/` pour que le Builder les exécute.

## ENTRÉES
- `GEMINI_API_KEY` (env)
- Fichiers stratégiques (lus depuis racine) :
  - `CAHIER_DES_CHARGES.md`
  - `MAP_BUSINESS_ET_AGENTS.md`
  - `NOUVELLES_IDEES.md`
- État réel du système (lu automatiquement) :
  - `.github/workflows/` : liste de tous les workflows existants
  - `scripts/` : liste de tous les scripts existants
  - `data/reports/` : derniers rapports produits
  - `data/build_queue/` : briefings en attente
  - `data/build_queue/done/` : briefings déjà traités (ce qui a été codé)
  - `products/` : structure des dossiers produits
- Optionnel : `data/system_state.json` (si existant) : métriques CI

## PROCESSUS

### Étape 1 : Inventaire de l'état réel
Scanner automatiquement :
```python
- workflows_existants = [f.name for f in Path(".github/workflows").glob("*.yml")]
- scripts_existants = [f.name for f in Path("scripts").glob("*.py")]
- briefings_en_queue = [f.name for f in Path("data/build_queue").glob("*.md")]
- briefings_traites = [f.name for f in Path("data/build_queue/done").glob("*.md")] si existant
- produits_existants = [d.name for d in Path("products").iterdir() if d.is_dir()]
- nb_rapports_brain = len(list(Path("data/reports").glob("*.json")))
```

### Étape 2 : Appel Gemini — Audit d'architecture
Système :
```
Tu es un architecte système expert en automatisation de production numérique.
Tu audites l'écart entre la vision (CAHIER DES CHARGES) et la réalité (ETAT ACTUEL).
Tu proposes des améliorations concrètes, priorisées, actionnables.

Critères d'évaluation :
- Impact sur la qualité des produits finaux
- Impact sur le niveau d'autonomie (moins Hugo intervient, mieux c'est)
- Impact sur la durabilité (pas de dépendances fragiles)
- Effort d'implémentation (faible = prioritaire)
- Risque d'effets de bord (impact sur ce qui fonctionne déjà)
```

Utilisateur :
```
=== VISION (CAHIER DES CHARGES) ===
[CONTENU CAHIER_DES_CHARGES.md - résumé des sections 5, 6, 7, 8, 13]

=== ETAT ACTUEL DU SYSTÈME ===
Workflows CI existants : [LISTE]
Scripts Python existants : [LISTE]
Produits produits : [LISTE]
Briefings en queue : [LISTE]
Briefings traités (déjà codés) : [LISTE]
Rapports Brain actifs : [NOMBRE]

=== ANALYSE DEMANDÉE ===

1. GAP ANALYSIS : qu'est-ce qui est prévu dans la vision mais absent de l'état réel ?
   Classe par impact et priorité.

2. FAILLES ARCHITECTURALES : quelles sont les vulnérabilités du système actuel ?
   (single points of failure, manque de résilience, dépendances fragiles, quotas,
   manque d'observabilité, risques de ban plateforme, etc.)

3. AMÉLIORATIONS DURABLES : les 5 changements qui auraient le plus d'impact
   sur la durabilité et la qualité du système à long terme.

4. AUTOMATIONS MANQUANTES : quelles actions Hugo fait encore manuellement
   qu'on pourrait automatiser sans risque ?

5. QUICK WINS : améliorations à effort FAIBLE et impact FORT, implémentables
   dans la semaine.

Pour chaque point :
- titre : court
- priorite : critique|haute|moyenne|faible
- impact : description en 2 phrases
- effort : faible|moyen|eleve
- implementation_concrete : ce qu'il faut exactement coder/configurer
- generer_briefing : true|false (doit-on créer un briefing Builder automatiquement ?)

Réponds en JSON pur entre ```json et ```.
```

### Étape 3 : Génération automatique de briefings
Pour chaque amélioration avec `generer_briefing: true` ET `priorite: critique|haute` :
- Générer un fichier `data/build_queue/AUTO_architecte_<slug>.md`
- Format standard de briefing (comme les briefings 01-13)
- Prefix `AUTO_` pour les distinguer des briefings manuels
- Le Builder les traitera au prochain cron

### Étape 4 : Rapport final
- `data/reports/architecture_YYYY-MM-DD.json` : analyse complète
- `data/reports/architecture_YYYY-MM-DD.md` : rapport lisible par Hugo

```markdown
# Rapport Architecte Système — [DATE]

## ℹ️ État du système
- Workflows actifs : N | Scripts : N | Produits : N
- Couverture vs CdC : XX%

## ⚠️ Points critiques à corriger
...

## 🚀 Quick wins (cette semaine)
...

## 📈 Améliorations durables (1-3 mois)
...

## 🤖 Briefings auto-générés dans build_queue/
[LISTE des briefings créés]

## 📊 Couverture des 13 agents du CdC
| Agent | Prévu | Implémenté |
|---|---|---|
| A1 Scout Marché | ✅ | 🟡 partiel |
...
```

## WORKFLOW CI
Créer `.github/workflows/architecte_systeme.yml` :
- **Cron** : tous les dimanches 04h00 UTC (audit hebdomadaire)
- **Trigger manuel** : `.triggers/architecte_systeme` ou `workflow_dispatch`
- Commit dans `data/reports/` ET `data/build_queue/` (pour les briefings auto)
- Exit 0 toujours

## STDLIB ONLY
`urllib.request`, `json`, `pathlib`, `os`, `re`, `datetime`
