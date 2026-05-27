#!/usr/bin/env python3
"""AGENT NOVEL WRITER - Brique 2 de l'usine Roman.

Ecrit les chapitres un par un, en injectant le contexte du chapitre precedent
pour maintenir la coherence. Chaque chapitre = 1 appel Gemini (~1500-1800 mots).
Idempotent : saute les chapitres deja ecrits.

Gate : necessite human_gates.gate_plan == 'approved' dans novel_plan.json.
Si un chapitre echoue, on continue avec le suivant (mode resilient).

Variables d'env :
  NOVEL_ID, GEMINI_API_KEY, GEMINI_MODEL
  START_CHAPTER  : reprendre a partir de ce numero (defaut: 1)
  MAX_CHAPTERS   : ecrire au max N chapitres (defaut: tous)
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOVELS_DIR = ROOT / "products" / "novels"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_FALLBACKS = ["gemini-2.5-flash", "gemini-2.0-flash"]
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

FORBIDDEN_PHRASES = [
    "the air crackled", "tension hung", "couldn't help but",
    "heart raced", "breath caught", "stomach dropped",
    "electricity in the air", "spine tingled", "mind reeled",
    "a smile played", "eyes widened", "jaw dropped",
    "she realized", "he realized", "it hit her", "it hit him",
    "something shifted between", "In conclusion", "It is worth noting",
    "tapestry of", "testament to", "palpable", "visceral",
    "resonate", "delve", "multifaceted",
]


def call_gemini(prompt: str, max_tokens: int = 2500) -> str | None:
    if not GEMINI_API_KEY:
        return None
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.92, "maxOutputTokens": max_tokens,
                             "topP": 0.95, "topK": 40},
    }).encode("utf-8")
    for model in [GEMINI_MODEL] + [m for m in GEMINI_FALLBACKS if m != GEMINI_MODEL]:
        url = f"{API_BASE}/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            req = urllib.request.Request(
                url, data=body,
                headers={"Content-Type": "application/json",
                         "User-Agent": "365days-NovelWriter/1.0"})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read())
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                continue
            time.sleep(8)
        except Exception:  # noqa: BLE001
            time.sleep(5)
    return None


def chapter_prompt(plan: dict, chapter: dict, previous_ending: str) -> str:
    brief = plan["brief"]
    forbidden = "\n".join(f'- "{p}"' for p in FORBIDDEN_PHRASES)
    context = (
        f"Previous chapter ended with:\n---\n{previous_ending}\n---\n"
        if previous_ending else "This is the opening chapter."
    )
    return f"""You are writing a {brief.get('genre', 'romance')} novel.
This is Chapter {chapter['number']} of {plan.get('chapters_target', 38)}.

STORY CONTEXT:
- Setting: {brief.get('setting', '')}
- Tone: {brief.get('tone', '')}
- Protagonist: {json.dumps(brief.get('protagonist', {}))}
- Love interest: {json.dumps(brief.get('love_interest', {}))}

CHAPTER GOAL:
{chapter.get('summary', 'Continue the story naturally.')}

STYLE GUIDE:
{plan.get('style_guide', '')}

FORBIDDEN phrases (NEVER use these):
{forbidden}

CONTEXT FROM PREVIOUS CHAPTER:
{context}

WRITING RULES:
- Write EXACTLY this chapter, 1400-1800 words
- Start with immediate action or dialogue, NOT with weather or description of waking up
- Use tight 3rd person limited POV (stay in protagonist's head only)
- Show emotions through physical sensation and behavior, NOT labels ('she was nervous')
- Vary sentence length: mix 4-word punches with longer sentences
- End the chapter at a moment of tension or change, not a resolution
- Write ONLY the chapter text, no title, no headers, no author notes
"""


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def check_ai_phrases(text: str) -> list[str]:
    return [p for p in FORBIDDEN_PHRASES if p.lower() in text.lower()]


def main() -> int:
    novel_id = os.environ.get("NOVEL_ID", "").strip()
    if not novel_id:
        print("NOVEL_ID manquant.", file=sys.stderr)
        return 1

    start = int(os.environ.get("START_CHAPTER", "1"))
    max_ch = int(os.environ.get("MAX_CHAPTERS", "999"))

    novel_dir = NOVELS_DIR / novel_id
    plan_path = novel_dir / "novel_plan.json"
    if not plan_path.exists():
        print(f"novel_plan.json absent pour {novel_id}", file=sys.stderr)
        return 1

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("status") != "approved":
        print(f"Plan non approuve (status={plan.get('status')}). Hugo doit valider d'abord.")
        return 0

    chapters_dir = novel_dir / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    chapters = plan.get("chapters", [])
    total = len(chapters)
    written = 0
    skipped = 0
    failed = 0
    previous_ending = ""

    print(f"=" * 60)
    print(f"NOVEL WRITER : {novel_id} | chapitres {start}-{min(start+max_ch-1, total)}")
    print(f"=" * 60)

    for ch in chapters:
        n = ch["number"]
        if n < start or written >= max_ch:
            # Charger le dernier chapitre existant pour contexte
            cp = chapters_dir / f"chapter_{n:03d}.txt"
            if cp.exists():
                text = cp.read_text(encoding="utf-8")
                previous_ending = " ".join(text.split()[-200:])
            continue

        ch_path = chapters_dir / f"chapter_{n:03d}.txt"
        if ch_path.exists():
            print(f"Chapter {n:03d} deja ecrit — skip.")
            text = ch_path.read_text(encoding="utf-8")
            previous_ending = " ".join(text.split()[-200:])
            skipped += 1
            continue

        print(f"Writing chapter {n:03d}: {ch.get('title', '')}...")
        prompt = chapter_prompt(plan, ch, previous_ending)
        text = call_gemini(prompt, max_tokens=2500)

        if not text or count_words(text) < 800:
            print(f"  ECHEC chapter {n} (reponse vide ou trop courte)", file=sys.stderr)
            failed += 1
            continue

        # Audit rapide anti-IA
        bad = check_ai_phrases(text)
        words = count_words(text)
        if bad:
            print(f"  ATTENTION: {len(bad)} phrase(s) IA detectees: {bad[:3]}")

        ch_path.write_text(text, encoding="utf-8")
        previous_ending = " ".join(text.split()[-200:])

        # Mise a jour statut dans le plan
        ch["status"] = "written"
        ch["word_count"] = words
        ch["ai_phrases_detected"] = bad
        ch["written_at"] = datetime.utcnow().isoformat() + "Z"

        print(f"  OK: {words} mots | AI flags: {len(bad)}")
        written += 1
        time.sleep(1)  # Rate limiting

    # Sauvegarder le plan avec statuts mis a jour
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    total_written = sum(1 for ch in chapters if ch.get("status") == "written")
    total_words = sum(ch.get("word_count", 0) for ch in chapters)
    print(f"\n{total_written}/{total} chapitres ecrits | {total_words} mots | {failed} echecs")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
