#!/usr/bin/env python3
"""AUDITEUR pilote par le cahier des charges + CONTROLEUR DE BOUCLE (Brique 3).

L'auditrice ne valide 'abouti' que si TOUS les criteres BLOQUANTS du brief passent.
Elle lit brief.audit_criteria et evalue CHAQUE critere -> verdict :
  PASS / FAIL / PENDING_PRODUCTION (produit pas encore genere)
       / NEEDS_VISION_CI (necessite Gemini Vision, en CI)
       / NEEDS_UNIQUENESS (recherche titre/auteur a faire)

Le CONTROLEUR DE BOUCLE applique loop_policy (max_iterations, stop_on_repeated_failure,
escalate_to_human) : generer -> auditer -> corriger -> ... -> abouti OU escalade Hugo.
Jamais de boucle infinie.

Usage :
  python scripts/agent_brief_auditor.py [BRIEF_ID]         # audit du produit (point par point)
  python scripts/agent_brief_auditor.py --demo-loop [ID]   # demonstration du controleur (hors-ligne)
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRIEFS_DIR = ROOT / "data" / "briefs"
GATE1_DIR = ROOT / "products" / "coloring_books" / "_gate1"

DEFAULT_BRIEF = os.environ.get("BRIEF_ID", "brief_2026-05-22_coloring_kawaii_mushroom_hollow")


def load_brief(bid):
    p = BRIEFS_DIR / f"{bid}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def find_product_dir(bid, brief):
    """Repertoire du produit fini (PDF + images). Absent tant que rien n'est genere."""
    slug = brief["target"]["collection"]["title"].lower().replace(" ", "_")
    cand = ROOT / "products" / "coloring_books" / slug
    return cand if (cand.exists() and any(cand.glob("*.pdf"))) else None


def load_plan(bid):
    p = GATE1_DIR / bid / "production_plan.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def classify(crit):
    """Categorise un critere selon sa methode de verification."""
    h = (crit.get("how_to_check", "") + " " + crit.get("criterion", "")).lower()
    if "amazon" in h or "etsy" in h or "deja utilis" in h:
        return "uniqueness"
    if "pixel" in h or "vision" in h or "ocr" in h:
        return "vision"
    if "dimension" in h or "pdf" in h or "presence" in h or "metadata" in h or "format kdp" in h:
        return "structural"
    return "vision"  # par defaut, prudence -> verif visuelle


def evaluate(brief, product_dir, plan):
    """Verdict par critere. Hors produit : PENDING ; structurels verifiables sur le PLAN en pre-vol."""
    results = []
    budget = brief.get("image_budget", {})
    bs = brief["target"].get("book_structure", {})
    for c in brief["audit_criteria"]:
        cat = classify(c)
        verdict, why = "PENDING_PRODUCTION", "produit pas encore genere"
        if cat == "uniqueness":
            checked = (brief["target"]["collection"].get("title_uniqueness_checked")
                       and brief["target"]["collection"].get("author_uniqueness_checked"))
            verdict, why = ("PASS", "verifie") if checked else ("NEEDS_UNIQUENESS", "titre/auteur a verifier (Amazon/Etsy)")
        elif cat == "vision":
            verdict = "NEEDS_VISION_CI" if product_dir else "PENDING_PRODUCTION"
            why = "necessite Gemini Vision sur les images generees"
        elif cat == "structural":
            if product_dir is None and plan is not None:
                # PRE-VOL : ce que le PLAN garantit deja
                cl = c["criterion"].lower()
                if "budget" in cl or "image" in cl:
                    verdict, why = ("PASS", f"plan {plan['images_planned']}<= {budget.get('max_images_total')}") \
                        if plan.get("within_budget") else ("FAIL", "plan depasse le budget")
                elif "liminaire" in cl or "accueil" in cl:
                    verdict, why = ("PLANNED", f"prevu: {plan.get('front_matter_typeset')}")
                elif "couverture" in cl or "4eme" in cl:
                    verdict, why = ("PLANNED", "couv avant+arriere prevues dans le plan")
                elif "completude" in cl:
                    ok = bool(plan.get("title") and plan.get("author"))
                    verdict, why = ("PLANNED", "titre+auteur+metadata prevus") if ok else ("FAIL", "titre/auteur manquant")
                elif "format kdp" in cl:
                    verdict, why = "PENDING_PRODUCTION", "verifiable sur le PDF genere"
                else:
                    verdict, why = "PENDING_PRODUCTION", "verifiable sur le produit"
            elif product_dir is not None:
                verdict, why = "TODO_STRUCTURAL", "a verifier sur le PDF (dimensions/pages/metadata)"
        results.append({"criterion": c["criterion"], "blocking": c["blocking"],
                        "category": cat, "verdict": verdict, "why": why})
    return results


