TARGET: scripts/generate_from_plan.py

## Rôle
Lit le production_plan.json d'un brief approuvé, génère chaque page via
scripts/lib/image_router.py, convertit en line-art via scripts/lib/image_to_coloring.py,
sauvegarde dans products/coloring_books/_gate1/<brief_id>/pages/.

## Variables d'environnement
- BRIEF_ID : identifiant du brief
- IMAGE_PROVIDERS : ordre providers (ex. "runware,pollinations")
- RUNWARE_API_KEY, TOGETHER_API_KEY, etc.
- LINE_THICKNESS : épaisseur de trait (défaut 2)
- MAX_PAGES : limite optionnelle

## Fichiers lus
- data/briefs/<BRIEF_ID>.json
- products/coloring_books/_gate1/<BRIEF_ID>/production_plan.json
  Structure: {"pages": [{"index": 1, "prompt": "...", "subject": "..."}, ...], "covers": {"front": {...}, "back": {...}}}

## Fichiers écrits
- products/coloring_books/_gate1/<BRIEF_ID>/pages/page_001.png ... page_030.png
- products/coloring_books/_gate1/<BRIEF_ID>/pages/cover_front.png
- products/coloring_books/_gate1/<BRIEF_ID>/generation_report.json
  {"pages": [{"page_number": 1, "status": "ok|failed|skipped", "provider_used": "..."}], "summary": {"ok": 28, "failed": 2}}

## Comportement
1. Vérifier gate_start == approved
2. Pour chaque page : si existe déjà → skip (idempotent)
3. Appeler image_router.generate(prompt, negative_prompt=..., width=832, height=1152, dest=tmp)
4. Si succès : image_to_coloring.convert(tmp, dest, line_thickness=LINE_THICKNESS)
5. Supprimer tmp intermédiaire
6. Covers : width=2625, height=3375 (KDP 300DPI)
7. Écrire generation_report.json
8. Exit 0 même si échecs partiels

## Imports
```python
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from lib.image_router import generate as ir_generate
from lib.image_to_coloring import convert as coloring_convert
```

## Dépendances
- scripts/lib/image_router.py (existant)
- scripts/lib/image_to_coloring.py (généré par briefing 01)
- Pillow, stdlib
