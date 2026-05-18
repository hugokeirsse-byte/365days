"""
Agent BRAIN META — 4 cerveaux perpétuels qui réfléchissent 24/7.

Chacun a un objectif spécialisé et tourne en cron toutes les 1-6 heures.
Tous lisent data/system_state.json (état projet, ventes, budget, possibilités)
et écrivent leurs propositions dans data/brain/<agent>_proposals.json.

Hugo valide les meilleures propositions, le système les exécute.

4 cerveaux :
1. brain_trends      — scan continu trends → opportunités produit
2. brain_tools       — recherche nouveaux outils/APIs gratuites à intégrer
3. brain_optimization — analyse ventes, propose optimisations pipelines
4. brain_niches      — cherche niches sous-exploitées + analyse concurrence

Active uniquement si GEMINI_API_KEY défini. Sinon mode dégradé qui
écrit un rapport "j'aurais besoin de la clé Gemini".

Variables d'env :
  GEMINI_API_KEY       clé Google AI Studio
  BRAIN_AGENT          nom du cerveau (trends/tools/optimization/niches)
  MAX_PROPOSALS=10     limite propositions par run
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
BRAIN_DIR = DATA_DIR / "brain"
STATE_PATH = DATA_DIR / "system_state.json"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-exp")
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

USER_AGENT = "365days-BrainMeta/1.0"
TIMEOUT = 60


# ============================================================
# AGENT DEFINITIONS — each one has a focused mission
# ============================================================

BRAIN_AGENTS = {
    "trends": {
        "title": "Trends Hunter Brain",
        "mission": (
            "You scan the digital product market 24/7 to find emerging trends "
            "that the 365days POD empire (Etsy/KDP/Cults3D/TGC) can monetize "
            "within 7-30 days. You report 5-10 concrete product opportunities "
            "per run, ordered by ROI potential."
        ),
        "prompt_template": """You are TRENDS HUNTER BRAIN, mission: find what could make Hugo richer in the next 30 days.

CURRENT SYSTEM STATE:
{state}

EXISTING PRODUCT PIPELINES (do not re-suggest):
{pipelines}

TASK: Propose 5-10 NEW concrete product opportunities Hugo could exploit. Focus on:
- Emerging trends Q2 2026 (Pinterest/TikTok/Reddit/Etsy bestseller patterns)
- Niches with high buyer intent + low competition saturation
- Compatible with our automation stack (no manual photography, no physical inventory)

OUTPUT JSON STRICT:
{{"proposals": [
  {{
    "rank": 1,
    "title": "Short title",
    "niche": "Specific micro-niche",
    "platforms": ["Etsy", "Redbubble"],
    "production_method": "viral_formats / coloring / stl / new_pipeline_needed",
    "estimated_monthly_revenue_eur_low": 50,
    "estimated_monthly_revenue_eur_high": 300,
    "effort_score_1_10": 3,
    "saturation_score_1_10": 4,
    "why_now": "Why this trend is hot right now",
    "evidence": "Concrete data points or trend signals",
    "first_action_hugo": "What Hugo should do first (concrete step)"
  }}
]}}""",
        "cron_hours": 4,
    },
    "tools": {
        "title": "Tools Scout Brain",
        "mission": (
            "You hunt for new FREE tools, APIs, services that could enhance "
            "the 365days automation system. You report 5-10 tools per run with "
            "concrete integration suggestions."
        ),
        "prompt_template": """You are TOOLS SCOUT BRAIN, mission: find new FREE tools/APIs to make Hugo's system more powerful.

CURRENT SYSTEM STATE:
{state}

CURRENT TOOLS ALREADY INTEGRATED:
{pipelines}

TASK: Propose 5-10 NEW free tools/APIs/services that could enhance the system. Focus on:
- Image generation (better quality, more volume, image references)
- Text generation, translation, content
- Trend scraping, market intelligence
- POD platforms we don't yet exploit
- Audio, video, 3D generation
- Marketing automation (Pinterest, TikTok, email)

