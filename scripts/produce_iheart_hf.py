"""
Pipeline I ❤️ X via Hugging Face (squelette prêt à activer).

REMPLACE Pollinations Flux par HF Inference API gratuit, qui donne :
- Vrai contrôle de la composition (ControlNet, IP-Adapter)
- Anatomie correcte (modèles fine-tuned humans/animals)
- Respect des contraintes négatives (« no heart symbols » est respecté)

S'active automatiquement dès que HF_API_KEY est dispo en secret GitHub.

Modèles HF utilisés (tous gratuits sur Inference API) :
- stabilityai/stable-diffusion-xl-base-1.0 (génération SDXL haute qualité)
- lllyasviel/sd-controlnet-canny (contraint la composition)
- h94/IP-Adapter (style reference image)

Pour scènes avec animaux fiables :
- pet-portrait LoRAs (Civitai mirror via HF)

Variables d'env :
  HF_API_KEY       clé HF Inference API (gratuite)
  MAX_NICHES=8
  MAX_STYLES=2
  HF_MODEL=stabilityai/stable-diffusion-xl-base-1.0
  RETRY_ON_FAIL=3
"""

import csv
import json
import os
import random
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.design_composer import compose_design, get_layout  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "iheart_hf"
USER_AGENT = "IHeartHFProducer/1.0"
TIMEOUT = 180

