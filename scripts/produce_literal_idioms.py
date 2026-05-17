"""
Pipeline LITERAL IDIOMS — humour visuel des expressions traduites mot-à-mot.

Angle de niche méconnu mais ultra viral : prendre des expressions
idiomatiques étrangères, les traduire LITTÉRALEMENT en anglais, et
illustrer la scène absurde qui en résulte. Le résultat est drôle,
décalé, partageable.

Exemples :
- 🇩🇪 "Ich verstehe nur Bahnhof" → "I only understand train station"
- 🇫🇷 "Avoir la moutarde qui monte au nez" → "To have mustard rising to your nose"
- 🇯🇵 "Neko ni koban" → "A gold coin to a cat"
- 🇮🇹 "In bocca al lupo" → "Into the mouth of the wolf"
- 🇪🇸 "Tomar el pelo" → "To take the hair"

Public cible : language learners (Reddit r/languagelearning 4M users),
linguistique TikTok, polyglottes, profs de langues, expats.

Pour chaque idiome : illustration littérale + plaque typo avec
original + traduction littérale + sens réel.

Variables d'env :
  MAX_IDIOMS=10   limite à N idiomes
"""

import csv
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERREUR : Pillow non installé")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "literal_idioms"
USER_AGENT = "LiteralIdiomsProducer/1.0"
TIMEOUT = 180

