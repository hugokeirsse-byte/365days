"""
Agent GEMINI QUALITY CHECK — validation visuelle IA des designs.

Utilise Gemini 2.0 Flash Vision (gratuit, 1500 req/jour) pour valider
chaque design contre les règles de viabilité définies dans
data/quality_rules.json.

Pour chaque image produite, Gemini reçoit :
1. L'image
2. Les règles critiques du pipeline concerné
3. Un prompt strict de QC

Et répond avec un JSON : verdict (approve/review/reject) + issues + rating.

Mode dégradé : si GEMINI_API_KEY absent, ne fait rien (passe l'audit
heuristique du agent_visual_audit qui marche sans clé).

Variables d'env :
  GEMINI_API_KEY            clé Google AI Studio (gratuit 1500 req/jour)
  GEMINI_MODEL              défaut: gemini-2.0-flash-exp
  AUTO_REJECT=1             déplace les rejected vers _rejected/
  MAX_IMAGES=50             limite par run (économie de quota API)
  RECHECK_DAYS=30           re-vérifie un design si > N jours
"""

import base64
import json
import os
import shutil
import sys
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"
DATA_DIR = ROOT / "data"
REJECTED_DIR = PRODUCTS_DIR / "_rejected"
RULES_PATH = DATA_DIR / "quality_rules.json"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-exp")
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

AUTO_REJECT = os.environ.get("AUTO_REJECT") == "1"
MAX_IMAGES = int(os.environ.get("MAX_IMAGES") or "50")
RECHECK_DAYS = int(os.environ.get("RECHECK_DAYS") or "30")


def load_rules() -> dict:
    if not RULES_PATH.exists():
        return {}
    return json.loads(RULES_PATH.read_text())


def detect_pipeline(design_dir: Path) -> str:
    parts = design_dir.relative_to(PRODUCTS_DIR).parts
    return parts[0] if parts else ""


def build_qc_prompt(pipeline: str, metadata: dict, rules: dict) -> str:
    """Construit le prompt envoyé à Gemini."""
    global_rules = rules.get("global_critical_rules", {})
    pipeline_rules = rules.get("pipelines", {}).get(pipeline, {})
    crit = pipeline_rules.get("critical_rules", [])
    warn = pipeline_rules.get("warning_rules", [])
    bad_examples = pipeline_rules.get("examples_of_unacceptable", [])

    expected = ""
    # Champs spécifiques selon pipeline
    if pipeline == "viral_formats":
        expected = (f"Expected text on design: \"{metadata.get('format_text', '?')}\". "
                    f"Niche: {metadata.get('niche_label', '?')}.")
    elif pipeline in ("iheart", "iheart_v2"):
        expected = (f"Expected design: 'I [heart] {metadata.get('niche_label', '?')}'. "
                    f"Style: {metadata.get('style', metadata.get('variant', '?'))}.")
    elif pipeline == "cultural_arbitrage":
        expected = (f"Expected word: \"{metadata.get('expression', '?')}\" "
                    f"(language: {metadata.get('language', '?')}). "
                    f"Format: {metadata.get('format', '?')}.")
    elif pipeline == "literal_idioms":
        expected = (f"Expected literal translation: \"{metadata.get('literal_translation', '?')}\". "
                    f"Scene should match the absurd literal meaning.")
    elif pipeline == "bible_verses":
        expected = (f"Expected verse: \"{metadata.get('verse_text', '?')}\" "
                    f"({metadata.get('reference', '?')}). Style: {metadata.get('style', '?')}.")
    elif pipeline == "coloring_books":
        expected = "Expected: thick black lines on pure white background, single coloring page, no shading."

    prompt = (
        "You are a strict quality control AI for a print-on-demand business. "
        f"Audit this image against the rules below for pipeline '{pipeline}'.\n\n"
        f"{expected}\n\n"
        f"CRITICAL rules (any violation = REJECT):\n"
    )
    for r in crit:
        desc = global_rules.get(r, {}).get("description", r)
        prompt += f"- {r}: {desc}\n"
    if warn:
        prompt += "\nWARNING rules (violation = REVIEW):\n"
        for r in warn:
            prompt += f"- {r}\n"
    if bad_examples:
        prompt += "\nEXAMPLES OF UNACCEPTABLE OUTPUTS:\n"
        for e in bad_examples[:3]:
            prompt += f"- {e}\n"
    prompt += (
        "\nReply ONLY with a valid JSON object, no other text, no markdown:\n"
        '{"verdict": "approve" | "review" | "reject", '
        '"issues": ["short string", ...], '
        '"rating_0_100": <integer>, '
        '"reasoning": "<one paragraph>"}\n'
    )
    return prompt


