#!/usr/bin/env python3
"""
Rédaction automatique des chapitres d'un roman KDP depuis un CdC approuvé.

Pipeline :
  1. Lit NOVEL_DIR (env) ou cherche le dernier roman avec gate_cdc=approved
  2. Vérifie gate_cdc == "approved" — sort proprement sinon
  3. Lit plan_38_chapitres, guide_style, personnages, identite_commerciale
  4. Crée products/novels/{slug}/chapters/
  5. Pour chaque chapitre (1–38) :
       - Skip si ch_{nn:02d}.txt existe (reprise idempotente)
       - Appel LLM via brain_utils.llm_call("roman_writer", ...)
       - Sauvegarde du texte brut
       - Fallback placeholder en cas d'échec
  6. Assemble manuscript.txt (en-têtes + contenu)
  7. Compte le nombre de mots, vérifie ≥ 50 000
  8. Met à jour cdc.json avec production_status + gate_production

Variables d'env :
  NOVEL_DIR     — chemin du dossier roman (products/novels/{slug})
                  si absent, cherche le premier roman avec gate_cdc=approved
                  sans production_status déjà renseigné
  GROQ_API_KEY  — obligatoire (roman_writer → Groq / Llama-3.3-70b)
"""

import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

# ── path bootstrap ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.lib.brain_utils import llm_call  # noqa: E402

# ── constantes ────────────────────────────────────────────────────────────────
NOVELS_DIR = ROOT / "products" / "novels"
TOTAL_CHAPTERS = 38
MIN_WORDS = 50_000
TARGET_WORDS_PER_CHAPTER = 1700   # 1500–1800 selon spec
SLEEP_BETWEEN_CALLS = 1            # secondes entre appels LLM


# ─────────────────────────────────────────────────────────────────────────────
# Utilitaires
# ─────────────────────────────────────────────────────────────────────────────

def count_words(text: str) -> int:
    """Compte les mots (séquences alphanumériques)."""
    return len(re.findall(r"\b\w+\b", text))


def last_200_words(text: str) -> str:
    """Retourne les ~200 derniers mots d'un texte (pour continuité narrative)."""
    words = text.split()
    return " ".join(words[-200:]) if len(words) > 200 else text


def build_characters_block(personnages: list) -> str:
    """Formate les fiches personnages en bloc compact pour le prompt."""
    lines = []
    for p in personnages:
        nom = p.get("nom", "?")
        role = p.get("role", "?")
        physique = p.get("description_physique", "")
        perso = p.get("personnalite", "")
        arc = p.get("arc_narratif", "")
        voice = p.get("voice", "")
        lines.append(
            f"- {nom} ({role}) | Physique: {physique} | "
            f"Personnalité: {perso} | Arc: {arc} | Voix: {voice}"
        )
    return "\n".join(lines) if lines else "(personnages non définis)"


