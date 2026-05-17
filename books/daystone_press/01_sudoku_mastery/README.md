# Daystone Press · The Puzzle Mastery Collection · Vol. I

## Sudoku Mastery — Become an Expert in 200 Puzzles

**Marque** : Daystone Press
**Collection** : The Puzzle Mastery Collection
**Volume** : I
**Statut** : en démarrage (Phase 1 / 5)

## Concept

Pas un énième livre de sudoku avec 200 grilles aléatoires.
**Une progression pédagogique structurée** : 200 puzzles répartis en 20 modules de 10 grilles chacun. Chaque module introduit **une nouvelle technique de résolution** clairement expliquée, puis 10 puzzles pour la pratiquer en conditions réelles.

À la fin du livre, le lecteur maîtrise **les 20 techniques essentielles** du sudoku, du niveau débutant au quasi-expert.

## Programme des 20 techniques (en anglais — marché US/UK)

| # | Module | Technique enseignée | Niveau |
|---|---|---|---|
| 1 | Single Candidate / Naked Single | Une seule possibilité dans une case | Débutant |
| 2 | Hidden Single | Un seul endroit possible pour un chiffre | Débutant |
| 3 | Pointing Pairs | Élimination par paire pointante | Débutant+ |
| 4 | Box/Line Reduction | Réduction case/ligne | Débutant+ |
| 5 | Naked Pairs | Paire nue | Intermédiaire |
| 6 | Hidden Pairs | Paire cachée | Intermédiaire |
| 7 | Naked Triples | Triplet nu | Intermédiaire |
| 8 | Hidden Triples | Triplet caché | Intermédiaire |
| 9 | Naked Quads | Quadruplet nu | Intermédiaire+ |
| 10 | X-Wing | Aile en X (parité de lignes/colonnes) | Avancé |
| 11 | Swordfish | Trident (extension X-Wing) | Avancé |
| 12 | Jellyfish | Méduse (extension Swordfish) | Avancé |
| 13 | Y-Wing | Aile en Y (chaîne de 3 cellules) | Avancé |
| 14 | XYZ-Wing | Variante XYZ | Avancé |
| 15 | Coloring | Coloration de cellules | Expert |
| 16 | Forcing Chain | Chaîne forçante | Expert |
| 17 | Skyscraper | Gratte-ciel | Expert |
| 18 | Empty Rectangle | Rectangle vide | Expert |
| 19 | Almost Locked Sets | Ensembles presque verrouillés | Expert+ |
| 20 | Nishio | Méthode Nishio (test/contradiction) | Expert+ |

## Structure de chaque module (10 pages)

- **Page 1** : Explication de la technique (diagramme + texte clair)
- **Page 2** : Exemple résolu pas-à-pas
- **Pages 3-7** : 5 puzzles "Easy" où la technique est nécessaire
- **Pages 8-9** : 3 puzzles "Medium"
- **Page 10** : 2 puzzles "Hard"

Total : 200 puzzles + 20 modules d'explication + intro + solutions = **~250 pages**.

## Pipeline de production

1. **Génération des 200 grilles** via lib Python `sudoku-generator` ou algorithme custom
   - Contrainte : chaque grille DOIT nécessiter la technique du module pour être résolue
   - Vérification automatique : on génère 100 candidats par module, on filtre ceux qui demandent vraiment la technique
2. **Rédaction des 20 explications de techniques** : Gemini ou Claude API (style pédagogique, anglais)
3. **Mise en page** : générateur Pillow Daystone (grille + texte + ornements discrets)
4. **Solutions** : section finale auto-générée
5. **Couverture** : générateur Pillow avec charte Daystone Press

## Cible commerciale

- **Format** : 8,5 × 8,5", softcover, ~250 pages
- **Prix de vente** : 9-13 €
- **Marge nette estimée** : 4-6 € par exemplaire
- **Public** : adultes 25-65 ans, amateurs sudoku, public cadeau "intelligent"
- **Différenciation** : marché sudoku saturé MAIS aucune offre pédagogique sérieuse. On est seul sur "progression structurée + techniques expliquées".

## Avancement

- [ ] Choisir la lib Sudoku (py-sudoku, sudoku-py, ou custom Python)
- [ ] Coder le générateur de grilles par technique imposée
- [ ] Générer les 200 grilles + solutions
- [ ] Rédiger les 20 explications de techniques (Gemini)
- [ ] Coder la mise en page Daystone Press
- [ ] Créer la couverture
- [ ] Assembler le PDF KDP final
- [ ] Proofreading anglais (Fiverr ~50 €)
- [ ] Upload KDP

## Tagline (à finaliser)

- *« Sudoku Mastery : Become an Expert in 200 Puzzles »* — clair, vendeur
- *« 200 Sudoku Puzzles to Train Your Brain, Step by Step »* — alternative
- *« The Sudoku Solver's Codex »* — premium, sobre
