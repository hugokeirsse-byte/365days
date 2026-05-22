#!/usr/bin/env python3
"""STRATEGE (Brique 1 de la boucle autonome).

Lit les trends (data/opportunities.json) et ECRIT TOUT SEUL un cahier des
charges complet (data/briefs/<id>.json) conforme au schema ProductBrief.
C'est l'agent qui remplace la redaction manuelle : Hugo n'intervient qu'au
GATE 1 (lire / choisir la reference / approuver).

Garde-fous :
  - FILE PLAFONNEE : ne genere pas de nouveau brief si la file de briefs
    AI-original EN ATTENTE (gate_start=pending) atteint MAX_PENDING (defaut 10).
  - ANTI-DOUBLON : ne refait pas un brief pour un theme deja en file.

Deux modes :
  - Gemini disponible (GEMINI_API_KEY + reseau, en CI) -> contenu creatif ecrit
    par l'IA (concept, 30 sujets distincts, blurb, page d'accueil, titre, auteur).
  - Sinon -> mode DETERMINISTE (gabarit) : produit quand meme un brief valide,
    pour tester le cablage de la boucle hors-ligne. NE GENERE AUCUNE IMAGE.

Env :
  GEMINI_API_KEY, GEMINI_MODEL (defaut gemini-2.5-flash)
  TARGET_PRODUCT_TYPE (defaut coloring_book)
  MAX_PENDING (defaut 10)
"""
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
BRIEFS_DIR = DATA_DIR / "briefs"
OPP_PATH = DATA_DIR / "opportunities.json"
SCHEMA_PATH = DATA_DIR / "schemas" / "product_brief.schema.json"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_FALLBACKS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
USER_AGENT = "365days-Strategist/1.0"
TIMEOUT = 60

TARGET_PRODUCT_TYPE = os.environ.get("TARGET_PRODUCT_TYPE", "coloring_book")
MAX_PENDING = int(os.environ.get("MAX_PENDING", "10"))

STYLE_NEGATIVE = ["color", "shading", "grayscale", "gray tones", "hatching", "crosshatching",
                  "sketch lines", "pencil texture", "fill", "text", "letters", "watermark",
                  "signature", "blurry", "deformed", "tiny unconnected details", "open broken outlines"]

PEN_NAMES = ["Maple Briarwood", "Luna Fernwick", "Posy Hollowell", "Wren Mossgrove",
             "Clover Ashby", "Hazel Thistledown", "Juniper Quill", "Fern Aldercott"]

# 30 scenes generiques (mode deterministe) -> combinees a un motif pour des sujets distincts.
SCENE_MODIFIERS = [
    "under a crescent moon and stars", "with a tiny fairy door", "beside a cozy cottage with a chimney",
    "holding an umbrella in the rain", "having tea with a friend", "with an owl companion",
    "wearing a little witch hat", "in a garden with bees and butterflies", "carrying a lantern at night",
    "reading a book by candlelight", "as a fairy house with windows", "dancing among falling leaves",
    "riding a snail", "with a ladybug friend", "in a field at dawn",
    "inside a glowing crystal ball", "with delicate butterfly wings", "sleeping under a leaf blanket",
    "decorated with a constellation pattern", "as a wise elder with a walking stick",
    "as a baker with apron and bread", "holding an ornate magic key", "with a sunflower companion",
    "with a sleepy kitten curled nearby", "with a frog playing a tiny flute", "wrapped in climbing vines",
    "in winter snow with pine cones", "emerging from the pages of a book", "perched on a tiny mushroom stool",
    "surrounded by floating sparkles",
]


def _models_to_try():
    seq = [GEMINI_MODEL]
    for m in GEMINI_FALLBACKS:
        if m not in seq:
            seq.append(m)
    return seq


def call_gemini(prompt, retries=3):
    if not GEMINI_API_KEY:
        return None, "GEMINI_API_KEY absent"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.85, "responseMimeType": "application/json", "maxOutputTokens": 4096},
    }).encode("utf-8")
    last = "inconnu"
    for model in _models_to_try():
        url = f"{API_BASE}/{model}:generateContent?key={GEMINI_API_KEY}"
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, data=body,
                    headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                    data = json.loads(r.read())
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text), model
            except urllib.error.HTTPError as exc:
                last = f"{model}: HTTP {exc.code}"
                if exc.code == 404:
                    break
                time.sleep((8 if exc.code == 429 else 3) + attempt * 4)
            except Exception as exc:  # noqa: BLE001
                last = f"{model}: {type(exc).__name__} {exc}"
                time.sleep(3 + attempt * 3)
    return None, last


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