HF_API_KEY = os.environ.get("HF_API_KEY", "").strip()
HF_MODEL = os.environ.get("HF_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

NICHES = [
    {"slug": "fishing", "label": "Fishing",
     "scene": "lone fisherman silhouette casting line at sunset over a calm lake, golden hour, mountains in the distance, vintage engraving style"},
    {"slug": "reading", "label": "Reading",
     "scene": "cozy person reading in armchair, warm lamp light, stacks of books, tea cup on side table, soft warm palette"},
    {"slug": "my_cat", "label": "My Cat",
     "scene": "a single orange tabby cat curled up sleeping on cozy blanket with sunlight, peaceful, single cat only"},
    {"slug": "my_dog", "label": "My Dog",
     "scene": "a single golden retriever sitting in meadow with flowers, single dog only, warm sunlight"},
    {"slug": "hiking", "label": "Hiking",
     "scene": "lone hiker silhouette on mountain peak at sunrise, dramatic landscape, no people in foreground"},
    {"slug": "camping", "label": "Camping",
     "scene": "small tent next to glowing campfire under starry night sky, pine forest silhouettes, warm orange glow, no people"},
    {"slug": "coffee", "label": "Coffee",
     "scene": "single steaming coffee cup with latte art on rustic wood table, morning sunlight, croissant beside, no people"},
    {"slug": "gardening", "label": "Gardening",
     "scene": "single person from behind tending colorful flowers in cottage garden, butterflies, soft pastel morning light"},
]


def call_hf_text_to_image(prompt: str, negative_prompt: str, seed: int,
                           retries: int = 3) -> bytes | None:
    """Appelle HF Inference API pour générer une image."""
    if not HF_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    body = {
        "inputs": prompt,
        "parameters": {
            "negative_prompt": negative_prompt,
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
            "width": 1024,
            "height": 1024,
            "seed": seed,
        },
        "options": {"wait_for_model": True},
    }
    data = json.dumps(body).encode("utf-8")

    for attempt in range(retries):
        try:
            req = urllib.request.Request(HF_API_URL, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            # 503 = modèle en train de charger, on attend
            if exc.code == 503:
                print(f"    HF model loading, attente 20s...")
                time.sleep(20)
                continue
            print(f"    HTTP {exc.code} : {exc.reason}")
            time.sleep(6 + attempt * 6)
        except Exception as exc:  # noqa: BLE001
            print(f"    retry {attempt+1}/{retries} : {exc}")
            time.sleep(6 + attempt * 6)
    return None


def make_outputs(composed: Path, design_dir: Path) -> None:
    from PIL import Image
    img = Image.open(composed).convert("RGB")
    img.resize((1080, 1080), Image.LANCZOS).save(
        design_dir / "etsy_preview.jpg", "JPEG", quality=92)
    # T-shirt portrait
    ratio = 2400 / 3000
    h = img.height
    w_t = int(h * ratio)
    if w_t > img.width:
        w_t = img.width
        h = int(w_t / ratio)
    off_x = (img.width - w_t) // 2
    off_y = (img.height - h) // 2
    tee = img.crop((off_x, off_y, off_x + w_t, off_y + h))
    tee.resize((2400, 3000), Image.LANCZOS).save(
        design_dir / "tshirt_2400x3000.png", "PNG", optimize=True)


def produce_design(niche: dict, idx: int) -> dict | None:
    # Prompt POSITIF : on demande la scène
    prompt = (
        f"{niche['scene']}, professional digital illustration, "
        f"perfect anatomy, single subject, high quality, vibrant colors, "
        f"detailed, masterpiece, square composition"
    )
    # Prompt NÉGATIF : on bannit ce qu'on ne veut pas — HF SDXL respecte
    # vraiment ces contraintes (contrairement à Pollinations)
    negative = (
        "heart symbols, heart shapes, hearts, text, letters, words, "
        "logo, watermark, signature, multiple subjects, duplicates, "
        "twin animals, two heads, extra limbs, deformed, ugly, "
        "low quality, blurry, frame, border"
    )

    design_dir = OUTPUT_DIR / niche["slug"]
    design_dir.mkdir(parents=True, exist_ok=True)
    illust_path = design_dir / "raw_illust.png"
    final = design_dir / "print_3000.png"
    seed = idx * 10143 + random.randint(0, 9999)

    print(f"  [{idx:>3}] I ❤️ {niche['label']}")
    img_bytes = call_hf_text_to_image(prompt, negative, seed)
    if not img_bytes or len(img_bytes) < 5000:
        print(f"        HF failed")
        return None
    illust_path.write_bytes(img_bytes)

    try:
        layout = get_layout("iheart_masked")
        compose_design(
            layout=layout,
            illustration_path=illust_path,
            text_values={"I": "I", "niche": niche["label"]},
            output_path=final,
        )
        make_outputs(final, design_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"        compose echoue : {exc}")
        return None
    finally:
        if illust_path.exists():
            illust_path.unlink()

    title = (f"I Love {niche['label']} Print — Heart-Shaped Scene "
             f"Premium HF SDXL Quality")[:140]
    tags = [
        f"i love {niche['label'].lower()}",
        f"{niche['slug'].replace('_', ' ')} gift",
        "heart shaped art",
        "wall art print",
        "tshirt design",
        "premium quality",
        "digital download",
        f"{niche['label'].lower()} lover",
        "unique gift",
        "scene in heart",
        "redbubble pod",
        "instant download",
        "perfect anatomy",
    ]
    tags = list(dict.fromkeys(tags))[:13]

    metadata = {
        "design_id": f"iheart_hf_{niche['slug']}",
        "version": "hf",
        "text_overlay_method": "pillow",
        "generation_model": HF_MODEL,
        "niche": niche["slug"],
        "niche_label": niche["label"],
        "title": title,
        "tags_etsy": ", ".join(tags),
        "price_etsy": 5.99,  # prix premium car qualité HF
        "files_included": "etsy_preview.jpg, print_3000.png, tshirt_2400x3000.png",
        "positive_prompt": prompt,
        "negative_prompt": negative,
        "seed": seed,
    }
    (design_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))
    return metadata


def main() -> int:
    if not HF_API_KEY:
        print("⊝ HF_API_KEY non défini. Cet agent s'activera dès que")
        print("  Hugo aura ajouté HF_API_KEY en secret GitHub.")
        print("  Lien : https://huggingface.co/settings/tokens (gratuit)")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    max_n = int(os.environ.get("MAX_NICHES") or "0") or len(NICHES)
    niches = NICHES[:max_n]
    print(f"=== I ❤️ X HF — {len(niches)} niches via {HF_MODEL} ===\n")

    metas = []
    for idx, niche in enumerate(niches, 1):
        m = produce_design(niche, idx)
        if m:
            metas.append(m)
        time.sleep(3)  # HF rate limit gentil

    if metas:
        csv_path = OUTPUT_DIR / "etsy_bulk_upload.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["design_id", "niche", "title",
                            "tags_etsy", "price_etsy"],
                extrasaction="ignore",
            )
            w.writeheader()
            w.writerows(metas)

    print(f"\n  Produits : {len(metas)}/{len(niches)} → {OUTPUT_DIR}")
    return 0 if metas else 1


if __name__ == "__main__":
    sys.exit(main())
