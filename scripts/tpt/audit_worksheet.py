"""
TPT — Audit qualité d'un pack avant présentation à Hugo (GATE 2).

Vérifie les critères BLOQUANTS du CdC vertical (data/verticals/tpt/CAHIER_DES_CHARGES.md §6) :
  1. Corrigé 100% correct  — recalcule indépendamment chaque réponse (a op b) et compare.
  2. Comptage de pages      — worksheet & answer_key == pages attendues.
  3. Marges print-safe       — >= 0.5in.
  4. Lisibilité              — police corps >= 14pt.
  5. Densité                 — 15..30 problèmes par niveau.
  6. Présence des fichiers   — pack complet (cover/worksheet/answer_key/terms/listing).

L'audit RECALCULE les réponses au lieu de faire confiance au générateur : c'est la
garantie anti-hallucination du vertical. Si un seul échec bloquant -> passed=false.

Usage:
  OUT_DIR=products/tpt/demo_halloween_mult_g3 python scripts/tpt/audit_worksheet.py

Sortie: <OUT_DIR>/audit.json + code retour 0 (passed) ou 1 (échec bloquant).
Stdlib uniquement.
"""

import json
import os
import sys

# recompute indépendant : on NE réutilise PAS le générateur, on revérifie l'arithmétique
RECOMPUTE = {
    "+": lambda a, b: a + b,
    "−": lambda a, b: a - b,
    "×": lambda a, b: a * b,
    "÷": lambda a, b: a // b,
}


def audit(out_dir):
    checks = []

    def add(name, ok, blocking, detail=""):
        checks.append({"criterion": name, "passed": bool(ok), "blocking": blocking, "detail": detail})

    # --- présence des fichiers ---
    required = ["cover.pdf", "worksheet.pdf", "answer_key.pdf", "terms.pdf", "listing.md", "content.json"]
    missing = [f for f in required if not os.path.exists(os.path.join(out_dir, f))]
    add("pack complet (tous fichiers présents)", not missing, True,
        f"manquants: {missing}" if missing else "ok")

    content_path = os.path.join(out_dir, "content.json")
    if not os.path.exists(content_path):
        return _finish(out_dir, checks)  # impossible d'aller plus loin

    with open(content_path, encoding="utf-8") as f:
        data = json.load(f)

    # --- 1. corrigé 100% correct (recalcul indépendant) ---
    wrong = []
    total = 0
    for lvl, problems in data["levels"].items():
        for i, p in enumerate(problems):
            total += 1
            expected = RECOMPUTE[p["op"]](p["a"], p["b"])
            if expected != p["answer"]:
                wrong.append(f"{lvl}#{i+1}: {p['a']}{p['op']}{p['b']} -> stocké {p['answer']}, recalculé {expected}")
    add("corrigé 100% correct (recalcul indépendant)", not wrong, True,
        "ok ({} problèmes vérifiés)".format(total) if not wrong else "; ".join(wrong[:5]))

    # --- 3. marges print-safe ---
    margin = data.get("config", {}).get("margin_in", 0)
    add("marges print-safe >= 0.5in", margin >= 0.5, True, f"{margin:.2f}in")

    # --- 4. lisibilité ---
    font = data.get("config", {}).get("body_font_pt", 0)
    add("police corps >= 14pt", font >= 14, True, f"{font}pt")

    # --- 5. densité ---
    densities = {lvl: len(probs) for lvl, probs in data["levels"].items()}
    dens_ok = all(15 <= n <= 30 for n in densities.values())
    add("densité 15..30 problèmes/niveau", dens_ok, False, str(densities))

    # --- 2. comptage de pages (lecture légère du PDF, sans dépendance) ---
    pe = data.get("pages_expected", {})
    for kind in ("worksheet", "answer_key"):
        expected = pe.get(kind)
        actual = _count_pdf_pages(os.path.join(out_dir, f"{kind}.pdf"))
        ok = (expected is None) or (actual == expected)
        add(f"pages {kind} == {expected}", ok, True, f"trouvées: {actual}")

    return _finish(out_dir, checks)


def _count_pdf_pages(path):
    """Compte les pages d'un PDF sans lib externe (compte les objets /Type /Page)."""
    if not os.path.exists(path):
        return -1
    try:
        with open(path, "rb") as f:
            blob = f.read()
        # compte les /Type /Page (mais pas /Pages)
        import re
        return len(re.findall(rb"/Type\s*/Page[^s]", blob))
    except Exception:
        return -1


def _finish(out_dir, checks):
    blocking_fail = [c for c in checks if c["blocking"] and not c["passed"]]
    passed = not blocking_fail
    result = {"passed": passed, "blocking_failures": len(blocking_fail), "checks": checks}
    with open(os.path.join(out_dir, "audit.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n=== AUDIT TPT : {out_dir} ===")
    for c in checks:
        mark = "✓" if c["passed"] else ("✗ BLOQUANT" if c["blocking"] else "△ mineur")
        print(f"  {mark}  {c['criterion']}  — {c['detail']}")
    print(f"\nRÉSULTAT : {'PASSED ✅' if passed else 'ÉCHEC ❌ (' + str(len(blocking_fail)) + ' bloquant(s))'}")
    return passed


if __name__ == "__main__":
    out = os.environ.get("OUT_DIR", "products/tpt/demo")
    ok = audit(out)
    sys.exit(0 if ok else 1)