def overall(results):
    blocking = [r for r in results if r["blocking"]]
    passed = [r for r in blocking if r["verdict"] == "PASS"]
    failed = [r for r in blocking if r["verdict"] == "FAIL"]
    pending = [r for r in blocking if r["verdict"] not in ("PASS", "FAIL", "PLANNED")]
    abouti = len(failed) == 0 and len(pending) == 0 and len(passed) == len(blocking)
    return {"abouti": abouti, "blocking_total": len(blocking),
            "pass": len(passed), "fail": len(failed),
            "pending_or_needs": len(pending),
            "planned_preflight": len([r for r in blocking if r["verdict"] == "PLANNED"])}


def do_audit(bid):
    brief = load_brief(bid)
    if not brief:
        print(f"✗ Brief introuvable: {bid}")
        return 1
    product_dir = find_product_dir(bid, brief)
    plan = load_plan(bid)
    print("=" * 64)
    print(f"AUDIT vs CAHIER DES CHARGES — {bid}")
    print("=" * 64)
    print(f"Produit fini : {'present' if product_dir else 'ABSENT (pre-vol sur le plan)' }")
    print(f"Plan de prod : {'present' if plan else 'absent'}\n")
    results = evaluate(brief, product_dir, plan)
    for r in results:
        flag = "[BLOQUANT]" if r["blocking"] else "[indicatif]"
        print(f"  {r['verdict']:18} {flag} {r['criterion'][:60]}  ({r['why']})")
    o = overall(results)
    print(f"\nVERDICT : {'✅ ABOUTI' if o['abouti'] else '⛔ NON abouti'} "
          f"(bloquants: {o['pass']} pass / {o['fail']} fail / {o['pending_or_needs']} en attente / {o['planned_preflight']} planifies)")
    if not o["abouti"]:
        print("  -> produit non valide tant que tous les bloquants ne passent pas (anti-derive).")
    out = (GATE1_DIR / bid)
    out.mkdir(parents=True, exist_ok=True)
    (out / "audit_vs_brief.json").write_text(
        json.dumps({"brief_id": bid, "results": results, "overall": o}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nRapport: {out / 'audit_vs_brief.json'}")
    return 0


def demo_loop(bid):
    """Demonstration HORS-LIGNE du controleur de boucle (loop_policy), sans generer."""
    brief = load_brief(bid)
    if not brief:
        print(f"✗ Brief introuvable: {bid}")
        return 1
    lp = brief.get("loop_policy", {})
    maxit = lp.get("max_iterations", 5)
    stopfail = lp.get("stop_on_repeated_failure", 2)
    escalate = lp.get("escalate_to_human", True)
    print("=" * 64)
    print(f"DEMO CONTROLEUR DE BOUCLE — {bid}")
    print(f"loop_policy: max_iterations={maxit}, stop_on_repeated_failure={stopfail}, escalate={escalate}")
    print("=" * 64)
    # Scenario simule : un critere ('trait noir pur') echoue de maniere persistante.
    failing = "Trait noir PUR (aucune couleur/gris/ombrage)"
    consecutive = 0
    for it in range(1, maxit + 1):
        print(f"\n— Iteration {it}/{maxit} —")
        print("  [generer] (simule) pages produites")
        # simulation : echec aux 2 premieres iterations sur le meme critere, puis on tente un contournement
        still_fail = it <= 2 or (it == 3 and consecutive >= stopfail)
        if it <= 2:
            consecutive += 1
            print(f"  [auditer] FAIL bloquant: '{failing}' (x{consecutive})")
            if consecutive >= stopfail:
                print(f"  [decision] meme critere echoue {consecutive}x >= {stopfail} -> CONTOURNEMENT (autre modele/prompt renforce)")
            else:
                print("  [decision] corriger les pages fautives -> nouvelle iteration")
        elif it == 3:
            print("  [auditer] le contournement n'a pas suffi: FAIL persistant")
            if escalate:
                print("  [decision] ⛔ INSOLUBLE -> ESCALADE A HUGO (STOP, pas de boucle infinie)")
                print("             -> alerte: 'le filet gratuit ne produit pas un trait pur ; passer a Runware ?'")
                return 0
        else:
            print("  [auditer] tous les bloquants PASS")
            print("  [decision] ✅ ABOUTI -> GATE 2 (presentation a Hugo)")
            return 0
    print("\n  max_iterations atteint sans aboutir -> escalade a Hugo.")
    return 0


def main(argv):
    if argv and argv[0] == "--demo-loop":
        return demo_loop(argv[1] if len(argv) > 1 else DEFAULT_BRIEF)
    return do_audit(argv[0] if argv else DEFAULT_BRIEF)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
