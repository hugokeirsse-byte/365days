#!/usr/bin/env python3
"""AGENT NOVEL PLANNER - Brique 1 de l'usine Roman.

A partir d'un brief roman (genre, tone, audience), appelle Gemini
pour generer :
  - Synopsis executif (3 lignes)
  - Bible personnages (protagonist + antagonist + 2-3 secondaires)
  - Plan chapitres (35-40 chapitres, 1-2 phrases chacun)
  - Guide stylistique anti-IA (phrases interdites + patterns imposes)
  - Premier paragraphe "hook"

Ecrit le tout dans products/novels/<novel_id>/novel_plan.json
et products/novels/<novel_id>/NOVEL_PLAN.md (lisible par Hugo).

Gate : Hugo doit valider le plan avant que le writer tourne.

Variables d'env :
  NOVEL_ID       : identifiant unique (ex: romance_001_hidden_cove)
  GEMINI_API_KEY
  GEMINI_MODEL   : defaut gemini-2.5-flash
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOVELS_DIR = ROOT / "products" / "novels"
BRIEFS_DIR = ROOT / "data" / "novel_briefs"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_FALLBACKS = ["gemini-2.5-flash", "gemini-2.0-flash"]
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Phrases IA interdites - injectees dans chaque prompt d'ecriture
FORBIDDEN_PHRASES = [
    "the air crackled", "tension hung", "couldn't help but",
    "heart raced", "breath caught", "stomach dropped",
    "electricity in the air", "spine tingled", "mind reeled",
    "a smile played", "eyes widened", "jaw dropped",
    "she/he realized", "it hit him/her", "something shifted",
    "In conclusion", "It is worth noting", "Notably",
    "Moreover", "Furthermore", "tapestry of", "testament to",
    "palpable", "visceral", "resonate", "delve", "multifaceted",
]

STYLE_CONSTRAINTS = """CONTRAINTES DE STYLE ABSOLUES (anti-IA) :
- Phrases variees : alterner phrases courtes (5-8 mots) et longues (20-30 mots)
- MONTRER, ne pas dire : pas d'etats internes explicites ('il etait nerveux'),
  montrer par les gestes, la parole, les actions
- Dialogue naturel : les gens ne s'appellent pas par leur prenom dans chaque replique
- Pas de metaphores generiques : trouver des images specifiques au cadre
- Tempo : commencer IN MEDIAS RES, pas de description de reveil ou de miroir
- POV strict : 3e personne limite (on est DANS la tete du protagonist uniquement)
- PAS de resume ou transition explicite en fin de chapitre
"""


def call_gemini(prompt: str, max_tokens: int = 8192) -> str | None:
    if not GEMINI_API_KEY:
        return None
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": max_tokens},
    }).encode("utf-8")
    for model in [GEMINI_MODEL] + [m for m in GEMINI_FALLBACKS if m != GEMINI_MODEL]:
        url = f"{API_BASE}/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            req = urllib.request.Request(
                url, data=body,
                headers={"Content-Type": "application/json",
                         "User-Agent": "365days-NovelPlanner/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read())
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                continue
            time.sleep(5)
        except Exception:  # noqa: BLE001
            time.sleep(3)
    return None


def load_brief(novel_id: str) -> dict:
    """Charge le brief roman depuis data/novel_briefs/<id>.json."""
    bp = BRIEFS_DIR / f"{novel_id}.json"
    if bp.exists():
        return json.loads(bp.read_text(encoding="utf-8"))
    # Brief par defaut pour test
    return {
        "id": novel_id,
        "genre": "contemporary romance",
        "subgenre": "small town / second chance",
        "language": "en",
        "target_audience": "women 25-45",
        "tone": "warm, witty, emotionally intense",
        "setting": "coastal small town, present day",
        "word_target": 60000,
        "chapters_target": 38,
        "comp_titles": ["Beach Read by Emily Henry", "The Kiss Quotient by Helen Hoang"],
        "hook_concept": "An ex-couple reunited as co-owners of a failing lighthouse B&B",
        "protagonist": {"name": "Mae", "age": 32, "profession": "architecture restorer",
                        "flaw": "avoids emotional risk", "want": "sell and leave",
                        "need": "to trust again"},
        "love_interest": {"name": "Finn", "age": 35, "profession": "boat carpenter",
                          "flaw": "refuses to fight for what he wants",
                          "want": "keep the B&B alive", "need": "to ask for help"},
    }


def plan_prompt(brief: dict) -> str:
    comp = ", ".join(brief.get("comp_titles", []))
    return f"""You are a professional romance novelist. Create a detailed novel plan.

BRIEF:
- Genre: {brief['genre']} / {brief.get('subgenre', '')}
- Tone: {brief['tone']}
- Setting: {brief['setting']}
- Audience: {brief['target_audience']}
- Hook: {brief['hook_concept']}
- Protagonist: {json.dumps(brief.get('protagonist', {}))}
- Love interest: {json.dumps(brief.get('love_interest', {}))}
- Comp titles (write at this level): {comp}
- Word target: {brief.get('word_target', 60000)} words in {brief.get('chapters_target', 38)} chapters