def build_style_block(guide_style: dict) -> str:
    """Formate le guide de style en bloc compact pour le prompt système."""
    ton = guide_style.get("ton_general", "")
    voix = guide_style.get("voix_narrative", "3e personne limitée")
    sensualite = guide_style.get("niveau_sensualite", "warm")
    longueur = guide_style.get("longueur_scene_type", "")
    pacing = guide_style.get("pacing", "")
    tropes_ok = ", ".join(guide_style.get("tropes_utilises", []))
    tropes_non = ", ".join(guide_style.get("tropes_a_eviter", []))
    return (
        f"Ton: {ton}\n"
        f"Voix narrative: {voix}\n"
        f"Niveau sensualité: {sensualite}\n"
        f"Longueur scène type: {longueur}\n"
        f"Pacing: {pacing}\n"
        f"Tropes à utiliser: {tropes_ok}\n"
        f"Tropes à éviter: {tropes_non}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────────────────────────────────────

def build_system_prompt(cdc: dict) -> str:
    """Prompt système : fiches personnages + guide de style + instructions."""
    personnages = cdc.get("personnages", [])
    guide_style = cdc.get("guide_style", {})
    concept = cdc.get("concept", {})
    langue = concept.get("langue", "en")

    chars_block = build_characters_block(personnages)
    style_block = build_style_block(guide_style)

    return f"""Tu es un romancier professionnel de fiction populaire.

== PERSONNAGES ==
{chars_block}

== GUIDE DE STYLE ==
{style_block}

== INSTRUCTIONS ==
- Écris UNIQUEMENT ce chapitre, 1500-1800 mots, en {langue}.
- Commence par une action, un dialogue ou une image forte — jamais par la météo ou un réveil.
- Reste dans le POV indiqué pour ce chapitre.
- Montre les émotions par les gestes et sensations physiques, pas par des étiquettes ("elle était triste").
- Varie la longueur des phrases : alternes phrases courtes (choc) et longues (flux).
- Termine sur un moment de tension, une question ouverte, une micro-révélation — jamais une résolution calme.
- Aucun titre, aucun numéro, aucune note auteur dans le texte.
- Texte narratif pur uniquement."""


def build_user_prompt(chapitre: dict, prev_ending: str) -> str:
    """Prompt utilisateur : titre + synopsis + hook + contexte précédent."""
    numero = chapitre.get("numero", "?")
    titre = chapitre.get("titre", "")
    pov = chapitre.get("pov", "")
    synopsis = chapitre.get("synopsis", "")
    hook_fin = chapitre.get("hook_fin", "")

    contexte = (
        f"Le chapitre précédent se terminait ainsi (derniers mots) :\n"
        f"\"{prev_ending}\"\n\n"
        if prev_ending
        else "C'est le premier chapitre du roman.\n\n"
    )

    return (
        f"{contexte}"
        f"Chapitre {numero} : {titre}\n"
        f"POV : {pov}\n\n"
        f"Synopsis : {synopsis}\n\n"
        f"Hook de fin attendu : {hook_fin}\n\n"
        f"Écris maintenant le texte complet de ce chapitre (1500-1800 mots)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Production des chapitres
# ─────────────────────────────────────────────────────────────────────────────

def write_chapter(
    n: int,
    chapitre: dict,
    chapters_dir: Path,
    system_prompt: str,
    prev_ending: str,
) -> tuple[str, bool]:
    """
    Écrit un chapitre et le sauvegarde.

    Retourne (texte, success).
    En cas d'échec LLM, sauvegarde un placeholder et retourne (placeholder, False).
    """
    ch_path = chapters_dir / f"ch_{n:02d}.txt"

    # --- Idempotence : skip si déjà écrit ---
    if ch_path.exists():
        text = ch_path.read_text(encoding="utf-8")
        wc = count_words(text)
        print(f"[Ch.{n:02d}/38] (déjà écrit — {wc} mots) SKIP")
        return text, True

    user_prompt = build_user_prompt(chapitre, prev_ending)

    text = llm_call(
        "roman_writer",
        system_prompt,
        user_prompt,
        temperature=0.85,
        max_tokens=3000,
        json_mode=False,
    )

    if not text or count_words(text) < 400:
        placeholder = f"[ÉCHEC CHAPITRE {n} — À RÉGÉNÉRER]\n"
        ch_path.write_text(placeholder, encoding="utf-8")
        titre = chapitre.get("titre", "")
        print(f"[Ch.{n:02d}/38] ECHEC LLM — placeholder sauvegardé ({titre})",
              file=sys.stderr)
        return placeholder, False

    ch_path.write_text(text, encoding="utf-8")
    titre = chapitre.get("titre", "")
    wc = count_words(text)
    print(f"[Ch.{n:02d}/38] {titre} ({wc} mots)")
    return text, True


# ─────────────────────────────────────────────────────────────────────────────
# Assemblage du manuscrit
# ─────────────────────────────────────────────────────────────────────────────

def assemble_manuscript(
    chapters_dir: Path,
    plan: list,
    titre_roman: str,
    nom_de_plume: str,
) -> tuple[Path, int]:
    """
    Assemble tous les chapitres en un seul manuscript.txt.

    Retourne (path_manuscrit, total_mots).
    """
    lines = [
        f"{titre_roman}",
        f"par {nom_de_plume}",
        "",
        "=" * 70,
        "",
    ]
    total_words = 0

    for chapitre in sorted(plan, key=lambda c: c.get("numero", 0)):
        n = chapitre.get("numero", 0)
        titre = chapitre.get("titre", f"Chapitre {n}")
        ch_path = chapters_dir / f"ch_{n:02d}.txt"

        lines.append("")
        lines.append(f"CHAPITRE {n} — {titre}")
        lines.append("-" * 50)
        lines.append("")

        if ch_path.exists():
            text = ch_path.read_text(encoding="utf-8")
            lines.append(text)
            total_words += count_words(text)
        else:
            placeholder = f"[CHAPITRE {n} MANQUANT — À RÉGÉNÉRER]\n"
            lines.append(placeholder)

        lines.append("")

    manuscript_path = chapters_dir.parent / "manuscript.txt"
    manuscript_path.write_text("\n".join(lines), encoding="utf-8")
    return manuscript_path, total_words


# ─────────────────────────────────────────────────────────────────────────────
# Localisation du roman à produire
# ─────────────────────────────────────────────────────────────────────────────

def find_novel_dir() -> Path | None:
    """
    Cherche le premier dossier roman avec gate_cdc=approved
    et sans production_status déjà renseigné.
    """
    if not NOVELS_DIR.exists():
        return None

    candidates = []
    for d in sorted(NOVELS_DIR.iterdir()):
        if not d.is_dir():
            continue
        cdc_path = d / "cdc.json"
        if not cdc_path.exists():
            continue
        try:
            cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
            if cdc.get("gate_cdc") == "approved" and not cdc.get("production_status"):
                candidates.append((d.stat().st_mtime, d))
        except Exception:
            continue

    if not candidates:
        return None
    # Prend le plus récent
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


# ─────────────────────────────────────────────────────────────────────────────
# Point d'entrée principal
# ─────────────────────────────────────────────────────────────────────────────

def run() -> int:
    # ── 1. Résolution du dossier roman ───────────────────────────────────────
    lc_dir_env = os.environ.get("NOVEL_DIR", os.environ.get("LC_DIR", "")).strip()

    if lc_dir_env:
        novel_dir = (
            Path(lc_dir_env)
            if Path(lc_dir_env).is_absolute()
            else ROOT / lc_dir_env
        )
    else:
        novel_dir = find_novel_dir()

    if novel_dir is None:
        print("[Roman] Aucun roman avec gate_cdc=approved trouvé dans products/novels/")
        print("[Roman] Générez d'abord un CdC : python scripts/agent_cdc_roman.py")
        return 0

    cdc_path = novel_dir / "cdc.json"
    if not cdc_path.exists():
        print(f"[Roman] cdc.json introuvable dans {novel_dir}", file=sys.stderr)
        return 1

    print(f"[Roman] Production depuis : {novel_dir}")

    # ── 2. Lecture et vérification du CdC ────────────────────────────────────
    cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
    gate = cdc.get("gate_cdc", "pending")

    if gate == "pending":
        print("[Roman] GATE = pending. Hugo doit valider le CdC avant production.")
        print(f"[Roman] Ouvrez {cdc_path} et passez gate_cdc à 'approved'.")
        return 0
    elif gate == "rejected":
        print("[Roman] GATE = rejected. Production annulée.")
        return 0
    elif gate != "approved":
        print(f"[Roman] GATE = {gate!r} (valeur inconnue). Production annulée.")
        return 0

    # ── 3. Extraction des données du CdC ─────────────────────────────────────
    plan_38 = cdc.get("plan_38_chapitres", [])
    if not plan_38:
        print("[Roman] plan_38_chapitres vide dans cdc.json", file=sys.stderr)
        return 1

    identite = cdc.get("identite_commerciale", {})
    nom_de_plume = identite.get("nom_de_plume", "Auteur Inconnu")
    concept = cdc.get("concept", {})
    titre_roman = concept.get("titre_principal", novel_dir.name)
    langue = concept.get("langue", "en")

    print(f"[Roman] Titre    : {titre_roman}")
    print(f"[Roman] Auteur   : {nom_de_plume}")
    print(f"[Roman] Langue   : {langue}")
    print(f"[Roman] Chapitres: {len(plan_38)}")

    # ── 4. Création du dossier chapitres ─────────────────────────────────────
    chapters_dir = novel_dir / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    # ── 5. Prompt système (constant pour tout le roman) ──────────────────────
    system_prompt = build_system_prompt(cdc)

    # ── 6. Boucle d'écriture ─────────────────────────────────────────────────
    print("=" * 70)
    print(f"PRODUCTION ROMAN : {titre_roman}")
    print("=" * 70)

    prev_ending = ""
    chapters_written = 0
    chapters_failed = 0

    plan_sorted = sorted(plan_38, key=lambda c: c.get("numero", 0))

    for chapitre in plan_sorted:
        n = chapitre.get("numero", 0)
        if n < 1 or n > TOTAL_CHAPTERS:
            continue

        ch_path = chapters_dir / f"ch_{n:02d}.txt"
        already_existed = ch_path.exists()

        text, success = write_chapter(
            n=n,
            chapitre=chapitre,
            chapters_dir=chapters_dir,
            system_prompt=system_prompt,
            prev_ending=prev_ending,
        )

        if success:
            # Mettre à jour le contexte pour le prochain chapitre
            prev_ending = last_200_words(text)
            if not already_existed:
                chapters_written += 1
        else:
            chapters_failed += 1
            # Ne pas mettre à jour prev_ending sur échec : réutilise le dernier bon

        # Petite pause entre appels (sauf si skip)
        if not already_existed:
            time.sleep(SLEEP_BETWEEN_CALLS)

    # ── 7. Assemblage du manuscrit ────────────────────────────────────────────
    print("")
    print("[Roman] Assemblage du manuscrit...")
    manuscript_path, total_words = assemble_manuscript(
        chapters_dir=chapters_dir,
        plan=plan_sorted,
        titre_roman=titre_roman,
        nom_de_plume=nom_de_plume,
    )
    print(f"[Roman] Manuscrit : {manuscript_path}")

    # ── 8. Résumé ─────────────────────────────────────────────────────────────
    chapters_on_disk = len(list(chapters_dir.glob("ch_*.txt")))
    print("")
    print("=" * 70)
    print(f"RÉSUMÉ DE PRODUCTION")
    print(f"  Chapitres écrits (cette session) : {chapters_written}")
    print(f"  Chapitres en échec                : {chapters_failed}")
    print(f"  Chapitres sur disque              : {chapters_on_disk}")
    print(f"  Mots totaux (manuscrit)           : {total_words:,}")
    print(f"  Seuil minimum                     : {MIN_WORDS:,}")
    print("=" * 70)

    # ── 9. Mise à jour cdc.json ───────────────────────────────────────────────
    gate_production = "complete" if total_words >= MIN_WORDS else "incomplete"
    cdc["production_status"] = {
        "date": date.today().isoformat(),
        "word_count": total_words,
        "chapters_written": chapters_on_disk,
        "chapters_failed": chapters_failed,
        "manuscript_path": (
            str(manuscript_path.relative_to(ROOT))
            if manuscript_path.is_relative_to(ROOT)
            else str(manuscript_path)
        ),
        "gate_production": gate_production,
    }
    cdc_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Roman] cdc.json mis à jour — gate_production={gate_production}")

    # ── 10. Code de sortie ────────────────────────────────────────────────────
    if total_words < MIN_WORDS:
        print(
            f"\n[Roman] INCOMPLET : {total_words:,} mots < {MIN_WORDS:,} minimum.",
            file=sys.stderr,
        )
        print(
            "[Roman] Relancez le script pour compléter les chapitres manquants.",
            file=sys.stderr,
        )
        return 1

    print(f"\n[Roman] ✓ Roman complet : {total_words:,} mots — prêt pour relecture.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
