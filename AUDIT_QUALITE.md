# 🔍 AUDIT QUALITÉ — diagnostic des productions IA et plan correctif

**Date** : 2026-05-17
**Méthode** : inspection visuelle directe de 5+ images produites par les pipelines V1 + analyse honnête sans complaisance.

---

## 🚨 PROBLÈME PRINCIPAL : le texte généré par Flux est gibberish

**Constat** : tous les pipelines qui demandent à Pollinations/Flux d'écrire du texte directement dans l'image produisent du gibberish illisible.

### Exemples concrets observés (productions du 17/05/2026)

| Pipeline | Attendu | Obtenu | Verdict |
|---|---|---|---|
| viral_formats medical / reading | « Reading is my therapy, cheaper than a shrink » | « eading saall thatby teareonsiy cenele chesier troep seter rhnx my lneak Srick » | ❌ Invendable |
| iheart_v2 my_cat / watercolor | « I ❤️ My Cat » | « I my Cat my at mat Mike » | ❌ Invendable |
| iheart_v2 fishing / vintage | « I ❤️ Fishing » | « I Fishrjijg » | ❌ Invendable |

**Cause technique** : tous les modèles de diffusion (Flux, SD, DALL-E 2/3) ont historiquement de gros problèmes avec le texte rendu. C'est un défaut connu, pas un bug Pollinations. Aucune itération de prompt ne corrige fiablement ça.

### ✅ Ce qui marche au contraire

- **`produce_kdp_cover.py`** (cover Mystical Mushrooms) : illustration générée par Flux SANS texte + overlay Pillow propre du titre/sous-titre → résultat **vendable**.
- **STL parametric** : 100% géométrique numpy-stl, fiabilité parfaite.
- **Coloring book** : sujet 70% bon (1 page sur 3 off-topic mais cela peut se filtrer).
- **COPE pack witchy** : aucun texte dans les images, juste illustration → vendable.

---

## 🎯 SOLUTION ADOPTÉE : « illustration only + overlay Pillow »

Tous les pipelines text-dependent migrent vers cette stratégie :

```
┌──────────────────────────────┐
│ 1. Pollinations génère       │
│    une illustration de FOND  │
│    SANS aucun texte           │
└──────────────────────────────┘
              ↓
┌──────────────────────────────┐
│ 2. Pillow overlay le texte   │
│    en grand avec une vraie   │
│    police TTF (DejaVu, etc.) │
└──────────────────────────────┘
              ↓
┌──────────────────────────────┐
│ 3. Composition finale propre │
│    PNG 3000×3000 @ 300 DPI   │
└──────────────────────────────┘
```

### Nouveaux pipelines V2/V3 codés et prêts

| Ancien (gibberish) | Nouveau (overlay) | Statut |
|---|---|---|
| `produce_viral_formats` | `produce_viral_formats_v2.py` | ✅ Codé |
| `produce_iheart_v2` | `produce_iheart_v3.py` | ✅ Codé |

### Pipelines à refondre prochainement
- `produce_cultural_arbitrage` : mots courts peuvent passer en V1 mais définition longue → V2 needed
- `produce_literal_idioms` : illustration littérale OK mais bloc texte → V2 needed
- `produce_bible_verses` : versets longs = Flux fail à 100% → V2 needed

---

## 🛡️ Système de QC en place (3 niveaux)

### Niveau 1 : Audit heuristique sans clé API
`scripts/agent_visual_audit.py` :
- Cron quotidien 23h UTC
- Détection auto : pipelines text-dependent sans `text_overlay_method=pillow` → flag en review systématique
- OCR Tesseract si disponible (sur GitHub Actions runner = oui)
- Écrit `AUDIT.txt` dans chaque dossier de design
- Score composite 0-100, verdict approve/review/reject

### Niveau 2 : Règles de viabilité par pipeline
`data/quality_rules.json` :
- `critical_rules` : violation = reject auto
- `warning_rules` : violation = review
- `examples_of_unacceptable` : référence concrète
- `approach` : statut de chaque pipeline (VIABLE / BLOCKED_REGENERATE_AS_V2 / etc.)

### Niveau 3 : QC IA via Gemini Vision (s'active dès clé HF dispo)
`scripts/agent_gemini_quality_check.py` :
- S'active automatiquement si `secrets.GEMINI_API_KEY` est défini
- Utilise Gemini 2.0 Flash Vision (1500 req/jour gratuits)
- Envoie l'image + les règles de viabilité du pipeline
- Reçoit JSON strict : `verdict` + `issues` + `rating_0_100` + `reasoning`
- Auto-reject en option (déplace vers `_rejected/`)