{STYLE_CONSTRAINTS}

Provide a COMPLETE novel plan in this EXACT format (use these section headers):

## LOGLINE
[One sentence, 25 words max]

## CHARACTERS
[Detailed profiles for protagonist, love interest, and 2-3 supporting characters.
Include: appearance (2 specific details), voice/speech pattern, secret, wound, want vs need]

## THREE-ACT STRUCTURE
[Act 1 beats, Act 2 midpoint + dark night, Act 3 climax - 3-5 bullet points each]

## CHAPTER PLAN
[For each of {brief.get('chapters_target', 38)} chapters: Chapter N: [title] — [2 sentences: what happens + emotional shift]
Be specific. No vague summaries.]

## STYLE GUIDE
[5-7 specific writing rules for THIS story. Include: narrative voice, sentence rhythm,
dialogue style, recurring motifs, specific things to AVOID for this story]

## OPENING HOOK (first 200 words)
[Write the actual opening. Start with action or striking sensory detail. No weather, no mirror]
"""


def parse_plan(raw: str) -> dict:
    """Extrait les sections du plan Gemini."""
    sections = {}
    current = None
    buf = []
    for line in raw.splitlines():
        if line.startswith("## "):
            if current:
                sections[current] = "\n".join(buf).strip()
            current = line[3:].strip().upper().replace(" ", "_")
            buf = []
        elif current:
            buf.append(line)
    if current:
        sections[current] = "\n".join(buf).strip()
    return sections


def parse_chapters(chapter_section: str) -> list[dict]:
    """Extrait la liste de chapitres depuis la section CHAPTER_PLAN."""
    chapters = []
    for line in chapter_section.splitlines():
        line = line.strip()
        if not line or not (line.startswith("Chapter") or line[0].isdigit()):
            continue
        # Patterns : "Chapter 1: Title — desc" ou "1. Title — desc"
        import re
        m = re.match(r"(?:Chapter\s*)?(\d+)[.:][\s]*([^—\-]+)?[—\-]?(.*)$", line)
        if m:
            n = int(m.group(1))
            title = (m.group(2) or f"Chapter {n}").strip()
            desc = (m.group(3) or "").strip()
            chapters.append({"number": n, "title": title, "summary": desc, "status": "pending"})
    return chapters


def main() -> int:
    novel_id = os.environ.get("NOVEL_ID", "novel_test_001").strip()
    print("=" * 64)
    print(f"NOVEL PLANNER — {novel_id}")
    print("=" * 64)

    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY absent — impossible de generer le plan.")
        return 1

    brief = load_brief(novel_id)
    out_dir = NOVELS_DIR / novel_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Eviter de re-planifier si deja fait
    plan_path = out_dir / "novel_plan.json"
    if plan_path.exists():
        existing = json.loads(plan_path.read_text())
        if existing.get("status") in ("planned", "approved"):
            print(f"Plan deja present (status={existing['status']}). Rien a faire.")
            return 0

    print("Appel Gemini pour generer le plan...")
    raw = call_gemini(plan_prompt(brief), max_tokens=16384)
    if not raw:
        print("Echec Gemini.", file=sys.stderr)
        return 1

    sections = parse_plan(raw)
    chapters = parse_chapters(sections.get("CHAPTER_PLAN", ""))

    print(f"Plan genere : {len(chapters)} chapitres")

    plan = {
        "id": novel_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "status": "planned",  # -> 'approved' apres validation Hugo
        "brief": brief,
        "logline": sections.get("LOGLINE", ""),
        "characters": sections.get("CHARACTERS", ""),
        "three_act": sections.get("THREE-ACT_STRUCTURE", ""),
        "chapters": chapters,
        "style_guide": sections.get("STYLE_GUIDE", ""),
        "opening_hook": sections.get("OPENING_HOOK_(FIRST_200_WORDS)", ""),
        "word_target": brief.get("word_target", 60000),
        "chapters_target": brief.get("chapters_target", 38),
        "raw_plan": raw,
    }
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    # Fichier lisible par Hugo
    md = f"""# Roman Plan : {novel_id}

Genere le {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC

**Logline :** {plan['logline']}

---

## Personnages
{plan['characters']}

---

## Structure en 3 actes
{plan['three_act']}

---

## Plan chapitres ({len(chapters)} chapitres)
{sections.get('CHAPTER_PLAN', '')}

---

## Guide stylistique
{plan['style_guide']}

---

## Accroche (200 premiers mots)
{plan['opening_hook']}

---

**VALIDATION HUGO :** pour approuver ce plan et lancer l'ecriture :
```bash
# Dans le brief JSON, setter :
# human_gates.gate_plan = "approved"
```
"""
    (out_dir / "NOVEL_PLAN.md").write_text(md, encoding="utf-8")
    print(f"Plan ecrit -> {out_dir / 'NOVEL_PLAN.md'}")
    print("En attente de validation Hugo (gate_plan = approved).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
