"""
Auditeur anti-IA — détecte et signale les marqueurs d'écriture IA.

Aucun appel API. Que des regex + statistiques sur le texte.
Tourne en quelques secondes sur un manuscrit de 80k mots.

3 passes :
1. Mots-tatoués IA (liste noire) → comptés + suggestions de remplacement
2. Patterns syntaxiques IA → détectés et signalés
3. Statistiques de répétition → mots/phrases surutilisés

Score AI-likeness 0-100 :
  < 25  : passe (humain crédible)
  25-50 : à corriger (quelques passes de réécriture nécessaires)
  > 50  : trop IA, à régénérer totalement le passage

Usage :
    python scripts/anti_ai_audit.py manuscript.txt
    python scripts/anti_ai_audit.py manuscript.txt --replace
        → réécrit auto les mots-tatoués (synonyme aléatoire)
"""

import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────
# 1. MOTS-TATOUÉS IA (avec synonymes humains de remplacement)
# ─────────────────────────────────────────────────────────────────────

AI_TATTOO_WORDS = {
    # Verbes IA-typiques
    "delve": ["explore", "examine", "look into", "dig into", "study"],
    "delves": ["explores", "examines", "digs into", "studies"],
    "delving": ["exploring", "examining", "digging into"],
    "delved": ["explored", "examined", "looked into"],
    "navigate": ["handle", "deal with", "work through", "manage"],
    "navigates": ["handles", "deals with", "manages"],
    "navigating": ["handling", "managing", "dealing with"],
    "embark": ["start", "begin", "set off on"],
    "embarks": ["starts", "begins"],
    "embarked": ["started", "began"],
    "leverage": ["use", "tap into", "rely on", "apply"],
    "leverages": ["uses", "applies", "taps"],
    "leveraging": ["using", "tapping into", "applying"],
    "leveraged": ["used", "applied"],
    "foster": ["build", "create", "nurture", "grow"],
    "fosters": ["builds", "creates"],
    "fostering": ["building", "creating", "growing"],
    "fostered": ["built", "created", "grew"],
    "underscore": ["highlight", "show", "make clear", "stress"],
    "underscores": ["highlights", "stresses", "shows"],
    "underscored": ["highlighted", "stressed"],
    "underpin": ["support", "back", "hold up"],
    "underpins": ["supports", "backs"],
    "showcase": ["show", "display", "present"],
    "showcases": ["shows", "displays"],
    "resonate": ["hit", "land", "strike a chord", "speak to"],
    "resonates": ["hits", "speaks to"],
    "resonated": ["hit", "struck a chord"],
    # Adjectifs/noms IA-typiques
    "tapestry": ["mix", "blend", "patchwork", "web", "weave"],
    "labyrinth": ["maze", "web", "twist of paths"],
    "labyrinthine": ["maze-like", "twisting", "confusing"],
    "myriad": ["countless", "many", "tons of", "endless"],
    "plethora": ["lots of", "tons of", "no shortage of", "plenty of"],
    "kaleidoscope": ["mix", "swirl", "blend", "patchwork"],
    "realm": ["world", "domain", "field", "space"],
    "realms": ["worlds", "spaces", "fields"],
    "robust": ["strong", "solid", "sturdy", "tough"],
    "comprehensive": ["full", "complete", "thorough"],
    "indelible": ["unforgettable", "lasting", "deep"],
    "evocative": ["vivid", "stirring", "moving"],
    "profound": ["deep", "huge", "strong"],
    "intricate": ["complex", "detailed", "fine", "elaborate"],
    "paradigm": ["model", "way", "approach", "system"],
    "ecosystem": ["network", "world", "circle", "scene"],  # hors tech
    "synergy": ["fit", "match", "combo", "alignment"],
    "groundbreaking": ["new", "fresh", "bold", "first"],
    "cutting-edge": ["latest", "newest", "modern"],
    "game-changer": ["big shift", "turning point", "huge"],
    "paradigm-shift": ["big change", "shift", "turning point"],
    "unwavering": ["steady", "firm", "solid"],
    "ever-evolving": ["changing", "shifting", "growing"],
    # Connecteurs IA-typiques
    "moreover": ["also", "plus", "and"],
    "furthermore": ["also", "and", "plus"],
    "additionally": ["also", "and"],
    "in conclusion": ["so", "all in all", "to wrap up"],
    "in essence": ["basically", "in short"],
    "in summary": ["to sum up", "so"],
    "it's worth noting": ["note that", ""],
    "it is worth noting": ["note that", ""],
    "that being said": ["that said", "still"],
    # Lexique creux générique
    "shed light": ["explain", "clarify", "show"],
    "stand testament": ["prove", "show"],
    "deep dive": ["close look", "study"],
}

