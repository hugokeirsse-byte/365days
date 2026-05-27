# Briefing 12 — agent_prospecteur_emergence.py

## IDENTITÉ
Agent **#34 Prospecteur d'Emergence** — cherche en permanence des
business/marchés en émergence QUE L'USINE N'EXPLOITE PAS ENCORE.
Il scan large (macro-tendances, nouveaux formats, plateformes naissantes)
et évalue l'applicabilité à notre système d'automatisation.

## PHILOSOPHIE
Le Scout Marché (A1) creuse les niches CONNUES.
Ce Prospecteur scanne ce qu'on n'a PAS encore vu.
Il cherche ce qui émerge, pas ce qui existe déjà.
Objectif : trouver le prochain marché AVANT les autres.

## ENTRÉES
- `GEMINI_API_KEY` (env)
- `data/reports/` : rapports Brain existants (pour savoir ce qu'on couvre déjà)
- `CAHIER_DES_CHARGES.md` (lu depuis la racine du repo) : business déjà prévus
- `MAP_BUSINESS_ET_AGENTS.md` : business déjà mappés
- `NOUVELLES_IDEES.md` : idées déjà explorées

## PROCESSUS

### Étape 1 : Construire le contexte « déjà couvert »
Lire les 3 fichiers stratégiques + rapports Brain.
Extraire la liste de tous les business/domaines déjà prévus ou en cours.

### Étape 2 : Premier appel Gemini — Scan d'émergence large
Système :
```
Tu es un analyste de marché spécialisé dans la détection précoce
d'opportunités digitales. Tu penses en dehors des sentiers battus.
Tu évalues chaque opportunité par sa compatibilité avec l'automatisation
par IA (python, LLM gratuits, GitHub Actions).

Critères d'évaluation pour notre usine :
- Automatisable à 90%+ par une IA ? (obligatoire)
- Coût de production proche de 0 ? (fortement préféré)
- Marché prouvé OU en émergence rapide ?
- Scalable sans intervention humaine constante ?
- Plateforme de distribution existante et accessible ?

Domai exclus (déjà couverts) :
[LISTE DES BUSINESS DEJA PREVUS]
```

Utilisateur :
```
Date : [DATE]
Signaux marché récents :
[RÉSUMÉ DES RAPPORTS BRAIN]

Explore ces axes de recherche :
1. Formats numériques émergents (nouveaux types de contenus qui émergent en 2025-2026)
2. Plateformes en croissance explosive non exploitées par la plupart
3. Croisements inattendus entre nos domaines existants et des niches vierges
4. Business digitaux que l'IA rend SOUDAINEMENT possibles (que des humains ne pouvaient pas faire avant)
5. Marchés de niche à forte intention d'achat pas encore saturés
6. Formats de vente inexploités sur des plateformes existantes
7. Services B2B automatisables (vendre à d'autres créateurs/entreprises)

Propose 10-15 idées de business INEXPLOITÉS par notre usine.
Pour chaque idée :
- nom : court et clair
- description : 2-3 phrases
- plateforme_cible : liste des plateformes de vente
- automatisable : oui/partiel/non
- cout_production : 0€|faible|moyen
- marche_taille : niche|moyen|large|massif
- urgence : prêt_maintenant|6_mois|1_an|speculative
- compatibilite_usine : /10
- exemple_concret : un produit concret qu'on pourrait produire demain
- signal_emergence : pourquoi MAINTENANT (trend, plateforme, tech, événement)

Réponds en JSON pur entre ```json et ```.
```

### Étape 3 : Deuxième appel Gemini — Deep dive sur le top 3
Pour les 3 idées avec le meilleur score `compatibilite_usine` :
```
Idée retenue : [NOM + DESCRIPTION]

Fais un deep dive complet :
1. Analyse du marché : taille, croissance, acteurs dominants, gaps
2. Comment notre usine (IA + GitHub Actions + Python) le produit concrètement
3. Stack technique proposée (outils gratuits existants)
4. Exemple de 3 produits concrets avec estimation de revenu
5. Risques et obstacles
6. Fenêtre d'opportunité : combien de temps avant saturation ?
7. Recommandation : LANCER_MAINTENANT | SURVEILLER_3MOIS | REPORTER

Réponds en Markdown structuré (pas JSON).
```

### Étape 4 : Rapport final
- `data/reports/emergence_YYYY-MM-DD.json` : toutes les idées (JSON)
- `data/reports/emergence_YYYY-MM-DD.md` : rapport lisible par Hugo
  - Résumé exécutif en 5 lignes
  - Top 3 deep dives complets
  - Tableau rapide des 10-15 idées avec scores
  - Section "Recommandations immédiates"

## WORKFLOW CI
Créer `.github/workflows/prospecteur_emergence.yml` :
- **Cron** : tous les jeudis 05h00 UTC (hebdomadaire)
- **Trigger manuel** : `.triggers/prospecteur_emergence` ou `workflow_dispatch`
- Installe aucune dépendance (stdlib only)
- Commit dans `data/reports/`
- Exit 0 toujours

## STDLIB ONLY
`urllib.request`, `json`, `pathlib`, `os`, `re`, `datetime`
