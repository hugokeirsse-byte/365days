# Briefing 09 — agent_cdc_lowcontent.py

## OBJECTIF
Créer `scripts/agent_cdc_lowcontent.py` — génère un Cahier des Charges ultra-complet pour un livre low-content KDP (journal, planner, notebook, tracker, logbook, puzzle book, activity book).

## PHILOSOPHIE
Le low-content est le produit KDP le plus rapide à produire et le plus récurrent.
Un bon CdC = un layout unique qui se démarque des 50 000 notebooks génériques.

## ENTRÉES
- `GEMINI_API_KEY` (env)
- `LC_ID` (env) : ex: `lowcontent_2026-05-27_witchy_moon_journal`
- `LC_TYPE` (env, optionnel) : `journal`, `planner`, `tracker`, `logbook`, `puzzle`, `activity` (défaut: auto)
- `LC_THEME` (env, optionnel) : ex: `witchy`, `mindfulness`, `fitness`, `travel`, `gratitude`
- `LC_AUDIENCE` (env, optionnel) : ex: `women`, `men`, `teens`, `seniors`, `professionals`

## SORTIES
Dossier : `products/lowcontent_kdp/<LC_ID>/`

### 1. `CAHIER_DES_CHARGES.md`
```markdown
# CAHIER DES CHARGES — [TITRE]
**Statut : EN ATTENTE DE VALIDATION**

## 1. IDENTITÉ COMMERCIALE
- **Titre** : ...
- **Sous-titre** : ...
- **Auteur/Marque** : [nom unique]
- **Type** : Journal / Planner / Tracker / ...
- **Thème** : ...
- **Audience** : ...
- **Nb de pages** : 120 (standard low-content)
- **Format** : 6x9in
- **Prix paperback** : $X.XX

## 2. CONCEPT ET ANGLE DIFFÉRENCIATEUR
- **Promesse** : ...
- **Ce qui le distingue** : [pas juste un autre journal "gratitude"]
- **Élément signature** : [...ce qu'il a d'unique: prompts, structure, illustrations, rubrique spéciale]

## 3. ANALYSE MARCHÉ (5 CONCURRENTS)
...

## 4. STRUCTURE ET LAYOUT DES PAGES
Décrire CHAQUE type de page avec son contenu exact :

### Pages préliminaires (pages 1-X)
- Page de titre
- "How to use this journal"
- [autres]

### Bloc principal (pages X-Y) — répété Z fois
- **Layout A** : [description précise: zones de texte, lignes, cases, icones]
- **Layout B** : ...
- **Frquence** : alternance A/B, ou A x5 puis B x1, etc.

### Pages bonus (si applicable)
- Section notes libres
- Tracker mensuel
- [autres]

## 5. ÉLÉMENTS GRAPHIQUES
- **Style** : minimaliste / illustré / typographique
- **Police** : ...
- **Icônes** : ...
- **En-têtes de section** : ...
- **Couverture** : [description précise pour génération image]

## 6. PROMPTS DE GÉNÉRATION (si images)
- Couverture : ...
- Séparateurs de section (si applicable) : ...

## 7. DESCRIPTION AMAZON + MOTS-CLÉS
...

## 8. COÛT ET CALENDRIER
- Outil de layout : ReportLab (Python, déjà installé)
- Durée CI : ~5 min
- Coût impression KDP (120p, 6x9) : ~$2.80
- Prix vente : $8.99-$12.99
- Revenu net : ~$3-5 par vente

## 9. CRITÈRES VALIDATION
- [ ] PDF généré et lisible
- [ ] Layout correct sur toutes les pages
- [ ] Couverture attrayante
- [ ] Hugo a vérifié visuellement

---
**✅ VALIDATION** : éditer `cdc.json` → `gate_cdc: "approved"`
```

### 2. `cdc.json` avec tous les champs

## PROMPT GEMINI
### Système
```
Tu es expert en livres low-content KDP (journals, planners, trackers).
Tu connaîs les layouts qui se vendent (pages lignées, cases, prompts journaliers, habit trackers, mood trackers).
Tu crées des produits originaux qui se démarquent des milliers de notebooks génériques.
```

### Utilisateur
```
Crée un Cahier des Charges complet pour un livre low-content KDP.
Type: [LC_TYPE]
Thème: [LC_THEME]
Audience: [LC_AUDIENCE]

Contraintes:
1. Layout unique avec au moins UNE fonctionnalité originale (pas juste des lignes)
2. Structure de page détaillée au millimètre (zones, tailles, proportions)
3. Analyse concurrentielle réelle
4. Description Amazon qui met en avant la valeur unique
5. Mots-clés longue traîne
Réponds en JSON pur entre ```json et ```.
```

## WORKFLOW CI
Créer `.github/workflows/cdc_lowcontent.yml`
Trigger: `.triggers/cdc_lowcontent`

## STDLIB ONLY + EXIT 0 TOUJOURS