PRIORITIZE 100% FREE OR GENEROUS FREE TIER (>100 requests/day).

OUTPUT JSON STRICT:
{{"proposals": [
  {{
    "rank": 1,
    "tool_name": "Tool name",
    "url": "https://...",
    "category": "image_gen / text / scraping / pod / audio / other",
    "free_tier_limits": "Concrete limits (req/day, monthly quota)",
    "quality_vs_alternatives_1_10": 8,
    "integration_difficulty_1_10": 3,
    "integration_suggestion": "Where to plug it in our pipelines",
    "would_replace": "Existing tool it could replace or supplement",
    "risk_or_caveat": "Honest risks (rate limit, content filter, ToS)"
  }}
]}}""",
        "cron_hours": 12,
    },
    "optimization": {
        "title": "Optimization Brain",
        "mission": (
            "You analyze the current state of the system (production volumes, "
            "estimated revenue, code quality) and propose 5-10 concrete "
            "optimizations that would amplify ROI per hour of Hugo's time."
        ),
        "prompt_template": """You are OPTIMIZATION BRAIN, mission: maximize Hugo's ROI per hour worked.

CURRENT SYSTEM STATE:
{state}

CURRENT PIPELINES & PRODUCTION VOLUMES:
{pipelines}

TASK: Propose 5-10 CONCRETE optimizations. Focus on:
- Bottlenecks Hugo faces (manual uploads, time-consuming tasks)
- Pipelines that produce volume but low quality (need refactor)
- Underexploited assets (existing products to repurpose)
- Cross-pollination (1 input → multiple outputs across pipelines)
- Workflow automation that reduces Hugo's manual touches

OUTPUT JSON STRICT:
{{"proposals": [
  {{
    "rank": 1,
    "title": "Optimization title",
    "target_pipeline_or_workflow": "Which part of the system to optimize",
    "estimated_time_saved_per_week_hours": 2,
    "estimated_revenue_uplift_eur_monthly": 50,
    "implementation_effort_hours": 1,
    "what_to_change": "Concrete change",
    "why_high_impact": "Why this delivers high ROI",
    "first_action_hugo_or_claude": "First step (Hugo or Claude)"
  }}
]}}""",
        "cron_hours": 6,
    },
    "niches": {
        "title": "Niches Explorer Brain",
        "mission": (
            "You explore ultra-specific underexploited niches with passionate "
            "buyer communities, suggesting which ones to attack next."
        ),
        "prompt_template": """You are NICHES EXPLORER BRAIN, mission: find ultra-specific niches with passionate buyers, low saturation.

CURRENT SYSTEM STATE:
{state}

NICHES ALREADY EXPLOITED:
{pipelines}

TASK: Propose 5-10 NEW ultra-specific niches the system should attack next. Focus on:
- Passionate communities with subreddits >50k members
- Specific professions with strong identity (surgeons, lighthouse keepers, cave divers)
- Sub-cultures with insider jokes (warhammer, vintage tractor restoration, taxidermy)
- Hobbies that combine identity + ritual (sourdough, mushroom foraging, ham radio)
- AVOID overdone (cat lovers, coffee drinkers, generic teachers)

