#!/usr/bin/env python3
"""Téléchargeur de sources domaine public — SANS clé API.

Lit data/sources/domain_public_manifests.json et récupère des images HD
depuis les backends gratuits qui ne demandent AUCUNE clé :
  - Met Open Access (CC0)  -> Hokusai, Dürer
  - Wikimedia Commons      -> Köhler, Haeckel

Les sources qui nécessitent une clé (NYPL, Smithsonian, Rijksmuseum, BHL…)
sont listées comme "🔑 plus tard" et ignorées pour l'instant.

Sortie : stage_local/domain_public/<source_id>/NNN.jpg + _attribution.json
(jamais committé — cf. .gitignore).

Usage :
  python scripts/download_domain_public_sources.py --list
  python scripts/download_domain_public_sources.py --source hokusai_estampes_pre_1900 --limit 10
  python scripts/download_domain_public_sources.py --all --limit 20 [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    sys.exit("ERREUR : httpx non installé (pip install httpx)")

try:
    from tenacity import retry, stop_after_attempt, wait_exponential
except ImportError:  # fallback : pas de retry si tenacity absent
    def retry(*_a, **_k):
        def deco(fn):
            return fn
        return deco

    def stop_after_attempt(*_a, **_k):
        return None

    def wait_exponential(*_a, **_k):
        return None

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "sources" / "domain_public_manifests.json"
OUT_BASE = ROOT / "stage_local" / "domain_public"
UA = "365days-PD-Downloader/1.0 (educational use; public-domain sources only)"
TIMEOUT = 60

# Backends accessibles SANS clé (source_id -> config).
BACKENDS = {
    "hokusai_estampes_pre_1900": {"type": "met", "query": "hokusai"},
    "durer_engravings": {"type": "met", "query": "durer"},
    "kohler_medicinal_plants_1887": {"type": "wikimedia", "category": "Köhler's Medizinal-Pflanzen"},
    "haeckel_kunstformen_natur_1899": {"type": "wikimedia", "category": "Kunstformen der Natur"},
}

# Sources nécessitant une clé / un travail supplémentaire (informational).
NEEDS_KEY = {
    "audubon_birds_america_1827": "NYPL token",
    "vesalius_anatomy_1543": "Wellcome IIIF",
    "smithsonian_open_access": "api.si.edu key",
    "rijksmuseum_dutch_masters_pre_1900": "Rijksmuseum key",
    "old_maps_loc": "LoC API (à mapper)",
    "internet_archive_books": "IA / IIIF (à mapper)",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _get(client: "httpx.Client", url: str, **kw):
    r = client.get(url, timeout=TIMEOUT, **kw)
    r.raise_for_status()
    return r


def met_image_urls(client, query: str, limit: int) -> list[str]:
    """Met Open Access : seules les œuvres isPublicDomain sont retenues (CC0)."""
    r = _get(
        client,
        "https://collectionapi.metmuseum.org/public/collection/v1/search",
        params={"q": query, "hasImages": "true"},
    )
    ids = (r.json().get("objectIDs") or [])[: limit * 5]  # marge : tous ne sont pas PD
    urls: list[str] = []
    for oid in ids:
        if len(urls) >= limit:
            break
        try:
            obj = _get(
                client,
                f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}",
            ).json()
        except Exception:
            continue
        if obj.get("isPublicDomain") and obj.get("primaryImage"):
            urls.append(obj["primaryImage"])
    return urls


def wikimedia_image_urls(client, category: str, limit: int) -> list[str]:
    """Wikimedia Commons : membres d'une catégorie -> URL HD (largeur 2400px)."""
    api = "https://commons.wikimedia.org/w/api.php"
    r = _get(
        client,
        api,
        params={
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmtype": "file",
            "cmlimit": str(min(limit * 2, 500)),
            "format": "json",
        },
    )
    members = r.json().get("query", {}).get("categorymembers", [])
    urls: list[str] = []
    for m in members:
        if len(urls) >= limit:
            break
        info = _get(
            client,
            api,
            params={
                "action": "query",
                "titles": m["title"],
                "prop": "imageinfo",
                "iiprop": "url",
                "iiurlwidth": "2400",
                "format": "json",
            },
        ).json()
        for page in info.get("query", {}).get("pages", {}).values():
            ii = (page.get("imageinfo") or [{}])[0]
            url = ii.get("thumburl") or ii.get("url")
            if url:
                urls.append(url)
    return urls


def _download(client, url: str, dest: Path) -> str:
    if dest.exists():
        return "skip"
    r = _get(client, url)
    dest.write_bytes(r.content)
    return "ok"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", help="id d'une source (cf. --list)")
    ap.add_argument("--all", action="store_true", help="toutes les sources sans clé")
    ap.add_argument("--limit", type=int, default=20, help="nb max d'images par source")
    ap.add_argument("--dry-run", action="store_true", help="liste sans télécharger")
    ap.add_argument("--list", action="store_true", help="liste les sources et sort")
    args = ap.parse_args()

    sources = json.loads(MANIFEST.read_text(encoding="utf-8"))["sources"]

    if args.list:
        print("✅ Téléchargeables SANS clé :")
        for sid, cfg in BACKENDS.items():
            print(f"   {sid}  [{cfg['type']}]")
        print("🔑 Nécessitent une clé (plus tard) :")
        for sid, why in NEEDS_KEY.items():
            print(f"   {sid}  ({why})")
        return

    if args.all:
        targets = list(BACKENDS)
    elif args.source:
        targets = [args.source]
    else:
        ap.error("précise --source <id>, --all, ou --list")

    with httpx.Client(headers={"User-Agent": UA}, follow_redirects=True) as client:
        for sid in targets:
            cfg = BACKENDS.get(sid)
            if not cfg:
                print(f"⚠ {sid} : pas de backend sans clé ({NEEDS_KEY.get(sid, 'non supporté')})")
                continue
            print(f"\n=== {sid} [{cfg['type']}] (limite {args.limit}) ===")
            try:
                if cfg["type"] == "met":
                    urls = met_image_urls(client, cfg["query"], args.limit)
                else:
                    urls = wikimedia_image_urls(client, cfg["category"], args.limit)
            except Exception as e:  # noqa: BLE001
                print(
                    f"  ✗ source injoignable ({type(e).__name__}). "
                    "Réseau tiers bloqué ? Ce script doit tourner là où l'accès "
                    "aux API publiques (Met, Wikimedia) est ouvert (PC/Termux, GitHub Actions)."
                )
                continue
            print(f"  {len(urls)} image(s) trouvée(s)")

            if args.dry_run:
                for u in urls[:5]:
                    print(f"    [dry] {u}")
                continue

            out = OUT_BASE / sid
            out.mkdir(parents=True, exist_ok=True)
            meta = sources.get(sid, {})
            (out / "_attribution.json").write_text(
                json.dumps(
                    {
                        "source_id": sid,
                        "rights_label": meta.get("rights_label_to_attach", "Public Domain"),
                        "license": meta.get("license", ""),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            ok = skip = err = 0
            for i, u in enumerate(urls):
                try:
                    res = _download(client, u, out / f"{i:03d}.jpg")
                    ok += res == "ok"
                    skip += res == "skip"
                except Exception as e:  # noqa: BLE001
                    err += 1
                    print(f"    ✗ {u[:60]}… : {e}")
            print(f"  → {ok} téléchargées, {skip} déjà présentes, {err} erreurs → {out}")


if __name__ == "__main__":
    main()
