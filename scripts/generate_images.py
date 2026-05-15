"""
Génère 365 images via Pollinations.ai depuis un fichier de prompts.

- Lit prompts.py à la racine (liste de dicts {id, filename, prompt[, seed]}).
- Appelle l'API publique Pollinations (Flux), gratuite, sans clé requise.
- Idempotent : skip les images déjà présentes (relance sûre).
- Commit intermédiaire toutes les COMMIT_EVERY images réussies pour que
  les workflows GitHub Actions long-running ne perdent jamais d'avancée.
- Retries avec backoff exponentiel sur les erreurs réseau / 429 / 5xx.
"""

import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

try:
    from prompts import PROMPTS  # noqa: E402
except ImportError:
    print("ERREUR : fichier prompts.py absent à la racine du repo.")
    print("Crée prompts.py en t'inspirant de prompts.example.py.")
    sys.exit(2)

GENERATED_DIR = os.path.join(ROOT, "generated_images")
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"
MODEL = (os.environ.get("POLLINATIONS_MODEL") or "flux").strip()
WIDTH = int(os.environ.get("POLLINATIONS_WIDTH") or "1024")
HEIGHT = int(os.environ.get("POLLINATIONS_HEIGHT") or "1024")
TOKEN = (os.environ.get("POLLINATIONS_TOKEN") or "").strip()

USER_AGENT = (
    "MirabiliaEditions-ImageRobot/1.0 "
    "(https://github.com/hugokeirsse-byte; +contact via GitHub)"
)
TIMEOUT_SECONDS = 180
DELAY_SECONDS = 2.0
MAX_RETRIES = 4
RETRY_BACKOFF = [5, 15, 30, 60]
COMMIT_EVERY = 20
MIN_IMAGE_BYTES = 2000  # en dessous, on considère que c'est une erreur HTML


def slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.UNICODE).strip()
    s = re.sub(r"[\s_-]+", "_", s)
    return s.strip("_")[:max_len] or "image"


def build_url(prompt: str, seed: int | None = None) -> str:
    encoded = urllib.parse.quote(prompt, safe="")
    params = [
        f"model={MODEL}",
        f"width={WIDTH}",
        f"height={HEIGHT}",
        "nologo=true",
        "private=true",
        "enhance=true",
    ]
    if seed is not None:
        params.append(f"seed={seed}")
    if TOKEN:
        params.append(f"token={urllib.parse.quote(TOKEN)}")
    return f"{POLLINATIONS_BASE}{encoded}?{'&'.join(params)}"


def generate(prompt: str, dest: str, seed: int | None = None) -> tuple[bool, str]:
    url = build_url(prompt, seed)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_err = ""
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                data = resp.read()
            if len(data) < MIN_IMAGE_BYTES:
                raise ValueError(
                    f"Réponse anormalement courte ({len(data)} octets)"
                )
            with open(dest, "wb") as f:
                f.write(data)
            return True, f"{len(data) // 1024} KB"
        except Exception as exc:  # noqa: BLE001
            last_err = f"{type(exc).__name__}: {exc}"
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF[attempt])
    return False, last_err


def git_checkpoint(label: str) -> None:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    branch = os.environ.get("GITHUB_REF_NAME", "")
    try:
        subprocess.run(["git", "add", "generated_images/"], check=True, cwd=ROOT)
        diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet"], cwd=ROOT
        ).returncode
        if diff == 0:
            return
        subprocess.run(
            ["git", "commit", "-m", f"Checkpoint images IA : {label}"],
            check=True,
            cwd=ROOT,
        )
        if branch:
            for attempt in range(5):
                push = subprocess.run(
                    ["git", "push", "origin", f"HEAD:{branch}"], cwd=ROOT
                )
                if push.returncode == 0:
                    break
                print(f"  ⟲ push rejeté, rebase + retry {attempt + 1}/5")
                subprocess.run(
                    ["git", "pull", "--rebase", "origin", branch],
                    cwd=ROOT, check=False,
                )
        print(f"  → checkpoint pushé : {label}")
    except subprocess.CalledProcessError as exc:
        print(f"  ! checkpoint en échec : {exc}")


def main() -> int:
    os.makedirs(GENERATED_DIR, exist_ok=True)
    print(f"Prompts à traiter : {len(PROMPTS)}")
    print(f"Modèle : {MODEL} · résolution : {WIDTH}x{HEIGHT}")
    print(f"Authentifié : {'oui' if TOKEN else 'non (anonyme)'}")
    print()

    generated = skipped = failed = 0
    failures = []
    since_last_commit = 0

    for i, entry in enumerate(PROMPTS, 1):
        eid = str(entry.get("id", i))
        slug = slugify(entry.get("filename") or entry.get("name", "") or eid)
        filename = f"{eid.zfill(3)}_{slug}.jpg"
        dest = os.path.join(GENERATED_DIR, filename)
        prompt = entry["prompt"]
        seed = entry.get("seed")

        if os.path.exists(dest) and os.path.getsize(dest) > MIN_IMAGE_BYTES:
            skipped += 1
            print(f"[{i:>3}/{len(PROMPTS)}] SKIP  {filename}")
            continue

        preview = prompt[:60].replace("\n", " ")
        print(f"[{i:>3}/{len(PROMPTS)}] GEN   {filename}  ← {preview}…")
        ok, info = generate(prompt, dest, seed)
        if ok:
            generated += 1
            since_last_commit += 1
            print(f"                  ✓ {info}")
            if since_last_commit >= COMMIT_EVERY:
                git_checkpoint(f"{generated} images générées")
                since_last_commit = 0
        else:
            failed += 1
            failures.append((filename, info))
            print(f"                  ✗ {info}")

        time.sleep(DELAY_SECONDS)

    print()
    print("=" * 60)
    print(f"Générées : {generated}")
    print(f"Ignorées : {skipped}")
    print(f"Échecs   : {failed}")

    if failures:
        log_path = os.path.join(ROOT, "generation_failures.log")
        with open(log_path, "w") as f:
            for filename, info in failures:
                f.write(f"{filename}\t{info}\n")
        print(f"Log des échecs : {log_path}")

    if generated == 0 and skipped == 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
