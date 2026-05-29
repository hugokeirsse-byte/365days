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
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
BRAIN_DIR = DATA_DIR / "brain"
STATE_PATH = DATA_DIR / "system_state.json"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
# Modèles essayés dans l'ordre : si l'un est déprécié (404), on passe au suivant.
# Rend les cerveaux résilients aux retraits de modèles par Google (cause du blocage initial).
GEMINI_FALLBACKS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

USER_AGENT = "365days-BrainMeta/1.0"
TIMEOUT = 60


# ============================================================
# AGENT DEFINITIONS — each one has a focused mission
# ============================================================

# Préambule système répété à chaque prompt (mission reminder anti-derive)
SYSTEM_PREAMBLE = """SYSTEM PREAMBLE (do not deviate):
You are part of a network of 5 perpetual specialized brains serving the 365days project of Hugo Keirsse.
Hugo is a solo entrepreneur in France building a digital product empire (POD on Etsy/Redbubble/Cults3D/TGC/KDP, gamedev assets, B2B partnerships).
HIS GOAL: make money — legally, ethically, with maximum ROI per hour worked.

GLOBAL CONSTRAINTS for ALL brains:
- Suggestions must be LEGAL (no copyright infringement, no spam, no fake accounts).
- Tools must be REAL and accessible NOW (no vaporware, no paid > 50$/month).
- Estimates must be HONEST (no overpromising).
- ANSWER STRICTLY IN VALID JSON. No prose outside JSON. No markdown fences.
- You have ONE specific role described below. Stay in your lane. Do not duplicate another brain's role.

YOUR ROLE NOW:
"""