def load_opportunities():
    if not OPP_PATH.exists():
        return []
    try:
        return json.loads(OPP_PATH.read_text(encoding="utf-8")).get("opportunities", [])
    except Exception:  # noqa: BLE001
        return []


def existing_briefs():
    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for p in BRIEFS_DIR.glob("brief_*.json"):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            pass
    return out


def pending_count(briefs):
    return sum(1 for b in briefs
               if b.get("requested_by") == "strategist_auto"
               and b.get("human_gates", {}).get("gate_start") == "pending")


def pick_opportunity(opps, briefs):
    """Meilleure opportunite du bon type, pas deja couverte par un brief existant."""
    seen = {b.get("trends_source", "") + b.get("target", {}).get("description", "")[:30] for b in briefs}
    cand = [o for o in opps if o.get("product_category", "").rstrip("s") in (TARGET_PRODUCT_TYPE.replace("_book", ""), "coloring_book")
            or o.get("product_category") == "coloring_books"]
    cand.sort(key=lambda o: o.get("composite_score", 0), reverse=True)
    for o in cand:
        key = (o.get("style_name", "") + o.get("trend_keyword", ""))
        if not any(key[:20] in s for s in seen):
            return o
    return cand[0] if cand else (opps[0] if opps else None)


def gemini_creative(opp):
    prompt = (
        "Tu es le STRATEGE d'un studio de coloriages KDP. Reponds STRICTEMENT en JSON valide, sans markdown.\n"
        f"Trend a exploiter : style='{opp.get('style_name')}', mot-cle='{opp.get('trend_keyword')}', "
        f"evenement='{opp.get('event_name')}'.\n"
        "Concois un livre de coloriage adulte CUTE/KAWAII, trait noir epais sur blanc (PAS de texte dans les images).\n"
        "Donne EXACTEMENT ces cles JSON :\n"
        '{ "theme_slug": "2-3 mots a-z", "title_en": "titre court accrocheur", '
        '"subtitle_en": "30 ... Coloring Pages for ...", "author_pen_name": "Prenom Nom (plausible, original)", '
        '"concept_fr": "1 phrase", "blurb_en": "4eme de couverture, 2-3 phrases vendeuses", '
        '"welcome_fr": "page d_accueil chaleureuse + 1 conseil d_utilisation", '
        '"page_subjects": ["30 sujets DISTINCTS et coherents, en anglais, courts"] }'
    )
    res, info = call_gemini(prompt)
    if res and isinstance(res.get("page_subjects"), list) and len(res["page_subjects"]) >= 20:
        res["page_subjects"] = res["page_subjects"][:30]
        res["_source"] = f"gemini:{info}"
        return res
    return None


def fallback_creative(opp):
    kw = (opp.get("trend_keyword") or "cute") + " " + (opp.get("style_name") or "")
    motif = "cute mushroom"
    if "creature" in kw.lower() or "fantasy" in kw.lower():
        motif = "cute baby dragon"
    elif "cottage" in kw.lower() or "cottagecore" in opp.get("style_key", ""):
        motif = "cozy cottagecore mushroom"
    theme = "kawaii cottage hollow"
    return {
        "theme_slug": slugify(theme),
        "title_en": "Cozy Hollow",
        "subtitle_en": "30 Cute Cottagecore Coloring Pages for Relaxation",
        "author_pen_name": PEN_NAMES[date.today().toordinal() % len(PEN_NAMES)],
        "concept_fr": "Un univers cottagecore kawaii et apaisant a colorier.",
        "blurb_en": "Escape into a cozy world of cute cottagecore scenes. 30 original, clean line-art pages for mindful relaxation.",
        "welcome_fr": "Bienvenue ! Installe-toi confortablement, glisse une feuille sous la page pour eviter les bavures, et prends ton temps.",
        "page_subjects": [f"{motif} {m}" for m in SCENE_MODIFIERS][:30],
        "_source": "deterministe (fallback hors-ligne)",
    }


