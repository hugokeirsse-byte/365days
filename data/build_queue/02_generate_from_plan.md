TARGET: scripts/generate_from_plan.py

## Rôle
Étape de génération d'images de la boucle autonome (après le Producteur).
Lit le `production_plan.json` d'un brief approuvé, génère chaque page via
`scripts/lib/image_router.py`, convertit en line-art via
`scripts/lib/image_to_coloring.py`, sauvegarde dans
`products/coloring_books/_gate1/<brief_id>/pages/`.

## Variables d'environnement
- `BRIEF_ID` : identifiant du brief (ex. `brief_2026-05-22_coloring_kawaii_mushroom_hollow`)
- `IMAGE_PROVIDERS` : ordre des providers (ex. `"runware,pollinations"`), optionnel
- `RUNWARE_API_KEY`, `TOGETHER_API_KEY`, `CLOUDFLARE_API_TOKEN`, etc. : transmis à image_router
- `LINE_THICKNESS` : épaisseur de trait pour image_to_coloring (défaut `2`)
- `MAX_PAGES` : limite optionnelle (utile pour tests)

## Fichiers lus
- `data/briefs/<BRIEF_ID>.json` (pour vérifier gate_start = approved + lire image_budget + style)
- `products/coloring_books/_gate1/<BRIEF_ID>/production_plan.json`
  Structure attendue :
  ```json
  {
    "pages": [
      {"page_number": 1, "title": "...", "prompt": "...", "negative_prompt": "..."},
      ...
    ],
    "covers": [
      {"type": "front", "prompt": "...", "negative_prompt": "..."},
      {"type": "back", "prompt": "...", "negative_prompt": "..."}
    ]
  }
  ```

## Fichiers écrits
- `products/coloring_books/_gate1/<BRIEF_ID>/pages/page_001.png` … `page_030.png`
- `products/coloring_books/_gate1/<BRIEF_ID>/pages/cover_front.png`
- `products/coloring_books/_gate1/<BRIEF_ID>/pages/cover_back.png` (si présent)
- `products/coloring_books/_gate1/<BRIEF_ID>/generation_report.json`
  ```json
  {
    "brief_id": "...",
    "generated_at": "ISO8601",
    "pages": [
      {"page_number": 1, "status": "ok|failed|skipped", "provider_used": "...", "path": "..."},
      ...
    ],
    "covers": [...],
    "summary": {"ok": 28, "failed": 2, "skipped": 0}
  }
  ```

## Comportement
1. Vérifier que `gate_start == "approved"` dans le brief ; sinon STOP avec exit(1)
2. Vérifier que `production_plan.json` existe ; sinon STOP
3. Charger image_router depuis le chemin relatif (sys.path.insert si nécessaire)
4. Pour chaque page dans `pages` :
   a. Si `pages/page_NNN.png` existe déjà → status = "skipped" (idempotent)
   b. Appeler `image_router.generate(prompt, negative_prompt, width=832, height=1152, dest=tmp_path)`
      (portrait, ratio proche A4/letter)
   c. Si succès : appeler `image_to_coloring.convert(tmp_path, dest_path, line_thickness=LINE_THICKNESS)`
   d. Supprimer le fichier intermédiaire tmp
   e. Si échec : status = "failed", continuer (ne pas stopper le pipeline)
5. Même logique pour les covers (width=2625, height=3375 pour front cover KDP 300DPI)
6. Écrire generation_report.json
7. Afficher un résumé : "OK: 28/30, FAILED: 2, SKIPPED: 0"
8. Exit 0 même s'il y a des échecs partiels (le rapport documente tout)

## Dépendances
- `scripts/lib/image_router.py` (déjà existant)
- `scripts/lib/image_to_coloring.py` (généré par briefing 01)
- Pillow (pour redimensionner si nécessaire)
- stdlib uniquement sinon

## Import image_router
```python
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.image_router import generate as ir_generate
from lib.image_to_coloring import convert as coloring_convert
```
