# Mirabilia · The Strategy Collection · Vol. I

## 365 Days of Chess Puzzles to Become a Better Player

**Marque** : Mirabilia Éditions
**Série** : 365 Days of Wonder
**Collection** : The Strategy Collection
**Volume** : I
**Statut** : en démarrage (Phase 1 / 6)

## Concept

Un livre = un an d'apprentissage progressif des tactiques d'échecs. 1 puzzle par jour pendant 365 jours, du débutant au joueur intermédiaire.

**Progression sur 12 mois** :
| Mois | Thème | Difficulté |
|---|---|---|
| 1 | Fourchettes (knight forks) | 800-1000 ELO |
| 2 | Clouages (pins) | 1000-1100 |
| 3 | Échecs découverts (discovered attacks) | 1100-1200 |
| 4 | Doubles attaques | 1200-1300 |
| 5 | Mat en 1 | 1300-1400 |
| 6 | Mat en 2 | 1400-1500 |
| 7 | Sacrifices simples | 1500-1600 |
| 8 | Combinaisons tactiques | 1600-1700 |
| 9 | Finales basiques (roi+pion vs roi) | 1700-1800 |
| 10 | Finales tours et fous | 1800-1900 |
| 11 | Stratégie positionnelle | 1900-2000 |
| 12 | Combinaisons complexes | 2000+ |

## Pipeline de production

1. **Sélection des puzzles** : base Lichess (CC0, 3 millions de puzzles classés par ELO et thème tactique)
2. **Génération des diagrammes** : `python-chess` + `cairosvg` à partir des FEN
3. **Rédaction des explications tactiques** : Gemini ou Claude API (anglais)
4. **Mise en page** : générateur Pillow Mirabilia
5. **Couverture** : générateur Pillow avec charte Mirabilia + visuel central (5 diagrammes emblématiques)

## Cible commerciale

- **Format** : 8,5 × 8,5", hardcover, 365 pages double-sided
- **Prix de vente** : 28-32 €
- **Marge nette estimée** : 10-13 € par exemplaire
- **Public** : amateurs d'échecs niveau débutant à intermédiaire (1.5 milliard de joueurs mondialement, 180 M sur chess.com)

## Avancement

- [ ] Coder le générateur de diagrammes (python-chess + image)
- [ ] Sélectionner les 365 puzzles Lichess (script de filtrage)
- [ ] Générer les 365 explications tactiques
- [ ] Coder la mise en page Mirabilia (page droite = diagramme, page gauche = explication)
- [ ] Créer la couverture
- [ ] Assembler le PDF KDP final
- [ ] Proofreading anglais
- [ ] Upload KDP

## Notes éditoriales

- Style des explications : pédagogique mais pas scolaire, ton Mirabilia (érudit sans pédantisme)
- Chaque puzzle a un titre court évocateur (« The Knight's Whisper », « A Bishop's Trap »)
- Solution complète au verso ou en bas de page (à décider après tests de mise en page)