def coloring_audit_criteria():
    B = lambda c, h: {"criterion": c, "how_to_check": h, "blocking": True}
    N = lambda c, h: {"criterion": c, "how_to_check": h, "blocking": False}
    return [
        B("Trait noir PUR (#000000), aucune couleur/gris/ombrage sur l'interieur", "analyse pixels + Gemini Vision"),
        B("Coherence stylistique entre TOUTES les pages vs reference verrouillee", "Gemini Vision page-a-page"),
        B("Formes fermees coloriables (pas de contours ouverts ni micro-details)", "Gemini Vision + heuristique"),
        B("Sujet de chaque page conforme au page_subject demande", "Gemini Vision vs page_subjects"),
        B("Zero texte/lettre/watermark parasite dans les images", "OCR + Gemini Vision"),
        B("Format KDP conforme (trim 8.5x11, bleed, gutter 0.75, rotation r/v)", "controle dimensions PDF"),
        B("Couverture avant conforme (couleur, titre+auteur lisibles miniature)", "Gemini Vision + OCR"),
        B("4eme de couverture conforme (blurb + bullets + zone code-barres)", "Gemini Vision + OCR"),
        B("Pages liminaires completes (titre, copyright, 'appartient a', accueil)", "presence pages PDF"),
        B("Page d'accueil presente et lisible (bienvenue + conseils)", "OCR + Gemini Vision"),
        B("Completude cle-en-main (titre + auteur + metadata KDP)", "presence champs metadata"),
        B("Titre et nom d'auteur verifies NON deja utilises", "recherche Amazon/Etsy avant publi"),
        N("Page de remerciement/avis presente en fin", "presence PDF"),
        N("Composition equilibree et centree, agreable a colorier", "Gemini Vision esthetique"),
    ]


def build_brief(opp, c):
    today = date.today().isoformat()
    bid = f"brief_{today}_coloring_{c['theme_slug']}"
    author = c["author_pen_name"]
    title = c["title_en"]
    return {
        "id": bid,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "business": "B1_coloriages",
        "product_type": "coloring_book",
        "generation_strategy": "mono_trend",
        "opportunity_rationale": (
            f"Trend '{opp.get('trend_keyword')}' x style '{opp.get('style_name')}' "
            f"(score composite {opp.get('composite_score')}). {c.get('concept_fr','')}"),
        "variations_target": 1,
        "trend_strength": "strong" if opp.get("composite_score", 0) >= 88 else "moderate",
        "trends_source": f"opportunities.json : {opp.get('style_name')} / {opp.get('trend_keyword')}",
        "target": {
            "description": c.get("concept_fr", ""),
            "style_reference": {
                "style_keywords": ["cute kawaii", "bold clean black line art", "cottagecore", "whimsical",
                                   "rounded shapes", "large expressive eyes"],
                "reference_image_urls": [],
                "negative": STYLE_NEGATIVE,
            },
            "format": {"trim": "8.5x11in", "bleed": "0.125in", "gutter": "0.75in", "margins": "0.5in",
                       "pages_interior": 30, "page_recto_verso_rotation": True,
                       "export": "PDF/X-1a (interieur N&B) + couverture separee"},
            "color_tone": "line-art noir epais sur blanc pur (aucune couleur, aucun gris)",
            "signature": "Douceur kawaii cottagecore, lisible et apaisant, complexite moyenne (coloriage adulte detente).",
            "cover": {
                "front": {"title_text": title, "subtitle_text": c["subtitle_en"], "author_byline": author,
                          "layout_note": "Couverture COULEUR : scene phare coloree pastel, titre haut lisible miniature, auteur bas.",
                          "reference_image_path": ""},
                "back": {"blurb": c["blurb_en"],
                         "inside_bullets": ["30 illustrations originales", "trait net facile a colorier",
                                            "grand format 8.5x11 pouces", "feutres, crayons, gel", "adultes & ados"],
                         "author_byline": author,
                         "barcode_isbn_zone": "espace reserve en bas a droite pour code-barres / ISBN KDP",
                         "layout_note": "Fond cottagecore doux assorti a la couv avant ; blurb lisible ; zone code-barres vide."},
            },
            "collection": {"title": title, "title_uniqueness_checked": False, "author": author,
                           "author_uniqueness_checked": False, "volume": 1, "decline_if_success": True,
                           "next_volumes_hint": []},
            "page_subjects": c["page_subjects"],
            "book_structure": {
                "note": "Livre COMPLET et professionnel : pas que les pages de coloriage.",
                "front_cover": "couleur (voir cover.front)",
                "front_matter": [
                    {"page": "title_page", "content": "titre + sous-titre + nom d'auteur"},
                    {"page": "copyright", "content": f"(c) {date.today().year} {author}. Tous droits reserves. Usage personnel."},
                    {"page": "belongs_to", "content": "'Ce livre appartient a : ____' (page mignonne assortie au style)"},
                    {"page": "welcome", "content": c["welcome_fr"]},
                ],
                "interior": "30 pages de coloriage (voir page_subjects), 1 dessin par page",
                "back_matter": [{"page": "thank_you", "content": "Merci + invitation a laisser un avis + teaser des prochains volumes."}],
                "back_cover": "couleur (voir cover.back)",
                "page_count_interior_total": 35,
                "page_count_breakdown": "4 liminaires + 30 coloriage + 1 remerciement = 35 (arrondi page paire KDP).",
            },
        },
        "audit_criteria": coloring_audit_criteria(),
        "image_budget": {"max_images_total": 50, "ideal_one_gen_one_use": True,
                         "regen_allowance_per_asset": 1, "reference_candidates_budget": 6},
        "reference_selection": {"mode": "generate_candidates", "candidates_count": 6,
                                "candidates_provider": "pollinations", "status": "pending_human_pick",
                                "chosen_reference_path": "", "character_model_sheets": []},
        "loop_policy": {"max_iterations": 5, "stop_on_repeated_failure": 2, "escalate_to_human": True},
        "human_gates": {"gate_start": "pending", "gate_end": "not_reached"},
        "requested_by": "strategist_auto",
        "_creative_source": c.get("_source", "?"),
    }