# 30 idiomes scéniques avec traduction littérale (potentiel viral max)
IDIOMS = [
    # 🇩🇪 Allemand
    {"original": "Ich verstehe nur Bahnhof", "lang": "german", "flag": "🇩🇪",
     "literal": "I only understand train station", "meaning": "I don't understand anything",
     "scene": "confused person standing in busy train station with question marks floating around their head, vintage train station with steam and crowds, watercolor illustration, humorous tone"},
    {"original": "Tomaten auf den Augen haben", "lang": "german", "flag": "🇩🇪",
     "literal": "To have tomatoes on your eyes", "meaning": "To be oblivious to what's happening",
     "scene": "person walking with two big red tomatoes over their eyes like glasses, watercolor whimsical illustration, soft background"},
    {"original": "Da steppt der Bär", "lang": "german", "flag": "🇩🇪",
     "literal": "The bear is dancing there", "meaning": "It's a great party",
     "scene": "happy brown bear dancing with disco ball at lively party, watercolor playful illustration"},
    # 🇫🇷 Français
    {"original": "Avoir le cafard", "lang": "french", "flag": "🇫🇷",
     "literal": "To have the cockroach", "meaning": "To feel blue / depressed",
     "scene": "melancholic person sitting on bench with a tiny grey cockroach companion, rainy Paris background, watercolor illustration, gentle humor"},
    {"original": "Poser un lapin à quelqu'un", "lang": "french", "flag": "🇫🇷",
     "literal": "To put a rabbit on someone", "meaning": "To stand someone up on a date",
     "scene": "person waiting alone at café table with a confused white rabbit sitting in the empty chair across, Parisian café watercolor, soft humor"},
    {"original": "Avoir les yeux plus gros que le ventre", "lang": "french", "flag": "🇫🇷",
     "literal": "To have eyes bigger than the belly", "meaning": "To take more food than you can eat",
     "scene": "small character with huge cartoonish eyes staring at giant feast, watercolor whimsy"},
    {"original": "Donner sa langue au chat", "lang": "french", "flag": "🇫🇷",
     "literal": "To give your tongue to the cat", "meaning": "To give up on guessing",
     "scene": "small cat holding a human tongue in its paws looking proud, soft watercolor illustration"},
    # 🇯🇵 Japonais
    {"original": "Neko ni koban", "lang": "japanese", "flag": "🇯🇵",
     "literal": "A gold coin to a cat", "meaning": "Wasting something valuable on someone who can't appreciate it",
     "scene": "cute cat looking unimpressed at golden Japanese coin, vintage japanese ukiyo-e style with modern softness"},
    {"original": "Saru mo ki kara ochiru", "lang": "japanese", "flag": "🇯🇵",
     "literal": "Even monkeys fall from trees", "meaning": "Even experts make mistakes",
     "scene": "embarrassed monkey falling from cherry blossom tree, Japanese watercolor, gentle humor"},
    {"original": "Hara ga tatsu", "lang": "japanese", "flag": "🇯🇵",
     "literal": "My stomach is standing up", "meaning": "I'm angry",
     "scene": "person with their visible cartoon stomach literally standing up out of their belly looking angry, watercolor humor"},
    # 🇮🇹 Italien
    {"original": "In bocca al lupo", "lang": "italian", "flag": "🇮🇹",
     "literal": "Into the mouth of the wolf", "meaning": "Good luck!",
     "scene": "small character cheerfully walking into a giant friendly wolf's open mouth, Italian watercolor, theatrical"},
    {"original": "Non tutte le ciambelle escono col buco", "lang": "italian", "flag": "🇮🇹",
     "literal": "Not all donuts come out with a hole", "meaning": "Not everything turns out as planned",
     "scene": "Italian bakery scene with various donuts some without holes, watercolor illustration"},
    {"original": "Avere le mani in pasta", "lang": "italian", "flag": "🇮🇹",
     "literal": "To have hands in the dough", "meaning": "To be involved in many things",
     "scene": "Italian nonna with hands plunged in giant pasta dough, warm watercolor"},
    # 🇪🇸 Espagnol
    {"original": "Tomar el pelo", "lang": "spanish", "flag": "🇪🇸",
     "literal": "To take the hair", "meaning": "To pull someone's leg / tease",
     "scene": "playful character running away holding a long lock of hair, watercolor Spanish illustration with humor"},
    {"original": "Ser pan comido", "lang": "spanish", "flag": "🇪🇸",
     "literal": "To be eaten bread", "meaning": "Easy as pie",
     "scene": "happy character casually munching a piece of bread, Spanish cafe watercolor"},
    {"original": "No tener pelos en la lengua", "lang": "spanish", "flag": "🇪🇸",
     "literal": "To have no hairs on the tongue", "meaning": "To speak frankly",
     "scene": "person looking surprised at perfectly smooth tongue in mirror, watercolor humor"},
    # 🇵🇹 Portugais
    {"original": "Pagar o pato", "lang": "portuguese", "flag": "🇵🇹",
     "literal": "To pay the duck", "meaning": "To take the blame for something you didn't do",
     "scene": "person at cash register trying to pay with a live duck looking grumpy, watercolor humor"},
    {"original": "Engolir sapos", "lang": "portuguese", "flag": "🇵🇹",
     "literal": "To swallow frogs", "meaning": "To endure unpleasant situations",
     "scene": "person reluctantly about to swallow a small green frog, watercolor whimsy with sympathetic tone"},
    # 🇳🇱 Néerlandais
    {"original": "Een aap uit de mouw schudden", "lang": "dutch", "flag": "🇳🇱",
     "literal": "To shake a monkey out of the sleeve", "meaning": "To reveal a secret",
     "scene": "person shaking jacket sleeve with surprised monkey falling out, watercolor humor"},
    {"original": "Iets onder de knie hebben", "lang": "dutch", "flag": "🇳🇱",
     "literal": "To have something under the knee", "meaning": "To master something",
     "scene": "confident character with small object held under their knee, watercolor illustration"},
    # 🇸🇪 Suédois
    {"original": "Att glida på en räkmacka", "lang": "swedish", "flag": "🇸🇪",
     "literal": "To slide on a shrimp sandwich", "meaning": "To get an easy ride in life",
     "scene": "person surfing on a giant shrimp sandwich smiling, Nordic watercolor humor"},
    # 🇷🇺 Russe
    {"original": "Vешать лапшу на уши", "lang": "russian", "flag": "🇷🇺",
     "literal": "To hang noodles on someone's ears", "meaning": "To deceive someone",
     "scene": "person with strands of pasta noodles draped over their ears looking suspicious, watercolor humor"},
    {"original": "Когда рак на горе свистнет", "lang": "russian", "flag": "🇷🇺",
     "literal": "When the crayfish whistles on the mountain", "meaning": "Never going to happen",
     "scene": "tiny crayfish standing on top of mountain attempting to whistle, watercolor whimsy"},
    # 🇨🇳 Chinois
    {"original": "马马虎虎", "lang": "chinese", "flag": "🇨🇳",
     "literal": "Horse horse tiger tiger", "meaning": "So-so / mediocre",
     "scene": "stylized illustration with two horses and two tigers in zen pose, Chinese ink wash style"},
    # 🇰🇷 Coréen
    {"original": "그림의 떡", "lang": "korean", "flag": "🇰🇷",
     "literal": "Rice cake in a painting", "meaning": "Something unattainable",
     "scene": "person reaching toward painting of rice cake on wall, traditional Korean watercolor"},
    # 🇮🇳 Hindi
    {"original": "नौ दो ग्यारह होना", "lang": "hindi", "flag": "🇮🇳",
     "literal": "To become nine-two-eleven", "meaning": "To run away quickly",
     "scene": "character sprinting away with numbers 9, 2, 11 floating behind, watercolor humor"},
    # 🇫🇮 Finlandais
    {"original": "Olla kuin myyrä auringonpaisteessa", "lang": "finnish", "flag": "🇫🇮",
     "literal": "To be like a mole in sunshine", "meaning": "To feel out of place",
     "scene": "small confused mole squinting in bright sun on green grass, watercolor humor"},
    # 🇵🇱 Polonais
    {"original": "Bułka z masłem", "lang": "polish", "flag": "🇵🇱",
     "literal": "A bread roll with butter", "meaning": "Easy peasy",
     "scene": "smiling character holding simple buttered bread roll victoriously, watercolor"},
    # 🇹🇷 Turc
    {"original": "Etekleri zil çalmak", "lang": "turkish", "flag": "🇹🇷",
     "literal": "Their skirts are ringing bells", "meaning": "To be extremely happy",
     "scene": "person dancing with skirts twirling and tiny bells ringing around them, watercolor joy"},
    # 🇬🇷 Grec
    {"original": "Σιγά τον πολυέλαιο", "lang": "greek", "flag": "🇬🇷",
     "literal": "Slow down the chandelier", "meaning": "Big deal / It's not that important",
     "scene": "person dramatically gesturing 'slow down' at giant ornate chandelier, watercolor humor"},
]


