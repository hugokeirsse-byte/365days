#!/usr/bin/env python3
"""PRODUCTEUR pilote par le cahier des charges (Brique 2 de la boucle).

NE GENERE AUCUNE IMAGE ici : il ECRIT LE PLAN DE PRODUCTION a partir d'un brief
approuve (GATE 1). C'est l'IA-redactrice-de-prompts : 30 prompts DISTINCTS mais
COHERENTS (meme base de style + meme reference verrouillee), + prompts couvertures,
le tout BORNE par le budget images. La generation reelle (CI, image_router) viendra
ensuite, en consommant ce plan.

Garde-fous :
  - REFUSE de produire si human_gates.gate_start != "approved" (rien sans ton OK).
  - REFUSE si la reference n'est pas verrouillee (reference_selection.chosen_reference_path).
  - RESPECTE image_budget.max_images_total (sinon STOP).

Modes : Gemini (enrichit chaque prompt) si dispo ; sinon DETERMINISTE (gabarit),
pour tester le cablage hors-ligne. Ecrit products/coloring_books/_gate1/<id>/production_plan.json
"""
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRIEFS_DIR = ROOT / "data" / "briefs"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_FALLBACKS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
USER_AGENT = "365days-Producer/1.0"
TIMEOUT = 60

BRIEF_ID = os.environ.get("BRIEF_ID", "brief_2026-05-22_coloring_kawaii_mushroom_hollow")

STYLE_BASE = (
    "adult coloring book page, clean BOLD black outline line art ONLY, "
    "uniform thick vector-style outlines on pure white background, "
    "closed simple shapes ready to color, flat clean cartoon style, "
    "professional coloring book quality"
)


def call_gemini(prompt, retries=2):
    if not GEMINI_API_KEY:
        return None, "GEMINI_API_KEY absent"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json", "maxOutputTokens": 4096},
    }).encode("utf-8")
    last = "inconnu"
    seq = [GEMINI_MODEL] + [m for m in GEMINI_FALLBACKS if m != GEMINI_MODEL]
    for model in seq:
        url = f"{API_BASE}/{model}:generateContent?key={GEMINI_API_KEY}"
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, data=body,
                    headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                    data = json.loads(r.read())
                return json.loads(data["candidates"][0]["content"]["parts"][0]["text"]), model
            except urllib.error.HTTPError as exc:
                last = f"{model}: HTTP {exc.code}"
                if exc.code == 404:
                    break
                time.sleep(3 + attempt * 3)
            except Exception as exc:  # noqa: BLE001
                last = f"{model}: {type(exc).__name__}"
                time.sleep(2 + attempt * 2)
    return None, last


def build_page_prompt(subject, style_keywords, negatives):
    """Prompt d'UNE page : base + style partage (coherence) + sujet unique + negatifs."""
    kw = ", ".join(style_keywords)
    neg = " ".join(f"no {n}," for n in negatives).rstrip(",")
    return f"{STYLE_BASE}, {kw}, {subject}, {neg}"


def gemini_refine(subjects, style_keywords):
    """Demande a Gemini d'enrichir chaque sujet en prompt detaille, en gardant la coherence."""
    prompt = (
        "Tu es le DESSINATEUR d'un studio de coloriages. Pour CHAQUE sujet, ecris UN prompt "
        "de generation d'image en anglais, DETAILLE, pour une page de coloriage adulte au TRAIT NOIR "
        "EPAIS sur blanc (PAS de couleur, PAS d'ombrage, PAS de texte). Garde une COHERENCE de style "
        f"sur toutes les pages (style: {', '.join(style_keywords)}). Reponds STRICTEMENT en JSON: "
        '{ "prompts": ["...", "..."] } un par sujet, MEME ORDRE.\nSujets:\n'
        + "\n".join(f"{i+1}. {s}" for i, s in enumerate(subjects))
    )
    res, info = call_gemini(prompt)
    if res and isinstance(res.get("prompts"), list) and len(res["prompts"]) >= len(subjects):
        return res["prompts"][:len(subjects)], f"gemini:{info}"
    return None, info


