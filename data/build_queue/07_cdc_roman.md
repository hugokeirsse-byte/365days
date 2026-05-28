# Briefing 07 — agent_cdc_roman.py

## OBJECTIF
Créer `scripts/agent_cdc_roman.py` — génère un Cahier des Charges ultra-complet pour un roman KDP.
Le CdC est la base de toute la production : rien ne part en production sans validation humaine de ce document.

## PHILOSOPHIE
Chaque roman est un produit commercial unique :
- Nom de plume EXCLUSIF au roman (jamais réutilisé pour un autre livre d'un genre différent)
- Positionnement décalé par rapport aux bestsellers (niche precis, pas copier-coller)
- CdC = contrat entre le système et le producteur humain

## ENTRÉES
- `GEMINI_API_KEY` (env)
- `ROMAN_ID` (env) : identifiant unique ex: `roman_2026-05-27_smalltown_romance`
- `ROMAN_GENRE` (env, optionnel) : ex: `romance`, `thriller`, `fantasy`, `mystery` (défaut: auto-select depuis trends)
- `ROMAN_SOUS_GENRE` (env, optionnel) : ex: `small-town`, `second-chance`, `grumpy-sunshine`
- `ROMAN_LANGUE` (env, optionnel) : `fr` ou `en` (défaut: `en`)
- `TRENDS_FILE` (env, optionnel) : chemin vers `data/reports/trends_realtime_latest.json` si disponible

## ENTRÉES OPTIONNELLES DEPUIS FICHIER TRIGGER
Le workflow lira `.triggers/cdc_roman` pour extraire :
```
roman_id=roman_2026-05-27_smalltown_romance
genre=romance
sous_genre=small-town second-chance
langue=en
```

## SORTIES
Dossier : `products/novels/<ROMAN_ID>/`

### 1. `CAHIER_DES_CHARGES.md` (document lisible par Hugo)
Document Markdown ultra-complet avec les sections suivantes (en français) :

```markdown
# CAHIER DES CHARGES — [TITRE ROMAN]
**Statut : EN ATTENTE DE VALIDATION**
**Date de génération :** ...
**Roman ID :** ...

---

## 1. IDENTITÉ COMMERCIALE
- **Titre** : ...
- **Sous-titre** : ...
- **Nom de plume** : [Prénom Nom — sonne authentique au genre]
- **Bio auteur** (150 mots) : [...paragraphe en troisième personne, crédible, humain]
- **Genre KDP** : ...
- **Sous-genre** : ...
- **Langue** : ...
- **Longueur cible** : XX 000 mots (env. XX chapitres)
- **Prix ebook** : $X.XX
- **Prix paperback** : $XX.XX
- **Copyright** : © [année] [Nom de plume]

## 2. CONCEPT ET POSITIONNEMENT
- **Logline** (1 phrase impactante) : ...
- **Pitch** (3-5 phrases) : ...
- **Accroche** (premières 50 mots du roman, in medias res) : ...
- **Angle différenciateur** (en quoi ce roman n'est PAS comme les autres) : ...

## 3. PUBLIC CIBLE
- **Profil principal** : ...
- **Âge** : ...
- **Centres d'intérêt** : ...
- **Occasion d'achat** : ...
- **Plateformes de découverte** : ...

## 4. ANALYSE MARCHÉ (5 CONCURRENTS KDP)
| Titre | Auteur | BSR | Note | Prix | Mots-clés | Points forts | Points faibles |
|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... | ... |

**Opportunité identifiée** : [...ce que les concurrents ne font pas bien]

## 5. DESCRIPTION AMAZON
(~500 mots, tone: engaging, commence par l'accroche, inclut CTA)

...

## 6. MOTS-CLÉS KDP (7 maximum)
1. ...
2. ...
...

## 7. CATÉGORIES KDP
- Catégorie 1 : ...
- Catégorie 2 : ...

## 8. PERSONNAGES PRINCIPAUX
### [Nom Héro/Héroïne]
- **Âge** :
- **Occupation** :
- **Apparence** :
- **Personnalité** :
- **Backstory** (secret, blessure intérieure) :
- **Arc narratif** (où il/elle commence, où il/elle finit) :
- **Voix / façon de parler** :

### [Nom Love Interest / Antagoniste / Second]
(même structure)

## 9. STRUCTURE EN 3 ACTES
### Acte 1 — Mise en place (chapitres 1-X)
...
### Acte 2 — Confrontation (chapitres X-Y)
...
### Acte 3 — Résolution (chapitres Y-fin)
...

## 10. PLAN DES CHAPITRES
| Ch. | Titre provisoire | Résumé (2-3 phrases) | POV | Tension |
|---|---|---|---|---|
| 1 | ... | ... | ... | ... |
...

## 11. GUIDE DE STYLE
- **Ton** : ...
- **POV** : 3ème personne limité (ou 1ère si justifié)
- **Longueur phrases** : variée, courtes en tension, longues en description
- **Registre** : ...
- **Phrases À BANNIR** : [liste des clichés IA]
- **Règle Show Don't Tell** : ...
- **Dialogue** : naturel, pas de dit-il/dit-elle systématique

## 12. EXIGENCES TECHNIQUES KDP
- Format : 5x8in ou 6x9in
- Police intérieur : Times New Roman 12pt ou Garamond 11pt
- Marges : top 0.75in, bottom 0.75in, ext 0.5in, int 0.75in
- Couverture : 2560x1600px (ebook) + 5.5x8.5in + bleed 0.125in (paperback)
- Numérotation : débute chapitre 1 (pages préliminaires non numérotées)

## 13. COÛT ET CALENDRIER ESTIMÉS
- Nb d'appels Gemini : ~40 (1 par chapitre + plan)
- Durée CI estimée : ~2h pour les 38 chapitres en batches de 10
- Coût API Gemini : gratuit (flash-2.0 dans la limite du quota)
- Coût impression KDP paperback : ~$3.50
- Revenu net estimé par vente (ebook $2.99) : ~$2.00
- Revenu net estimé par vente (PB $11.99) : ~$4.00

## 14. CRITÈRES DE VALIDATION FINALE
- [ ] 100% des chapitres écrits et > 1400 mots chacun
- [ ] 0 phrase banned détectée
- [ ] Cohérence personnages vérifiée chapitre par chapitre
- [ ] PDF KDP généré et lisible
- [ ] Description Amazon rédigée
- [ ] Couverture générée
- [ ] Hugo a lu et validé les 3 premiers et les 3 derniers chapitres

---
## ✅ VALIDATION
Pour lancer la production, éditer `cdc.json` et passer `gate_cdc` à `"approved"`.
```
```

### 2. `cdc.json` (JSON machine)
```json
{
  "roman_id": "...",
  "titre": "...",
  "nom_de_plume": "...",
  "genre": "...",
  "sous_genre": "...",
  "langue": "en",
  "mots_cibles": 75000,
  "nb_chapitres": 38,
  "prix_ebook": 2.99,
  "prix_paperback": 11.99,
  "mots_cles_kdp": [...],
  "categories_kdp": [...],
  "description_amazon": "...",
  "bio_auteur": "...",
  "personnages": [...],
  "plan_chapitres": [...],
  "style_guide": {...},
  "forbidden_phrases": [...],
  "gate_cdc": "pending",
  "generated_at": "ISO8601",
  "status": "awaiting_approval"
}
```

## PROMPT GEMINI

### Système
```
Tu es un éditeur littéraire expert en romans commerciaux (KDP, romance, thriller, cozy mystery).
Tu connais parfaitement le marché KDP : BSR, catégories, mots-clés, prix, descriptions.
Tu crées des cahiers des charges de production pour des romans destinés à se vendre sur Amazon KDP.
Tu évites les clichés IA. Ton roman doit sonner comme un livre écrit par un humain pour des humains.
```

### Utilisateur
```
Crée un Cahier des Charges complet pour un roman KDP.

Genre: [ROMAN_GENRE]
Sous-genre: [ROMAN_SOUS_GENRE]
Langue: [ROMAN_LANGUE]

Contraintes obligatoires:
1. Invente un nom de plume unique et crédible pour ce genre
2. Propose un titre accrocheur et différenciant
3. Analyse le marché réel (cite des titres réellement populaires dans ce sous-genre)
4. Crée des personnages avec des défauts réels, pas des stéréotypes lisses
5. Le plan des chapitres doit être suffisamment détaillé pour qu'un auteur commence à écrire sans poser de questions
6. La description Amazon doit être hypnotique, pas générique
7. Les mots-clés KDP doivent être spécifiques (longue traîne, pas "romance novel")

Réponds en JSON pur entre ```json et ```. Chaque champ texte long en anglais si langue=en.
```

## EXTRACTION
- Mode texte plain (PAS application/json)
- Regex: extraire entre ```json et ```
- Si échec: logger l'erreur, sauvegarder `cdc_raw.txt` et exit 0

## WORKFLOW CI
Créer `.github/workflows/cdc_roman.yml` :
```yaml
name: CdC Roman Generator
on:
  push:
    paths: ['.triggers/cdc_roman']
  workflow_dispatch:
    inputs:
      roman_id: {required: true}
      genre: {default: 'romance'}
      sous_genre: {default: 'small-town second-chance'}
      langue: {default: 'en'}
env:
  GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
jobs:
  generate-cdc:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - name: Résoudre ROMAN_ID et params
        id: params
        run: |
          if [ "${{ github.event_name }}" = "push" ]; then
            ID=$(grep -oP '^roman_id=\K.*' .triggers/cdc_roman 2>/dev/null | head -1)
            G=$(grep -oP '^genre=\K.*' .triggers/cdc_roman 2>/dev/null | head -1)
            SG=$(grep -oP '^sous_genre=\K.*' .triggers/cdc_roman 2>/dev/null | head -1)
            L=$(grep -oP '^langue=\K.*' .triggers/cdc_roman 2>/dev/null | head -1)
          else
            ID="${{ inputs.roman_id }}"
            G="${{ inputs.genre }}"
            SG="${{ inputs.sous_genre }}"
            L="${{ inputs.langue }}"
          fi
          echo "roman_id=${ID:-roman_$(date +%Y-%m-%d)_$(echo $G | tr ' ' '_')}" >> $GITHUB_OUTPUT
          echo "genre=${G:-romance}" >> $GITHUB_OUTPUT
          echo "sous_genre=${SG:-small-town second-chance}" >> $GITHUB_OUTPUT
          echo "langue=${L:-en}" >> $GITHUB_OUTPUT
      - name: Générer CdC
        env:
          ROMAN_ID: ${{ steps.params.outputs.roman_id }}
          ROMAN_GENRE: ${{ steps.params.outputs.genre }}
          ROMAN_SOUS_GENRE: ${{ steps.params.outputs.sous_genre }}
          ROMAN_LANGUE: ${{ steps.params.outputs.langue }}
        run: python scripts/agent_cdc_roman.py
      - name: Commit CdC
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add products/novels/
          git diff --cached --quiet || git commit -m "CdC Roman généré — ${{ steps.params.outputs.roman_id }} — EN ATTENTE VALIDATION"
          git push
```

## STDLIB ONLY
`urllib.request`, `json`, `pathlib`, `os`, `re`, `datetime`

## CONTRAINTES
- Crée `products/novels/<roman_id>/` si inexistant
- Sauvegarde TOUJOURS le raw Gemini dans `cdc_raw.txt` (debug)
- `gate_cdc` toujours `"pending"` en sortie (Hugo modifie manuellement)
- Exit 0 toujours
- Print clair : `[CdC] Titre: ...`, `[CdC] Nom de plume: ...`, `[CdC] Fichier: ...`
