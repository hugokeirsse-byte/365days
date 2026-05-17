"""
Pipeline COPE — Create Once, Distribute Everywhere.

Pour chaque NICHE :
1. Pollinations Flux génère N designs en source PNG haute-déf
2. Pillow découpe chaque design en plusieurs formats multi-plateformes :
   - Source 2048×2048 (archive maître)
   - Pinterest pin 1000×1500 (2:3)
   - Etsy preview 2000×2500 (4:5)
   - Society6 / Displate 3000×4000 (3:4)
   - Wallpaper 1920×1080
3. Gemini ou template génère les métadonnées SEO par plateforme
   (titre, description, tags Etsy 13, tags Redbubble 15)
4. Output organisé : products/<niche>/design_<NN>/<formats>
5. CSV bulk upload pré-rempli pour Etsy (et Redbubble en variante)

Pas de stickers transparents en v1 (demande rembg + onnxruntime, 300 MB).
Pas de mockups produits physiques en v1 (demande templates PNG dédiés).
À ajouter en v2 quand v1 sera validée.

Usage :
    SOURCE_NICHE=witchy_cottagecore python scripts/produce_cope_pack.py

Ou via workflow GitHub Actions déclenché par .triggers/cope_pack.
"""

import csv
import json
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERREUR : Pillow non installé. pip install Pillow")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products"
USER_AGENT = "CopeProducer/1.0 (+github actions)"
TIMEOUT = 180

# ─────────────────────────────────────────────────────────────────────
# FORMATS DE SORTIE (1 image source → N déclinaisons)
# ─────────────────────────────────────────────────────────────────────

FORMATS = [
    {"name": "source",          "size": (2048, 2048), "ext": "png", "fit": "cover"},
    {"name": "pinterest_pin",   "size": (1000, 1500), "ext": "jpg", "fit": "cover"},
    {"name": "pinterest_idea",  "size": (1080, 1920), "ext": "jpg", "fit": "cover"},
    {"name": "etsy_preview",    "size": (2000, 2500), "ext": "jpg", "fit": "cover"},
    {"name": "society6_poster", "size": (3000, 4000), "ext": "jpg", "fit": "cover"},
    {"name": "wallpaper_hd",    "size": (1920, 1080), "ext": "jpg", "fit": "cover"},
]

# ─────────────────────────────────────────────────────────────────────
# NICHES INITIALES (5 niches à fort ROI / faible saturation 2026)
# ─────────────────────────────────────────────────────────────────────