def pollinations_url(prompt: str, seed: int, width: int = 1536, height: int = 1536) -> str:
    encoded = urllib.parse.quote(prompt, safe="")
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?model=flux&width={width}&height={height}"
        f"&seed={seed}&nologo=true&private=true&enhance=true"
    )


def http_get(url: str, dest: Path, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read()
            if len(data) < 5000:
                raise ValueError(f"too short {len(data)}")
            dest.write_bytes(data)
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"    retry {attempt + 1}/{retries} : {exc}")
            time.sleep(6 + attempt * 6)
    return False


def slugify(text: str) -> str:
    import re
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:50]


def make_outputs(raw: Path, design_dir: Path) -> None:
    img = Image.open(raw).convert("RGB")
    side = min(img.width, img.height)
    off_x = (img.width - side) // 2
    off_y = (img.height - side) // 2
    sq = img.crop((off_x, off_y, off_x + side, off_y + side))
    sq.resize((1080, 1080), Image.LANCZOS).save(
        design_dir / "etsy_preview.jpg", "JPEG", quality=92)
    sq.resize((3000, 3000), Image.LANCZOS).save(
        design_dir / "print_3000.png", "PNG", optimize=True)


def produce_design(idiom: dict, idx: int) -> dict | None:
    prompt = (
        f"editorial illustration poster with two zones: top 70% shows "
        f"{idiom['scene']}, bottom 30% has clean typography with original "
        f"phrase '{idiom['original']}' in bold serif then below smaller italic "
        f"text 'literally: {idiom['literal']}' then in smallest text 'meaning: "
        f"{idiom['meaning']}', vintage editorial design, soft cream paper "
        f"background, museum poster quality, no signature no watermark"
    )
    word_slug = slugify(idiom["literal"])
    design_dir = OUTPUT_DIR / idiom["lang"] / word_slug
    design_dir.mkdir(parents=True, exist_ok=True)
    raw = design_dir / "raw.png"
    seed = idx * 10013 + random.randint(0, 9999)
    url = pollinations_url(prompt, seed)

    print(f"  [{idx:>3}] {idiom['flag']} « {idiom['literal']} »")
    if not http_get(url, raw):
        print(f"        echec Pollinations")
        return None

    try:
        make_outputs(raw, design_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"        traitement echoue : {exc}")
        return None
    finally:
        if raw.exists():
            raw.unlink()

    title = (f"{idiom['literal']} — Funny {idiom['lang'].title()} Idiom "
             f"Translation Art Print")
    tags = [
        f"funny {idiom['lang']} idiom",
        f"{idiom['lang']} learning",
        "language learner gift",
        "polyglot art",
        "linguistics print",
        "translation humor",
        f"{idiom['lang']} expression",
        "language teacher gift",
        "etymology art",
        "literal translation",
        "language nerd",
        "idiom wall art",
        "humor poster",
    ]
    tags = list(dict.fromkeys(tags))[:13]

    metadata = {
        "design_id": f"idiom_{idiom['lang']}_{word_slug}",
        "language": idiom["lang"],
        "original": idiom["original"],
        "literal_translation": idiom["literal"],
        "actual_meaning": idiom["meaning"],
        "title": title[:140],
        "tags_etsy": ", ".join(tags),
        "price_etsy": 4.99,
        "files_included": "etsy_preview.jpg, print_3000.png (3000x3000 @ 300dpi)",
        "prompt_used": prompt,
        "seed": seed,
    }
    (design_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))
    return metadata


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    max_i = int(os.environ.get("MAX_IDIOMS") or "0") or len(IDIOMS)
    idioms = IDIOMS[:max_i]
    print(f"=== LITERAL IDIOMS — {len(idioms)} idiomes ===\n")

    metas = []
    for idx, idiom in enumerate(idioms, 1):
        m = produce_design(idiom, idx)
        if m:
            metas.append(m)
        time.sleep(2)

    if metas:
        csv_path = OUTPUT_DIR / "etsy_bulk_upload.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["design_id", "language", "original",
                            "literal_translation", "actual_meaning",
                            "title", "tags_etsy", "price_etsy"],
                extrasaction="ignore",
            )
            w.writeheader()
            w.writerows(metas)

    print(f"\n{'=' * 60}")
    print(f"  Produits : {len(metas)}/{len(idioms)}")
    print(f"  Dossier  : {OUTPUT_DIR}")
    return 0 if metas else 1


if __name__ == "__main__":
    sys.exit(main())