BRAIN_AGENTS = {
    "money_maker": {
        "title": "Money Maker Brain",
        "mission": (
            "Your single obsession is: how does Hugo make MORE MONEY in the "
            "next 30 days? You propose direct revenue actions, not technical "
            "improvements. Operational concrete moves only."
        ),
        "prompt_template": SYSTEM_PREAMBLE + """MONEY MAKER BRAIN — your only obsession is direct revenue uplift in the next 30 days.

CURRENT SYSTEM STATE:
{state}

EXISTING PIPELINES (do not re-suggest existing as new):
{pipelines}

TASK: Propose 5-10 CONCRETE direct revenue moves Hugo can ship within 30 days. Focus on:
- Upload N products to platform X (specific numbers, specific platforms)
- Pricing experiments (raise/lower X, bundle deals, premium versions)
- New revenue streams (affiliate, sponsorship, B2B, niche subscriptions)
- Conversion uplifts (better Etsy listings, Pinterest pin strategy, SEO tags)
- Cross-sell / upsell existing buyers
- Reactivate dormant assets (already-produced products not yet uploaded)
- NOT system improvements (that's optimizer brain's role)
- NOT niche discovery (that's niches brain's role)

OUTPUT STRICT JSON:
{{"proposals": [
  {{
    "rank": 1,
    "action_title": "Concrete revenue move",
    "type": "upload / pricing / new_stream / conversion / cross_sell / reactivate",
    "target_platform": "Etsy / Redbubble / Cults3D / TGC / itch.io / KDP / direct",
    "estimated_revenue_uplift_eur_30days_low": 50,
    "estimated_revenue_uplift_eur_30days_high": 300,
    "hugo_effort_hours": 2,
    "why_this_works_now": "Concrete evidence or rationale",
    "first_action_today": "What Hugo does in the next 24h"
  }}
]}}""",
        "cron_hours": 6,
    },
    "trends_realtime": {
        "title": "Trends Realtime Brain",
        "mission": (
            "You scan TIME-SENSITIVE trends across social platforms (TikTok, "
            "Reddit, Pinterest, Etsy) and identify niches, sub-niches and "
            "keywords gaining momentum RIGHT NOW (last 14 days)."
        ),
        "prompt_template": SYSTEM_PREAMBLE + """TRENDS REALTIME BRAIN — what is BLOWING UP across social media right now (last 14 days)?

CURRENT SYSTEM STATE:
{state}

CURRENTLY KNOWN PIPELINES (so you don't duplicate):
{pipelines}

TASK: Propose 5-10 TIME-SENSITIVE trend signals (LAST 14 DAYS ONLY). Focus on:
- Specific TikTok hashtags or viral memes spreading fast
- Reddit subreddit topics with sudden engagement spikes
- Etsy bestseller patterns shifting in last 2 weeks
- Pinterest search trends accelerating
- Sub-niches BIRTHED by current events (season, news, celebrity, viral moment)
- Specific KEYWORDS Hugo should use in titles/tags right now

For each, give CONCRETE keywords + platform evidence. NOT generic ("crochet is popular") but specific ("the term «butterfly chair crochet» exploded on TikTok 14 May 2026").

OUTPUT STRICT JSON:
{{"proposals": [
  {{
    "rank": 1,
    "trend_keyword": "specific keyword/phrase",
    "platform_where_spotted": "TikTok / Reddit / Pinterest / Etsy",
    "momentum_score_1_10": 9,
    "estimated_lifespan_days": 21,
    "saturation_now_1_10": 3,
    "best_product_format": "tshirt / wall_art / coloring_book / sticker / mug",
    "best_pipeline_match": "viral_formats / iheart_v3 / cultural_arbitrage / etc",
    "title_template_suggestion": "Suggested Etsy listing title with keyword embedded",
    "evidence_url_or_signal": "Where the signal was observed"
  }}
]}}""",
        "cron_hours": 4,
    },
    "system_optimizer": {
        "title": "System Optimizer Brain",
        "mission": (
            "You audit the 365days system internals — pipelines, code quality, "
            "workflows, security, failure modes — and propose concrete "
            "improvements to make it more reliable, faster, less Hugo-time."
        ),
        "prompt_template": SYSTEM_PREAMBLE + """SYSTEM OPTIMIZER BRAIN — find weaknesses, failure modes and inefficiencies in the system. Propose fixes.

CURRENT SYSTEM STATE:
{state}

EXISTING PIPELINES (analyze these for weaknesses):
{pipelines}

TASK: Propose 5-10 CONCRETE optimizations or weakness fixes. Focus on:
- Bottlenecks (manual steps for Hugo that should auto)
- Failure modes (what breaks silently, retries, error handling)
- Quality bugs (gibberish text, broken anatomy, off-topic outputs)
- Pipeline coverage gaps (products generated but never audited/uploaded)
- Cross-pipeline pollination missed (1 design → 8 formats not exploited)
- Security/legal risks (TOS, API quotas, ban risks)
- Code maintainability (duplicate code, missing tests, brittle assumptions)
- NOT new revenue moves (that's money_maker)
- NOT new trends or niches (other brains' roles)

OUTPUT STRICT JSON:
{{"proposals": [
  {{
    "rank": 1,
    "issue_title": "Bug/weakness short title",
    "category": "bottleneck / failure_mode / quality_bug / coverage_gap / cross_polination / security / code_quality",
    "affected_pipelines": ["pipeline1", "pipeline2"],
    "current_pain_description": "What is failing or sub-optimal now",
    "proposed_fix": "Concrete fix as a code change or workflow change",
    "estimated_implementation_hours_claude": 1,
    "estimated_value_unlocked": "Time saved / quality uplift / risk avoided",
    "priority_1_10": 8
  }}
]}}""",
        "cron_hours": 6,
    },
    "tools_scout": {
        "title": "Tools Scout Brain",
        "mission": (
            "You hunt new FREE tools, APIs, platforms, services emerging in "
            "2026 that could be integrated to our automation stack. Focus on "
            "what's NEW or UNDER-USED in the AI/POD/marketplace landscape."
        ),
        "prompt_template": SYSTEM_PREAMBLE + """TOOLS SCOUT BRAIN — find NEW free tools/APIs/platforms that could supercharge the system.

CURRENT SYSTEM STATE:
{state}

TOOLS ALREADY USED:
{pipelines}

TASK: Propose 5-10 NEW free or generous-free-tier tools/APIs/platforms. Focus on:
- Emerging AI image/video/audio generators (better quality, more volume)
- New POD platforms or marketplaces opening up
- Free APIs for market intelligence (search trends, social listening)
- New gamedev/asset marketplaces (the 'assets in expansion' opportunity)
- Niche distribution platforms (mobile, audiobooks, indie stores)
- Open-source self-hostable tools that could replace paid services
- AVOID anything we already use (Pollinations, HF, Gemini, Etsy, Cults3D, TGC, itch.io)

OUTPUT STRICT JSON:
{{"proposals": [
  {{
    "rank": 1,
    "tool_or_platform": "Name",
    "url": "https://...",
    "category": "ai_image / ai_text / ai_audio / pod / marketplace / scraping / analytics / dev_tool",
    "free_tier_concrete_limits": "X req/day, Y MB storage, etc.",
    "what_it_does_uniquely": "Specifically what makes it better than alternatives",
    "would_integrate_where": "Which pipeline + concrete integration step",
    "novelty_2026_1_10": 8,
    "risk_or_caveat": "ToS / rate limit / content filter / known issue"
  }}
]}}""",
        "cron_hours": 12,
    },
    "niches_explorer": {
        "title": "Niches & Assets Explorer Brain",
        "mission": (
            "You explore ultra-specific niches with passionate underserved "
            "communities AND identify expansion opportunities in adjacent "
            "markets (gamedev assets, B2B monuments, faceless content, etc.)."
        ),
        "prompt_template": SYSTEM_PREAMBLE + """NICHES & ASSETS EXPLORER BRAIN — find ultra-specific underserved niches AND adjacent expansion markets.

CURRENT SYSTEM STATE:
{state}

NICHES & PILLARS ALREADY EXPLOITED:
{pipelines}

TASK: Propose 5-10 NEW niche or adjacent-market opportunities. Focus on:
- Ultra-specific professions/hobbies with passionate but underserved communities (>50k members, low Etsy saturation)
- Adjacent markets in EXPANSION (gamedev assets, indie game music, AI prompt packs, Notion templates, mobile app accessories)
- Sub-cultures with strong identity codes & insider vocabulary
- Untapped B2B opportunities (monuments, local museums, sports clubs, professional associations)
- Avoid already-overdone (cat moms, coffee, generic teachers, basic dog parents)

OUTPUT STRICT JSON:
{{"proposals": [
  {{
    "rank": 1,
    "name": "Specific niche or market",
    "type": "deep_niche / adjacent_market / b2b / sub_culture",
    "audience_size_estimate": 80000,
    "passion_level_1_10": 9,
    "current_saturation_1_10": 3,
    "growth_trajectory": "exploding / steady / slow / unknown",
    "buyer_persona": "Detailed buyer description",
    "product_angles": ["idea 1", "idea 2", "idea 3"],
    "best_pipeline_or_new": "Which existing pipeline OR new pipeline name",
    "first_test_product": "Concrete first product to ship",
    "estimated_monthly_revenue_year1_eur": 300
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

def _models_to_try() -> list[str]:
    """Modèle principal puis fallbacks (sans doublon)."""
    seq = [GEMINI_MODEL]
    for m in GEMINI_FALLBACKS:
        if m not in seq:
            seq.append(m)
    return seq


def call_gemini(prompt: str, retries: int = 3) -> tuple[dict | None, str]:
    """Appelle Gemini (JSON strict). Retourne (resultat, info).

    info = nom du modèle qui a répondu, ou message d'erreur explicite (pour
    diagnostic). Essaie chaque modèle de _models_to_try() ; sur 404 (modèle
    déprécié) passe au suivant, sur 429 (quota) applique un backoff.
    """
    if not GEMINI_API_KEY:
        return None, "GEMINI_API_KEY absent"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            # thinkingBudget=0 : désactive le thinking de gemini-2.5-flash.
            # Sans ça, les tokens de "thinking" consomment tout le budget
            # maxOutputTokens et la réponse JSON est tronquée ou vide.
            # responseMimeType n'est PAS utilisé : combiné au thinking, il
            # provoque des réponses vides (bug Gemini API confirmé en prod).
            "thinkingConfig": {"thinkingBudget": 0},
            "maxOutputTokens": 8000,
        },
    }).encode("utf-8")
    last_err = "inconnu"
    for model in _models_to_try():
        url = f"{API_BASE}/{model}:generateContent?key={GEMINI_API_KEY}"
        for attempt in range(retries):
            req = urllib.request.Request(
                url, data=body,
                headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
            )
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    resp_data = json.loads(resp.read())
                parts = resp_data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts)
                if not text:
                    raise ValueError(f"Réponse vide (finishReason={resp_data.get('candidates',[{}])[0].get('finishReason','?')})")
                # Strip markdown fences si présentes (sans responseMimeType)
                t = text.strip()
                if t.startswith("```"):
                    parts_fence = t.split("```")
                    inner = parts_fence[1] if len(parts_fence) > 1 else ""
                    if inner.startswith("json"):
                        inner = inner[4:]
                    t = inner.strip()
                elif not (t.startswith("{") or t.startswith("[")):
                    start = t.find("{")
                    if start != -1:
                        t = t[start:]
                return json.loads(t), model
            except urllib.error.HTTPError as exc:
                detail = exc.read()[:200].decode(errors="ignore")
                last_err = f"{model}: HTTP {exc.code} {detail}"
                print(f"    {last_err}")
                if exc.code == 404:
                    break  # modèle inexistant/déprécié -> modèle suivant
                time.sleep((30 if exc.code == 429 else 3) + attempt * 10)
            except Exception as exc:  # noqa: BLE001
                last_err = f"{model}: {type(exc).__name__} {exc}"
                print(f"    {last_err}")
                time.sleep(3 + attempt * 3)
    return None, last_err


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
    result, info = call_gemini(prompt)

    if not result:
        print(f"✗ Gemini call failed : {info}")
        # Rapport d'erreur explicite (pas de silence) pour diagnostic via Actions.
        (BRAIN_DIR / f"{agent_key}_proposals.json").write_text(json.dumps({
            "agent": agent_key,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "ERROR — Gemini call failed",
            "error": info,
            "models_tried": _models_to_try(),
        }, indent=2, ensure_ascii=False))
        return 1

    # Format report
    report = {
        "agent": agent_key,
        "title": agent["title"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model": info,
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
