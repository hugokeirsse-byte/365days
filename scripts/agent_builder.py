#!/usr/bin/env python3
"""BUILDER — la machine qui construit l'usine.

Transforme un BRIEFING (cahier des charges technique en .md) en CODE, via Gemini.
But : DELEGUER l'ecriture du code a Gemini (gratuit) au lieu que Claude le tape
a la main. Claude n'ecrit plus que de petits briefings ; Gemini produit le fichier ;
Hugo/Claude valident.

Convention d'un briefing.md :
  - une ligne `TARGET: chemin/du/fichier.py`
  - le reste = description, entrees, sorties, contraintes, dependances autorisees.

Usage (en CI, Gemini dispo) :
  BRIEFING=data/build_queue/xxx.md python scripts/agent_builder.py
  (sinon prend le 1er .md de data/build_queue/ non encore construit)

Ecrit le fichier cible, deplace le briefing dans data/build_queue/done/.
NE COMMIT PAS (le workflow CI s'en charge).
"""
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "data" / "build_queue"
DONE = QUEUE / "done"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_FALLBACKS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def call_gemini_text(prompt, retries=2):
    """Appelle Gemini en mode texte libre (plus fiable pour le code)."""
    if not GEMINI_API_KEY:
        return None, "GEMINI_API_KEY absent"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 16384},
    }).encode("utf-8")
    last = "inconnu"
    for model in [GEMINI_MODEL] + [m for m in GEMINI_FALLBACKS if m != GEMINI_MODEL]:
        url = f"{API_BASE}/{model}:generateContent?key={GEMINI_API_KEY}"
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, data=body,
                    headers={"Content-Type": "application/json", "User-Agent": "365days-Builder/1.0"})
                with urllib.request.urlopen(req, timeout=180) as r:
                    data = json.loads(r.read())
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text, model
            except urllib.error.HTTPError as exc:
                last = f"{model}: HTTP {exc.code}"
                if exc.code == 404:
                    break
                time.sleep(3 + attempt * 3)
            except Exception as exc:  # noqa: BLE001
                last = f"{model}: {type(exc).__name__}"
                time.sleep(2 + attempt * 2)
    return None, last


def extract_code(text):
    """Extrait le code Python de la réponse Gemini (markdown ou texte brut)."""
    # Cherche un bloc ```python ... ``` ou ``` ... ```
    m = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Fallback : retourner le texte brut si ça ressemble à du Python
    stripped = text.strip()
    if stripped.startswith(("#!/", "import ", "from ", "#", "def ", "class ")):
        return stripped
    return None


def pick_briefing():
    env = os.environ.get("BRIEFING", "").strip()
    if env:
        p = Path(env)
        return p if p.exists() else None
    QUEUE.mkdir(parents=True, exist_ok=True)
    for p in sorted(QUEUE.glob("*.md")):
        return p
    return None


def main():
    print("=" * 60)
    print("BUILDER — briefing.md -> code (via Gemini)")
    print("=" * 60)
    if not GEMINI_API_KEY:
        print("⊝ GEMINI_API_KEY absent. Le Builder ne tourne qu'en CI (Gemini requis).")
        return 0
    bf = pick_briefing()
    if not bf:
        print("Aucun briefing en attente dans data/build_queue/.")
        return 0
    text = bf.read_text(encoding="utf-8")
    m = re.search(r"^TARGET:\s*(\S+)", text, re.MULTILINE)
    if not m:
        print(f"✗ {bf.name} : ligne 'TARGET: chemin' manquante.")
        return 1
    target = m.group(1)
    print(f"Briefing : {bf.name}  ->  cible : {target}")

    prompt = (
        "Tu es un developpeur Python senior. A partir du CAHIER DES CHARGES ci-dessous, "
        "ecris le FICHIER COMPLET demande. Code robuste, commente sobrement, sans dependances "
        "lourdes hors celles autorisees.\n"
        "Reponds UNIQUEMENT avec le code Python dans un bloc ```python ... ```. "
        "Rien d'autre avant ou apres le bloc.\n\n"
        "=== CAHIER DES CHARGES ===\n" + text
    )
    raw, info = call_gemini_text(prompt)
    if not raw:
        print(f"✗ Gemini n'a pas repondu ({info}).")
        return 2
    code = extract_code(raw)
    if not code:
        print(f"✗ Impossible d'extraire le code de la reponse Gemini ({info}).")
        print(f"  Debut reponse : {raw[:200]}")
        return 2
    out = ROOT / target
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(code, encoding="utf-8")
    print(f"✓ Code ecrit par Gemini ({info}) : {out}  ({len(code)} car.)")

    # verif syntaxe si Python
    if str(out).endswith(".py"):
        import py_compile
        try:
            py_compile.compile(str(out), doraise=True)
            print("  py_compile OK")
        except Exception as exc:  # noqa: BLE001
            print(f"  ⚠ py_compile ECHEC : {exc} (a valider par Claude/Hugo)")

    DONE.mkdir(parents=True, exist_ok=True)
    bf.rename(DONE / bf.name)
    print(f"  briefing archive -> {DONE / bf.name}")
    print("  -> a VALIDER avant usage (Claude relit, Hugo approuve).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
