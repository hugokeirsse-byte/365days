"""
Test 5 cryptides US — style Coco Wyo cute pour la 4ème marque.

Objectif : valider que Pollinations Flux peut produire des illustrations
dans le style Coco Wyo (lignes noires fines, formes rondes, grands yeux
expressifs, espace blanc généreux, adorable) avec un sujet cryptide
mignon devant un monument architectural emblématique de son état US.

Si la qualité est bonne, on lance les 50 cryptides du Vol I de la 4ᵉ
marque (Snug & Strange / Plush & Peculiar / autre — à valider).
"""

STYLE = (
    "cute kawaii coloring book illustration, minimalist line art style, "
    "thick clean black ink outlines on PURE WHITE background, NO COLOR, "
    "NO SHADING, NO GRADIENT, large round expressive eyes, simple "
    "rounded shapes, friendly chubby proportions, generous white space, "
    "professional adult coloring book quality, square composition, "
    "adorable and whimsical, sharp crisp lines, no text in the image, "
    "no signature, gentle smile, peaceful mood, decorative elements to "
    "color around the main scene"
)

PROMPTS = [
    {
        "id": "1",
        "filename": "test_cryptid_bigfoot_seattle",
        "prompt": (
            "An adorable chubby Bigfoot creature with round friendly face and "
            "fluffy fur, standing in front of the Seattle Space Needle tower, "
            "small Pacific Northwest pine trees around, a small steaming "
            "coffee cup at his feet, "
            + STYLE
        ),
        "seed": 2001,
    },
    {
        "id": "2",
        "filename": "test_cryptid_mothman_west_virginia",
        "prompt": (
            "An adorable little Mothman creature with round body, fluffy wings "
            "and big innocent glowing eyes, hovering in front of the Silver "
            "Bridge of Point Pleasant West Virginia, a tiny lantern in its "
            "hands, small moths flying around, "
            + STYLE
        ),
        "seed": 2002,
    },
    {
        "id": "3",
        "filename": "test_cryptid_jersey_devil_atlantic_city",
        "prompt": (
            "An adorable little Jersey Devil creature with tiny horns, small "
            "wings, and a cute curious expression, standing on the Atlantic "
            "City Boardwalk with the iconic ferris wheel pier in the "
            "background, small seashells and ice cream cone in the decor, "
            + STYLE
        ),
        "seed": 2003,
    },
    {
        "id": "4",
        "filename": "test_cryptid_champ_vermont",
        "prompt": (
            "An adorable chubby plesiosaur-like Champ creature with round "
            "friendly face poking out of Lake Champlain water, the iconic "
            "Champlain Bridge in the background, small water lilies and a "
            "tiny rowboat in the decor, "
            + STYLE
        ),
        "seed": 2004,
    },
    {
        "id": "5",
        "filename": "test_cryptid_skunk_ape_everglades",
        "prompt": (
            "An adorable chubby Skunk Ape creature with shaggy round fur and "
            "happy expression, peeking from behind palmetto plants in the "
            "Florida Everglades, a small airboat and tropical flowers in the "
            "background, "
            + STYLE
        ),
        "seed": 2005,
    },
]