NICHES = {
    "witchy_cottagecore": {
        "title_template": "Witchy Cottagecore {subject} — Digital Print Wall Art",
        "description": (
            "Adorable witchy cottagecore digital print perfect for your dark "
            "academia, gothic cottage, or autumn aesthetic decor. Instant "
            "digital download — print at home or at a local shop.\n\n"
            "✦ High-resolution files included\n"
            "✦ Multiple sizes for Pinterest, Etsy listing, Society6, posters\n"
            "✦ Personal use included (small commercial OK up to 100 items)\n"
            "✦ Instant download\n\n"
            "Perfect for: kitchen decor, cozy reading nook, autumn vibes, "
            "halloween mood, witchy aesthetic, dark cottagecore, fall."
        ),
        "tags_etsy": [
            "witchy decor", "cottagecore print", "dark academia",
            "gothic wall art", "halloween art", "autumn aesthetic",
            "witchy aesthetic", "moon print", "occult art",
            "moody decor", "fall decor", "spell book art", "magical",
        ],
        "tags_redbubble": [
            "witchy", "cottagecore", "dark academia", "gothic", "halloween",
            "autumn", "moon", "occult", "witch", "spells", "mushrooms",
            "ravens", "tarot", "potions", "witchcraft",
        ],
        "price_etsy_digital": 4.99,
        "price_etsy_pod_mug": 22.99,
        "price_etsy_pod_tshirt": 24.99,
        "design_prompts": [
            "vintage witch's cauldron with bubbling potion, mushrooms and herbs around, moody autumn forest background, dark academia color palette of deep green, burgundy and gold, illustration style watercolor and ink, atmospheric and cozy, soft warm lighting",
            "open spellbook with pressed flowers, dripping candle, raven feather and crystal, dark wood table, moody library setting, dark academia aesthetic, warm amber light, watercolor illustration style",
            "cozy witch's cottage in misty autumn forest, smoke rising from chimney, glowing window with warm light, pumpkins and lanterns by the door, deep teal and burnt orange palette, illustration",
            "moon phases with botanical illustrations of medicinal herbs around each phase, vintage scientific style on parchment, gold and deep green, ornate decorative",
            "raven perched on a stack of ancient leather books with a brass key and candle, gothic library setting, dark moody atmosphere, warm candlelight, watercolor and ink illustration",
            "vintage tarot card style illustration of the moon, with wolves howling and a winding path, deep midnight blue and gold, ornate borders, art nouveau influence",
            "cozy witch's kitchen with jars of herbs and potions, dried flowers hanging from ceiling, copper cauldron on stove, autumn light through window, warm cottagecore illustration",
            "old apothecary cabinet with labeled potion bottles, dried plants, ravens, and skulls, dark academia mood, warm lamp light, detailed illustration",
            "mystical mushroom forest with glowing fairy lights, witch's cottage in distance, dark magical atmosphere, deep purple and gold, watercolor illustration",
            "vintage scientific botanical illustration of poisonous plants like belladonna and mandrake, on aged parchment with handwritten labels, sepia and dark green",
            "moon goddess in vintage illustration style, surrounded by stars and crescent moons, gold ornaments, deep midnight blue, art nouveau decorative borders",
            "witch's familiar black cat sleeping on a stack of grimoires, candle flame flickering, magical sparks in the air, cozy moody atmosphere, warm illustration",
            "vintage hand drawn tarot deck spread on dark velvet, candle flame, crystal ball, ornate decorative style, deep burgundy and gold",
            "autumn forest at twilight with floating lanterns, mushrooms glowing on tree trunks, mystical atmosphere, deep teal and amber palette, illustration",
            "vintage illustration of a witch flying on a broomstick across a full moon, silhouettes of trees, owls, and bats, gothic atmosphere, deep blue and black",
            "magical herbarium page with pressed flowers, latin names, ink illustrations of mushrooms and herbs, parchment background, dark academia style",
            "cottagecore tea ceremony with vintage teapot, dried herbs, open spellbook, autumn leaves, warm cozy atmosphere, watercolor illustration",
            "vintage zodiac wheel illustration with botanical elements, deep midnight blue background, gold details, ornate art nouveau style",
            "witch's altar with crystals, candles, dried herbs, animal skull, vintage photographs, moody atmosphere, dark academia, warm candlelight, illustration",
            "magical forest path leading to glowing cottage in distance, full moon overhead, fireflies, mystical autumn atmosphere, deep teal and amber, illustration",
        ],
    },
    "funny_coffee_quotes": {
        "title_template": "Funny Coffee Quote {subject} Mug — Digital Print",
        "description": (
            "Hilarious coffee quote design perfect for caffeine lovers, office "
            "humor, mom life, or anyone surviving on coffee. Available as "
            "digital print + ready for mug and t-shirt printing.\n\n"
            "✦ Multiple format included\n"
            "✦ Print at home or send to print shop\n"
            "✦ Personal use and small commercial OK"
        ),
        "tags_etsy": [
            "coffee mug design", "funny coffee quote", "caffeine lover",
            "office humor", "mom needs coffee", "coffee addict",
            "coffee printable", "monday motivation", "coffee t-shirt",
            "barista gift", "coffee lover gift", "kitchen wall art",
            "coffee humor",
        ],
        "tags_redbubble": [
            "coffee", "funny", "humor", "caffeine", "mom life", "office",
            "monday", "morning person", "espresso", "barista", "coffee shop",
            "tired", "introvert", "coffee addict", "but first coffee",
        ],
        "price_etsy_digital": 3.99,
        "price_etsy_pod_mug": 19.99,
        "price_etsy_pod_tshirt": 22.99,
        "design_prompts": [
            "vintage typography illustration with the phrase 'But First Coffee' in elegant hand-lettered serif on parchment background, coffee bean and steam decorative elements, warm sepia tones, art deco style",
            "minimalist line drawing of a coffee cup with steam forming the word 'Survive', black on cream background, hand-drawn style, modern minimalist",
            "vintage typography design 'Coffee is My Love Language' in flowing script, watercolor coffee splash background, warm browns and creams, romantic illustration",
            "retro 70s style design with bold lettering 'Powered By Coffee', coffee beans floating around, mustard yellow and brown palette, vintage funky",
            "minimalist black line illustration of stick figure pouring coffee into eye, caption 'Morning Self-Care', humorous, white background",
            "vintage tin sign style 'Coffee Before Talkie', distressed look, red and cream colors, retro Americana style illustration",
            "watercolor coffee cup with phrase 'Espresso Yourself' in playful lettering, splash of brown watercolor, art deco style",
            "minimalist typography 'I Bean Thinking About You' with coffee bean illustration, black on cream, modern hand-lettered style",
            "retro pin-up style illustration of woman drinking coffee with sunglasses, caption 'Don't Talk To Me Yet', vintage 50s aesthetic, warm colors",
            "calligraphy script 'Decaf Is Just Sad Coffee' with elegant flourishes on aged paper, sepia tones, vintage handwritten style",
            "minimalist illustration of a brain made of coffee beans, caption 'Coffee Goes Here', neuroscience-inspired humor, black on cream",
            "vintage coffee shop sign 'World's Okayest Barista' with art nouveau decorative border, warm earthy tones, hand-painted style",
            "retro 80s neon style typography 'Caffeine Queen' with stars and coffee cup, pink and purple neon glow, vintage 80s aesthetic",
            "minimalist black silhouette of coffee cup with steam spelling 'Help', dark humor design, white background, modern illustration",
            "elegant calligraphy 'Life Begins After Coffee' on watercolor coffee stain background, warm browns and creams, romantic vintage style",
            "vintage Americana diner style 'Pour Decisions Were Made' with coffee cup tilting, red and cream retro palette, hand-painted look",
            "minimalist line art of stick figure marathon running with coffee IV drip, caption 'Endurance Athlete', funny modern illustration",
            "watercolor splash design with hand-lettered 'Bean Counter' joke for accountants, coffee bean motif, warm sepia, vintage style",
            "retro typography 'Espresso Patronum' with magical wand made of coffee beans, gold and brown palette, Harry Potter reference vintage style",
            "minimalist black hand-drawn 'Mom Fuel' with coffee cup featuring tiny crown, white background, humor mom design",
        ],
    },
    "mountain_adventure_aesthetic": {
        "title_template": "Mountain Adventure {subject} — Nature Wall Art Print",
        "description": (
            "Stunning mountain landscape print for outdoor lovers, hikers, "
            "and adventurers. Perfect for cabin decor, office wall, gift "
            "for travelers and nature enthusiasts.\n\n"
            "✦ High-resolution files\n"
            "✦ Multiple sizes for Pinterest, Etsy, posters\n"
            "✦ Personal and small commercial use included"
        ),
        "tags_etsy": [
            "mountain wall art", "adventure print", "hiking poster",
            "national park art", "cabin decor", "outdoor lover gift",
            "wanderlust print", "explore more", "nature wall art",
            "minimalist mountain", "travel poster", "rocky mountains",
            "pine tree art",
        ],
        "tags_redbubble": [
            "mountain", "adventure", "hiking", "outdoor", "nature",
            "wanderlust", "explore", "camping", "national park",
            "rocky mountains", "pine trees", "wilderness", "trekking",
            "scenic", "landscape",
        ],
        "price_etsy_digital": 4.99,
        "price_etsy_pod_mug": 21.99,
        "price_etsy_pod_tshirt": 23.99,
        "design_prompts": [
            "minimalist illustration of mountain range silhouette in three layers, deep teal, sage green and dusty rose palette, simple geometric style, modern wall art",
            "vintage national park style poster of pine forest with cabin and rising sun, warm orange and brown tones, art deco WPA style illustration",
            "watercolor landscape of misty mountains at sunrise with pine trees, soft purple and orange palette, dreamy atmospheric illustration",
            "minimalist line art of mountain peaks with crescent moon overhead, single weight black lines on cream background, modern Scandinavian style",
            "vintage explorer style illustration of mountain range with vintage compass overlay, sepia tones, parchment background, adventure aesthetic",
            "geometric polygon style mountain landscape, low poly illustration in cool blues and purples, modern art style",
            "minimalist boho style mountain with sun setting behind, terracotta and cream palette, simple shapes, modern wall art",
            "vintage WPA national park poster style of geyser erupting at sunset, mountain backdrop, warm earthy tones, art deco illustration",
            "watercolor of canoe on misty mountain lake at dawn, soft pastels of pink and blue, peaceful atmospheric illustration",
            "minimalist mountain landscape with full moon and pine trees silhouettes, navy and gold palette, modern celestial style",
            "vintage adventure poster of cabin in pine forest with smoke from chimney, autumn leaves, warm earth tones, retro park style",
            "watercolor mountain peaks at golden hour with eagle soaring, warm oranges and purples, dramatic atmospheric illustration",
            "minimalist illustration of camping tent under starry sky with mountain silhouettes, navy background with white stars, modern simple style",
            "vintage railway poster style of train approaching snowy mountains, art deco illustration in jewel tones, retro travel poster",
            "boho mountain landscape with sun and moon, terracotta cream and dusty pink palette, minimalist celestial style, modern wall art",
            "watercolor of wolf howling on mountain ridge silhouette with full moon, deep blue and silver palette, atmospheric illustration",
            "vintage map style illustration of mountain range with topographic lines, compass rose, sepia tones, explorer aesthetic",
            "minimalist three mountain peaks with rising sun rays, monochrome black on cream, modern Japanese-inspired style",
            "watercolor landscape of forest path through pine trees toward mountain, soft greens and blues, peaceful illustration",
            "vintage hiking badge style illustration with mountain logo and circular border, warm earth tones, retro outdoor aesthetic",
        ],
    },
    "pet_mom_aesthetic": {
        "title_template": "{subject} — Pet Mom Cute Design",
        "description": (
            "Adorable pet design perfect for proud pet parents. Great for "
            "mugs, t-shirts, totebags, and home decor. The perfect gift for "
            "anyone who loves their fur baby more than people.\n\n"
            "✦ High-resolution download\n"
            "✦ Personal and small commercial use\n"
            "✦ Instant download"
        ),
        "tags_etsy": [
            "cat mom shirt", "dog mom gift", "pet lover decor",
            "fur mama", "cat lady gift", "dog dad",
            "pet portrait style", "rescue mom", "cat shirt",
            "dog shirt", "pet mug", "cat wall art",
            "dog wall art",
        ],
        "tags_redbubble": [
            "cat mom", "dog mom", "pet mom", "fur mama", "cat lady",
            "dog dad", "rescue", "adopt don't shop", "cat lover",
            "dog lover", "kitten", "puppy", "golden retriever",
            "black cat", "labrador",
        ],
        "price_etsy_digital": 3.99,
        "price_etsy_pod_mug": 19.99,
        "price_etsy_pod_tshirt": 22.99,
        "design_prompts": [
            "cute illustration of a black cat sitting with witch hat, surrounded by stars and moons, watercolor style, deep purple and gold palette, kawaii aesthetic",
            "minimalist line drawing of golden retriever face with closed eyes happy smile, simple black on cream background, modern pet portrait",
            "watercolor portrait of orange tabby cat with daisy crown, soft pastel palette of pink and yellow, kawaii style illustration",
            "vintage tattoo style illustration of dachshund with banner saying 'Mom', traditional Americana tattoo aesthetic, bold lines and color",
            "minimalist illustration of cat silhouette made of plant leaves and flowers, botanical style, sage green palette, modern art",
            "watercolor portrait of cute corgi puppy with party hat, pastel palette, kawaii birthday illustration style",
            "vintage anatomy poster style of cat with labeled body parts in funny way, parchment background, sepia tones, scientific humor",
            "minimalist line art of dog and human hand meeting, simple black on cream, emotional modern illustration",
            "cute kawaii illustration of black cat surrounded by witchy items like crystals and tarot cards, moody purple palette, mystical pet design",
            "watercolor of golden retriever holding a flower in mouth, soft pastels, romantic illustration style",
            "vintage breed standard poster of german shepherd with elegant typography, sepia and beige palette, classic dog show aesthetic",
            "minimalist geometric illustration of cat face made of triangles and circles, monochrome modern art style on cream",
            "kawaii style illustration of three small dogs (pug, dachshund, chihuahua) in a row, watercolor pastels, cute pet portrait",
            "vintage scientific botanical style portrait of cat with herbs and plants around, parchment, sepia and green palette, apothecary aesthetic",
            "watercolor portrait of black labrador with autumn leaves, warm orange and brown palette, cozy fall pet illustration",
            "minimalist Scandinavian style illustration of cat sleeping in cozy chair with blanket, simple shapes, hygge aesthetic",
            "vintage circus poster style of dog jumping through hoop with elegant typography, bold colors of red and gold, retro aesthetic",
            "cute kawaii illustration of pug with crown and royal robe, watercolor pastels, funny royalty pet illustration",
            "minimalist line art portrait of cat with single weight black lines, modern simple pet portrait style on cream",
            "watercolor of cat curled up with book and tea, cozy reading aesthetic, warm browns and creams, kawaii illustration",
        ],
    },
    "faith_christian_aesthetic": {
        "title_template": "{subject} — Christian Faith Wall Art Print",
        "description": (
            "Beautiful faith-inspired wall art and apparel design. Perfect "
            "for Sunday school teachers, Bible study groups, church members, "
            "and anyone wanting to share their faith.\n\n"
            "✦ Multiple sizes included\n"
            "✦ Personal and small commercial use\n"
            "✦ Instant download"
        ),
        "tags_etsy": [
            "christian wall art", "faith print", "bible verse art",
            "sunday school gift", "christian decor", "scripture art",
            "jesus loves you", "blessed mama", "church gift",
            "faith over fear", "psalm print", "proverbs art",
            "religious decor",
        ],
        "tags_redbubble": [
            "christian", "faith", "bible verse", "scripture", "jesus",
            "blessed", "religious", "prayer", "amen", "hallelujah",
            "psalm", "proverbs", "god is good", "faith over fear",
            "trust god",
        ],
        "price_etsy_digital": 4.99,
        "price_etsy_pod_mug": 19.99,
        "price_etsy_pod_tshirt": 22.99,
        "design_prompts": [
            "vintage hand-lettered calligraphy of Psalm 23 verse on aged parchment background, sepia and gold palette, elegant script style",
            "watercolor cross with botanical elements like olive branches and wildflowers, soft pastels of cream and sage, peaceful illustration",
            "minimalist line art of praying hands with subtle dove and rays of light, single weight black lines on cream, modern faith design",
            "vintage stained glass window style illustration of cross with sun rays, jewel tones of blue and gold, ornate religious art",
            "elegant calligraphy 'Faith Over Fear' on watercolor mountain landscape background, dusty rose and sage palette, inspirational design",
            "watercolor of dove with olive branch in flight, soft cream and gold palette, peace symbol Christian illustration",
            "minimalist illustration of cross made of olive branches with subtle leaves, sage green on cream background, modern faith decor",
            "vintage hymnal style typography 'Amazing Grace' with art nouveau decorative borders, sepia and gold palette",
            "watercolor of open Bible with cross bookmark and warm light beams, soft cream and gold, devotional aesthetic illustration",
            "minimalist Scandinavian style illustration of mountain with cross at summit, warm earthy tones, modern faith design",
            "vintage cross-stitch style sampler with bible verse Proverbs 31, traditional folk art aesthetic, cream and rose palette",
            "watercolor floral wreath surrounding the words 'Be Still' Psalm 46:10, soft pastels of peach and sage, peaceful inspirational design",
            "minimalist black line drawing of dove with cross subtly hidden in wings, modern simple Christian art on cream",
            "vintage chalk lettering 'God is Good' on dark slate background with subtle floral border, hand-painted style",
            "watercolor sunrise over mountain landscape with cross silhouette, warm orange and pink palette, inspirational morning illustration",
            "minimalist illustration of two hands open in prayer with subtle gold rays, neutral palette, modern devotional art",
            "vintage scientific botanical illustration style of olive branch with biblical reference, sepia and green palette, classic devotional aesthetic",
            "elegant calligraphy 'She Is Clothed In Strength And Dignity' Proverbs 31 on watercolor floral background, dusty rose palette, feminine inspirational design",
            "watercolor landscape of cross on hill with rays of light breaking through clouds, dramatic warm palette, easter aesthetic",
            "minimalist line art of cross with subtle vine and grapes growing around, modern Mediterranean Christian decor style",
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────────────────────────────


def pollinations_url(prompt: str, seed: int, size: int = 2048) -> str:
    encoded = urllib.parse.quote(prompt, safe="")
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?model=flux&width={size}&height={size}"
        f"&seed={seed}&nologo=true&private=true&enhance=true"
    )


def http_get(url: str, dest: Path, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read()
            if len(data) < 5000:
                raise ValueError(f"réponse trop courte ({len(data)} bytes)")
            dest.write_bytes(data)
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"    ↻ retry {attempt + 1}/{retries} : {exc}")
            time.sleep(8 + attempt * 8)
    return False


def fit_image(src: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Recadre et redimensionne en mode 'cover' (couvre tout, peut rogner)."""
    src_ratio = src.width / src.height
    target_ratio = target_w / target_h
    if src_ratio > target_ratio:
        # Source plus large : on coupe sur les côtés
        new_w = int(src.height * target_ratio)
        offset = (src.width - new_w) // 2
        src = src.crop((offset, 0, offset + new_w, src.height))
    elif src_ratio < target_ratio:
        # Source plus haute : on coupe en haut/bas
        new_h = int(src.width / target_ratio)
        offset = (src.height - new_h) // 2
        src = src.crop((0, offset, src.width, offset + new_h))
    return src.resize((target_w, target_h), Image.LANCZOS)


def slugify(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    s = re.sub(r"[\s_-]+", "_", s)
    return s[:max_len] or "design"


def short_subject(prompt: str) -> str:
    """Extrait un sujet court du prompt (pour titres)."""
    words = re.findall(r"\b[a-z]{4,}\b", prompt.lower())
    keepers = [w for w in words if w not in {
        "with", "from", "into", "this", "that", "their", "these", "those",
        "style", "color", "palette", "background", "illustration", "vintage",
        "watercolor", "minimalist", "modern", "design", "warm", "deep",
    }][:3]
    return " ".join(w.capitalize() for w in keepers) or "Design"


# ─────────────────────────────────────────────────────────────────────
# CŒUR DU PIPELINE
# ─────────────────────────────────────────────────────────────────────


def produce_design(niche_key: str, niche: dict, idx: int, prompt: str) -> dict | None:
    """Génère 1 design + toutes ses déclinaisons + métadonnées."""
    design_dir = OUTPUT_DIR / niche_key / f"design_{idx:02d}"
    design_dir.mkdir(parents=True, exist_ok=True)

    raw_path = design_dir / "raw.png"
    seed = idx * 10000 + random.randint(0, 9999)

    # 1. Génération
    print(f"  [{idx:>2}] {prompt[:70]}…")
    if not http_get(pollinations_url(prompt, seed, size=2048), raw_path):
        print(f"        ✗ génération Pollinations échouée")
        return None

    # 2. Déclinaisons
    try:
        src = Image.open(raw_path).convert("RGB")
    except Exception as exc:  # noqa: BLE001
        print(f"        ✗ image illisible : {exc}")
        return None

    for fmt in FORMATS:
        out = design_dir / f"{fmt['name']}.{fmt['ext']}"
        cropped = fit_image(src, *fmt["size"])
        if fmt["ext"] == "jpg":
            cropped.save(out, "JPEG", quality=90, optimize=True)
        else:
            cropped.save(out, "PNG", optimize=True)

    raw_path.unlink()  # cleanup

    # 3. Métadonnées
    subject = short_subject(prompt)
    title = niche["title_template"].format(subject=subject)
    metadata = {
        "design_id": f"{niche_key}_{idx:02d}",
        "title": title[:140],
        "title_short": title[:70],
        "description": niche["description"],
        "tags_etsy": ", ".join(niche["tags_etsy"][:13]),
        "tags_redbubble": ", ".join(niche["tags_redbubble"][:15]),
        "price_etsy_digital": niche["price_etsy_digital"],
        "price_etsy_pod_mug": niche["price_etsy_pod_mug"],
        "price_etsy_pod_tshirt": niche["price_etsy_pod_tshirt"],
        "prompt_used": prompt,
        "seed": seed,
        "pinterest_pin_description": (
            f"{subject} • {niche_key.replace('_', ' ').title()} • "
            f"Get the digital download or printed product on Etsy. "
            f"Perfect for {niche['tags_etsy'][0]}, {niche['tags_etsy'][1]}."
        )[:500],
    }
    (design_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    print(f"        ✓ {len(FORMATS)} formats produits")
    return metadata


def produce_niche(niche_key: str, niche: dict, max_designs: int | None = None) -> int:
    print(f"\n=== NICHE : {niche_key} ===")
    prompts = niche["design_prompts"]
    if max_designs:
        prompts = prompts[:max_designs]
    print(f"À produire : {len(prompts)} designs × {len(FORMATS)} formats\n")

    metas = []
    for i, prompt in enumerate(prompts, 1):
        meta = produce_design(niche_key, niche, i, prompt)
        if meta:
            metas.append(meta)
        time.sleep(2)

    # CSV bulk-upload Etsy
    csv_path = OUTPUT_DIR / niche_key / "etsy_bulk_upload.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["design_id", "title", "title_short", "description",
                        "tags_etsy", "tags_redbubble",
                        "price_etsy_digital", "price_etsy_pod_mug",
                        "price_etsy_pod_tshirt",
                        "pinterest_pin_description"],
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(metas)

    print(f"\n  → {len(metas)}/{len(prompts)} designs produits, CSV : {csv_path}")
    return len(metas)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    target_niche = os.environ.get("SOURCE_NICHE", "").strip()
    max_designs = int(os.environ.get("MAX_DESIGNS") or "0") or None

    if target_niche:
        if target_niche not in NICHES:
            print(f"NICHE inconnue : {target_niche}. Choix : {list(NICHES)}")
            return 2
        produce_niche(target_niche, NICHES[target_niche], max_designs)
    else:
        for key, niche in NICHES.items():
            produce_niche(key, niche, max_designs)

    print(f"\n{'=' * 60}\nProduction terminée. Output : {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
