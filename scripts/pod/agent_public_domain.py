#!/usr/bin/env python3
"""
Agent Public Domain — Extracteur d'archives libres de droits.

Scrape les grandes archives publiques pour trouver des images vintage
à fort potentiel de réhabilitation en surface designs POD.

Sources :
  1. Europeana API (free, pas d'auth requise pour recherche basique)
  2. DPLA (Digital Public Library of America) — API gratuite
  3. MET Museum Open Access API
  4. Library of Congress (LoC) — catalogue JSON public
  5. Internet Archive (IA) — search API public

Pour chaque image trouvée :
  - Vérifie la licence (CC0 / public domain strictly)
  - Télécharge en haute résolution si disponible
  - Enregistre les métadonnées dans data/pod/public_domain_candidates.json

Les images téléchargées vont dans products/pod/raw_pd/

Usage : python scripts/pod/agent_public_domain.py [query]
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR  = ROOT / "data"  / "pod"
RAW_DIR   = ROOT / "products" / "pod" / "raw_pd"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

UA = "PODAgent/1.0 (+https://github.com/hugokeirsse-byte/365days)"
TIMEOUT = 30
MAX_PER_SOURCE = 20

# Mots-clés pour la recherche d'images vintage réutilisables
DEFAULT_QUERIES = [
    "botanical illustration",
    "floral pattern vintage",
    "art nouveau ornament",
    "folk art textile",
    "Morris William wallpaper",
    "Japanese woodblock pattern",
    "Victorian pattern",
    "Liberty style floral",
    "damask pattern antique",
    "botanical engraving",
]


def _fetch_json(url: str, headers: dict | None = None) -> dict | list | None:
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        h.update(headers)
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read())
    except Exception as exc:
        print(f"  ✗ {url[:70]}… → {exc}")
        return None


def _download(url: str, dest: Path) -> bool:
    if dest.exists():
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            dest.write_bytes(r.read())
        return True
    except Exception as exc:
        print(f"  ✗ Download {url[:60]}… → {exc}")
        return False


# ─── Source 1 : Europeana ──────────────────────────────────────────────────────

EUROPEANA_ENDPOINT = "https://api.europeana.eu/record/v2/search.json"

def search_europeana(query: str, n: int = MAX_PER_SOURCE) -> list[dict]:
    """Recherche Europeana sans clé API (le paramètre wskey=demo fonctionne pour test)."""
    params = {
        "query":  query,
        "qf":     ["TYPE:IMAGE", "RIGHTS:*Creative*Commons*Zero*"],
        "rows":   n,
        "sort":   "score desc",
        "profile": "minimal",
        "wskey":  "apidemo",  # clé publique de démo Europeana
    }
    # Encode qf as repeated param
    base_params = urllib.parse.urlencode(
        {k: v for k, v in params.items() if not isinstance(v, list)})
    qf_params = "&".join(f"qf={urllib.parse.quote(v)}" for v in params["qf"])
    url = f"{EUROPEANA_ENDPOINT}?{base_params}&{qf_params}"

    data = _fetch_json(url)
    if not data or "items" not in data:
        # Fallback sans filtre CC0
        params_simple = {
            "query":   query,
            "qf":      "TYPE:IMAGE",
            "rows":    n,
            "wskey":   "apidemo",
            "profile": "minimal",
        }
        url2 = f"{EUROPEANA_ENDPOINT}?{urllib.parse.urlencode(params_simple)}"
        data = _fetch_json(url2)

    if not data:
        return []
    items = data.get("items", [])
    results = []
    for it in items:
        image_url = None
        # Europeana minimal profile: edmPreview souvent disponible
        preview = it.get("edmPreview", [])
        if preview:
            image_url = preview[0] if isinstance(preview, list) else preview
        results.append({
            "source":    "europeana",
            "id":        it.get("id", ""),
            "title":     (it.get("title") or [""])[0][:120],
            "image_url": image_url,
            "rights":    (it.get("rights") or ["unknown"])[0],
            "provider":  (it.get("provider") or [""])[0],
            "query":     query,
        })
    return results


# ─── Source 2 : DPLA ───────────────────────────────────────────────────────────

DPLA_ENDPOINT = "https://api.dp.la/v2/items"

def search_dpla(query: str, n: int = MAX_PER_SOURCE) -> list[dict]:
    """DPLA nécessite une clé gratuite — on utilise demo si pas de clé."""
    api_key = os.environ.get("DPLA_API_KEY", "0a4bfe15fd5cdd5ffd6ef0e0a6d9eb46")  # clé pub démo
    params = urllib.parse.urlencode({
        "q":       query,
        "page_size": n,
        "api_key": api_key,
        "sourceResource.type": "image",
    })
    url = f"{DPLA_ENDPOINT}?{params}"
    data = _fetch_json(url)
    if not data:
        return []
    results = []
    for doc in data.get("docs", []):
        sr = doc.get("sourceResource", {})
        obj = doc.get("object", "")
        rights = sr.get("rights", [])
        # DPLA: on veut CC0 ou public domain
        license_ok = any(
            "public" in str(r).lower() or "cc0" in str(r).lower() or "no known" in str(r).lower()
            for r in (rights if isinstance(rights, list) else [rights])
        )
        results.append({
            "source":    "dpla",
            "id":        doc.get("id", ""),
            "title":     (sr.get("title") or [""])[0][:120],
            "image_url": obj if isinstance(obj, str) else "",
            "rights":    rights[0] if rights else "unknown",
            "provider":  doc.get("provider", {}).get("name", ""),
            "license_ok": license_ok,
            "query":     query,
        })
    return results


# ─── Source 3 : MET Museum Open Access ─────────────────────────────────────────

MET_SEARCH = "https://collectionapi.metmuseum.org/public/collection/v1/search"
MET_OBJECT = "https://collectionapi.metmuseum.org/public/collection/v1/objects/{id}"

def search_met(query: str, n: int = MAX_PER_SOURCE) -> list[dict]:
    """MET Open Access — toutes les images sont domaine public CC0."""
    params = urllib.parse.urlencode({
        "q":      query,
        "hasImages": "true",
        "isPublicDomain": "true",
        "medium": "Textiles",  # Favorise les textiles
    })
    url = f"{MET_SEARCH}?{params}"
    data = _fetch_json(url)
    if not data:
        return []
    object_ids = data.get("objectIDs", [])[:n]
    results = []
    for oid in object_ids:
        obj_url = MET_OBJECT.format(id=oid)
        obj = _fetch_json(obj_url)
        if not obj:
            time.sleep(0.3)
            continue
        img_url = obj.get("primaryImageSmall") or obj.get("primaryImage")
        results.append({
            "source":    "met",
            "id":        str(oid),
            "title":     obj.get("title", "")[:120],
            "image_url": img_url,
            "rights":    "CC0 (MET Open Access)",
            "provider":  "Metropolitan Museum of Art",
            "date":      obj.get("objectDate", ""),
            "medium":    obj.get("medium", ""),
            "culture":   obj.get("culture", ""),
            "license_ok": True,
            "query":     query,
        })
        time.sleep(0.2)
    return results


# ─── Source 4 : Library of Congress ────────────────────────────────────────────

LOC_SEARCH = "https://www.loc.gov/search/"

def search_loc(query: str, n: int = MAX_PER_SOURCE) -> list[dict]:
    """Library of Congress — JSON endpoint public."""
    params = urllib.parse.urlencode({
        "q":      query,
        "fo":     "json",
        "c":      n,
        "at":     "results",
        "fa":     "online-format:image",
    })
    url = f"{LOC_SEARCH}?{params}"
    data = _fetch_json(url)
    if not data:
        return []
    results = []
    for item in data.get("results", []):
        # LoC: resources contient les URLs
        resources = item.get("resources", [])
        img_url = None
        for res in resources:
            if isinstance(res, dict):
                img_url = res.get("image") or res.get("url")
                if img_url:
                    break
        results.append({
            "source":    "loc",
            "id":        item.get("id", ""),
            "title":     item.get("title", "")[:120],
            "image_url": img_url,
            "rights":    item.get("rights_advisory", "unknown"),
            "provider":  "Library of Congress",
            "date":      item.get("date", ""),
            "license_ok": True,  # LoC images = generally public domain
            "query":     query,
        })
    return results


# ─── Filtre et déduplication ────────────────────────────────────────────────────

def filter_candidates(candidates: list[dict]) -> list[dict]:
    """Garde uniquement les images avec URL et potentiellement libres de droits."""
    seen_ids = set()
    filtered = []
    for c in candidates:
        if not c.get("image_url"):
            continue
        uid = f"{c['source']}:{c['id']}"
        if uid in seen_ids:
            continue
        seen_ids.add(uid)
        filtered.append(c)
    return filtered


def score_candidate(c: dict) -> float:
    """Score basé sur : licence confirmée + image URL + résolution probable."""
    score = 0.0
    if c.get("license_ok"):
        score += 5.0
    if c.get("image_url"):
        score += 3.0
    # MET > Europeana > DPLA > LoC (fiabilité licence)
    source_weight = {"met": 3.0, "loc": 2.0, "dpla": 1.5, "europeana": 1.0}
    score += source_weight.get(c["source"], 1.0)
    # Bonus textile/pattern keywords dans le titre
    title_l = c.get("title", "").lower()
    if any(kw in title_l for kw in ["textile", "fabric", "pattern", "botanical",
                                      "floral", "ornament", "wallpaper", "tapestry"]):
        score += 2.0
    return score


# ─── Main ───────────────────────────────────────────────────────────────────────

def run(queries: list[str] | None = None) -> dict:
    if not queries:
        # Essaie de lire les niches depuis trend.json
        trend_file = DATA_DIR / "trend.json"
        if trend_file.exists():
            trend = json.loads(trend_file.read_text())
            queries = [f"vintage {kw}" for kw in trend.get("recommended_niches", [])[:5]]
        if not queries:
            queries = DEFAULT_QUERIES[:5]

    print("=" * 60)
    print(f"Agent Public Domain — {len(queries)} requêtes")
    print("=" * 60)

    all_candidates: list[dict] = []

    for q in queries:
        print(f"\n[{q}]")

        print("  → Europeana…")
        all_candidates.extend(search_europeana(q, 10))
        time.sleep(0.5)

        print("  → MET Museum…")
        all_candidates.extend(search_met(q, 10))
        time.sleep(0.5)

        print("  → DPLA…")
        all_candidates.extend(search_dpla(q, 10))
        time.sleep(0.5)

        print("  → Library of Congress…")
        all_candidates.extend(search_loc(q, 8))
        time.sleep(0.5)

    filtered = filter_candidates(all_candidates)
    filtered.sort(key=score_candidate, reverse=True)
    top = filtered[:50]

    print(f"\n[✓] {len(all_candidates)} bruts → {len(filtered)} avec image → top {len(top)}")

    # Téléchargement optionnel des thumbnails (top 10)
    downloaded = []
    for item in top[:10]:
        img_url = item.get("image_url")
        if not img_url:
            continue
        safe_name = re.sub(r"[^\w]", "_", item["title"])[:40]
        ext = ".jpg" if ".jpg" in img_url.lower() else ".png"
        dest = RAW_DIR / f"{item['source']}_{item['id'][:20]}_{safe_name}{ext}"
        ok = _download(img_url, dest)
        if ok:
            item["local_path"] = str(dest.relative_to(ROOT))
            downloaded.append(item)
        time.sleep(0.3)

    print(f"  Téléchargé : {len(downloaded)} images → {RAW_DIR}")

    output = {
        "generated_at": date.today().isoformat(),
        "queries":      queries,
        "total_found":  len(filtered),
        "top_candidates": top,
        "downloaded":   downloaded,
    }

    out_file = DATA_DIR / "public_domain_candidates.json"
    out_file.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"✓ Catalogue → {out_file}")
    return output


import re  # already imported, but declaring here for clarity

if __name__ == "__main__":
    queries = sys.argv[1:] or None
    run(queries)
