#!/usr/bin/env python3
"""Genere les IMAGES DE REFERENCE CANDIDATES d'un cahier des charges (GATE 1).

Lit un brief (data/briefs/<BRIEF_ID>.json), genere N variantes d'un sujet
representatif dans le style cible, et les depose sous
products/coloring_books/_gate1/<BRIEF_ID>/ref_candidates/ pour que Hugo en
choisisse une (elle verrouillera ensuite le style de tout le livre).

Tourne en GitHub Actions (reseau ouvert). Utilise l'ImageRouter : Runware
(FLUX.1 schnell) si RUNWARE_API_KEY est present, sinon bascule vers le filet
gratuit (Pollinations). Cout Runware ~0.0006$/image.

Env :
  BRIEF_ID           (defaut: brief_2026-05-22_coloring_kawaii_mushroom_hollow)
  REFERENCE_SUBJECT  (optionnel) sujet representatif ; defaut = 1er page_subject
  REFERENCE_PROVIDER (optionnel) force un fournisseur (ex. "pollinations")
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "lib"))
import image_router  # noqa: E402

BRIEF_ID = os.environ.get("BRIEF_ID", "brief_2026-05-22_coloring_kawaii_mushroom_hollow")
BRIEF_PATH = ROOT / "data" / "briefs" / f"{BRIEF_ID}.json"

BASE = (
    "adult coloring book page, clean BOLD black outline line art ONLY, "
    "uniform thick vector-style outlines on pure white background, "
    "closed simple shapes ready to color, flat clean cartoon style, "
    "professional coloring book quality"
)


def build_prompt(brief: dict, subject: str) -> str:
    sr = brief.get("target", {}).get("style_reference", {})
    keywords = ", ".join(sr.get("style_keywords", []))
    # le routeur n'a pas de champ negatif -> on integre en "no <terme>" (comme STYLE_BASE eprouve)
    negatives = " ".join(f"no {n}," for n in sr.get("negative", [])).rstrip(",")
    parts = [BASE]
    if keywords:
        parts.append(keywords)
    parts.append(subject)
    if negatives:
        parts.append(negatives)
    return ", ".join(parts)


def main() -> int:
    if not BRIEF_PATH.exists():
        print(f"ERREUR: brief introuvable: {BRIEF_PATH}")
        return 1
    brief = json.loads(BRIEF_PATH.read_text(encoding="utf-8"))

    subjects = brief.get("target", {}).get("page_subjects", [])
    subject = os.environ.get("REFERENCE_SUBJECT") or (subjects[0] if subjects else "cute subject")

    refsel = brief.get("reference_selection", {})
    budget = brief.get("image_budget", {})
    count = int(refsel.get("candidates_count") or budget.get("reference_candidates_budget") or 6)

    provider = os.environ.get("REFERENCE_PROVIDER", "").strip()
    providers = [provider] if provider else None  # None -> ordre par defaut (runware->...->pollinations)

    prompt = build_prompt(brief, subject)
    out_dir = ROOT / "products" / "coloring_books" / "_gate1" / BRIEF_ID / "ref_candidates"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Brief        : {BRIEF_ID}")
    print(f"Sujet ref    : {subject}")
    print(f"Candidates   : {count}")
    print(f"Fournisseur  : {provider or 'auto (runware->...->pollinations)'}")
    print(f"Prompt       : {prompt}\n")

    produced = []
    for i in range(1, count + 1):
        dest = out_dir / f"cand_{i}.png"
        res = image_router.generate(prompt, seed=i * 7, width=1024, height=1024,
                                    providers=providers, dest=str(dest), timeout=180)
        ok = bool(res)
        print(f"  cand_{i}: {'OK' if ok else 'FAIL'}", flush=True)
        if ok:
            produced.append(dest.name)

    index = {
        "brief_id": BRIEF_ID,
        "subject": subject,
        "prompt": prompt,
        "requested": count,
        "produced": produced,
        "status_note": "Hugo choisit une candidate -> reporter son chemin dans brief.reference_selection.chosen_reference_path et passer status=locked.",
    }
    (out_dir / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n{len(produced)}/{count} candidates -> {out_dir}")
    return 0 if produced else 2


if __name__ == "__main__":
    raise SystemExit(main())