---

## 📋 RÈGLES DE VIABILITÉ STRICTES (extrait `data/quality_rules.json`)

### Inacceptable global (tous pipelines)
- ❌ Texte gibberish généré par IA visible
- ❌ Watermarks, signatures parasites
- ❌ Mains à 7 doigts, visages déformés
- ❌ Contenu NSFW accidentel
- ❌ Résolution < 1000×1000 px

### Coloring books
- ❌ Couleurs ou ombres (devrait être line art pur)
- ❌ Sujet hors prompt
- ❌ Traits trop fins pour coloriage adulte
- ❌ Texte parasite dans l'image

### Bible verses (verset KJV doit être EXACT)
- ❌ Verset modifié ou texte hors-Bible
- ❌ Imagerie offensante ou hors-sujet

### I ❤️ X (toute version)
- ❌ Pas de forme de cœur identifiable
- ❌ Scène hors sujet (un t-shirt 'reading' qui montre une voiture)
- ❌ Texte « I X » au lieu de « I [cœur] X »

---

## 🔄 BOUCLE D'AMÉLIORATION CONTINUE

```
Production V1 → Audit visuel auto → Détection problème
                                          ↓
Hugo screenshot le problème → Claude code une V2 corrigée
                                          ↓
Production V2 → Audit visuel auto → Compare ROI V1 vs V2
                                          ↓
Si V2 meilleure : remplace V1 par défaut
Si V2 = V1 : on cherche V3 (autre modèle, autre stratégie)
```

**Itérations attendues** : 3-5 versions par pipeline avant stabilisation.

---

## 🎓 LEÇONS POUR LA SUITE

1. **Ne JAMAIS demander à Flux de l'écriture longue** → toujours overlay Pillow
2. **Auditer SYSTÉMATIQUEMENT avant upload** → ne pas charger Etsy avec du gibberish
3. **Tester en petit batch d'abord** (5-10 designs) → valider visuellement → produire en masse
4. **Garder une version V1 et V2 en parallèle** pour comparer ROI réel (data-driven)
5. **Coloring book** : Pollinations 70% OK, mais HF SDXL + ControlNet sera meilleur (besoin clé HF)
6. **Le concept compte plus que le pixel** : iheart_v3 (concept de scène dans le cœur) > iheart_v1 (cœur générique en fond), même qualité visuelle

---

## 🚦 STATUT ACTUEL PAR PIPELINE (au 2026-05-17)

| Pipeline | Statut | Production | Action |
|---|---|---|---|
| `viral_formats` V1 | ❌ Gibberish | 25 designs invendables | Ne pas uploader |
| `viral_formats_v2` | ✅ Codé | 0 (à trigger) | Lancer demain |
| `iheart_v2` | ❌ Gibberish | 10 designs invendables | Ne pas uploader |
| `iheart_v3` | ✅ Codé | 0 (à trigger) | Lancer demain |
| `coloring_books` | ⚠ 70% bon | 1 PDF + cover | Uploadable mais curer pages |
| `stl_parametric` | ✅ Fiable | 10 STL | Uploadable direct |
| `cope_pack` witchy | ✅ Fiable | 5 designs | Uploadable direct |
| `cultural_arbitrage` | ⏳ Pas tourné | 0 | V2 à coder |
| `literal_idioms` | ⏳ Pas tourné | 0 | V2 à coder |
| `bible_verses` | ⏳ Pas tourné | 0 | V2 à coder |
| `tumbler_wraps` | ⏳ Pas tourné | 0 | V1 OK (pas de texte) |
| `chess_book` | ✅ Fiable | 0 (à trigger) | Texte généré par python-chess |

---

## 📊 ESTIMATION CORRIGÉE DU STOCK VENDABLE

| Source | Nominal | Réellement vendable | Différence |
|---|---|---|---|
| viral_formats V1 (25 produits) | 25 | 0 | -25 |
| iheart_v2 (10 produits) | 10 | 0 | -10 |
| coloring book (1 livre) | 1 | 1 (à curer 5 pages) | 0 |
| STL (10 fichiers) | 10 | 10 | 0 |
| cope_pack (5 designs) | 5 | 5 | 0 |
| **TOTAL** | **51** | **~16 vendables** | **-35 (-69%)** |

**Conclusion honnête** : 2/3 de la production V1 est invendable. Le pivot V2/V3 est urgent. Une fois les V2 lancés, on devrait atteindre 80-90% vendable.