def call_gemini_vision(image_bytes: bytes, prompt: str, retries: int = 3) -> dict | None:
    """Appelle Gemini Vision API avec image + prompt."""
    if not GEMINI_API_KEY:
        return None
    url = f"{API_BASE}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    img_b64 = base64.b64encode(image_bytes).decode("ascii")
    body = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                resp_data = json.loads(resp.read())
            text = resp_data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except Exception as exc:  # noqa: BLE001
            print(f"    retry {attempt+1}/{retries} : {type(exc).__name__}: {exc}")
            time.sleep(4 + attempt * 4)
    return None


def already_audited_recently(design_dir: Path) -> bool:
    audit_path = design_dir / "GEMINI_AUDIT.json"
    if not audit_path.exists():
        return False
    try:
        data = json.loads(audit_path.read_text())
        ts = datetime.fromisoformat(data["audited_at"].rstrip("Z"))
        return (datetime.utcnow() - ts).days < RECHECK_DAYS
    except Exception:
        return False


def write_gemini_audit(design_dir: Path, audit: dict, pipeline: str) -> None:
    audit_record = {
        "audited_at": datetime.utcnow().isoformat() + "Z",
        "pipeline": pipeline,
        "model": GEMINI_MODEL,
        **audit,
    }
    (design_dir / "GEMINI_AUDIT.json").write_text(
        json.dumps(audit_record, indent=2, ensure_ascii=False))


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not GEMINI_API_KEY:
        print("⊝ GEMINI_API_KEY non défini. Cet agent s'activera dès que")
        print("  Hugo aura ajouté GEMINI_API_KEY en secret GitHub.")
        print("  Pour le moment, agent_visual_audit (heuristique) fait le QC.")
        return 0

    if not PRODUCTS_DIR.exists():
        print(f"✗ {PRODUCTS_DIR} inexistant")
        return 1

    rules = load_rules()
    if not rules:
        print(f"✗ {RULES_PATH} introuvable ou vide")
        return 1

    print("=" * 70)
    print(f"GEMINI QUALITY CHECK — modèle {GEMINI_MODEL}")
    print("=" * 70)

    audits = []
    counters = {"approve": 0, "review": 0, "reject": 0, "skip": 0, "error": 0}
    processed = 0

    for meta_path in sorted(PRODUCTS_DIR.rglob("metadata.json")):
        if processed >= MAX_IMAGES:
            print(f"\n→ Limite {MAX_IMAGES} atteinte, arrêt.")
            break
        design_dir = meta_path.parent
        pipeline = detect_pipeline(design_dir)
        if "_rejected" in str(design_dir):
            continue
        if already_audited_recently(design_dir):
            counters["skip"] += 1
            continue

        preview = design_dir / "etsy_preview.jpg"
        if not preview.exists():
            preview = next(design_dir.glob("*.jpg"), None)
        if not preview or not preview.exists():
            continue

        try:
            metadata = json.loads(meta_path.read_text())
        except Exception:
            metadata = {}

        prompt = build_qc_prompt(pipeline, metadata, rules)
        try:
            img_bytes = preview.read_bytes()
        except Exception as exc:
            print(f"  ✗ {design_dir} : image illisible {exc}")
            counters["error"] += 1
            continue

        print(f"  [{processed+1:>3}] {pipeline} / "
              f"{design_dir.relative_to(PRODUCTS_DIR / pipeline)}")
        result = call_gemini_vision(img_bytes, prompt)
        processed += 1

        if not result:
            counters["error"] += 1
            print(f"         ✗ Gemini API failed")
            continue

        verdict = result.get("verdict", "review")
        counters[verdict] = counters.get(verdict, 0) + 1
        rating = result.get("rating_0_100", 50)
        issues = result.get("issues", [])

        icon = {"approve": "✓", "review": "⚠", "reject": "✗"}.get(verdict, "?")
        print(f"         {icon} {verdict.upper():<8} rating {rating}/100")
        if issues:
            print(f"         issues: {'; '.join(issues[:2])}")

        write_gemini_audit(design_dir, result, pipeline)
        audits.append({
            "design_path": str(design_dir.relative_to(PRODUCTS_DIR)),
            "pipeline": pipeline,
            **result,
        })

        # Auto-reject : déplace vers _rejected/
        if AUTO_REJECT and verdict == "reject":
            dest = REJECTED_DIR / pipeline / design_dir.relative_to(
                PRODUCTS_DIR / pipeline)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.move(str(design_dir), str(dest))
                print(f"         ⛔ moved to _rejected/")

        # Rate limiting Gemini gratuit : 15 req/min max
        time.sleep(4.5)

    # Rapport global
    report = {
        "audited_at": datetime.utcnow().isoformat() + "Z",
        "model": GEMINI_MODEL,
        "total_processed": processed,
        "counters": counters,
        "audits": audits,
    }
    out_path = DATA_DIR / "gemini_quality_report.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print(f"\n{'=' * 70}")
    print(f"BILAN Gemini Quality Check :")
    for k, v in counters.items():
        print(f"  {k:<10} {v}")
    print(f"\n→ Rapport : {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
