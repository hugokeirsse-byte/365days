import argparse
import sys
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps, ImageDraw

def convert(
    src: str | Path,
    dst: str | Path | None = None,
    *,
    line_thickness: int = 2,
    threshold: int = 128,
    invert_input: bool = False,
) -> Path:
    """
    Convertit une image couleur ou niveaux de gris en line-art de coloriage.

    Le résultat aura un fond blanc pur et des contours noirs épais, fermés,
    prêts à être coloriés. Aucune couleur, aucun gris résiduel.

    Args:
        src: Chemin vers le fichier image source (PNG ou JPEG).
        dst: Chemin optionnel pour sauvegarder l'image de sortie. Si None, un nom par défaut
             (<nom_source>_coloring.png) sera généré dans le même répertoire que src.
        line_thickness: Épaisseur désirée des lignes noires.
        threshold: Seuil de binarisation (0-255). Les pixels plus sombres que ce seuil
                   deviendront noirs, les autres blancs.
        invert_input: Si True, les couleurs de l'image d'entrée seront inversées
                      avant le traitement.

    Returns:
        L'objet Path de l'image de sortie sauvegardée.

    Raises:
        FileNotFoundError: Si l'image source n'existe pas.
        ValueError: Si line_thickness ou threshold sont hors de la plage valide.
        IOError: En cas de problème lors de l'ouverture ou de la sauvegarde de l'image.
    """
    if not isinstance(src, Path):
        src = Path(src)

    if not src.is_file():
        raise FileNotFoundError(f"Fichier source non trouvé : {src}")

    if not (1 <= line_thickness <= 10):
        raise ValueError("line_thickness doit être entre 1 et 10.")
    if not (0 <= threshold <= 255):
        raise ValueError("threshold doit être entre 0 et 255.")

    # Déterminer le chemin de destination
    if dst is None:
        dst = src.parent / f"{src.stem}_coloring.png"
    elif not isinstance(dst, Path):
        dst = Path(dst)

    # 1. Ouvrir l'image, convertir en L (niveaux de gris)
    img = Image.open(src).convert("L")

    # Appliquer l'inversion d'entrée si demandée
    if invert_input:
        img = ImageOps.invert(img)

    # 2. Appliquer ImageFilter.SMOOTH (réduire le bruit)
    img = img.filter(ImageFilter.SMOOTH)

    # 3. Appliquer ImageFilter.FIND_EDGES (détection de contours)
    img = img.filter(ImageFilter.FIND_EDGES)

    # 4. Inverser les contours pour les rendre sombres sur un fond clair, puis épaissir avec MinFilter.
    #    FIND_EDGES produit souvent des lignes claires sur un fond sombre. L'inversion les rend sombres.
    #    MinFilter épaissit ensuite ces lignes sombres.
    img = ImageOps.invert(img)
    # La taille du MinFilter (line_thickness * 2 + 1) assure un épaississement d'environ
    # `line_thickness` pixels de chaque côté d'une ligne d'un pixel.
    img = img.filter(ImageFilter.MinFilter(size=line_thickness * 2 + 1))

    # 5. Binariser : point(lambda p: 0 if p < threshold else 255)
    #    Cela rend les pixels plus sombres que le seuil purement noirs (0), les autres purement blancs (255).
    img = img.point(lambda p: 0 if p < threshold else 255)

    # 6. Forcer fond=255 (blanc), traits=0 (noir)
    #    Ceci est déjà réalisé par l'étape de binarisation (étape 5).
    #    Aucune action explicite n'est nécessaire ici, car l'opération 'point' assure du noir/blanc pur.

    # 7. Convertir en RGB, sauvegarder en PNG
    img = img.convert("RGB")
    img.save(dst, "PNG")

    return dst

