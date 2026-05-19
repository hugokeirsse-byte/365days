"""Module 20 — Anti-Slop Textuel.

Détecte les signatures LLM courantes qui trahissent un texte généré par IA.
Si une de ces signatures apparaît dans un titre/description/keyword, l'asset
est bloqué (ou re-router vers Mistral avec consigne de reformulation).

Aucun appel LLM. 100% déterministe.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Signatures lexicales très courantes en sortie ChatGPT/Claude/Gemini par défaut.
# Source : empirique, ce qui trahit immédiatement aux yeux d'un humain Etsy/KDP averti.
LEXICAL_SIGNATURES = [
    r"\bunleash\b",
    r"\bembrace\b",
    r"\bdive\s+into\b",
    r"\bdiscover\s+the\b",
    r"\bin\s+the\s+realm\s+of\b",
    r"\btapestry\b",
    r"\brich\s+tapestry\b",
    r"\bwhimsical\s+journey\b",
    r"\bjourney\s+through\b",
    r"\bmeticulously\s+(?:crafted|designed)\b",
    r"\bdelve\s+into\b",
    r"\bcaptivating\b",
    r"\bharness(?:ing)?\s+the\s+power\s+of\b",
    r"\bgame[\s-]changer\b",
    r"\belevate\s+your\b",
    r"\btransform(?:ative)?\s+(?:experience|journey)\b",
    r"\bunlock\s+the\b",
    r"\bin\s+today'?s\s+fast[\s-]paced\s+world\b",
    r"\bnavigate\s+the\s+(?:complexities|landscape)\b",
    r"\bbespoke\b",
    r"\bsynergy\b",
    r"\bholistic\s+approach\b",
    r"\btreasure\s+trove\b",
    r"\benchant(?:ing|ed)?\b(?!\s+forest)",
]

# Erreurs catastrophiques (oubli de copier-coller depuis le prompt).
LEFTOVER_PROMPT_LEAKS = [
    r"let\s+me\s+know\s+if\s+you('?d|\s+would)\s+like",
    r"i\s+hope\s+this\s+helps",
    r"as\s+an\s+ai\s+(?:language\s+)?model",
    r"i'?m\s+sorry,?\s+but",
    r"however,?\s+i\s+cannot",
    r"here'?s?\s+(?:a|the)\s+(?:list|response|answer|version|revised)",
    r"sure!?\s+here'?s",
    r"certainly!?\s+here",
    r"of\s+course!?\s+here",
    r"\[insert\s+",
    r"<\s*[a-z_]+\s*>",
]

# Patterns de ponctuation excessive (em-dash en masse, Oxford comma forcée).
PUNCTUATION_PATTERNS = [
    (r"(—.*?){3,}", "excess_em_dash"),
    (r"^\s*(\s*[•\-\*])\s+.+\n(\s*[•\-\*])\s+.+\n(\s*[•\-\*])\s+.+\n(\s*[•\-\*])\s+.+\n(\s*[•\-\*])\s+.+", "bullet_overload"),
]


@dataclass
class SlopVerdict:
    passed: bool
    lexical_hits: list[str] = field(default_factory=list)
    prompt_leaks: list[str] = field(default_factory=list)
    punctuation_issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "lexical_hits": self.lexical_hits,
            "prompt_leaks": self.prompt_leaks,
            "punctuation_issues": self.punctuation_issues,
        }


def check_text(text: str) -> SlopVerdict:
    """Retourne un verdict détaillé. `passed=False` dès qu'une signature est détectée."""
    if not text or not text.strip():
        return SlopVerdict(passed=True)

    lexical_hits: list[str] = []
    for pattern in LEXICAL_SIGNATURES:
        if re.search(pattern, text, flags=re.IGNORECASE):
            lexical_hits.append(pattern)

    prompt_leaks: list[str] = []
    for pattern in LEFTOVER_PROMPT_LEAKS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            prompt_leaks.append(pattern)

    punctuation_issues: list[str] = []
    for pattern, label in PUNCTUATION_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            punctuation_issues.append(label)

    passed = not (lexical_hits or prompt_leaks or punctuation_issues)
    return SlopVerdict(
        passed=passed,
        lexical_hits=lexical_hits,
        prompt_leaks=prompt_leaks,
        punctuation_issues=punctuation_issues,
    )


def check_metadata_bundle(
    title: str | None = None,
    description: str | None = None,
    bullets: list[str] | None = None,
    keywords: list[str] | None = None,
) -> SlopVerdict:
    """Check de métadonnées de listing complète. Agrège dans un seul verdict."""
    parts: list[str] = []
    if title:
        parts.append(title)
    if description:
        parts.append(description)
    if bullets:
        parts.extend(bullets)
    if keywords:
        parts.extend(keywords)
    return check_text("\n".join(parts))


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m scripts.lib.anti_slop_text '<text>'", file=sys.stderr)
        sys.exit(2)
    verdict = check_text(sys.argv[1])
    print(json.dumps(verdict.to_dict(), indent=2, ensure_ascii=False))
    sys.exit(0 if verdict.passed else 1)
