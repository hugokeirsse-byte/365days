"""
Pipeline VIRAL FORMATS — machine à concepts viraux print-on-demand.

50+ formats moteurs ultra-déclinables × N niches × 2 styles visuels.
Exploite les leviers psychologiques saturés mais éternels :
fierté, auto-dérision, cynisme, introversion, addiction comique.

Chaque format est un TEMPLATE de phrase avec un slot {niche} à remplir.
Pour 50 formats × 20 niches × 2 styles = jusqu'à 2000 designs uniques.

L'ANGLE PROPRIÉTAIRE : on ajoute 15 formats inventés "maison" que
personne n'utilise encore (à itérer pour identifier notre marque).

Variables d'env :
  MAX_FORMATS=10     limite à N formats
  MAX_NICHES=10      limite à N niches
  MAX_STYLES=2       limite à N styles
  FORMAT_FAMILY=medical   filtre par famille (medical, geek, vintage…)
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
    print("ERREUR : Pillow non installé")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "viral_formats"
USER_AGENT = "ViralFormatsProducer/1.0"
TIMEOUT = 180

# ============================================================
# 65 FORMATS MOTEURS (50 d'Hugo + 15 propriétaires "maison")
# Chaque entrée : (key, family, text_template_EN, visual_style_hint)
# ============================================================
FORMATS = [
    # --- FAMILY: MEDICAL / DIAGNOSIS (#1-7) ---
    {"key": "diagnosed_terminal", "family": "medical",
     "text_en": "Diagnosed with terminal {niche}",
     "visual": "vintage medical prescription pad style with red stamp"},
    {"key": "strict_prescription", "family": "medical",
     "text_en": "Strict prescription: daily dose of {niche}",
     "visual": "pharmaceutical pill bottle label vintage style"},
    {"key": "blood_level_warning", "family": "medical",
     "text_en": "WARNING: {niche} levels critically high in bloodstream",
     "visual": "biohazard medical chart with red highlight"},
    {"key": "allergic_humans", "family": "medical",
     "text_en": "Allergic to humans. Tolerant only of {niche}",
     "visual": "vintage medical record card style"},
    {"key": "cheaper_than_therapy", "family": "medical",
     "text_en": "{niche}: my daily therapy, cheaper than a shrink",
     "visual": "minimalist serif typography on cream"},
    {"key": "iv_drip", "family": "medical",
     "text_en": "Need {niche} via IV drip",
     "visual": "vintage hospital chart illustration"},
    {"key": "rehab_failed", "family": "medical",
     "text_en": "Sorry, I'm in rehab for {niche}. It's not working",
     "visual": "AA-meeting style poster vintage"},

    # --- FAMILY: CERTIFICATION / OFFICIAL (#8-11, +22) ---
    {"key": "certified_zero_patience", "family": "certification",
     "text_en": "Certified 100% out of patience for anything but {niche}",
     "visual": "official seal stamp vintage style"},
    {"key": "label_rouge", "family": "certification",
     "text_en": "Premium {niche} of Controlled Origin",
     "visual": "AOC red badge french certification style"},
    {"key": "official_league", "family": "certification",
     "text_en": "Official member: League of {niche} Enthusiasts",
     "visual": "university crest blazon vintage"},
    {"key": "approved_committee", "family": "certification",
     "text_en": "Approved by the invisible committee of {niche} addicts",
     "visual": "official notary stamp red wax"},
    {"key": "best_of_office", "family": "certification",
     "text_en": "Voted best {niche} enthusiast in the office (by me)",
     "visual": "gold trophy badge cheap office award"},

    # --- FAMILY: WARNING / DANGER (#12-19, +14) ---
    {"key": "talk_for_hours", "family": "warning",
     "text_en": "Lifetime guarantee: can talk about {niche} for 8 hours without breathing",
     "visual": "warning sign yellow triangle"},
    {"key": "premium_club", "family": "warning",
     "text_en": "Premium member: club of people who prefer {niche} to humans",
     "visual": "exclusive black tie club emblem"},
    {"key": "may_start_talking", "family": "warning",
     "text_en": "Warning: may start talking about {niche} at any moment",
     "visual": "yellow caution warning sign road"},
    {"key": "dont_feed", "family": "warning",
     "text_en": "Do not feed. Do not disturb. Unless bringing {niche}",
     "visual": "zoo enclosure warning sign vintage"},
    {"key": "safety_perimeter", "family": "warning",
     "text_en": "Safety zone: intensive {niche} in progress",
     "visual": "police crime scene yellow tape"},
    {"key": "unstable_without", "family": "warning",
     "text_en": "Highly unstable without my {niche} dose",
     "visual": "radioactive hazard sign nuclear"},
    {"key": "special_voice", "family": "warning",
     "text_en": "Don't make me use my special {niche} voice",
     "visual": "warning poster bold black text"},
    {"key": "working_for_pet", "family": "warning",
     "text_en": "Working hard so my {niche} doesn't lack anything",
     "visual": "vintage work poster propaganda style"},

    # --- FAMILY: OFFICE / WORK-LIFE (#20-25) ---
    {"key": "boss_thinks_brain", "family": "office",
     "text_en": "My boss thinks I'm working. My brain is thinking about {niche}",
     "visual": "pie chart infographic minimal"},
    {"key": "sorry_for_what_i_said", "family": "office",
     "text_en": "Sorry for what I said when you stopped me from doing {niche}",
     "visual": "handwritten apology note cursive"},
    {"key": "survived_meeting", "family": "office",
     "text_en": "Survived a meeting that could have been a {niche} moment",
     "visual": "bold serif typography brick red"},
    {"key": "faking_interest", "family": "office",
     "text_en": "Currently faking human interest while wanting to do {niche}",
     "visual": "modern minimalist sans-serif black"},
    {"key": "personality_trait", "family": "office",
     "text_en": "{niche} isn't a hobby, it's a personality trait",
     "visual": "elegant serif quote layout cream"},
    {"key": "didnt_choose_life", "family": "office",
     "text_en": "You don't choose the {niche} life, it chooses you",
     "visual": "streetwear bold sans-serif urban"},

    # --- FAMILY: MINIMALIST QUOTE (#27-30) ---
    {"key": "less_drama_more", "family": "quote",
     "text_en": "Less drama, more {niche}",
     "visual": "minimalist black on white serif"},
    {"key": "expert_spoke", "family": "quote",
     "text_en": "The {niche} expert has spoken. Debate over",
     "visual": "elegant typography poster style"},
    {"key": "born_to_forced", "family": "quote",
     "text_en": "Born to {niche}. Forced to do groceries",
     "visual": "vintage typography Americana"},
    {"key": "god_made_world", "family": "quote",
     "text_en": "God created the world, but {niche} lovers make it spin",
     "visual": "gothic typography stained glass"},

    # --- FAMILY: GEEK / TECH (#31-35) ---
    {"key": "error_404", "family": "geek",
     "text_en": "ERROR 404: interest in anything but {niche} not found",
     "visual": "retro computer terminal blue screen"},
    {"key": "mode_activated", "family": "geek",
     "text_en": "Mode: {niche} ACTIVATED. Status: Unavailable",
     "visual": "ON/OFF switch interface mockup"},
    {"key": "powered_by_ai", "family": "geek",
     "text_en": "Powered by AI: Intoxication of {niche}",
     "visual": "circuit board neon cyberpunk"},
    {"key": "system_update", "family": "geek",
     "text_en": "System update required: critical lack of {niche}",
     "visual": "command line terminal screenshot"},
    {"key": "ctrl_z_day", "family": "geek",
     "text_en": "Ctrl+Z on my day, returning to {niche}",
     "visual": "keyboard shortcut illustration flat"},

    # --- FAMILY: VINTAGE / RETRO (#36-39) ---
    {"key": "was_better_before", "family": "vintage",
     "text_en": "{niche} was better back in the day",
     "visual": "cassette tape vinyl illustration 80s"},
    {"key": "old_school_club", "family": "vintage",
     "text_en": "Old school {niche} club, established 1980",
     "visual": "thrift shop vintage worn style"},
    {"key": "retro_sounds", "family": "vintage",
     "text_en": "Retro sounds and {niche} sessions",
     "visual": "80s neon synthwave vibes purple"},
    {"key": "garage_property", "family": "vintage",
     "text_en": "Exclusive property of a {niche} fan",
     "visual": "vintage garage workshop sign rusted"},

    # --- FAMILY: INTROVERT / SOLO (#40-44) ---
    {"key": "cant_have", "family": "introvert",
     "text_en": "Sorry, can't. I have {niche}",
     "visual": "minimalist handwritten cursive"},
    {"key": "plan_today", "family": "introvert",
     "text_en": "Plan for today: 1. {niche}. 2. That's it",
     "visual": "to-do list checkboxes vintage paper"},
    {"key": "introvert_but", "family": "introvert",
     "text_en": "Introvert. But will scream if you mention {niche}",
     "visual": "cute kawaii character peeking"},
    {"key": "avoid_calls", "family": "introvert",
     "text_en": "My life: avoiding calls and doing {niche}",
     "visual": "phone with bandaid kawaii illustration"},
    {"key": "love_pet_more", "family": "introvert",
     "text_en": "Sorry, my {niche} is waiting and I love it more than you",
     "visual": "vintage romance card style sepia"},

    # --- FAMILY: DICTIONARY ENTRY (#45-46) ---
    {"key": "dict_noun", "family": "dictionary",
     "text_en": "{niche} (noun): the art of spending all your money on it",
     "visual": "vintage dictionary entry typography"},
    {"key": "dict_verb", "family": "dictionary",
     "text_en": "{niche} (verb): ignoring responsibilities for happiness",
     "visual": "vintage dictionary entry typography"},

    # --- FAMILY: ESOTERIC / SPIRITUAL (#47-50) ---
    {"key": "guided_stars", "family": "esoteric",
     "text_en": "Guided by the stars and by {niche}",
     "visual": "tarot card style mystical illustration"},
    {"key": "witchcraft_niche", "family": "esoteric",
     "text_en": "Witchcraft & {niche}",
     "visual": "ancient grimoire spell book parchment"},
    {"key": "modern_alchemy", "family": "esoteric",
     "text_en": "Modern alchemy: turning stress into {niche}",
     "visual": "Da Vinci sketch sepia ink illustration"},
    {"key": "occult_forces", "family": "esoteric",
     "text_en": "Protected by the occult forces of {niche}",
     "visual": "sacred geometry mandala black"},

    # --- FAMILY: HOUSE FORMATS (15 propriétaires inventés) ---
    {"key": "house_anonymous", "family": "house",
     "text_en": "Hi, I'm a {niche}aholic. It's been 0 days",
     "visual": "AA meeting whiteboard parody vintage"},
    {"key": "house_side_effects", "family": "house",
     "text_en": "Side effects of {niche} may include: pure joy",
     "visual": "medical leaflet small print parody"},
    {"key": "house_department", "family": "house",
     "text_en": "Department of {niche} Affairs",
     "visual": "official government seal mockup"},
    {"key": "house_powered_by", "family": "house",
     "text_en": "Powered by {niche} & espresso",
     "visual": "fuel gauge dashboard illustration"},
    {"key": "house_union_one", "family": "house",
     "text_en": "The {niche} Union — current members: 1",
     "visual": "vintage union worker propaganda poster"},
    {"key": "house_survived_today", "family": "house",
     "text_en": "I survived {niche} today — please respect my space",
     "visual": "vintage merit badge boy scout style"},
    {"key": "house_mathematically_optimal", "family": "house",
     "text_en": "Mathematically optimal {niche} enjoyer",
     "visual": "chalkboard equation handwritten chalk"},
    {"key": "house_off_the_grid", "family": "house",
     "text_en": "Off the grid, on the {niche}",
     "visual": "rustic wood burned sign cabin style"},
    {"key": "house_more_less", "family": "house",
     "text_en": "More {niche}, less people",
     "visual": "minimalist sans-serif bold black"},
    {"key": "house_patiently_ing", "family": "house",
     "text_en": "Patiently {niche}ing",
     "visual": "cottagecore watercolor pastel soft"},
    {"key": "house_local_specialist", "family": "house",
     "text_en": "Local {niche} specialist — available for consults",
     "visual": "vintage business card calling card"},
    {"key": "house_personality_type", "family": "house",
     "text_en": "Personality type: {niche}",
     "visual": "MBTI style chart minimalist"},
    {"key": "house_excellence_since", "family": "house",
     "text_en": "Excellence in {niche} since [the day I tried it]",
     "visual": "corporate vintage 1950s ad style"},
    {"key": "house_terms_conditions", "family": "house",
     "text_en": "Terms & Conditions: must love {niche} to be my friend",
     "visual": "legal document parody small print"},
    {"key": "house_404_replaced", "family": "house",
     "text_en": "Replaced my personality with {niche}. No regrets",
     "visual": "modern flat sans-serif text only"},
]

# ============================================================
# 25 NICHES UNIVERSELLES (testées qui vendent)
# ============================================================
NICHES = [
    # Hobbies créatifs
    {"slug": "knitting", "label": "Knitting", "audience": "knitters"},
    {"slug": "crochet", "label": "Crochet", "audience": "crocheters"},
    {"slug": "embroidery", "label": "Embroidery", "audience": "embroiderers"},
    {"slug": "reading", "label": "Reading", "audience": "booktok readers"},
    {"slug": "gardening", "label": "Gardening", "audience": "gardeners"},
    {"slug": "baking", "label": "Baking", "audience": "home bakers"},
    {"slug": "painting", "label": "Painting", "audience": "amateur painters"},
    # Animaux
    {"slug": "cats", "label": "Cats", "audience": "cat parents"},
    {"slug": "dogs", "label": "Dogs", "audience": "dog parents"},
    {"slug": "horses", "label": "Horses", "audience": "horse riders"},
    {"slug": "chickens", "label": "Chickens", "audience": "chicken keepers"},
    # Hobbies geek
    {"slug": "dnd", "label": "D&D", "audience": "tabletop gamers"},
    {"slug": "chess", "label": "Chess", "audience": "chess players"},
    {"slug": "gaming", "label": "Gaming", "audience": "gamers"},
    {"slug": "puzzles", "label": "Puzzles", "audience": "puzzle solvers"},
    # Lifestyle
    {"slug": "coffee", "label": "Coffee", "audience": "coffee lovers"},
    {"slug": "tea", "label": "Tea", "audience": "tea drinkers"},
    {"slug": "wine", "label": "Wine", "audience": "wine enthusiasts"},
    {"slug": "yoga", "label": "Yoga", "audience": "yoga practitioners"},
    {"slug": "running", "label": "Running", "audience": "runners"},
    # Métiers
    {"slug": "teaching", "label": "Teaching", "audience": "teachers"},
    {"slug": "nursing", "label": "Nursing", "audience": "nurses"},
    # Activités outdoor
    {"slug": "fishing", "label": "Fishing", "audience": "anglers"},
    {"slug": "hiking", "label": "Hiking", "audience": "hikers"},
    {"slug": "camping", "label": "Camping", "audience": "campers"},
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
    # T-shirt portrait
    ratio = 2400 / 3000
    h = img.height
    w = int(h * ratio)
    if w > img.width:
        w = img.width
        h = int(w / ratio)
    off_x = (img.width - w) // 2
    off_y = (img.height - h) // 2
    tee = img.crop((off_x, off_y, off_x + w, off_y + h))
    tee.resize((2400, 3000), Image.LANCZOS).save(
        design_dir / "tshirt_2400x3000.png", "PNG", optimize=True)


def produce_design(fmt: dict, niche: dict, style_idx: int, idx: int) -> dict | None:
    text = fmt["text_en"].format(niche=niche["label"])
    visual_hint = fmt["visual"]
    style_modifiers = [
        "centered composition, generous white space, professional commercial illustration",
        "bold composition, dramatic lighting, modern editorial poster style",
    ]
    style_mod = style_modifiers[style_idx % len(style_modifiers)]

    prompt = (
        f"merch design poster with bold text exactly reading: \"{text}\", "
        f"design style: {visual_hint}, {style_mod}, no watermark no signature, "
        f"clean composition suitable for t-shirt mug poster"
    )

    design_dir = OUTPUT_DIR / fmt["family"] / fmt["key"] / niche["slug"] / f"v{style_idx}"
    design_dir.mkdir(parents=True, exist_ok=True)
    raw = design_dir / "raw.png"
    seed = idx * 10039 + random.randint(0, 9999)
    url = pollinations_url(prompt, seed)

    print(f"  [{idx:>4}] [{fmt['family']}] {fmt['key']} × {niche['slug']} v{style_idx}")
    if not http_get(url, raw):
        print(f"         echec Pollinations")
        return None

    try:
        make_outputs(raw, design_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"         traitement echoue : {exc}")
        return None
    finally:
        if raw.exists():
            raw.unlink()

    title = f"{text} — Funny {niche['label']} Gift Print"
    tags = [
        f"{niche['label'].lower()} gift",
        f"{niche['audience']}",
        "funny tshirt design",
        "hobby gift",
        "humor print",
        fmt["family"],
        "personality gift",
        "introvert humor",
        "self deprecating",
        f"{niche['slug']} lover",
        "digital download",
        "etsy bestseller",
        "redbubble pod",
    ]
    tags = list(dict.fromkeys(tags))[:13]

    metadata = {
        "design_id": f"viral_{fmt['key']}_{niche['slug']}_v{style_idx}",
        "format_key": fmt["key"],
        "format_family": fmt["family"],
        "format_text": text,
        "niche": niche["slug"],
        "niche_label": niche["label"],
        "audience": niche["audience"],
        "style_variant": style_idx,
        "title": title[:140],
        "tags_etsy": ", ".join(tags),
        "price_etsy": 3.99,
        "files_included": (
            "etsy_preview.jpg (1080x1080), print_3000.png (3000x3000), "
            "tshirt_2400x3000.png (Printful)"
        ),
        "prompt_used": prompt,
        "seed": seed,
    }
    (design_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))
    return metadata


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    max_f = int(os.environ.get("MAX_FORMATS") or "0") or len(FORMATS)
    max_n = int(os.environ.get("MAX_NICHES") or "0") or len(NICHES)
    max_s = int(os.environ.get("MAX_STYLES") or "0") or 2
    family_filter = os.environ.get("FORMAT_FAMILY", "").strip().lower()

    formats = FORMATS[:max_f]
    if family_filter:
        formats = [f for f in formats if f["family"] == family_filter]
        print(f"Filtré sur family={family_filter} : {len(formats)} formats")

    niches = NICHES[:max_n]
    total = len(formats) * len(niches) * max_s
    print(f"=== VIRAL FORMATS — {len(formats)} formats × {len(niches)} niches "
          f"× {max_s} styles = {total} designs ===\n")

    metas = []
    idx = 0
    for fmt in formats:
        for niche in niches:
            for style_idx in range(max_s):
                idx += 1
                m = produce_design(fmt, niche, style_idx, idx)
                if m:
                    metas.append(m)
                time.sleep(2)

    if metas:
        csv_path = OUTPUT_DIR / "etsy_bulk_upload.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["design_id", "format_family", "format_key",
                            "format_text", "niche", "title",
                            "tags_etsy", "price_etsy"],
                extrasaction="ignore",
            )
            w.writeheader()
            w.writerows(metas)

    print(f"\n{'=' * 60}")
    print(f"  Produits : {len(metas)}/{total}")
    print(f"  Dossier  : {OUTPUT_DIR}")
    print(f"\n  Tip: filtre par family pour lots ciblés :")
    print(f"  FORMAT_FAMILY=medical (parodies médicales)")
    print(f"  FORMAT_FAMILY=geek (humour tech)")
    print(f"  FORMAT_FAMILY=house (nos formats propriétaires à tester)")
    return 0 if metas else 1


if __name__ == "__main__":
    sys.exit(main())
