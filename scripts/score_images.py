"""
Juge IA des images générées — pré-notation automatique via Gemini Vision.

Principe : on génère 500 images avec generate_images.py, ce script les fait
toutes noter par Gemini selon les critères du livre (lus depuis meta_livre.py),
et produit image_scores.json avec un classement. Tu n'as plus qu'à examiner
les 50-100 mieux notées.

Économie typique : ~2h de tri manuel par livre.

Lit :
  - meta_livre.py (critères, accord visuel)
  - prompts.py    (prompt original de chaque image)
  - generated_images/ ou images/ (les images à noter)

Écrit :
  - image_scores.json : tableau trié par score décroissant
  - image_scores_log.txt : log lisible humain
"""

import base64
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

try:
    import google.generativeai as genai
except ImportError:
    print("ERREUR : google-generativeai n'est pas installé.")
    print("Le workflow GitHub Actions s'en charge automatiquement.")
    sys.exit(2)

try:
    from meta_livre import META
except ImportError:
    print("ERREUR : meta_livre.py absent à la racine du repo.")
    sys.exit(2)

try:
    from prompts import PROMPTS  # noqa: E402
except ImportError:
    PROMPTS = []
    print("AVERTISSEMENT : prompts.py absent. On notera sans contexte de prompt.")

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
TARGET_DIR_ARG = os.environ.get("TARGET_DIR", "generated_images")
TARGET_DIR = os.path.join(ROOT, TARGET_DIR_ARG)
DELAY_SECONDS = float(os.environ.get("SCORE_DELAY", "1.0"))
MAX_RETRIES = 3
RETRY_BACKOFF = [5, 15, 45]

if not API_KEY:
    print("ERREUR : GEMINI_API_KEY non fourni.")
    print("Va sur https://aistudio.google.com/app/apikey pour en créer une (gratuit),")
    print("puis ajoute-la dans Settings → Secrets du repo sous le nom GEMINI_API_KEY.")
    sys.exit(2)

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL_NAME)


def build_prompt(image_filename: str, original_prompt: str) -> str:
    crits = META["jugement_images"]["critères"]
    crits_txt = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(crits))
    thème = META["livre"]["thème"]
    accroche = META["marketing"]["accroche_courte"]
    return f"""Tu es directeur artistique pour Mirabilia Éditions, une maison française qui publie des livres-objets soignés en esthétique « cabinet de curiosités du XIXᵉ siècle ».

Tu juges une image qui doit illustrer une fiche du livre :
- Thème du livre : {thème}
- Accroche : {accroche}
- Fichier : {image_filename}
- Prompt original envoyé au générateur : "{original_prompt or '[inconnu]'}"

Note cette image de 1 à 5 sur les critères suivants :
{crits_txt}

Réponds UNIQUEMENT par un JSON strict de cette forme, sans préambule, sans markdown :

{{
  "scores": {{
    "critère_1": <int 1-5>,
    "critère_2": <int 1-5>,
    "critère_3": <int 1-5>,
    "critère_4": <int 1-5>
  }},
  "score_moyen": <float, moyenne arrondie à 0.1>,
  "verdict": "<une phrase honnête : forces principales et défauts éliminatoires s'il y en a>",
  "à_garder": <true si score_moyen >= {META['jugement_images']['seuil_acceptation']}, false sinon>
}}"""


def load_image_part(path: str) -> dict:
    with open(path, "rb") as f:
        data = f.read()
    return {"mime_type": "image/jpeg", "data": data}


def find_original_prompt(filename: str) -> str:
    base = os.path.splitext(filename)[0]
    parts = base.split("_", 1)
    if len(parts) < 2:
        return ""
    target_id = parts[0].lstrip("0") or "0"
    for entry in PROMPTS:
        if str(entry.get("id")) == target_id:
            return entry.get("prompt", "")
    for entry in PROMPTS:
        if entry.get("filename") in base:
            return entry.get("prompt", "")
    return ""


def score_one(image_path: str) -> dict | None:
    filename = os.path.basename(image_path)
    original_prompt = find_original_prompt(filename)
    text_prompt = build_prompt(filename, original_prompt)
    image_part = load_image_part(image_path)

    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(
                [text_prompt, image_part],
                generation_config={"temperature": 0.2, "response_mime_type": "application/json"},
            )
            raw = (response.text or "").strip()
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            return json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            err = f"{type(exc).__name__}: {exc}"
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF[attempt])
            else:
                return {"error": err}
    return None


def main() -> int:
    if not os.path.isdir(TARGET_DIR):
        print(f"ERREUR : dossier {TARGET_DIR} introuvable.")
        return 2

    images = sorted(
        f
        for f in os.listdir(TARGET_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        and not f.startswith(".")
    )
    if not images:
        print(f"Aucune image dans {TARGET_DIR}.")
        return 1

    print(f"Modèle : {MODEL_NAME}")
    print(f"Dossier : {TARGET_DIR}")
    print(f"Images à noter : {len(images)}")
    print(f"Seuil d'acceptation : {META['jugement_images']['seuil_acceptation']}/5")
    print()

    results = []
    for i, filename in enumerate(images, 1):
        path = os.path.join(TARGET_DIR, filename)
        print(f"[{i:>3}/{len(images)}] {filename} …", end=" ", flush=True)
        result = score_one(path)
        if not result or "error" in (result or {}):
            err = (result or {}).get("error", "réponse vide")
            print(f"✗ {err}")
            results.append({"filename": filename, "error": err, "score_moyen": 0.0})
        else:
            score = result.get("score_moyen", 0.0)
            keep = "✓" if result.get("à_garder") else "·"
            print(f"{keep} {score}/5")
            results.append({"filename": filename, **result})
        time.sleep(DELAY_SECONDS)

    results.sort(key=lambda r: r.get("score_moyen", 0.0), reverse=True)

    json_path = os.path.join(ROOT, META["sources"]["scores"])
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    log_path = os.path.join(ROOT, "image_scores_log.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Classement des {len(results)} images notées par {MODEL_NAME}\n")
        f.write(f"Seuil : {META['jugement_images']['seuil_acceptation']}/5\n\n")
        kept = sum(1 for r in results if r.get("à_garder"))
        f.write(f"À garder : {kept}  ·  À écarter : {len(results) - kept}\n\n")
        for r in results:
            mark = "✓" if r.get("à_garder") else " "
            f.write(f"{mark} {r.get('score_moyen', 0.0):>4.1f}  {r['filename']}\n")
            verdict = r.get("verdict") or r.get("error", "")
            f.write(f"        {verdict}\n")

    print()
    print("=" * 60)
    kept = sum(1 for r in results if r.get("à_garder"))
    print(f"Total notées : {len(results)}")
    print(f"À garder    : {kept}")
    print(f"À écarter   : {len(results) - kept}")
    print(f"JSON : {json_path}")
    print(f"Log  : {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
