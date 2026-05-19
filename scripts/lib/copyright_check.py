"""Module 19 — Censeur Copyright.

Vérifie qu'une string, des métadonnées, ou une asset path ne déclenche
aucun pattern de `data/whitelists/blacklist_copyright.json` et que tout
parent PD utilisé apparaît bien dans `whitelist_pd.json`.

Aucun appel LLM. 100% déterministe.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BLACKLIST_PATH = REPO_ROOT / "data" / "whitelists" / "blacklist_copyright.json"
WHITELIST_PATH = REPO_ROOT / "data" / "whitelists" / "whitelist_pd.json"


@dataclass
class CopyrightVerdict:
    passed: bool
    matched_blacklist_patterns: list[str]
    unknown_pd_parents: list[str]
    notes: list[str]

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "matched_blacklist_patterns": self.matched_blacklist_patterns,
            "unknown_pd_parents": self.unknown_pd_parents,
            "notes": self.notes,
        }


def _load_blacklist() -> dict:
    return json.loads(BLACKLIST_PATH.read_text(encoding="utf-8"))


def _load_whitelist() -> dict:
    return json.loads(WHITELIST_PATH.read_text(encoding="utf-8"))


def _all_pd_ids(whitelist: dict) -> set[str]:
    ids: set[str] = set()
    for section in ("literature", "art_visual", "superheroes_golden_age_pd"):
        for entry in whitelist.get(section, []):
            if "id" in entry:
                ids.add(entry["id"])
    return ids


def check_text(text: str) -> list[str]:
    """Retourne la liste des patterns blacklist matchés dans `text`."""
    if not text:
        return []
    blacklist = _load_blacklist()
    matched: list[str] = []
    haystack = text.lower()
    for rule in blacklist.get("by_keyword_pattern", []):
        try:
            if re.search(rule["pattern"], haystack, flags=re.IGNORECASE):
                matched.append(rule["pattern"])
        except re.error:
            continue
    return matched


def check_parents(parent_ids: list[str]) -> list[str]:
    """Retourne la liste des parent_ids ABSENTS de whitelist_pd.json (donc à investiguer)."""
    if not parent_ids:
        return []
    whitelist = _load_whitelist()
    known = _all_pd_ids(whitelist)
    return [pid for pid in parent_ids if pid not in known]


def check_asset(
    title: str | None = None,
    description: str | None = None,
    keywords: list[str] | None = None,
    parents_pd: list[str] | None = None,
) -> CopyrightVerdict:
    """Check complet d'un asset avant publication.

    Args:
        title: titre du produit
        description: description longue
        keywords: tags / mots-clés
        parents_pd: IDs des parents domaine public utilisés (Module W / U / V)
    """
    haystack_parts: list[str] = []
    if title:
        haystack_parts.append(title)
    if description:
        haystack_parts.append(description)
    if keywords:
        haystack_parts.extend(keywords)
    haystack = " | ".join(haystack_parts)

    matched = check_text(haystack)
    unknown_parents = check_parents(parents_pd or [])

    notes: list[str] = []
    if matched:
        notes.append(f"{len(matched)} pattern(s) blacklist matché(s) — refus publication")
    if unknown_parents:
        notes.append(
            f"Parents PD non whitelistés : {unknown_parents} — ajouter à whitelist_pd.json ou retirer"
        )
    if not matched and not unknown_parents:
        notes.append("Asset propre — peut entrer en staging")

    return CopyrightVerdict(
        passed=not matched and not unknown_parents,
        matched_blacklist_patterns=matched,
        unknown_pd_parents=unknown_parents,
        notes=notes,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python -m scripts.lib.copyright_check '<title>' ['<description>']",
            file=sys.stderr,
        )
        sys.exit(2)
    title = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else None
    verdict = check_asset(title=title, description=description)
    print(json.dumps(verdict.to_dict(), indent=2, ensure_ascii=False))
    sys.exit(0 if verdict.passed else 1)
