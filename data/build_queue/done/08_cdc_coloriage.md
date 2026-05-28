# Briefing 08 — agent_cdc_coloriage.py

## OBJECTIF
Créer `scripts/agent_cdc_coloriage.py` — génère un Cahier des Charges ultra-complet pour un livre de coloriage KDP.

## PHILOSOPHIE
Chaque livre de coloriage est un produit commercial unique avec un positionnement précis.
Rien ne part en production sans validation du CdC par Hugo.

## ENTRÉES
- `GEMINI_API_KEY` (env)
- `COLORIAGE_ID` (env) : ex: `coloriage_2026-05-27_botanical_vintage`
- `COLORIAGE_THEME` (env, optionnel) : ex: `botanical`, `animals`, `mandala`, `fantasy` (défaut: auto depuis trends)
- `COLORIAGE_STYLE` (env, optionnel) : ex: `kawaii`, `realistic`, `geometric`, `intricate` (défaut: auto)
- `COLORIAGE_AUDIENCE` (env, optionnel) : ex: `adults`, `kids`, `seniors` (défaut: adults)

## SORTIES
Dossier : `products/coloring_books/<COLORIAGE_ID>/`

### 1. `CAHIER_DES_CHARGES.md`
```markdown
# CAHIER DES CHARGES — [TITRE LIVRE DE COLORIAGE]
**Statut : EN ATTENTE DE VALIDATION**

## 1. IDENTITÉ COMMERCIALE
- **Titre** : ...
- **Sous-titre** : (ex: "A Relaxing Adult Coloring Book with...")
- **Auteur/Marque** : [nom unique par livre]
- **Genre KDP** : Coloring Books > Adults
- **Audience** : ...
- **Nb de pages** : 30 (intérieur) + couverture
- **Format** : 8.5 x 11 inches (Letter)
- **Prix ebook** : $0 (non applicable coloring)
- **Prix paperback** : $X.XX
- **Copyright** : ...

## 2. CONCEPT ET POSITIONNEMENT
- **Angle unique** : ...
- **En quoi c'est différent des bestsellers** : ...
- **Promesse au lecteur** : ...

## 3. ANALYSE MARCHÉ (5 CONCURRENTS KDP)
| Titre | BSR | Note | Prix | Nb pages | Points forts | Points faibles |
|---|---|---|---|---|---|---|
...

**Opportunité identifiée** : ...

## 4. LISTE DES 30 SUJETS (PAGES)
Chaque sujet = 1 page de coloriage. Format: numéro | sujet | description breve | niveau complexité
1 | ... | ... | simple/medium/complex
...
30 | ... | ... | ...

## 5. PROMPTS IMAGE (PRÉ-RÉDIGÉS)
Chaque prompt = version opt pour Stable Diffusion / Pollinations. Style cohérent défini ici.
- **Style global** : "coloring book, black and white line art, clean lines, no shading, white background, ..."
- Prompt couverture (colorée) : ...
1: "..."
...

## 6. DESCRIPTION AMAZON (~300 mots)
...

## 7. MOTS-CLÉS KDP (7)
1. ...
...

## 8. CATÉGORIES KDP
...

## 9. EXIGENCES TECHNIQUES
- Pages intérieur : 8.5x11in, 300 DPI, NOIR ET BLANC pur (pas de gris)
- Marge sécurité : 0.25in de chaque côté
- Couverture : couleur, 8.75x11.25in (avec bleed 0.125in)
- Papier : white (pour coloriage)

## 10. COÛT ET CALENDRIER
- Appels API image : 31 (30 pages + 1 couverture)
- Coût API Pollinations : $0 (gratuit)
- Durée CI : ~15 min
- Coût impression KDP : ~$2.15
- Prix vente : $7.99
- Revenu net par vente : ~$2.50

## 11. CRITÈRES VALIDATION FINALE
- [ ] 30 pages générées, toutes noir et blanc pur
- [ ] Couverture colorée attrayante
- [ ] PDF KDP généré et correct
- [ ] Audit automatique score > 75/100
- [ ] Hugo a regardé 5 pages minimum

---
## ✅ VALIDATION
Éditer `cdc.json` et passer `gate_cdc` à `"approved"`.
```

### 2. `cdc.json`
```json
{
  "coloriage_id": "...",
  "titre": "...",
  "auteur": "...",
  "theme": "...",
  "style": "...",
  "audience": "adults",
  "nb_pages": 30,
  "prix_paperback": 7.99,
  "mots_cles_kdp": [...],
  "categories_kdp": [...],
  "description_amazon": "...",
  "style_prompt_global": "coloring book page, black and white line art...",
  "pages": [
    {"num": 1, "sujet": "...", "prompt": "...", "complexite": "medium"}
  ],
  "prompt_couverture": "...",
  "gate_cdc": "pending",
  "generated_at": "ISO8601",
  "status": "awaiting_approval"
}
```

## PROMPT GEMINI
### Système
```
Tu es un expert en livres de coloriage commerciaux pour adultes vendus sur KDP Amazon.
Tu connais les tendances (botanical, mindfulness, fantasy, animaux, mandalas, vintage).
Tu crées des cahiers des charges avec des sujets originaux et des prompts d'image précis.
```

### Utilisateur
```
Crée un Cahier des Charges complet pour un livre de coloriage KDP.
Thème: [COLORIAGE_THEME]
Style: [COLORIAGE_STYLE]
Audience: [COLORIAGE_AUDIENCE]

Contraintes:
1. Titre original et accrocheur (pas "Ultimate Adult Coloring Book")
2. 30 sujets variés avec différents niveaux de complexité (simple, medium, complex)
3. Prompts image en anglais, style cohérent, optimisés pour Stable Diffusion
4. Analyse réelle de concurrents (titres vraisemblables avec BSR)
5. Description Amazon engageante
6. Mots-clés longue traîne (pas juste "coloring book")
Réponds en JSON pur entre ```json et ```.
```

## WORKFLOW CI
Créer `.github/workflows/cdc_coloriage.yml` (même structure que cdc_roman.yml).
Trigger: `.triggers/cdc_coloriage`
Variables: `COLORIAGE_ID`, `COLORIAGE_THEME`, `COLORIAGE_STYLE`, `COLORIAGE_AUDIENCE`

## STDLIB ONLY + EXIT 0 TOUJOURS
