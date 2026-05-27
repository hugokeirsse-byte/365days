#!/usr/bin/env python3
"""GATE 2 (Brique 4 de la boucle) — presentation du produit fini + decision de Hugo.

Ne presente un produit QUE s'il est 'abouti' (tous les criteres bloquants passes,
selon audit_vs_brief.json). Construit un PAQUET GATE 2 lisible (titre, auteur,
contenu, PDF, couvertures, resume d'audit) et passe human_gates.gate_end='pending'.
Hugo decide ensuite : approuver (=> publication) ou rejeter.

RIEN NE SE PUBLIE sans la decision de Hugo.

Usage :
  python scripts/agent_gate2.py [BRIEF_ID]                  # presenter (si abouti)
  python scripts/agent_gate2.py --decide approve [ID]       # Hugo approuve -> publication
  python scripts/agent_gate2.py --decide reject  [ID]       # Hugo rejette -> retour prod
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRIEFS_DIR = ROOT / "data" / "briefs"
GATE1_DIR = ROOT / "products" / "coloring_books" / "_gate1"

DEFAULT_BRIEF = os.environ.get("BRIEF_ID", "brief_2026-05-22_coloring_kawaii_mushroom_hollow")


def load_brief(bid):
    p = BRIEFS_DIR / f"{bid}.json"
    return (p, json.loads(p.read_text(encoding="utf-8"))) if p.exists() else (p, None)


def load_audit(bid):
    p = GATE1_DIR / bid / "audit_vs_brief.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def present(bid):
    bpath, brief = load_brief(bid)
    if not brief:
        print(f"✗ Brief introuvable: {bid}")
        return 1
    audit = load_audit(bid)
    print("=" * 64)
    print(f"GATE 2 — presentation produit fini — {bid}")
    print("=" * 64)
    if not audit:
        print("⊝ Aucun audit. Le produit doit d'abord etre produit ET audite. GATE 2 refuse.")
        return 0
    if not audit.get("overall", {}).get("abouti"):
        o = audit["overall"]
        print(f"⊝ Produit NON abouti (bloquants: {o['pass']} pass / {o['fail']} fail / "
              f"{o['pending_or_needs']} en attente). GATE 2 REFUSE — on ne presente pas un produit non fini.")
        return 0

    tgt = brief["target"]
    col = tgt["collection"]
    pkg = {
        "brief_id": bid, "presented_at": datetime.utcnow().isoformat() + "Z",
        "title": col["title"], "author": col["author"],
        "subtitle": tgt["cover"]["front"].get("subtitle_text"),
        "deliverables": ["interieur PDF (35 pages)", "couverture avant (couleur)",
                         "4eme de couverture (couleur)", "metadata KDP"],
        "audit": "TOUS les criteres bloquants PASS ✓",
        "decision_attendue": "Hugo : approve (publication) ou reject (retour prod)",
    }
    out = GATE1_DIR / bid
    out.mkdir(parents=True, exist_ok=True)
    (out / "GATE2_PACKAGE.json").write_text(json.dumps(pkg, indent=2, ensure_ascii=False), encoding="utf-8")
    md = (f"# GATE 2 — Produit fini : {col['title']}\n\n"
          f"**Auteur :** {col['author']}\n**Sous-titre :** {pkg['subtitle']}\n\n"
          f"**Audit :** ✅ tous les critères bloquants passés.\n\n"
          f"**Livrables :**\n" + "".join(f"- {d}\n" for d in pkg["deliverables"]) +
          f"\n**Ta décision :** approuver la **publication** (KDP/Etsy) ou rejeter.\n")
    (out / "GATE2_PACKAGE.md").write_text(md, encoding="utf-8")

    brief["human_gates"]["gate_end"] = "pending"
    bpath.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Produit ABOUTI -> paquet GATE 2 cree : {out / 'GATE2_PACKAGE.md'}")
    print(f"   gate_end = pending. En attente de ta decision (approve / reject).")
    return 0


def decide(verdict, bid):
    bpath, brief = load_brief(bid)
    if not brief:
        print(f"✗ Brief introuvable: {bid}")
        return 1
    if verdict not in ("approve", "reject"):
        print("✗ decision invalide (approve|reject)")
        return 1
    brief["human_gates"]["gate_end"] = "approved" if verdict == "approve" else "rejected"
    bpath.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    if verdict == "approve":
        print(f"✅ GATE 2 APPROUVE par Hugo -> '{brief['target']['collection']['title']}' PRET POUR PUBLICATION (KDP/Etsy).")
    else:
        print(f"⛔ GATE 2 REJETE par Hugo -> retour en production / archivage. Rien n'est publie.")
    return 0


def main(argv):
    if argv and argv[0] == "--decide":
        return decide(argv[1] if len(argv) > 1 else "", argv[2] if len(argv) > 2 else DEFAULT_BRIEF)
    return present(argv[0] if argv else DEFAULT_BRIEF)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