def validate(brief):
    req = ["id", "product_type", "target", "audit_criteria", "loop_policy"]
    missing = [k for k in req if k not in brief]
    if missing:
        return False, f"champs requis manquants: {missing}"
    if len(brief["target"].get("page_subjects", [])) < 20:
        return False, "moins de 20 sujets de pages"
    try:
        import jsonschema  # type: ignore
        jsonschema.validate(brief, json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001
        return False, f"schema: {exc}"
    return True, "ok"


def main():
    print("=" * 64)
    print("STRATEGE — generation autonome de cahier des charges")
    print("=" * 64)
    briefs = existing_briefs()
    pending = pending_count(briefs)
    print(f"File actuelle : {pending} brief(s) AI-original en attente (plafond {MAX_PENDING})")
    if pending >= MAX_PENDING:
        print("⊝ File pleine -> on n'ecrit PAS de nouveau brief (anti-emballement). STOP.")
        return 0

    opps = load_opportunities()
    if not opps:
        print("✗ Aucune opportunite dans opportunities.json.")
        return 1
    opp = pick_opportunity(opps, briefs)
    if not opp:
        print("✗ Aucune opportunite exploitable pour ce type de produit.")
        return 1
    print(f"Opportunite retenue : {opp.get('style_name')} / {opp.get('trend_keyword')} "
          f"(score {opp.get('composite_score')})")

    creative = gemini_creative(opp) if GEMINI_API_KEY else None
    if creative is None:
        print("  (Gemini indisponible -> mode deterministe)")
        creative = fallback_creative(opp)
    print(f"  Source creative : {creative['_source']}")

    brief = build_brief(opp, creative)
    if (BRIEFS_DIR / f"{brief['id']}.json").exists():
        print(f"⊝ Brief '{brief['id']}' existe deja -> rien a faire.")
        return 0

    ok, info = validate(brief)
    if not ok:
        print(f"✗ Brief invalide : {info}")
        return 2
    out = BRIEFS_DIR / f"{brief['id']}.json"
    out.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Cahier des charges ecrit : {out}")
    print(f"  titre='{brief['target']['collection']['title']}' auteur='{brief['target']['collection']['author']}' "
          f"pages={len(brief['target']['page_subjects'])} criteres={len(brief['audit_criteria'])}")
    print("  -> En attente GATE 1 (lecture + choix reference par Hugo).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
