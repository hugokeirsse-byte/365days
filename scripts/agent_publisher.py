import os
import sys
import json
import urllib.request
import urllib.error
import textwrap

# --- Configuration ---
# Base path for product files
PRODUCTS_BASE_DIR = "products/coloring_books/_gate1"
# Default Gemini model if not specified in environment
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
# Fixed price for KDP
KDP_PRICE = 8.99

# --- Helper Functions ---

def get_env_variable(name, default=None, required=False):
    """Retrieves an environment variable, with optional default and requirement."""
    value = os.getenv(name, default)
    if required and value is None:
        print(f"Erreur: La variable d'environnement '{name}' est requise.", file=sys.stderr)
        sys.exit(1)
    return value

def create_directory_if_not_exists(path):
    """Creates a directory if it doesn't already exist."""
    os.makedirs(path, exist_ok=True)

def load_json_file(filepath):
    """Loads and returns content from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erreur: Fichier non trouvé à '{filepath}'.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Erreur: Impossible de décoder le JSON dans '{filepath}'.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Erreur lors de la lecture de '{filepath}': {e}", file=sys.stderr)
        sys.exit(1)

def save_json_file(filepath, data):
    """Saves data to a JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur lors de l'écriture de '{filepath}': {e}", file=sys.stderr)
        sys.exit(1)

