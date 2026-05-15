"""
Génération de propositions de logos pour Inkwell & Hush et Daystone Press.

Fichier temporaire — sera supprimé après que les logos auront été
copiés dans _shared/<marque>/logo_propositions/.

10 propositions par marque dans des styles variés pour ratisser large
et permettre une sélection visuelle informée.
"""

PROMPTS = [
    # ─────────────────────────────────────────────────────────────────
    # INKWELL & HUSH — marque coloriage, calme, contemplatif
    # Logo destiné à figurer petit en bas des couvertures coloriage.
    # ─────────────────────────────────────────────────────────────────
    {
        "id": "1",
        "filename": "inkwell_hush_v01_classic_monogram",
        "prompt": "Elegant minimalist logo featuring an ornate monogram letter combination of I and H, art nouveau style flourishes, dusty blue grey on cream background, fine line ink illustration, vintage publisher emblem, centered composition, plenty of negative space, refined typography, sophisticated literary mark, subtle elegance, no text outside the monogram, square format, high contrast clean lines.",
        "seed": 101,
    },
    {
        "id": "2",
        "filename": "inkwell_hush_v02_quill_inkwell",
        "prompt": "Minimalist logo of a single feather quill resting in an inkwell, fine line illustration, deep blue ink on cream paper background, vintage stationery aesthetic, no text, centered minimalist composition, contemplative quiet mood, hand-drawn ink style, plenty of breathing space around the icon, square format, art deco simplicity.",
        "seed": 102,
    },
    {
        "id": "3",
        "filename": "inkwell_hush_v03_moon_owl",
        "prompt": "Mystical minimalist logo, owl silhouette in front of a crescent moon, geometric flat design, deep navy and bone white, contemplative wisdom symbol, modern vintage hybrid, fine lines, no text, centered composition with empty space, square format, calming spiritual brand mark.",
        "seed": 103,
    },
    {
        "id": "4",
        "filename": "inkwell_hush_v04_botanical_seal",
        "prompt": "Botanical seal logo, circular emblem with delicate fern leaves surrounding empty central space, sage green and bone, fine engraving style, vintage botanical book aesthetic, refined herbarium feel, no text, intricate but quiet, square format with circular emblem centered.",
        "seed": 104,
    },
    {
        "id": "5",
        "filename": "inkwell_hush_v05_typographic_mark",
        "prompt": "Typographic logo, the words INKWELL and HUSH stacked, elegant serif typeface like Cormorant or Playfair, deep ink blue letters on cream background, with a small ornamental flourish between the two words, vintage publisher house aesthetic, refined and quiet, centered square composition.",
        "seed": 105,
    },
    {
        "id": "6",
        "filename": "inkwell_hush_v06_paper_crane",
        "prompt": "Minimalist origami paper crane logo, single fold lines visible, soft dusty pink and bone white, Japanese-inspired simplicity, peaceful meditative brand mark, hand-folded paper aesthetic, no text, centered composition with vast white space, square format, zen quiet mood.",
        "seed": 106,
    },
    {
        "id": "7",
        "filename": "inkwell_hush_v07_circle_typography",
        "prompt": "Circular logo with the brand name INKWELL & HUSH curved along the top arc of the circle, a single small ink drop in the center, elegant thin serif typography, monochrome dark teal on cream, vintage label aesthetic, refined and sophisticated, square format with circular emblem perfectly centered.",
        "seed": 107,
    },
    {
        "id": "8",
        "filename": "inkwell_hush_v08_lotus_meditation",
        "prompt": "Minimalist lotus flower logo from above, perfectly symmetric, deep indigo line art on cream, meditation and contemplation symbol, fine clean geometry, no text, plenty of negative space, centered composition, sacred geometry simplicity, square format, peaceful and contemplative brand mark.",
        "seed": 108,
    },
    {
        "id": "9",
        "filename": "inkwell_hush_v09_book_steam",
        "prompt": "Minimalist logo of an open book with delicate steam or smoke rising from its pages forming abstract curls, fine ink line illustration, charcoal grey on warm cream, evoking quiet reading and contemplation, no text, centered composition with breathing space, square format, vintage literary brand mark.",
        "seed": 109,
    },
    {
        "id": "10",
        "filename": "inkwell_hush_v10_geometric_mandala",
        "prompt": "Geometric mandala logo, perfectly symmetric 8-fold pattern based on intersecting circles and triangles, fine line ink on cream paper, sacred geometry, deep eggplant purple on bone white, brand mark for a coloring book publisher, no text, square format, contemplative spiritual emblem, very fine clean lines.",
        "seed": 110,
    },

    # ─────────────────────────────────────────────────────────────────
    # DAYSTONE PRESS — low-content, journaux/planners, solide, méthodique
    # Logo destiné aux couvertures de journaux et trackers.
    # ─────────────────────────────────────────────────────────────────
    {
        "id": "11",
        "filename": "daystone_v01_geometric_stone",
        "prompt": "Bold geometric logo, abstract stone or pebble shape with horizontal sun rising behind it, flat modern design, terracotta orange and charcoal black on off-white background, strong and grounded brand mark, no text, centered composition, contemporary publisher emblem, clean vector style, square format.",
        "seed": 201,
    },
    {
        "id": "12",
        "filename": "daystone_v02_typographic_block",
        "prompt": "Typographic logo, the words DAYSTONE PRESS in two stacked lines, strong bold sans-serif geometric typeface, deep ink black on cream paper, with a small geometric ornament between the two words like a single triangle or square, modern editorial design, centered square composition, confident and grounded.",
        "seed": 202,
    },
    {
        "id": "13",
        "filename": "daystone_v03_sun_horizon",
        "prompt": "Minimalist logo of a half sun rising over a horizon line, three short rays visible, ochre yellow and charcoal grey, evoking a new day every morning, modern flat design, no text, centered with empty space, square format, contemporary mindful brand mark.",
        "seed": 203,
    },
    {
        "id": "14",
        "filename": "daystone_v04_compass_mark",
        "prompt": "Minimalist compass rose logo, four cardinal points marked, fine line drawing in deep forest green on bone white background, vintage cartographer aesthetic but modernized, evoking direction and intention, no text, centered composition, square format, refined and timeless.",
        "seed": 204,
    },
    {
        "id": "15",
        "filename": "daystone_v05_seal_emblem",
        "prompt": "Circular seal emblem, the letter D and P intertwined in the center, surrounded by the curved text DAYSTONE PRESS along the top arc and EST 2026 along the bottom arc, vintage wax seal style modernized, dark navy and burnt sienna, no other text, centered square composition, refined publisher mark.",
        "seed": 205,
    },
    {
        "id": "16",
        "filename": "daystone_v06_stacked_stones",
        "prompt": "Minimalist illustration of three stacked round stones in a cairn formation, fine ink line drawing, charcoal black on warm beige, zen meditation aesthetic, evoking patience and accumulation over time, no text, centered composition with breathing room, square format, mindful productivity brand.",
        "seed": 206,
    },
    {
        "id": "17",
        "filename": "daystone_v07_calendar_grid",
        "prompt": "Geometric logo combining a small calendar grid and a stone or solid square shape, abstract integration, deep teal and warm amber on off-white, contemporary editorial design, evoking daily structure and durability, no text, centered square composition, modern minimalist brand mark.",
        "seed": 207,
    },
    {
        "id": "18",
        "filename": "daystone_v08_hourglass",
        "prompt": "Minimalist hourglass logo with sand grains visible flowing through, fine line illustration, dark slate grey on cream, vintage scientific aesthetic, evoking the passage of time and daily reflection, no text, centered composition with negative space, square format, refined timepiece brand mark.",
        "seed": 208,
    },
    {
        "id": "19",
        "filename": "daystone_v09_obelisk_modern",
        "prompt": "Geometric logo of a tall narrow obelisk or standing stone, modernist flat design, three horizontal lines crossing it suggesting daily entries, ochre and charcoal on bone white, strong vertical composition centered in square frame, contemporary monolithic brand mark, no text, sophisticated and durable.",
        "seed": 209,
    },
    {
        "id": "20",
        "filename": "daystone_v10_signet_d",
        "prompt": "Single letter D as a signet ring stamp, embossed circular emblem, serif geometric letter with subtle texture, deep oxblood red and gold on bone parchment, vintage wax signet aesthetic modernized for contemporary publisher, no other text or letters, centered square composition, sophisticated personal mark.",
        "seed": 210,
    },
]