OUTPUT JSON STRICT:
{{"proposals": [
  {{
    "rank": 1,
    "niche_name": "Ultra-specific niche",
    "community_size_estimate": 80000,
    "passion_level_1_10": 9,
    "current_etsy_saturation_1_10": 3,
    "buyer_persona": "Who exactly buys",
    "product_angles": ["product idea 1", "product idea 2", "product idea 3"],
    "vocabulary_inside_jokes": ["jargon1", "jargon2"],
    "best_pipeline_match": "viral_formats / coloring / lowcontent_kdp / stl / etc.",
    "first_test_product": "Concrete first product to ship"
  }}
]}}""",
        "cron_hours": 8,
    },
}


# ============================================================
# STATE READER
# ============================================================

def load_system_state() -> dict:
    """Load or initialize system_state.json."""
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            pass
    # Default state
    return {
        "_doc": "Updated by Hugo manually OR by agent_state_collector.py automatically.",
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "monthly_revenue_eur": 0,
        "active_platforms": [],
        "hugo_available_hours_per_week": 10,
        "hugo_budget_eur": 0,
        "current_priorities": [],
        "recent_sales_summary": "",
        "open_issues": [],
        "hardware": "Android phone only (no PC yet)",
    }


def list_pipelines() -> list[str]:
    """List all produce_*.py and agent_*.py scripts as 'already integrated tools'."""
    scripts_dir = ROOT / "scripts"
    pipelines = []
    if scripts_dir.exists():
        for f in sorted(scripts_dir.glob("produce_*.py")):
            pipelines.append(f.stem)
        for f in sorted(scripts_dir.glob("agent_*.py")):
            pipelines.append(f.stem)
    return pipelines


# ============================================================
# GEMINI API CALL
# ============================================================

def call_gemini(prompt: str, retries: int = 3) -> dict | None:
    """Appelle Gemini avec response JSON strict."""
    if not GEMINI_API_KEY:
        return None
    url = f"{API_BASE}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "responseMimeType": "application/json",
            "maxOutputTokens": 4096,
        },
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                resp_data = json.loads(resp.read())
            text = resp_data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except Exception as exc:  # noqa: BLE001
            print(f"    retry {attempt+1}/{retries} : {type(exc).__name__}")
            time.sleep(4 + attempt * 4)
    return None


# ============================================================
# RUN ONE BRAIN
# ============================================================

def run_brain(agent_key: str) -> int:
    if agent_key not in BRAIN_AGENTS:
        print(f"✗ Brain '{agent_key}' inconnu. Choix : {list(BRAIN_AGENTS)}")
        return 1
    agent = BRAIN_AGENTS[agent_key]

    BRAIN_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"BRAIN — {agent['title']}")
    print("=" * 70)

    if not GEMINI_API_KEY:
        print("\n⊝ GEMINI_API_KEY non défini.")
        print("   Ce cerveau s'activera dès que Hugo ajoutera la clé en secret.")
        report = {
            "agent": agent_key,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "PAUSED — waiting for GEMINI_API_KEY secret",
            "mission": agent["mission"],
            "note": "Add GEMINI_API_KEY to GitHub secrets to activate this brain.",
        }
        (BRAIN_DIR / f"{agent_key}_proposals.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    # Load state + pipelines
    state = load_system_state()
    pipelines = list_pipelines()
    state_str = json.dumps(state, indent=2, ensure_ascii=False)[:3000]
    pipelines_str = "\n".join(f"- {p}" for p in pipelines)

    # Build prompt
    prompt = agent["prompt_template"].format(
        state=state_str,
        pipelines=pipelines_str,
    )
    print(f"\n→ Calling Gemini {GEMINI_MODEL}...")
    result = call_gemini(prompt)

    if not result:
        print("✗ Gemini call failed")
        return 1

    # Format report
    report = {
        "agent": agent_key,
        "title": agent["title"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model": GEMINI_MODEL,
        "system_state_snapshot": state,
        "pipelines_known": pipelines,
        **result,
    }

    out_path = BRAIN_DIR / f"{agent_key}_proposals.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n✓ {len(result.get('proposals', []))} proposals saved : {out_path}")

    # Print top 3
    for i, prop in enumerate(result.get("proposals", [])[:3], 1):
        title = prop.get("title") or prop.get("tool_name") or prop.get("niche_name", "?")
        print(f"  #{i} {title}")

    return 0


def main() -> int:
    agent_key = os.environ.get("BRAIN_AGENT", "").strip().lower()
    if not agent_key:
        # Run all 4 in sequence
        codes = []
        for key in BRAIN_AGENTS:
            print()
            codes.append(run_brain(key))
            time.sleep(2)
        return max(codes) if codes else 0
    return run_brain(agent_key)


if __name__ == "__main__":
    sys.exit(main())