def save_markdown_file(filepath, content):
    """Saves content to a Markdown file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"Erreur lors de l'écriture de '{filepath}': {e}", file=sys.stderr)
        sys.exit(1)

def call_gemini_api(api_key, model, prompt):
    """Makes a request to the Gemini API."""
    if not api_key:
        return None # Indicate Gemini is not available

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        req = urllib.request.Request(api_url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            # Extract text from the response
            if 'candidates' in response_data and response_data['candidates']:
                first_candidate = response_data['candidates'][0]
                if 'content' in first_candidate and 'parts' in first_candidate['content']:
                    for part in first_candidate['content']['parts']:
                        if 'text' in part:
                            return part['text']
            print(f"Avertissement: Réponse Gemini inattendue: {response_data}", file=sys.stderr)
            return None
    except urllib.error.HTTPError as e:
        print(f"Erreur HTTP Gemini ({e.code}): {e.read().decode('utf-8')}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"Erreur de connexion Gemini: {e.reason}", file=sys.stderr)
        return None
    except json.JSONDecodeError:
        print("Erreur: Réponse Gemini non-JSON.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Erreur inattendue lors de l'appel Gemini: {e}", file=sys.stderr)
        return None

def generate_content_with_gemini_or_fallback(brief_data, gemini_api_key, gemini_model):
    """
    Generates KDP blurb, Etsy description, tags, and keywords using Gemini or fallback templates.
    Returns a dictionary with generated content.
    """
    title = brief_data.get('title', 'Livre de Coloriage')
    author = brief_data.get('author', 'Nom de l\'Auteur')
    main_theme = brief_data.get('main_theme', 'animaux mignons')
    target_audience = brief_data.get('target_audience', 'enfants de 4 à 8 ans')

    print("Tentative de génération de contenu via Gemini...")
    gemini_output = None
    if gemini_api_key:
        # Combined prompt for all required outputs
        combined_prompt = textwrap.dedent(f"""
        Génère le contenu suivant pour un livre de coloriage intitulé "{title}" par "{author}",
        dont le thème principal est "{main_theme}" et l'audience cible est "{target_audience}".

        1.  **BLURB KDP (150-200 mots)**: Une description engageante pour Amazon KDP.
        2.  **DESCRIPTION ETSY (500-800 mots)**: Une description détaillée et optimisée SEO pour Etsy,
            incluant des mots-clés pertinents pour le coloriage, les enfants, le thème, etc.
        3.  **TAGS ETSY (13 tags, séparés par des virgules)**: Des tags pertinents pour Etsy.
        4.  **KEYWORDS KDP (7 mots-clés, séparés par des virgules)**: Des mots-clés pertinents pour KDP.

        Structure de la réponse attendue (strictement):
        BLURB_KDP: <blurb ici>
        DESCRIPTION_ETSY: <description ici>
        TAGS_ETSY: <tag1, tag2, ...>
        KEYWORDS_KDP: <keyword1, keyword2, ...>
        """)
        gemini_raw_response = call_gemini_api(gemini_api_key, gemini_model, combined_prompt)

        if gemini_raw_response:
            gemini_output = {}
            lines = gemini_raw_response.strip().split('\n')
            current_key = None
            current_value = []
            for line in lines:
                line = line.strip()
                if line.startswith("BLURB_KDP:"):
                    if current_key: gemini_output[current_key] = "\n".join(current_value).strip()
                    current_key = "BLURB_KDP"
                    current_value = [line[len("BLURB_KDP:"):].strip()]
                elif line.startswith("DESCRIPTION_ETSY:"):
                    if current_key: gemini_output[current_key] = "\n".join(current_value).strip()
                    current_key = "DESCRIPTION_ETSY"
                    current_value = [line[len("DESCRIPTION_ETSY:"):].strip()]
                elif line.startswith("TAGS_ETSY:"):
                    if current_key: gemini_output[current_key] = "\n".join(current_value).strip()
                    current_key = "TAGS_ETSY"
                    current_value = [line[len("TAGS_ETSY:"):].strip()]
                elif line.startswith("KEYWORDS_KDP:"):
                    if current_key: gemini_output[current_key] = "\n".join(current_value).strip()
                    current_key = "KEYWORDS_KDP"
                    current_value = [line[len("KEYWORDS_KDP:"):].strip()]
                elif current_key:
                    current_value.append(line)
            if current_key: gemini_output[current_key] = "\n".join(current_value).strip()

            # Basic validation of Gemini output
            if all(k in gemini_output for k in ["BLURB_KDP", "DESCRIPTION_ETSY", "TAGS_ETSY", "KEYWORDS_KDP"]):
                print("Contenu généré avec succès par Gemini.")
            else:
                print("Avertissement: La réponse de Gemini n'a pas le format attendu. Utilisation du mode fallback.", file=sys.stderr)
                gemini_output = None # Force fallback
        else:
            print("Avertissement: Gemini n'a pas pu générer le contenu. Utilisation du mode fallback.", file=sys.stderr)

    if not gemini_output:
        print("Utilisation du mode fallback pour la génération de contenu.")
        # Fallback templates
        kdp_blurb = textwrap.dedent(f"""
        Plongez dans un monde de créativité avec notre livre de coloriage "{title}" !
        Conçu spécialement pour les {target_audience}, ce livre regorge de magnifiques illustrations sur le thème des {main_theme}.
        Chaque page est une invitation à l'aventure artistique, parfaite pour développer la motricité fine et l'imagination.
        Offrez des heures de plaisir et de détente avec ce compagnon idéal pour les jeunes artistes.
        """)

        etsy_description = textwrap.dedent(f"""
        Découvrez le livre de coloriage ultime pour les {target_audience} : "{title}" !
        Ce magnifique recueil d'illustrations sur le thème des {main_theme} est parfait pour stimuler la créativité et offrir des moments de calme.
        Avec ses pages grand format et ses dessins clairs, il est idéal pour les petites mains.
        Que ce soit pour un anniversaire, un cadeau de Noël ou simplement pour occuper les enfants de manière éducative,
        ce livre de coloriage est un choix parfait. Il aide à développer la concentration, la reconnaissance des couleurs
        et la coordination œil-main. Imprimable à la maison, il offre une flexibilité incroyable.
        Procurez-vous le vôtre dès aujourd'hui et laissez l'aventure artistique commencer !
        """)

        etsy_tags = [
            f"coloriage {main_theme}", "livre coloriage", "activite enfant", "cadeau enfant",
            "dessin a colorier", "pages a colorier", "art pour enfants", "livre d'activite",
            "coloriage educatif", "telechargement numerique", "imprimable enfant",
            f"theme {main_theme}", f"pour {target_audience.replace(' ', '-')}"
        ]
        kdp_keywords = [
            f"coloriage {main_theme}", "livre coloriage enfant", f"dessin {main_theme}",
            "activite creative", "cadeau pour enfant", "livre d'art", "pages a imprimer"
        ]

        return {
            "BLURB_KDP": kdp_blurb,
            "DESCRIPTION_ETSY": etsy_description,
            "TAGS_ETSY": ", ".join(etsy_tags),
            "KEYWORDS_KDP": ", ".join(kdp_keywords)
        }
    else:
        return {
            "BLURB_KDP": gemini_output["BLURB_KDP"],
            "DESCRIPTION_ETSY": gemini_output["DESCRIPTION_ETSY"],
            "TAGS_ETSY": gemini_output["TAGS_ETSY"],
            "KEYWORDS_KDP": gemini_output["KEYWORDS_KDP"]
        }

def main():
    """Main function to orchestrate the publication package generation."""
    # 1. Get BRIEF_ID from CLI or environment
    brief_id = sys.argv[1] if len(sys.argv) > 1 else get_env_variable("BRIEF_ID")
    if not brief_id:
        print("Erreur: BRIEF_ID doit être fourni en argument CLI ou via la variable d'environnement BRIEF_ID.", file=sys.stderr)
        sys.exit(1)

    print(f"Préparation du paquet de publication pour BRIEF_ID: {brief_id}")

    # Define paths
    brief_dir = os.path.join(PRODUCTS_BASE_DIR, brief_id)
    kdp_package_path = os.path.join(brief_dir, "kdp_package.json")
    publication_output_dir = os.path.join(brief_dir, "publication")

    # Ensure output directory exists
    create_directory_if_not_exists(publication_output_dir)

    # 2. Verify kdp_package.json
    kdp_package_data = load_json_file(kdp_package_path)

    if not kdp_package_data.get('ready_for_gate2'):
        print(f"Erreur: kdp_package.json n'indique pas 'ready_for_gate2=true' pour BRIEF_ID '{brief_id}'.", file=sys.stderr)
        sys.exit(1)

    print("kdp_package.json vérifié et prêt pour GATE 2.")

    # Extract essential data from kdp_package.json
    brief_title = kdp_package_data.get('title', 'Livre de Coloriage')
    brief_author = kdp_package_data.get('author', 'Nom de l\'Auteur')
    brief_categories = kdp_package_data.get('categories', ["Art & Dessin", "Livres pour enfants"])
    brief_main_theme = kdp_package_data.get('main_theme', 'animaux mignons')
    brief_target_audience = kdp_package_data.get('target_audience', 'enfants de 4 à 8 ans')

    # 3. Get Gemini API key and model
    gemini_api_key = get_env_variable("GEMINI_API_KEY")
    gemini_model = get_env_variable("GEMINI_MODEL", default=DEFAULT_GEMINI_MODEL)

    # 4. Generate content (Gemini or fallback)
    generated_content = generate_content_with_gemini_or_fallback(
        {
            'title': brief_title,
            'author': brief_author,
            'main_theme': brief_main_theme,
            'target_audience': brief_target_audience
        },
        gemini_api_key,
        gemini_model
    )

    kdp_description = generated_content["BLURB_KDP"]
    etsy_description = generated_content["DESCRIPTION_ETSY"]
    etsy_tags_str = generated_content["TAGS_ETSY"]
    kdp_keywords_str = generated_content["KEYWORDS_KDP"]

    # Process tags and keywords into lists
    etsy_tags = [tag.strip() for tag in etsy_tags_str.split(',') if tag.strip()]
    kdp_keywords = [kw.strip() for kw in kdp_keywords_str.split(',') if kw.strip()]

    # Ensure KDP keywords are exactly 7
    if len(kdp_keywords) > 7:
        kdp_keywords = kdp_keywords[:7]
    elif len(kdp_keywords) < 7:
        # Pad with generic keywords if Gemini didn't provide enough
        print("Avertissement: Moins de 7 mots-clés KDP générés. Ajout de mots-clés génériques.", file=sys.stderr)
        generic_kws = ["livre coloriage", "activite enfant", "dessin enfant", "art therapie", "cadeau enfant", "loisirs creatifs", "livre d'activite"]
        for kw in generic_kws:
            if kw not in kdp_keywords and len(kdp_keywords) < 7:
                kdp_keywords.append(kw)

    # Ensure Etsy tags are exactly 13
    if len(etsy_tags) > 13:
        etsy_tags = etsy_tags[:13]
    elif len(etsy_tags) < 13:
        print("Avertissement: Moins de 13 tags Etsy générés. Ajout de tags génériques.", file=sys.stderr)
        generic_tags = ["coloriage", "livre enfant", "activite manuelle", "cadeau unique", "art numerique", "telechargeable", "imprimable", "loisir creatif", "dessin", "pages a colorier", "pour enfants", "activite maison", "fun"]
        for tag in generic_tags:
            if tag not in etsy_tags and len(etsy_tags) < 13:
                etsy_tags.append(tag)


    # 5. Prepare and write kdp_metadata.json
    kdp_metadata = {
        "title": brief_title,
        "author": brief_author,
        "description": kdp_description,
        "keywords": kdp_keywords,
        "categories": brief_categories,
        "price": KDP_PRICE
    }
    kdp_metadata_path = os.path.join(publication_output_dir, "kdp_metadata.json")
    save_json_file(kdp_metadata_path, kdp_metadata)
    print(f"Fichier KDP metadata écrit: {kdp_metadata_path}")

    # 6. Prepare and write etsy_listing.json
    # Etsy title: max 140 chars, keywords-first
    etsy_title_base = f"{brief_title} - Livre de Coloriage {brief_main_theme} pour {brief_target_audience}"
    etsy_title = etsy_title_base
    if len(etsy_title) > 140:
        etsy_title = etsy_title[:137] + "..." # Truncate if too long

    etsy_listing = {
        "title": etsy_title,
        "description": etsy_description,
        "tags": etsy_tags
    }
    etsy_listing_path = os.path.join(publication_output_dir, "etsy_listing.json")
    save_json_file(etsy_listing_path, etsy_listing)
    print(f"Fichier Etsy listing écrit: {etsy_listing_path}")

    # 7. Prepare and write PUBLICATION_READY.md
    publication_ready_content = textwrap.dedent(f"""
    ---
    title: "Paquet de Publication Prêt pour {brief_title}"
    date: {os.popen('date +%Y-%m-%d').read().strip()}
    draft: false
    ---

    # Paquet de Publication pour "{brief_title}" (ID: {brief_id})

    Ce document résume les informations générées pour la publication sur KDP et Etsy.

    ## Résumé Hugo

    Le paquet de publication pour le livre de coloriage **"{brief_title}"** est prêt.
    Il inclut les métadonnées KDP, la fiche produit Etsy, et ce résumé.
    Le thème principal est **"{brief_main_theme}"** et l'audience cible est **"{brief_target_audience}"**.

    ## Checklist KDP

    - [x] Titre: `{brief_title}`
    - [x] Auteur: `{brief_author}`
    - [x] Description (Blurb):