def _run_integrated_test():
    """
    Exécute un test intégré en créant une image synthétique, en la convertissant,
    et en vérifiant le résultat.
    """
    print("Exécution du test intégré...")
    test_input_path = Path("test_input_coloring.png")
    test_output_path = Path("test_output_coloring.png")

    try:
        # Créer une image de test synthétique : rectangle rouge sur fond vert
        img_size = (200, 150)
        test_img = Image.new("RGB", img_size, color="green")
        draw = ImageDraw.Draw(test_img)
        # Dessiner un rectangle rouge (x0, y0, x1, y1)
        draw.rectangle((50, 30, 150, 120), fill="red")
        test_img.save(test_input_path)
        print(f"Image de test synthétique créée : {test_input_path}")

        # Convertir l'image de test
        converted_path = convert(
            test_input_path,
            test_output_path,
            line_thickness=2,
            threshold=128,
            invert_input=False,
        )
        print(f"Image de test convertie en : {converted_path}")

        # Vérifier la sortie
        output_img = Image.open(converted_path)

        # Vérifier le mode
        if output_img.mode != "RGB":
            raise ValueError(f"Le mode de l'image de sortie est {output_img.mode}, attendu RGB.")

        # Vérifier qu'il n'y a que des couleurs noir/blanc pur
        # getcolors() retourne None s'il y a plus de `maxcolors` couleurs.
        # Nous nous attendons à seulement 2 couleurs : (0,0,0) et (255,255,255).
        colors = output_img.getcolors(maxcolors=3) # Max 3 pour détecter une éventuelle troisième couleur inattendue
        if colors is None or len(colors) > 2 or not all(c[1] in [(0, 0, 0), (255, 255, 255)] for c in colors):
            raise ValueError(f"L'image de sortie contient des couleurs inattendues ou n'est pas purement N&B : {colors}")

        # Vérifier des valeurs de pixels spécifiques
        # Attendu : fond blanc, contour de rectangle noir
        # Le centre du rectangle (100, 75) doit être blanc
        if output_img.getpixel((100, 75)) != (255, 255, 255):
            raise ValueError(f"Le pixel central du rectangle (100, 75) n'est pas blanc : {output_img.getpixel((100, 75))}")
        # L'extérieur du rectangle (10, 10) doit être blanc
        if output_img.getpixel((10, 10)) != (255, 255, 255):
            raise ValueError(f"Le pixel extérieur du rectangle (10, 10) n'est pas blanc : {output_img.getpixel((10, 10))}")

        # Les bords du rectangle doivent être noirs.
        # Avec line_thickness=2, la ligne sera d'environ 5 pixels de large, centrée sur le bord original.
        # Donc, vérifier la coordonnée exacte du bord devrait donner du noir.
        if output_img.getpixel((50, 75)) != (0, 0, 0): # Bord gauche
            raise ValueError(f"Le pixel du bord gauche (50, 75) n'est pas noir : {output_img.getpixel((50, 75))}")
        if output_img.getpixel((150, 75)) != (0, 0, 0): # Bord droit
            raise ValueError(f"Le pixel du bord droit (150, 75) n'est pas noir : {output_img.getpixel((150, 75))}")
        if output_img.getpixel((100, 30)) != (0, 0, 0): # Bord supérieur
            raise ValueError(f"Le pixel du bord supérieur (100, 30) n'est pas noir : {output_img.getpixel((100, 30))}")
        if output_img.getpixel((100, 120)) != (0, 0, 0): # Bord inférieur
            raise ValueError(f"Le pixel du bord inférieur (100, 120) n'est pas noir : {output_img.getpixel((100, 120))}")

        print("OK")

    except Exception as e:
        print(f"Test ÉCHOUÉ : {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Nettoyer les fichiers temporaires
        if test_input_path.exists():
            test_input_path.unlink()
        if test_output_path.exists():
            test_output_path.unlink()

def main():
    """
    Fonction principale pour analyser les arguments de la ligne de commande et
    exécuter la conversion ou le test.
    """
    parser = argparse.ArgumentParser(
        description="Convertit une image en line-art de coloriage. Si aucun argument n'est fourni, exécute un test intégré."
    )
    parser.add_argument(
        "src",
        nargs="?",  # Rend src optionnel pour le mode test
        type=Path,
        help="Fichier image source (ex: input.png)",
    )
    parser.add_argument(
        "dst",
        nargs="?",  # Rend dst optionnel
        type=Path,
        help="Fichier image de destination (ex: output.png). Si non fourni, par défaut <nom_source>_coloring.png",
    )
    parser.add_argument(
        "--thickness",
        type=int,
        default=2,
        help="Épaisseur des lignes (par défaut: 2)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=128,
        help="Seuil de binarisation (0-255, par défaut: 128)",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Inverser l'image d'entrée avant le traitement",
    )

    args = parser.parse_args()

    if args.src is None:
        # Aucun argument fourni, exécuter le test intégré
        _run_integrated_test()
    else:
        # Mode CLI
        src_path = args.src
        dst_path = args.dst

        if not src_path.is_file():
            print(f"Erreur : Fichier source non trouvé : {src_path}", file=sys.stderr)
            sys.exit(1)

        if dst_path is None:
            dst_path = src_path.parent / f"{src_path.stem}_coloring.png"

        try:
            converted_path = convert(
                src_path,
                dst_path,
                line_thickness=args.thickness,
                threshold=args.threshold,
                invert_input=args.invert,
            )
            print(f"Image convertie avec succès : {converted_path}")
        except Exception as e:
            print(f"Erreur lors de la conversion : {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()