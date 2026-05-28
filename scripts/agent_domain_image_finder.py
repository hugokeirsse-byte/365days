import argparse
import html
import json
import pathlib
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

# Configuration globale
USER_AGENT = "365days-ImageFinder/1.0 (hugo.keirsse@gmail.com)"
TIMEOUT = 30


def slugify(text: str) -> str:
    """Convertit un texte en chaîne de caractères sûre pour les noms de fichiers."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def clean_html(text: str) -> str:
    """Supprime les balises HTML et décode les entités HTML d'une chaîne."""
    if not text:
        return ""
    # Supprime les balises HTML
    cleaned = re.sub(r"<[^<]+?>", "", text)
    # Décode les entités HTML (ex: &amp; -> &)
    return html.unescape(cleaned).strip()


def api_request(url: str) -> dict:
    """Effectue une requête GET HTTP vers l'API Wikimedia avec le User-Agent requis."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def find_and_download(
    theme: str,
    out_dir: str | Path,
    max_images: int = 20,
    min_width_px: int = 800,
) -> list[dict]:
    """Recherche et télécharge des images libres de droits depuis Wikimedia Commons."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    theme_slug = slugify(theme)

    # Chargement des métadonnées existantes pour assurer l'idempotence
    existing_urls = set()
    for json_file in out_dir.glob(f"{theme_slug}_*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
                if "source_url" in meta:
                    existing_urls.add(meta["source_url"])
        except Exception:
            pass

    # Étape 1 : Recherche sur Wikimedia Commons (Namespace 6 = File)
    encoded_theme = urllib.parse.quote(theme)
    search_url = (
        f"https://commons.wikimedia.org/w/api.php?action=query&list=search"
        f"&srsearch={encoded_theme}&srnamespace=6&srlimit=50&format=json"
    )

    try:
        search_data = api_request(search_url)
    except Exception as e:
        print(f"FAIL: Impossible de contacter l'API de recherche : {e}")
        return []

    search_results = search_data.get("query", {}).get("search", [])
    downloaded_list = []
    stats = {"ok": 0, "skip": 0, "fail": 0}

    for item in search_results:
        if stats["ok"] >= max_images:
            break

        pageid = item.get("pageid")
        if not pageid:
            continue

        # Étape 2 : Récupération des informations détaillées de l'image
        info_url = (
            f"https://commons.wikimedia.org/w/api.php?action=query"
            f"&pageids={pageid}&prop=imageinfo&iiprop=url|size|extmetadata&format=json"
        )

        try:
            info_data = api_request(info_url)
            pages = info_data.get("query", {}).get("pages", {})
            page_info = pages.get(str(pageid), {})
            imageinfos = page_info.get("imageinfo", [])
            if not imageinfos:
                continue
            info = imageinfos[0]
        except Exception as e:
            stats["fail"] += 1
            print(f"FAIL: Impossible de récupérer les infos du pageid {pageid} : {e}")
            continue

        # Extraction et validation des métadonnées
        image_url = info.get("url", "")
        width = info.get("width", 0)
        height = info.get("height", 0)
        extmetadata = info.get("extmetadata", {})

        if not image_url:
            continue

        # Validation du format (uniquement JPG/PNG)
        parsed_url = urllib.parse.urlparse(image_url)
        ext = Path(parsed_url.path).suffix.lower().lstrip(".")
        if ext not in ("jpg", "jpeg", "png"):
            continue

        if ext == "jpeg":
            ext = "jpg"

        # Validation de la taille minimale
        if width < min_width_px:
            continue

        # Validation de la licence
        license_name = extmetadata.get("LicenseShortName", {}).get("value", "")
        allowed_licenses = ["cc0", "public domain", "cc-by", "cc-by-sa"]
        if not any(lic in license_name.lower() for lic in allowed_licenses):
            continue

        # Nettoyage du titre et de l'auteur
        raw_title = extmetadata.get("ObjectName", {}).get("value", "")
        if not raw_title:
            raw_title = page_info.get("title", "Sans titre").replace("File:", "")
        title = clean_html(raw_title)

        raw_author = extmetadata.get("Artist", {}).get("value", "Inconnu")
        author = clean_html(raw_author)

        # Idempotence : vérification si déjà téléchargé
        if image_url in existing_urls:
            stats["skip"] += 1
            print(f"SKIP: {title} [{license_name}] (Déjà téléchargé)")
            continue

        # Détermination du prochain index disponible pour le nommage
        index = 1
        while True:
            img_path = out_dir / f"{theme_slug}_{index:03d}.{ext}"
            json_path = out_dir / f"{theme_slug}_{index:03d}.json"
            if not img_path.exists() and not json_path.exists():
                dest_img = img_path
                dest_json = json_path
                break
            index += 1

        # Étape 3 : Téléchargement et sauvegarde
        try:
            req = urllib.request.Request(image_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                img_data = response.read()

            # Sauvegarde du fichier image
            with open(dest_img, "wb") as f:
                f.write(img_data)

            # Sauvegarde des métadonnées JSON
            meta_data = {
                "title": title,
                "author": author,
                "license": license_name,
                "source_url": image_url,
                "width": width,
                "height": height,
                "local_path": str(dest_img),
            }
            with open(dest_json, "w", encoding="utf-8") as f:
                json.dump(meta_data, f, indent=2, ensure_ascii=False)

            stats["ok"] += 1
            print(f"OK: {title} [{license_name}]")
            downloaded_list.append(meta_data)

        except Exception as e:
            stats["fail"] += 1
            print(f"FAIL: {title} [{license_name}] - Erreur: {e}")

    print(
        f"\n{stats['ok']} images telechargees, {stats['skip']} sautees, {stats['fail']} echecs"
    )
    return downloaded_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Télécharge des images du domaine public depuis Wikimedia Commons."
    )
    parser.add_argument(
        "theme", type=str, help="Thème de recherche (ex: 'botanical vintage')"
    )
    parser.add_argument(
        "--out", type=str, required=True, help="Dossier de destination"
    )
    parser.add_argument(
        "--max", type=int, default=20, help="Nombre maximum d'images à télécharger"
    )
    parser.add_argument(
        "--min-width", type=int, default=800, help="Largeur minimale en pixels"
    )

    args = parser.parse_args()

    try:
        find_and_download(
            theme=args.theme,
            out_dir=args.out,
            max_images=args.max,
            min_width_px=args.min_width,
        )
    except KeyboardInterrupt:
        print("\nInterrompu par l'utilisateur.")
        sys.exit(1)