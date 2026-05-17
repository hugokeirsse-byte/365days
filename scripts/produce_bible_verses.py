"""
Pipeline BIBLE VERSES — gros marché US "christian wall art".

Top 20 catégories Etsy US. Public ultra payeur, achats récurrents
(cadeau religieux, anniv, baptême, mariage, fête des mères).
Concurrence existe mais marché large = place pour tous.

50 versets bibliques les plus populaires × 4 styles visuels = 200
designs. Layout : Verset en grand + référence biblique en petit +
illustration douce thématique en fond.

100% du domaine public (Bible texts via copyright public, illustrations
Pollinations). Aucun risque légal.

Variables d'env :
  MAX_VERSES=10           limite à N versets
  MAX_STYLES=2            limite à N styles par verset
  TESTAMENT=both          old, new, both
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
OUTPUT_DIR = ROOT / "products" / "bible_verses"
USER_AGENT = "BibleVersesProducer/1.0"
TIMEOUT = 180

# Top 50 versets les plus populaires (sales-tested sur Etsy)
VERSES = [
    # New Testament
    {"ref": "John 3:16", "text": "For God so loved the world",
     "topic": "love", "testament": "new"},
    {"ref": "Philippians 4:13", "text": "I can do all things through Christ who strengthens me",
     "topic": "strength", "testament": "new"},
    {"ref": "Jeremiah 29:11", "text": "For I know the plans I have for you",
     "topic": "hope", "testament": "old"},
    {"ref": "Romans 8:28", "text": "All things work together for good",
     "topic": "trust", "testament": "new"},
    {"ref": "Proverbs 3:5-6", "text": "Trust in the Lord with all your heart",
     "topic": "trust", "testament": "old"},
    {"ref": "Psalm 23:1", "text": "The Lord is my shepherd, I shall not want",
     "topic": "comfort", "testament": "old"},
    {"ref": "Isaiah 41:10", "text": "Fear not, for I am with you",
     "topic": "courage", "testament": "old"},
    {"ref": "Joshua 1:9", "text": "Be strong and courageous",
     "topic": "courage", "testament": "old"},
    {"ref": "Matthew 6:33", "text": "Seek first the kingdom of God",
     "topic": "faith", "testament": "new"},
    {"ref": "1 Corinthians 13:4-7", "text": "Love is patient, love is kind",
     "topic": "love", "testament": "new"},
    {"ref": "Psalm 46:10", "text": "Be still, and know that I am God",
     "topic": "peace", "testament": "old"},
    {"ref": "Ephesians 2:8-9", "text": "By grace you have been saved through faith",
     "topic": "grace", "testament": "new"},
    {"ref": "Romans 12:2", "text": "Be transformed by the renewing of your mind",
     "topic": "transformation", "testament": "new"},
    {"ref": "Galatians 5:22-23", "text": "The fruit of the Spirit",
     "topic": "spirit", "testament": "new"},
    {"ref": "Hebrews 11:1", "text": "Faith is the substance of things hoped for",
     "topic": "faith", "testament": "new"},
    {"ref": "Matthew 11:28", "text": "Come to me all who are weary",
     "topic": "rest", "testament": "new"},
    {"ref": "James 1:2-3", "text": "Consider it pure joy when you face trials",
     "topic": "joy", "testament": "new"},
    {"ref": "Psalm 91:11", "text": "He will command his angels concerning you",
     "topic": "protection", "testament": "old"},
    {"ref": "1 Peter 5:7", "text": "Cast all your anxiety on him",
     "topic": "anxiety", "testament": "new"},
    {"ref": "Lamentations 3:22-23", "text": "His mercies are new every morning",
     "topic": "mercy", "testament": "old"},
    {"ref": "Psalm 27:1", "text": "The Lord is my light and my salvation",
     "topic": "light", "testament": "old"},
    {"ref": "Matthew 7:7", "text": "Ask, and it will be given to you",
     "topic": "prayer", "testament": "new"},
    {"ref": "Isaiah 40:31", "text": "Those who hope in the Lord renew strength",
     "topic": "strength", "testament": "old"},
    {"ref": "Proverbs 31:25", "text": "She is clothed with strength and dignity",
     "topic": "strength", "testament": "old"},
    {"ref": "Psalm 139:14", "text": "I am fearfully and wonderfully made",
     "topic": "identity", "testament": "old"},
    {"ref": "Ecclesiastes 3:1", "text": "To everything there is a season",
     "topic": "wisdom", "testament": "old"},
    {"ref": "Psalm 118:24", "text": "This is the day the Lord has made",
     "topic": "joy", "testament": "old"},
    {"ref": "Matthew 5:14", "text": "You are the light of the world",
     "topic": "identity", "testament": "new"},
    {"ref": "John 14:6", "text": "I am the way, the truth, and the life",
     "topic": "faith", "testament": "new"},
    {"ref": "Romans 5:8", "text": "Christ died for us while we were sinners",
     "topic": "grace", "testament": "new"},
    {"ref": "Genesis 1:1", "text": "In the beginning God created the heavens and the earth",
     "topic": "creation", "testament": "old"},
    {"ref": "John 1:5", "text": "The light shines in the darkness",
     "topic": "light", "testament": "new"},
    {"ref": "2 Timothy 1:7", "text": "God has not given us a spirit of fear",
     "topic": "courage", "testament": "new"},
    {"ref": "Psalm 121:1-2", "text": "I lift up my eyes to the mountains",
     "topic": "help", "testament": "old"},
    {"ref": "1 John 4:19", "text": "We love because He first loved us",
     "topic": "love", "testament": "new"},
    {"ref": "Colossians 3:23", "text": "Whatever you do, do it with all your heart",
     "topic": "work", "testament": "new"},
    {"ref": "Matthew 19:26", "text": "With God all things are possible",
     "topic": "faith", "testament": "new"},
    {"ref": "Psalm 34:18", "text": "The Lord is close to the brokenhearted",
     "topic": "comfort", "testament": "old"},
    {"ref": "Isaiah 43:2", "text": "When you pass through the waters, I will be with you",
     "topic": "trust", "testament": "old"},
    {"ref": "John 16:33", "text": "I have overcome the world",
     "topic": "victory", "testament": "new"},
    {"ref": "Romans 15:13", "text": "May the God of hope fill you with all joy",
     "topic": "joy", "testament": "new"},
    {"ref": "Psalm 19:14", "text": "Let the words of my mouth be pleasing",
     "topic": "prayer", "testament": "old"},
    {"ref": "Galatians 6:9", "text": "Let us not grow weary in doing good",
     "topic": "perseverance", "testament": "new"},
    {"ref": "Numbers 6:24-26", "text": "The Lord bless you and keep you",
     "topic": "blessing", "testament": "old"},
    {"ref": "Psalm 51:10", "text": "Create in me a clean heart, O God",
     "topic": "prayer", "testament": "old"},
    {"ref": "Proverbs 27:17", "text": "As iron sharpens iron, so one person sharpens another",
     "topic": "friendship", "testament": "old"},
    {"ref": "Deuteronomy 31:6", "text": "Be strong and courageous, do not be afraid",
     "topic": "courage", "testament": "old"},
    {"ref": "Psalm 16:11", "text": "You will fill me with joy in your presence",
     "topic": "joy", "testament": "old"},
    {"ref": "Matthew 28:20", "text": "I am with you always, to the end of the age",
     "topic": "presence", "testament": "new"},
    {"ref": "Psalm 145:18", "text": "The Lord is near to all who call on him",
     "topic": "prayer", "testament": "old"},
]

# Styles visuels par mood
STYLES = [
    {"key": "soft_watercolor",
     "name": "Soft Watercolor",
     "describe": "soft watercolor illustration with gentle floral elements, warm cream and dusty rose palette, peaceful christian aesthetic, hand-painted feel"},
    {"key": "vintage_botanical",
     "name": "Vintage Botanical",
     "describe": "vintage botanical illustration with delicate leaves and flowers, sepia and forest green tones, scholarly christian aesthetic with subtle cross or dove motif"},
    {"key": "minimalist_serif",
     "name": "Minimalist Serif",
     "describe": "minimalist elegant serif typography on cream background, subtle gold leaf accents, modern christian wall art, generous white space"},
    {"key": "modern_mountains",
     "name": "Modern Mountains",
     "describe": "modern minimalist mountain landscape silhouette, soft sunrise palette of peach and lavender, contemporary christian poster style"},
]


def pollinations_url(prompt: str, seed: int, w: int = 1536, h: int = 1536) -> str:
    encoded = urllib.parse.quote(prompt, safe="")
    return (f"https://image.pollinations.ai/prompt/{encoded}"
            f"?model=flux&width={w}&height={h}"
            f"&seed={seed}&nologo=true&private=true&enhance=true")


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
            print(f"    retry {attempt+1}/{retries} : {exc}")
            time.sleep(6 + attempt * 6)
    return False


def make_outputs(raw: Path, dest_dir: Path) -> None:
    img = Image.open(raw).convert("RGB")
    side = min(img.width, img.height)
    off_x = (img.width - side) // 2
    off_y = (img.height - side) // 2
    sq = img.crop((off_x, off_y, off_x + side, off_y + side))
    sq.resize((1080, 1080), Image.LANCZOS).save(
        dest_dir / "etsy_preview.jpg", "JPEG", quality=92)
    sq.resize((3000, 3000), Image.LANCZOS).save(
        dest_dir / "print_3000.png", "PNG", optimize=True)


def slugify(text: str) -> str:
    import re
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:40]


def produce_design(verse: dict, style: dict, idx: int) -> dict | None:
    prompt = (
        f"christian wall art poster, large elegant serif typography with "
        f"the bible verse text: \"{verse['text']}\", below in smaller "
        f"text the reference: \"{verse['ref']}\", "
        f"background style: {style['describe']}, centered composition, "
        f"professional inspirational wall art quality, no watermark"
    )
    ref_slug = slugify(verse["ref"])
    design_dir = OUTPUT_DIR / verse["testament"] / verse["topic"] / \
                  f"{ref_slug}_{style['key']}"
    design_dir.mkdir(parents=True, exist_ok=True)
    raw = design_dir / "raw.png"
    seed = idx * 10047 + random.randint(0, 9999)
    url = pollinations_url(prompt, seed)

    print(f"  [{idx:>3}] {verse['ref']:<20} → {style['name']}")
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

    title = (f"{verse['ref']} Bible Verse Print — {style['name']} "
             f"Christian Wall Art Decor")
    tags = [
        f"{verse['ref'].lower()}",
        "bible verse art",
        "christian wall art",
        f"{verse['topic']} verse",
        "scripture print",
        "religious decor",
        "faith print",
        "christian gift",
        "church decor",
        "baptism gift",
        "prayer room art",
        style["key"].replace("_", " "),
        "inspirational quote",
    ]
    tags = list(dict.fromkeys(tags))[:13]

    metadata = {
        "design_id": f"bible_{ref_slug}_{style['key']}",
        "reference": verse["ref"],
        "verse_text": verse["text"],
        "topic": verse["topic"],
        "testament": verse["testament"],
        "style": style["key"],
        "title": title[:140],
        "tags_etsy": ", ".join(tags),
        "price_etsy": 4.99,
        "files_included": "etsy_preview.jpg (1080x1080), print_3000.png (3000x3000)",
        "prompt_used": prompt,
        "seed": seed,
    }
    (design_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))
    return metadata


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    max_v = int(os.environ.get("MAX_VERSES") or "0") or len(VERSES)
    max_s = int(os.environ.get("MAX_STYLES") or "0") or len(STYLES)
    testament = os.environ.get("TESTAMENT", "both").strip().lower()

    verses = VERSES[:max_v]
    if testament in ("old", "new"):
        verses = [v for v in verses if v["testament"] == testament]
        print(f"Filtré sur testament={testament} : {len(verses)} versets")

    styles = STYLES[:max_s]
    total = len(verses) * len(styles)
    print(f"=== BIBLE VERSES — {len(verses)} versets × {len(styles)} "
          f"styles = {total} designs ===\n")

    metas = []
    idx = 0
    for verse in verses:
        for style in styles:
            idx += 1
            m = produce_design(verse, style, idx)
            if m:
                metas.append(m)
            time.sleep(2)

    if metas:
        csv_path = OUTPUT_DIR / "etsy_bulk_upload.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["design_id", "reference", "topic", "testament",
                            "style", "title", "tags_etsy", "price_etsy"],
                extrasaction="ignore",
            )
            w.writeheader()
            w.writerows(metas)

    print(f"\n{'=' * 60}")
    print(f"  Produits : {len(metas)}/{total}")
    print(f"  Dossier  : {OUTPUT_DIR}")
    return 0 if metas else 1


if __name__ == "__main__":
    sys.exit(main())