def main():
    print("=" * 64)
    print("PRODUCTEUR pilote par cahier des charges — PLAN (aucune image generee)")
    print("=" * 64)
    bp = BRIEFS_DIR / f"{BRIEF_ID}.json"
    if not bp.exists():
        print(f"✗ Brief introuvable: {bp}")
        return 1
    brief = json.loads(bp.read_text(encoding="utf-8"))

    gate = brief.get("human_gates", {}).get("gate_start")
    if gate != "approved":
        print(f"⊝ GATE 1 non approuve (gate_start={gate}). Production REFUSEE tant que Hugo n'a pas valide.")
        return 0
    ref = brief.get("reference_selection", {}).get("chosen_reference_path", "")
    if not ref:
        print("⊝ Reference non verrouillee. Production REFUSEE (il faut une reference choisie).")
        return 0

    tgt = brief["target"]
    subjects = tgt["page_subjects"]
    style_kw = tgt["style_reference"]["style_keywords"]
    negatives = tgt["style_reference"]["negative"]
    budget = brief.get("image_budget", {})
    max_images = budget.get("max_images_total", 50)

    # Redaction des prompts : Gemini si dispo, sinon deterministe (1 prompt distinct/sujet)
    prompts, source = (None, "")
    if GEMINI_API_KEY:
        prompts, source = gemini_refine(subjects, style_kw)
    if not prompts:
        prompts = [build_page_prompt(s, style_kw, negatives) for s in subjects]
        source = "deterministe (1 prompt distinct par sujet, base de style partagee)"

    pages = [{"index": i + 1, "subject": subjects[i], "prompt": prompts[i], "seed": (i + 1) * 7}
             for i in range(len(subjects))]

    cover = tgt.get("cover", {})
    front = cover.get("front", {})
    back = cover.get("back", {})
    covers = {
        "front": {"prompt": (f"book cover illustration, COLOR, soft pastel cottagecore scene, "
                             f"{', '.join(style_kw)}, {front.get('title_text','')} theme, cute and inviting, "
                             "vertical book cover, no text"),
                  "seed": 999, "note": front.get("layout_note", "")},
        "back": {"prompt": (f"back cover background, COLOR, soft pastel cottagecore pattern, "
                            f"{', '.join(style_kw)}, gentle and uncluttered, space for text and barcode, no text"),
                 "seed": 998, "note": back.get("layout_note", "")},
    }

    # Pages liminaires = typographie (0 image generee)
    total_images = len(pages) + 2  # 30 pages + 2 couvertures
    within = total_images <= max_images

    plan = {
        "brief_id": BRIEF_ID,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "title": tgt.get("collection", {}).get("title"),
        "author": tgt.get("collection", {}).get("author"),
        "reference_image": ref,
        "coherence": "tous les prompts partagent STYLE_BASE + style_keywords + la MEME reference verrouillee (img2img/IP-Adapter a la generation)",
        "style_base": STYLE_BASE,
        "negative_terms": negatives,
        "prompt_source": source,
        "front_matter_typeset": [p["page"] for p in tgt.get("book_structure", {}).get("front_matter", [])],
        "pages": pages,
        "covers": covers,
        "images_planned": total_images,
        "image_budget_max": max_images,
        "within_budget": within,
        "status": "PLAN PRET — aucune image generee. Lancer la generation = etape suivante (CI / image_router).",
    }
    if not within:
        plan["status"] = f"✗ DEPASSE LE BUDGET ({total_images} > {max_images}) — STOP."

    out_dir = ROOT / "products" / "coloring_books" / "_gate1" / BRIEF_ID
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "production_plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Brief        : {BRIEF_ID} (GATE 1 approuve ✓, reference verrouillee ✓)")
    print(f"Source prompts: {source}")
    print(f"Pages        : {len(pages)} prompts distincts")
    print(f"Distincts ?  : {len(set(p['prompt'] for p in pages))}/{len(pages)} uniques")
    print(f"Images planifiees: {total_images} / budget {max_images}  -> {'OK' if within else 'DEPASSE'}")
    print(f"Exemple page 1: {pages[0]['prompt'][:110]}...")
    print(f"Exemple page 7: {pages[6]['prompt'][:110]}...")
    print(f"Plan ecrit   : {out_dir / 'production_plan.json'}")
    print("  -> AUCUNE image generee. Pret a lancer quand tu valides.")
    return 0 if within else 2


if __name__ == "__main__":
    raise SystemExit(main())
