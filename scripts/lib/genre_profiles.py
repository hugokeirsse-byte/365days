"""
Profils éditoriaux par genre — modélisation des codes du marché.

Chaque profil contient les paramètres techniques (word count, structure,
POV, tense) et marketing (mots-clés Amazon, catégories KDP, prix, palette
de couverture, structure de blurb) qui correspondent aux bestsellers du
genre. C'est la matière première du pipeline produce_ebook.py.

Mise à jour régulière en analysant les tops Amazon par catégorie.
"""

GENRE_PROFILES = {
    # ─────────────────────────────────────────────────────────────────
    # ROMANCE
    # ─────────────────────────────────────────────────────────────────
    "romance_contemporary": {
        "display_name": "Contemporary Romance",
        "word_count_target": 70000,
        "word_count_range": (55000, 90000),
        "trim_size": "5x8",
        "chapters": 25,
        "chapter_word_count": 2800,
        "structure_template": "three_act_meet_cute",
        "narrative_beats": [
            "Hook chapter 1 (protagonist's normal life)",
            "Meet Cute or Inciting Incident (ch 2-3)",
            "Forced Proximity / First Spark (ch 4-7)",
            "First Kiss / Emotional Intimacy (ch 8-10)",
            "Rising Tension (ch 11-15)",
            "Black Moment / Breakup (ch 16-18)",
            "Grand Gesture / Reunion (ch 19-23)",
            "HEA + Epilogue (ch 24-25)",
        ],
        "pov": "dual_first_person_alternating",
        "tense": "past",
        "voice": "intimate_internal_monologue",
        "ending_required": "HEA",  # Happy Ever After OBLIGATOIRE
        "required_tropes_anyof": [
            "enemies_to_lovers", "friends_to_lovers", "second_chance",
            "fake_dating", "forced_proximity", "grumpy_sunshine",
            "single_dad", "boss_employee", "small_town",
        ],
        "anti_patterns": [
            "no cheating endings",
            "no love triangle without clear resolution",
            "no death of main protagonist",
            "no abrupt happy endings without earned conflict",
        ],
        "cover_brief": {
            "style": "modern romance",
            "elements": "couple silhouette or single object (mug, flower, ring)",
            "palette": "warm tones, blush pink, terracotta, cream",
            "typography": "flowing serif title large, italic subtitle, author name top",
            "mood": "swoony, intimate, hopeful",
        },
        "blurb_template": (
            "When {protag_A} {situation_A} crosses paths with "
            "{protag_B} {situation_B}, sparks fly — but {obstacle}. "
            "As {tension_event}, both must {choice}. "
            "Will they {question_HEA}?"
        ),
        "amazon_keywords": [
            "{trope1} romance",
            "{setting} romance",
            "contemporary romance {sub_theme}",
            "swoon worthy",
            "binge worthy series",
            "{tropes} romance fans",
        ],
        "amazon_categories": [
            "Books > Romance > Contemporary",
            "Kindle Store > Kindle eBooks > Romance > Contemporary",
        ],
        "price_usd": 3.99,
        "audible_eligible": True,
    },

    "romance_paranormal": {
        "display_name": "Paranormal Romance",
        "word_count_target": 75000,
        "word_count_range": (60000, 100000),
        "trim_size": "5x8",
        "chapters": 26,
        "chapter_word_count": 2900,
        "structure_template": "fated_mates_or_supernatural_conflict",
        "narrative_beats": [
            "Hook (paranormal element revealed)",
            "Meet (often dangerous/forbidden)",
            "Magic system / world rules established",
            "Forbidden attraction grows",
            "Mating bond / commitment moment",
            "External supernatural threat",
            "Dark moment (death threat, separation by magic)",
            "Climactic battle / sacrifice",
            "HEA bonded mates",
        ],
        "pov": "dual_first_person_OR_close_third",
        "tense": "past",
        "voice": "intense_passionate_with_otherworldly_atmosphere",
        "ending_required": "HEA_with_bonded_mates",
        "required_tropes_anyof": [
            "fated_mates", "vampire_human", "werewolf_alpha",
            "fae_warrior", "demon_redemption", "witch_hunter",
            "monster_romance", "supernatural_council",
        ],
        "anti_patterns": [
            "no cheating between fated mates",
            "no harem unless reverse harem genre",
            "no abrupt magic deus ex machina",
        ],
        "cover_brief": {
            "style": "dark fantasy romance",
            "elements": "supernatural creature silhouette, moonlight, magical symbols",
            "palette": "deep blue, midnight black, blood red, silver accents",
            "typography": "gothic serif title, runic accents",
            "mood": "dangerous, passionate, otherworldly",
        },
        "amazon_keywords": [
            "fated mates romance",
            "{creature} romance",
            "paranormal romance series",
            "monster romance",
            "supernatural alpha",
            "dark paranormal romance",
        ],
        "amazon_categories": [
            "Books > Romance > Paranormal",
            "Books > Romance > Vampires" + " OR Werewolves OR Witches & Wizards",
        ],
        "price_usd": 4.99,
        "audible_eligible": True,
    },

    # ─────────────────────────────────────────────────────────────────
    # THRILLER / MYSTERY
    # ─────────────────────────────────────────────────────────────────
    "thriller_psychological": {
        "display_name": "Psychological Thriller",
        "word_count_target": 85000,
        "word_count_range": (70000, 110000),
        "trim_size": "5.5x8.5",
        "chapters": 50,
        "chapter_word_count": 1700,
        "structure_template": "red_herrings_with_twist",
        "narrative_beats": [
            "Hook (uncanny event in chapter 1)",
            "Protagonist's seemingly normal life",
            "Crack in the facade (chapter 4-6)",
            "Investigation begins (ch 7-15)",
            "Red herring 1 (ch 12-15)",
            "Mid-book twist (ch 22-25)",
            "Red herring 2 (ch 30-35)",
            "False resolution (ch 38-42)",
            "True antagonist revealed (ch 45)",
            "Climax + dark ambiguous ending (ch 48-50)",
        ],
        "pov": "first_person_unreliable_OR_close_third",
        "tense": "past_OR_present",
        "voice": "tense_short_sentences_in_action_scenes",
        "ending_required": "twist_OR_dark_resolution",
        "required_tropes_anyof": [
            "unreliable_narrator", "memory_loss", "stalker",
            "dark_family_secret", "missing_person", "domestic_thriller",
            "twin_doppelganger", "online_obsession",
        ],
        "anti_patterns": [
            "no deus ex machina resolutions",
            "no fully explained motivations in first half",
            "no obvious villain telegraphed in act 1",
        ],
        "cover_brief": {
            "style": "ominous psychological",
            "elements": "isolated landscape, fog, silhouette, single object",
            "palette": "muted dark blues, greys, blacks, single accent red",
            "typography": "bold sans-serif title, fragmented or torn effect",
            "mood": "tense, unsettling, claustrophobic",
        },
        "amazon_keywords": [
            "psychological thriller",
            "twist ending thriller",
            "page turner thriller",
            "unreliable narrator",
            "domestic thriller",
            "you won't see it coming",
        ],
        "amazon_categories": [
            "Books > Mystery, Thriller & Suspense > Thrillers > Psychological",
            "Books > Literature & Fiction > Genre Fiction > Domestic Life",
        ],
        "price_usd": 4.99,
        "audible_eligible": True,
    },

    "cozy_mystery": {
        "display_name": "Cozy Mystery",
        "word_count_target": 60000,
        "word_count_range": (50000, 75000),
        "trim_size": "5x8",
        "chapters": 25,
        "chapter_word_count": 2400,
        "structure_template": "small_town_amateur_sleuth",
        "narrative_beats": [
            "Establish cozy setting + protagonist's hobby/job",
            "Body found by chapter 2-3 (off-page or non-graphic)",
            "Suspect introductions",
            "Amateur investigation begins",
            "Red herrings interleaved with daily life",
            "Recipes / crafts / pet moments between clues",
            "Climax confrontation",
            "Killer caught + recipe at end",
        ],
        "pov": "first_person_OR_close_third",
        "tense": "past",
        "voice": "warm_funny_witty_chatty",
        "ending_required": "mystery_solved_killer_caught_protagonist_safe",
        "required_tropes_anyof": [
            "baking_mystery", "knitting_mystery", "cat_owner",
            "bookshop_owner", "florist", "tea_shop",
            "small_town_quirky_characters", "retired_librarian",
        ],
        "anti_patterns": [
            "no graphic violence on page",
            "no graphic sex or romance subplot center stage",
            "no swearing",
            "main character is NOT police or PI (must be amateur)",
            "killer must be from cast already introduced",
        ],
        "cover_brief": {
            "style": "cute illustrated cozy",
            "elements": "small town scene, cute element (cat, cupcake, knitting, bookshop)",
            "palette": "warm pastels, sage green, cream, soft coral",
            "typography": "rounded serif or playful script title",
            "mood": "warm, inviting, charming",
        },
        "amazon_keywords": [
            "cozy mystery",
            "amateur sleuth",
            "{theme} mystery (baking, knitting, cat, bookshop, etc.)",
            "small town mystery",
            "cozy mystery series",
            "feel good mystery",
        ],
        "amazon_categories": [
            "Books > Mystery, Thriller & Suspense > Mystery > Cozy",
            "Books > Mystery, Thriller & Suspense > Mystery > Women Sleuths",
        ],
        "price_usd": 3.99,
        "audible_eligible": True,
    },

    # ─────────────────────────────────────────────────────────────────
    # FANTASY / SCI-FI
    # ─────────────────────────────────────────────────────────────────
    "fantasy_ya": {
        "display_name": "Young Adult Fantasy",
        "word_count_target": 90000,
        "word_count_range": (75000, 110000),
        "trim_size": "5.5x8.5",
        "chapters": 30,
        "chapter_word_count": 3000,
        "structure_template": "hero_journey_with_chosen_one",
        "narrative_beats": [
            "Ordinary world",
            "Call to adventure",
            "Mentor / magical introduction",
            "Crossing threshold",
            "Tests, allies, enemies",
            "Approach to inmost cave",
            "Ordeal / death/rebirth",
            "Reward",
            "Road back",
            "Resurrection / climax",
            "Return with elixir",
        ],
        "pov": "first_person_OR_close_third",
        "tense": "past_OR_present",
        "voice": "teen_voice_authentic_emotional",
        "ending_required": "victory_with_sacrifice_setup_next_book",
        "required_tropes_anyof": [
            "chosen_one", "academy_setting", "found_family",
            "enemies_to_lovers_subplot", "ancient_prophecy",
            "magical_creature_companion", "dark_lord",
        ],
        "anti_patterns": [
            "no explicit sex (YA limit)",
            "no graphic torture",
            "no protagonist over 19",
        ],
        "cover_brief": {
            "style": "epic fantasy YA",
            "elements": "protagonist with weapon/magic, dramatic landscape, magical creature",
            "palette": "vivid jewel tones, gold accents, mystical glow",
            "typography": "epic serif title with magical flourish",
            "mood": "epic, mystical, hopeful with darkness",
        },
        "amazon_keywords": [
            "YA fantasy",
            "young adult fantasy series",
            "chosen one fantasy",
            "magic academy",
            "epic fantasy YA",
            "fantasy adventure teen",
        ],
        "amazon_categories": [
            "Books > Teens > Science Fiction & Fantasy > Fantasy",
            "Kindle Store > Kindle eBooks > Teens > Science Fiction & Fantasy",
        ],
        "price_usd": 4.99,
        "audible_eligible": True,
    },

    "litrpg_progression": {
        "display_name": "LitRPG / Progression Fantasy",
        "word_count_target": 100000,
        "word_count_range": (80000, 130000),
        "trim_size": "6x9",
        "chapters": 35,
        "chapter_word_count": 2900,
        "structure_template": "power_progression_with_dungeons",
        "narrative_beats": [
            "Introduction to system / virtual world",
            "Starting weakness",
            "First level up / first power",
            "Party formation",
            "Dungeon arcs (3-5 per book)",
            "Skill tree expansion",
            "Boss fights with stat blocks",
            "New class unlock or evolution",
            "Cliffhanger or boss defeat",
        ],
        "pov": "first_person_OR_close_third",
        "tense": "present_for_action_past_for_reflection",
        "voice": "gamer_protagonist_with_stat_blocks_inserted",
        "ending_required": "boss_defeated_OR_cliffhanger_for_next_book",
        "required_tropes_anyof": [
            "isekai", "system_apocalypse", "dungeon_core",
            "necromancer_protagonist", "crafting_class",
            "kingdom_building", "harem_party",
        ],
        "anti_patterns": [
            "no protagonist already overpowered at start",
            "no skipping the level grind (readers want it)",
        ],
        "cover_brief": {
            "style": "video game fantasy",
            "elements": "protagonist with stat overlay or weapon glow, dungeon background",
            "palette": "neon blue/green stats overlay on darker fantasy",
            "typography": "gaming-influenced bold sans-serif title",
            "mood": "epic, gamified, leveling",
        },
        "amazon_keywords": [
            "LitRPG",
            "progression fantasy",
            "system apocalypse",
            "{class} progression",
            "isekai LitRPG",
            "dungeon crawler",
        ],
        "amazon_categories": [
            "Books > Science Fiction & Fantasy > Fantasy > Epic",
            "Kindle > Genre Fiction > LitRPG",
        ],
        "price_usd": 4.99,
        "audible_eligible": True,
    },

    # ─────────────────────────────────────────────────────────────────
    # NON-FICTION
    # ─────────────────────────────────────────────────────────────────
    "self_help_niche": {
        "display_name": "Self-Help (niche)",
        "word_count_target": 45000,
        "word_count_range": (30000, 60000),
        "trim_size": "6x9",
        "chapters": 12,
        "chapter_word_count": 3700,
        "structure_template": "problem_framework_steps",
        "narrative_beats": [
            "Hook : reader's pain point",
            "Your story / credentials",
            "Why current solutions fail",
            "The framework (named, memorable)",
            "Each chapter = 1 pillar",
            "Case studies / examples",
            "Action steps end of each chapter",
            "Conclusion : 30-day plan",
        ],
        "pov": "second_person_addressing_reader",
        "tense": "present",
        "voice": "authoritative_friendly_coach",
        "ending_required": "actionable_30_day_plan",
        "required_tropes_anyof": [
            "morning_routine", "anti_procrastination", "habit_stacking",
            "atomic_habits_style", "minimalism", "productivity_for_X",
            "{niche}_burnout_recovery", "boundaries_for_{niche}",
        ],
        "anti_patterns": [
            "no fluff (no padding chapters)",
            "no AI-generic generic advice",
            "no \"you can do anything\" empty motivation",
        ],
        "cover_brief": {
            "style": "modern minimal self-help",
            "elements": "single iconic visual, clean geometric shape",
            "palette": "single bold color + white, optional accent",
            "typography": "bold geometric sans-serif title large, subtitle clean",
            "mood": "clear, confident, expert",
        },
        "amazon_keywords": [
            "{topic} self help",
            "habits {niche}",
            "productivity {niche}",
            "{topic} for {audience}",
            "step by step guide",
            "actionable",
        ],
        "amazon_categories": [
            "Books > Self-Help > Personal Transformation",
            "Books > Self-Help > Time Management",
        ],
        "price_usd": 9.99,
        "audible_eligible": True,
    },

    "cookbook_niche": {
        "display_name": "Niche Cookbook",
        "word_count_target": 25000,
        "word_count_range": (15000, 40000),
        "trim_size": "7x10",  # plus large pour photos recettes
        "chapters": 8,
        "chapter_word_count": 3000,
        "structure_template": "intro_then_recipes_by_category",
        "narrative_beats": [
            "Personal story / why this cookbook",
            "Key ingredients pantry",
            "Tools needed",
            "Recipes section 1 (breakfast)",
            "Recipes section 2 (lunch)",
            "Recipes section 3 (dinner)",
            "Recipes section 4 (dessert/snack)",
            "Meal plans + shopping lists",
        ],
        "pov": "first_person_OR_neutral_chef_voice",
        "tense": "imperative_for_recipes",
        "voice": "warm_enthusiast_chef",
        "ending_required": "meal_plans_or_pantry_essentials",
        "required_tropes_anyof": [
            "30_minute_meals", "5_ingredients_or_less",
            "instant_pot_{niche}", "vegan_{niche}", "keto_{niche}",
            "gluten_free_{niche}", "budget_friendly", "kid_friendly",
        ],
        "anti_patterns": [
            "no AI-generated recipe titles that don't make sense",
            "no recipes without clear ingredient quantities",
            "no overly complex techniques for niche '5-ingredients' books",
        ],
        "cover_brief": {
            "style": "appetizing food photography",
            "elements": "hero dish, ingredients arranged decoratively",
            "palette": "warm food tones, contrasting background",
            "typography": "bold serif or playful script title, subtitle clear",
            "mood": "appetizing, inviting, achievable",
        },
        "amazon_keywords": [
            "{diet} cookbook",
            "{technique} recipes",
            "easy {niche} recipes",
            "{audience} cookbook",
            "beginner cookbook",
            "quick {niche} meals",
        ],
        "amazon_categories": [
            "Books > Cookbooks, Food & Wine > Special Diet",
            "Books > Cookbooks, Food & Wine > Cooking by Ingredient",
        ],
        "price_usd": 9.99,
        "audible_eligible": False,
    },

    # ─────────────────────────────────────────────────────────────────
    # CHILDREN'S
    # ─────────────────────────────────────────────────────────────────
    "children_chapter_book": {
        "display_name": "Children's Chapter Book (ages 6-10)",
        "word_count_target": 12000,
        "word_count_range": (8000, 18000),
        "trim_size": "5x8",
        "chapters": 10,
        "chapter_word_count": 1200,
        "structure_template": "adventure_with_friendship_lesson",
        "narrative_beats": [
            "Introduction protagonist + ordinary world",
            "Problem / quest appears",
            "Friend joins",
            "First obstacle",
            "Setback",
            "Cleverness wins",
            "Climax",
            "Resolution + lesson learned",
            "Setup next book",
        ],
        "pov": "close_third_OR_first",
        "tense": "past",
        "voice": "simple_engaging_age_appropriate",
        "ending_required": "happy_resolution_with_subtle_lesson",
        "required_tropes_anyof": [
            "animal_companion", "secret_treehouse", "magic_school",
            "talking_pet", "best_friend_duo", "found_family",
            "mystery_in_neighborhood",
        ],
        "anti_patterns": [
            "no violence beyond age-appropriate",
            "no dark themes",
            "no romance",
            "no complex vocabulary (Lexile 500-700)",
        ],
        "cover_brief": {
            "style": "bright illustrated children's",
            "elements": "protagonist with friend/pet, fun scene",
            "palette": "bright cheerful colors, primary tones",
            "typography": "fun rounded title large and bright",
            "mood": "exciting, friendly, adventurous",
        },
        "amazon_keywords": [
            "chapter book ages 6 9",
            "kids adventure book",
            "{theme} chapter book",
            "early reader chapter",
            "boys/girls adventure book",
            "series for young readers",
        ],
        "amazon_categories": [
            "Books > Children's Books > Literature & Fiction > Chapter Books",
            "Books > Children's Books > Action & Adventure",
        ],
        "price_usd": 4.99,
        "audible_eligible": True,
    },

    # ─────────────────────────────────────────────────────────────────
    # MEMOIR / NICHE NON-FICTION
    # ─────────────────────────────────────────────────────────────────
    "memoir_transformation": {
        "display_name": "Memoir / Transformation Story",
        "word_count_target": 70000,
        "word_count_range": (55000, 90000),
        "trim_size": "5.5x8.5",
        "chapters": 20,
        "chapter_word_count": 3500,
        "structure_template": "before_descent_transformation_after",
        "narrative_beats": [
            "Opening : moment of crisis or pivotal scene",
            "Backstory : how I got here",
            "The descent : worst moments",
            "Turning point",
            "Slow transformation : missteps and wins",
            "Insights gained along the way",
            "New normal",
            "Lessons for the reader",
        ],
        "pov": "first_person",
        "tense": "past_with_present_reflection",
        "voice": "honest_vulnerable_introspective",
        "ending_required": "transformation_achieved_lessons_distilled",
        "required_tropes_anyof": [
            "addiction_recovery", "career_pivot", "grief_journey",
            "spiritual_awakening", "physical_transformation",
            "from_homeless_to_X", "overcoming_{niche}",
        ],
        "anti_patterns": [
            "no AI-generic life advice",
            "no fully resolved everything at the end (humans don't)",
            "no name-dropping without earning",
        ],
        "cover_brief": {
            "style": "minimalist memoir",
            "elements": "single iconic visual or author photo",
            "palette": "muted earth tones or single bold accent",
            "typography": "elegant serif title, subtitle clear",
            "mood": "introspective, hopeful, raw",
        },
        "amazon_keywords": [
            "memoir {topic}",
            "{transformation} story",
            "true story recovery",
            "personal journey {niche}",
            "transformation memoir",
            "raw honest memoir",
        ],
        "amazon_categories": [
            "Books > Biographies & Memoirs > Memoirs",
            "Books > Self-Help > Personal Transformation",
        ],
        "price_usd": 4.99,
        "audible_eligible": True,
    },
}


def get_profile(genre_key: str) -> dict:
    """Retourne le profil ou lève une ValueError si genre inconnu."""
    if genre_key not in GENRE_PROFILES:
        raise ValueError(
            f"Genre inconnu : '{genre_key}'. Disponibles : "
            f"{list(GENRE_PROFILES.keys())}"
        )
    return GENRE_PROFILES[genre_key]


def list_genres() -> list[str]:
    return list(GENRE_PROFILES.keys())


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) > 1:
        print(json.dumps(get_profile(sys.argv[1]), indent=2))
    else:
        print(f"{len(GENRE_PROFILES)} profils disponibles :")
        for key, profile in GENRE_PROFILES.items():
            print(f"  {key:<30} → {profile['display_name']:<35}  "
                  f"{profile['word_count_target']/1000:.0f}k mots  "
                  f"${profile['price_usd']}")