# Mots IA mais sans remplacement automatique simple (manuel recommandé)
AI_FLAG_NO_REPLACE = {
    "as such", "in light of", "in the wake of", "in order to",
    "a multitude of", "a wealth of", "navigate the complexities",
    "in the heart of", "at the forefront", "at its core",
}

# ─────────────────────────────────────────────────────────────────────
# 2. PATTERNS SYNTAXIQUES IA
# ─────────────────────────────────────────────────────────────────────

AI_SYNTAX_PATTERNS = [
    (r"\bnot only\b.{1,80}?\bbut also\b", "Not only X, but also Y (excès)"),
    (r"^[A-Z][a-z]+ly,\s", "Adverbe -ly en début de phrase"),
    (r"\bis more than\b.{1,30}?\bit['']s\b", "X is more than Y, it's Z (creux)"),
    (r"\bin the realm of\b", "in the realm of (creux)"),
    (r"\bin a world\b", "in a world (creux)"),
    (r"\bin today['']s.{1,30}?world\b", "in today's [...] world (creux)"),
    (r"\bjourney\b.{0,40}?\bjourney\b", "Répétition 'journey' rapprochée"),
    (r"\b(very|really|truly|actually)\s+\1\b", "Intensifieur répété"),
    (r"\bwith\s+(unwavering|profound|intricate)\b",
     "Tag IA classique (with unwavering/profound/intricate)"),
]

# ─────────────────────────────────────────────────────────────────────
# 3. ANALYSE STATISTIQUE
# ─────────────────────────────────────────────────────────────────────


def word_repetition_analysis(text: str, threshold_per_1000: int = 5) -> dict:
    words = re.findall(r"\b[a-z]{4,}\b", text.lower())
    counter = Counter(words)
    total_words = len(words)
    if total_words == 0:
        return {}
    common_english = {
        "this", "that", "with", "from", "they", "their", "what", "have",
        "would", "could", "should", "about", "there", "where", "when",
        "your", "yours", "more", "than", "very", "much", "such", "even",
        "into", "onto", "over", "under", "after", "before", "while",
        "because", "since", "still", "just", "only", "also", "ever",
        "never", "always", "often", "sometimes", "though", "although",
    }
    overused = {}
    for word, count in counter.items():
        if word in common_english:
            continue
        rate = count * 1000 / total_words
        if rate >= threshold_per_1000:
            overused[word] = {"count": count, "rate_per_1000": round(rate, 2)}
    return dict(sorted(overused.items(), key=lambda x: -x[1]["rate_per_1000"]))


# ─────────────────────────────────────────────────────────────────────
# AUDIT
# ─────────────────────────────────────────────────────────────────────


