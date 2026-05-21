#!/usr/bin/env python3
"""Test AI Horde — generateur d'images GRATUIT (GPU communautaires).

Gratuit, cle anonyme '0000000000' (file d'attente) ou cle perso (priorite).
Supporte text2img ET img2img (image de reference). Asynchrone : on soumet,
on attend (polling), on recupere. Resultats dans products/_generator_test/.

Env : AIHORDE_API_KEY (optionnel, defaut anonyme).
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "products" / "_generator_test"
BASE_IMAGE = ROOT / "products" / "coloring_books" / "mystical_creatures" / "pages" / "page_01.png"

API_KEY = os.environ.get("AIHORDE_API_KEY", "0000000000").strip()
BASE = "https://aihorde.net/api/v2"
HEADERS = {"apikey": API_KEY, "Content-Type": "application/json",
           "Client-Agent": "365days-coloring:1.0:github-actions"}

PROMPT = (
    "adult coloring book page, clean bold black outline line art only, "
    "no shading no grey no hatching no sketch, flat clean cartoon style, "
    "cute kawaii baby dragon in a cozy cottage with fireplace, books and "
    "potted plants, full scene with background, pure white background"
)


def _post(path: str, payload: dict) -> dict:
    req = urllib.request.Request(f"{BASE}{path}", data=json.dumps(payload).encode("utf-8"),
                                 headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def _get(path: str) -> dict:
    req = urllib.request.Request(f"{BASE}{path}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def run(name: str, payload: dict, max_wait: int = 540) -> str:
    try:
        gid = _post("/generate/async", payload).get("id")
    except urllib.error.HTTPError as exc:  # type: ignore[attr-defined]
        return f"❌ {name} : submit HTTP {exc.code} {exc.read()[:200].decode(errors='ignore')}"
    except Exception as exc:  # noqa: BLE001
        return f"❌ {name} : submit {type(exc).__name__} {exc}"
    if not gid:
        return f"❌ {name} : pas d'id"
    t0 = time.time()
    while time.time() - t0 < max_wait:
        try:
            st = _get(f"/generate/check/{gid}")
        except Exception:  # noqa: BLE001
            time.sleep(10)
            continue
        if st.get("done"):
            break
        time.sleep(12)
    else:
        return f"❌ {name} : timeout file d'attente ({max_wait}s)"
    try:
        status = _get(f"/generate/status/{gid}")
        gens = status.get("generations", [])
        if not gens:
            return f"❌ {name} : aucune generation"
        img = gens[0].get("img", "")
        if img.startswith("http"):
            with urllib.request.urlopen(img, timeout=120) as r:
                data = r.read()
        else:
            data = base64.b64decode(img)
        (OUT / f"aihorde_{name}.png").write_bytes(data)
        return f"✅ {name} : OK {len(data)}o ({time.time()-t0:.0f}s) -> aihorde_{name}.png"
    except Exception as exc:  # noqa: BLE001
        return f"❌ {name} : fetch {type(exc).__name__} {exc}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    mode = "perso" if API_KEY != "0000000000" else "anonyme"
    report = [f"AI Horde test (cle: {mode})", "=" * 50]

    report.append(run("text2img", {
        "prompt": PROMPT,
        "params": {"width": 1024, "height": 1024, "steps": 25, "n": 1},
        "nsfw": False, "censor_nsfw": True,
    }))

    if BASE_IMAGE.exists():
        src = base64.b64encode(BASE_IMAGE.read_bytes()).decode()
        report.append(run("img2img", {
            "prompt": "clean bold black outline coloring page line art, no shading no grey, flat cartoon",
            "params": {"width": 1024, "height": 1024, "steps": 25, "denoising_strength": 0.55, "n": 1},
            "source_image": src, "source_processing": "img2img",
            "nsfw": False, "censor_nsfw": True,
        }))
    else:
        report.append(f"⊘ img2img : image de base absente ({BASE_IMAGE})")

    (OUT / "_aihorde_report.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
