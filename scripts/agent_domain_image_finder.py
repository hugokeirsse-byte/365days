#!/usr/bin/env python3
"""
Agent de recherche et de téléchargement d'images du domaine public sur Wikimedia Commons.
Conçu pour alimenter un pipeline de livres de coloriage sans IA générative.
"""

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Union

# Configuration globale
USER_AGENT = "365days-ImageFinder/1.0 (hugo.keirsse@gmail.com)"
HEADERS = {"User-Agent": USER_AGENT}
TIMEOUT = 30


def slugify(text: str) -> str:
    """Convertit un texte en chaîne de caractères sécurisée pour les noms de fichiers."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "_", text).strip("_")


def clean_html(text: str) -> str:
    """Supprime les balises HTML d'une chaîne de caractères."""
    if not text:
        return ""
    return re.sub(r"<[^>]*>", "", text).strip()


def api_request(params: dict) -> dict:
    """Effectue une requête GET robuste vers l'API Wikimedia Commons."""
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def find_and_download(
    theme: str,
    out_dir: Union[str, Path],
    max_images: int = 20,
    min_width_px: int = 800,
) -> List[Dict[str, Any]]:
    """
    Recherche et télécharge des images libres de droits depuis Wikimedia Commons.
    Filtre par taille, format et licence, puis sauvegarde l'image et ses métadonnées.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    theme_slug = slugify(theme)

    # Étape 1 : Recherche de pages dans l'espace de noms File (ns=6)
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": theme,
        "srnamespace": "6",
        "srlimit": "50",
        "format": "json",
    }

    try:
        search_results = api_request(search_params)
    except Exception as e:
        print(f"Erreur lors de la recherche API : {e}", file=sys.stderr)
        return []

    search_items = search_results.get("query", {}).get("search", [])
    page_ids = [item["pageid"] for item in search_items if "pageid" in item]

    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    img_index = 1
    results = []

    # Étape 2 : Analyse de chaque image trouvée
    for page_id in page_ids:
        if downloaded_count >= max_images:
            break

        info_params = {
            "action": "query",
            "pageids": str(page_id),
            "prop": "imageinfo",
            "iiprop": "url|size|extmetadata",
            "format": "json",
        }

        try:
            info_data = api_request(info_params)
            pages = info_data.get("query", {}).get("pages", {})
            if not pages:
                continue
            page_info = list(pages.values())[0]
            imageinfo_list = page_info.get("imageinfo", [])
            if not imageinfo_list:
                continue
            info = imageinfo_list[0]
        except Exception as e:
            print(f"FAIL: Impossible de récupérer les infos du pageid {page_id} - {e}")
            failed_count += 1
            continue

        # Extraction des données de base
        url = info.get("url", "")
        width = info.get("width", 0)
        height = info.get("height", 0)
        extmetadata = info.get("extmetadata", {})

        # Filtre de qualité (largeur minimale)
        if width < min_width_px:
            continue

        # Filtre de format (uniquement JPG/JPEG ou PNG)
        parsed_url = urllib.parse.urlparse(url)
        ext = Path(parsed_url.path).suffix.lower().lstrip(".")
        if ext not in ["jpg", "jpeg", "png"]:
            continue
        if ext == "jpeg":
            ext = "jpg"

        # Filtre de licence
        license_name = extmetadata.get("LicenseShortName", {}).get("value", "")
        license_upper = license_name.upper()
        allowed_licenses = ["CC0", "PUBLIC DOMAIN", "CC-BY", "CC-BY-SA", "PD"]
        is_valid_license = any(lic in license_upper for lic in allowed_licenses)

        if not is_valid_license:
            continue

        # Nettoyage des métadonnées
        raw_title = extmetadata.get("ObjectName", {}).get("value", "") or page_info.get("title", "")
        title = clean_html(raw_title)
        if title.lower().startswith("file:"):
            title = title[5:]

        author = clean_html(extmetadata.get("Artist", {}).get("value", "Unknown"))
        source_url = info.get("descriptionurl", url)

        # Définition des chemins de sortie
        filename = f"{theme_slug}_{img_index:03d}.{ext}"
        dest_path = out_path / filename
        meta_path = out_path / f"{theme_slug}_{img_index:03d}.json"

        img_index += 1

        # Idempotence : si l'image et ses métadonnées existent déjà, on passe
        if dest_path.exists() and meta_path.exists():
            print(f"SKIP: {title} ({license_name})")
            skipped_count += 1
            downloaded_count += 1
            results.append({
                "path": str(dest_path),
                "title": title,
                "author": author,
                "license": license_name,
                "url": url,
            })
            continue

        # Étape 3 : Téléchargement et écriture des fichiers
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                img_data = response.read()

            # Sauvegarde de l'image
            with open(dest_path, "wb") as f:
                f.write(img_data)

            # Sauvegarde des métadonnées
            meta_data = {
                "title": title,
                "author": author,
                "license": license_name,
                "source_url": source_url,
                "width": width,
                "height": height,
                "local_path": str(dest_path),
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta_data, f, indent=2, ensure_ascii=False)

            print(f"OK: {title} ({license_name})")
            downloaded_count += 1
            results.append({
                "path": str(dest_path),
                "title": title,
                "author": author,
                "license": license_name,
                "url": url,
            })

        except Exception as e:
            print(f"FAIL: {title} ({license_name}) - {e}")
            failed_count += 1

    # Affichage du bilan final
    actual_downloads = downloaded_count - skipped_count
    print(f"\n{actual_downloads} images telechargees, {skipped_count} sautees, {failed_count} echecs")
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Télécharge des images libres de droits depuis Wikimedia Commons."
    )
    parser.add_argument("theme", type=str, help="Thème de recherche (ex: 'botanical vintage')")
    parser.add_argument("--out", type=str, required=True, help="Dossier de sortie")
    parser.add_argument("--max", type=int, default=20, help="Nombre maximum d'images à télécharger")
    parser.add_argument("--min-width", type=int, default=800, help="Largeur minimale en pixels")

    args = parser.parse_args()
    find_and_download(
        theme=args.theme,
        out_dir=args.out,
        max_images=args.max,
        min_width_px=args.min_width,
    )


if __name__ == "__main__":
    main()