def audit_text(text: str) -> dict:
    issues_words = {}
    word_count = len(re.findall(r"\b\w+\b", text))
    if word_count == 0:
        return {"error": "empty text"}

    # 1. Mots-tatoués
    for word in AI_TATTOO_WORDS:
        pattern = r"\b" + re.escape(word) + r"\b"
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            issues_words[word] = {
                "count": len(matches),
                "suggestions": AI_TATTOO_WORDS[word],
            }
    for phrase in AI_FLAG_NO_REPLACE:
        pattern = r"\b" + re.escape(phrase) + r"\b"
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            issues_words[phrase] = {"count": len(matches), "suggestions": []}

    # 2. Patterns syntaxiques
    issues_patterns = []
    for pattern, label in AI_SYNTAX_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if matches:
            issues_patterns.append({
                "label": label,
                "count": len(matches),
                "samples": matches[:3],
            })

    # 3. Répétitions excessives
    overused = word_repetition_analysis(text)

    # Scoring
    total_word_issues = sum(d["count"] for d in issues_words.values())
    total_pattern_issues = sum(i["count"] for i in issues_patterns)
    total_repetition_issues = sum(d["count"] for d in overused.values())

    # Densité (par 1000 mots)
    word_density = total_word_issues * 1000 / word_count
    pattern_density = total_pattern_issues * 1000 / word_count

    ai_score = min(
        round(word_density * 3 + pattern_density * 5 +
              len(overused) * 0.5, 1),
        100,
    )

    if ai_score < 25:
        verdict = "PASS — texte crédible, humain plausible"
    elif ai_score < 50:
        verdict = "WARN — quelques marqueurs IA, à corriger"
    else:
        verdict = "FAIL — trop de marqueurs IA, à réécrire"

    return {
        "word_count": word_count,
        "ai_likeness_score": ai_score,
        "verdict": verdict,
        "issues": {
            "tattoo_words": issues_words,
            "syntax_patterns": issues_patterns,
            "overused_words": overused,
        },
        "stats": {
            "tattoo_word_density_per_1000": round(word_density, 2),
            "pattern_density_per_1000": round(pattern_density, 2),
            "overused_words_count": len(overused),
        },
    }


def auto_replace(text: str, deterministic: bool = False) -> tuple[str, int]:
    """Remplace les mots-tatoués IA par un synonyme humain."""
    replacements = 0
    for word, synonyms in AI_TATTOO_WORDS.items():
        if not synonyms:
            continue
        pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
        def repl(match):
            nonlocal replacements
            replacements += 1
            syn = synonyms[0] if deterministic else random.choice(synonyms)
            original = match.group(0)
            if original.istitle():
                return syn.capitalize()
            elif original.isupper():
                return syn.upper()
            return syn
        text = pattern.sub(repl, text)
    return text, replacements


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Fichier texte à auditer")
    parser.add_argument("--replace", action="store_true",
                        help="Réécrit auto les mots-tatoués IA")
    parser.add_argument("--output", help="Fichier de sortie pour --replace")
    parser.add_argument("--json", action="store_true",
                        help="Sortie audit en JSON")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Fichier introuvable : {path}")
        return 2
    text = path.read_text(encoding="utf-8")

    if args.replace:
        new_text, n = auto_replace(text)
        out_path = Path(args.output or path.stem + "_cleaned" + path.suffix)
        out_path.write_text(new_text, encoding="utf-8")
        print(f"✓ {n} remplacements effectués → {out_path}")
        return 0

    audit = audit_text(text)
    if args.json:
        print(json.dumps(audit, indent=2, ensure_ascii=False))
    else:
        print(f"\n=== Audit anti-IA de {path.name} ===\n")
        print(f"Word count        : {audit['word_count']:,}")
        print(f"AI-likeness score : {audit['ai_likeness_score']}/100")
        print(f"Verdict           : {audit['verdict']}")
        print(f"\nTattoo words (top 10) :")
        for w, info in list(audit["issues"]["tattoo_words"].items())[:10]:
            sug = ", ".join(info["suggestions"][:3]) if info["suggestions"] else "(manuel)"
            print(f"  • {w:<20} ×{info['count']:<3}  →  {sug}")
        print(f"\nPatterns syntaxiques détectés :")
        for p in audit["issues"]["syntax_patterns"][:10]:
            print(f"  • {p['label']:<45} ×{p['count']}")
        print(f"\nMots surutilisés :")
        for w, info in list(audit["issues"]["overused_words"].items())[:10]:
            print(f"  • {w:<20} ×{info['count']:<3}  ({info['rate_per_1000']}/1000)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
