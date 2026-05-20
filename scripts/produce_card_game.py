"""
Pipeline CARD GAME — jeux de cartes ultra-nichés pour The Game Crafter.

Format : Poker card 2.5×3.5 inches @ 300 DPI = 750×1050 px avec bleed
(2.75×3.75 inches = 825×1125 px). The Game Crafter accepte PNG.

Mécanique « Cliché Maximum » (style Blanc Manger Coco) : phrases à
trous + cartes-réponses. Joué en groupe. 200 cartes par deck (100
questions + 100 réponses).

Décliné sur niches ultra-spécifiques pour public captif :
- DevOps / Admin sys
- Sapeurs-Pompiers
- Profs de lycée
- Pêche professionnelle
- Nurses / infirmières
- Tu peux étendre via NICHE_DECKS dict

Production : Pollinations génère un fond/motif niche-spécifique SANS
texte, design_composer overlay 100% propre du texte de chaque carte.

Sortie :
- products/card_game/{niche}/{card_type}/card_{NN}.png (carte unique)
- products/card_game/{niche}/print_sheet_9x.png (9 cartes par feuille)
- products/card_game/{niche}/tgc_upload.csv (manifest)

Variables d'env :
  NICHE=devops         (devops, pompiers, profs, peche, nurses)
  MAX_CARDS=20         limite test
"""

import csv
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERREUR : Pillow non installé")
    sys.exit(2)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.design_composer import compose_design, DesignLayout, \
    TextZone, DecorativeElement  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "card_game"
USER_AGENT = "CardGameProducer/1.0"
TIMEOUT = 180

# TGC Poker card dimensions
CARD_W = 825   # 2.75" bleed × 300 DPI
CARD_H = 1125  # 3.75" bleed × 300 DPI

# Layout carte QUESTION (phrase à trou) — fond niché coloré + texte
LAYOUT_QUESTION_CARD = DesignLayout(
    name="question_card",
    canvas_size=(CARD_W, CARD_H),
    background_color=(245, 235, 220),
    background_overlay=(245, 235, 220, 200),
    blur_bg=8.0,
    text_zones=[
        TextZone(text_key="text", center_xy_pct=(0.5, 0.5),
                 max_box_pct=(0.82, 0.75), font_role="title_bold",
                 color=(30, 25, 20), max_lines=8, auto_size=True,
                 min_size=30),
        TextZone(text_key="deck_label", center_xy_pct=(0.5, 0.94),
                 max_box_pct=(0.7, 0.04), font_role="body_serif_italic",
                 color=(120, 100, 80), max_lines=1, auto_size=False,
                 fallback_size=28),
    ],
    decorative_elements=[
        DecorativeElement(type="horizontal_line",
                          center_xy_pct=(0.5, 0.08),
                          size_pct=0.20, color=(140, 100, 60),
                          extra={"thickness": 3}),
        DecorativeElement(type="horizontal_line",
                          center_xy_pct=(0.5, 0.91),
                          size_pct=0.20, color=(140, 100, 60),
                          extra={"thickness": 3}),
    ],
)

# Layout carte RÉPONSE — fond blanc cassé + texte bold
LAYOUT_ANSWER_CARD = DesignLayout(
    name="answer_card",
    canvas_size=(CARD_W, CARD_H),
    background_color=(252, 248, 240),
    text_zones=[
        TextZone(text_key="text", center_xy_pct=(0.5, 0.5),
                 max_box_pct=(0.82, 0.65), font_role="title_bold",
                 color=(40, 30, 25), max_lines=6, auto_size=True,
                 min_size=35),
        TextZone(text_key="deck_label", center_xy_pct=(0.5, 0.94),
                 max_box_pct=(0.7, 0.04), font_role="body_serif_italic",
                 color=(120, 100, 80), max_lines=1, auto_size=False,
                 fallback_size=28),
    ],
)

# ============================================================
# CONTENU DES DECKS (niches)
# Format : {niche_key: {"name", "bg_prompt", "questions" [list], "answers" [list]}}
# 10-25 questions et 20-50 réponses par deck minimum pour jouabilité
# ============================================================

NICHE_DECKS = {
    "pitch_black_en": {
        "name": "Pitch Black: The Adult Party Game",
        "tagline": "Adult 18+. Dark comedy, no filter. For people who laughed at things they shouldn't.",
        "language": "en",
        "bg_prompt": "subtle dark moody black gothic decorative pattern texture background, ABSOLUTELY NO TEXT NO LETTERS",
        "mature": True,
        "questions": [
            "My therapist banned me from talking about ____.",
            "The autopsy revealed ____ in the body.",
            "My ex sent me ____ three years after we broke up.",
            "At my parents' anniversary dinner, I announced ____.",
            "The DNA test results revealed that ____.",
            "What ruined my wedding day : ____.",
            "I quit my job by emailing ____ to the entire company.",
            "When I finally cracked at work, I was found doing ____ in the bathroom.",
            "To celebrate my divorce, I immediately ____.",
            "The Christmas reunion ended when grandma showed everyone ____.",
            "My last Tinder date ended with ____.",
            "Mom found ____ in my browser history.",
            "My next door neighbor calls the police about ____ every week.",
            "The funeral director gently told us ____ couldn't be in the open casket.",
            "What's hidden in my parents' garage : ____.",
            "My HR file contains a note saying I ____.",
            "I have unresolved trauma about ____.",
            "The midwife handed me my newborn and whispered ____.",
            "At the family reunion, the worst secret revealed was ____.",
            "My psychiatrist refused to see me again after I confessed ____.",
            "The pet's vet bill came to $4,200 because ____.",
            "What I do at 3 AM when nobody is watching : ____.",
            "The judge sentenced me to ____.",
            "My wedding vows included the line « I promise to never ____ ».",
            "What I'll regret on my deathbed : ____.",
        ],
        "answers": [
            "An existential crisis at Walmart",
            "A spectacular emotional breakdown",
            "Three Costco tubs of ice cream and Pinot Grigio",
            "A Tinder date with a sleep paralysis demon",
            "A messy public divorce on Instagram",
            "A cardiac event narrowly avoided",
            "An expensive midlife crisis red convertible",
            "Becoming a goat farmer in rural Vermont",
            "An OnlyFans account paying my mortgage",
            "An impulsive vasectomy on a Tuesday",
            "A LinkedIn rage-quit post that went viral",
            "Three decades of repressed trauma",
            "A mortgage I'll never afford",
            "The slow death of my will to live",
            "Filing for bankruptcy with style",
            "An emotional support iguana",
            "A pyramid scheme dressed as wellness",
            "Therapy nobody can afford",
            "Disappointing my immigrant parents",
            "Sliding into the boss's DMs",
            "A diet of dry pasta and despair",
            "A divorce attorney on retainer",
            "Crying alone in my Tesla",
            "Sending a text I can't take back",
            "A pet I can't afford to keep",
            "Three children I never wanted",
            "A second marriage that's clearly a mistake",
            "Crying in the work bathroom",
            "An expensive astrology phone app",
            "An emotionally unavailable parent",
            "A 'wellness retreat' that's secretly a cult",
            "Microwaved leftover trauma",
            "A Reddit hyperfixation",
            "A funeral I have to attend sober",
            "Generational debt and disappointment",
            "Existential dread in aisle 7",
        ],
    },
    "corporate_burnout_en": {
        "name": "Corporate Burnout: The Card Game",
        "tagline": "Mature 16+. The game for people who actually hit rock bottom in corporate life.",
        "language": "en",
        "bg_prompt": "subtle corporate dystopia office cubicle fluorescent lighting dark background ABSOLUTELY NO TEXT",
        "mature": True,
        "questions": [
            "My 2 PM meeting ended when I pulled out ____.",
            "The open-plan office got evacuated after Mark from accounting ____.",
            "The CEO announced at the all-hands that ____.",
            "On my first WFH day, I celebrated by ____.",
            "My annual review took a turn when HR brought up ____.",
            "The team building retreat ended in ____.",
            "By the water cooler, the only topic is ____.",
            "My final email to the CEO contained ____.",
            "To reduce burn rate, the CFO suggested ____.",
            "The Friday 5 PM standup lasted 4 hours because of ____.",
            "My doctor's note for medical leave cited ____.",
            "During the layoff round, we found out that ____.",
            "My manager asked me to ____ before he left on vacation.",
            "Management replaced our free espresso with ____.",
            "At my farewell party, they gave me ____.",
            "The Slack channel #random became a crime scene when ____.",
            "My LinkedIn now lists my title as ____.",
            "The board meeting got cancelled when ____.",
            "We pivoted from a SaaS startup to ____.",
            "The intern outperformed everyone by ____.",
        ],
        "answers": [
            "A diagnosed brown-out",
            "An open resignation letter to the entire firm",
            "A LinkedIn rage-quit post (3M views)",
            "A crying breakdown in a Zoom call",
            "An 18-month masked depression",
            "Gross misconduct termination",
            "The tight talent market",
            "A hostile merger and acquisition",
            "A 87-slide PowerPoint",
            "A team outsourced to Madagascar",
            "A vulture fund buyout",
            "An open space without desks",
            "A rotten union agreement",
            "A guru CEO",
            "A $90,000 MBA",
            "Therapy through work",
            "A precautionary suspension",
            "80-hour work-from-home weeks",
            "Expired Nespresso coffee",
            "An honorary Mickey watch",
            "A constructive dismissal",
            "A rotten mutual separation",
            "An open space at 65°F",
            "A manager on burnout leave 6 months",
            "Three years in employment tribunal",
            "A neglectful occupational physician",
            "A spreadsheet of regrets",
            "Crying in the parking lot before standup",
            "A pivot to AI grift",
            "A wellness program nobody used",
        ],
    },
    "teachers_en": {
        "name": "Teacher Survival: The Card Game",
        "tagline": "Adult 16+. The game for teachers who've seen too much.",
        "language": "en",
        "bg_prompt": "subtle classroom blackboard chalk marks decorative background ABSOLUTELY NO TEXT NO LETTERS",
        "mature": True,
        "questions": [
            "The worst parent excuse note I received: ____.",
            "What I found in a student's locker on the last day : ____.",
            "The most surprising thing a student turned in for their essay : ____.",
            "My secret survival technique with difficult classes is ____.",
            "The principal calls me in every term to discuss ____.",
            "What we actually talk about in the teachers' lounge : ____.",
            "What I find in my Sunday-night grading pile : ____.",
            "What ChatGPT got wrong on the AI-generated homework : ____.",
            "The board of education has officially banned ____.",
            "Parents' association demands we add ____ to the curriculum.",
            "The hottest gossip in the staff room is ____.",
            "What I confiscated from a student this week : ____.",
            "What a student told me to justify being late : ____.",
            "What the head of department said during my evaluation : ____.",
            "The faculty meeting got out of hand when ____.",
            "The exam I dread most is ____.",
            "What I bought with my own money for the classroom : ____.",
            "The new educational reform requires us to ____.",
            "What appeared on the school's anonymous feedback form : ____.",
            "After parent-teacher night, I went home and ____.",
        ],
        "answers": [
            "« My child broke a nail »",
            "A TikTok dance as a research project",
            "Confiscate the phone permanently",
            "Run out of students",
            "The coffee machine is broken (again)",
            "The retired colleague absent for 3 years",
            "A typo in the principal's email",
            "Hand out too many candy bribes",
            "The uncertain future of cursive writing",
            "A meeting with no break",
            "A yogurt forgotten in the staff fridge",
            "Reforming spelling",
            "A pigeon ate the homework",
            "The school's only working photocopier",
            "An essay topic on Marcel Proust",
            "Post-it notes",
            "The class president",
            "Lost their glasses again",
            "The foosball table bought at the fair",
            "Nobody knew the answer",
            "A brilliant but unmotivated student",
            "ChatGPT plagiarized everything",
            "The principal in shorts",
            "An excused absence note",
            "An unworking smartboard",
            "A note written by the student themselves",
            "Three minutes of universal lateness",
            "A two-hour lecture that should've been an email",
            "Existential dread in the supply closet",
            "Three espressos before noon",
        ],
    },
    "parents_en": {
        "name": "Parenthood Unfiltered: The Card Game",
        "tagline": "Adult 18+. The card game for parents who can't say it out loud.",
        "language": "en",
        "bg_prompt": "subtle nursery toys playroom messy decorative pattern background ABSOLUTELY NO TEXT NO LETTERS",
        "mature": True,
        "questions": [
            "What I do in the bathroom for 45 minutes is ____.",
            "The most expensive thing my toddler destroyed was ____.",
            "What I told my child the dog actually did was ____.",
            "I lied to my pediatrician about ____.",
            "What I actually feed the kids when no one's looking : ____.",
            "The reason I'm three glasses of wine in by Tuesday : ____.",
            "What I scream into the pillow at 3 AM : ____.",
            "The thing I told my mother-in-law to back off about : ____.",
            "What's hidden in my purse for emergency calm : ____.",
            "The reason I'm late to PTA meetings : ____.",
            "What I Google at 2 AM about my children : ____.",
            "The reason I locked myself in the car : ____.",
            "My partner and I argue most about ____.",
            "What I bribe my kids with when guests come : ____.",
            "The truth about the « organic homemade » food in the lunchbox : ____.",
            "What ruined the family vacation : ____.",
            "What I hide from my children at the back of the cupboard : ____.",
            "Why I'm in therapy : ____.",
            "What I scream-cried about while folding laundry : ____.",
            "The reason I avoid the school parent group chat : ____.",
        ],
        "answers": [
            "An emergency screen time pass",
            "Hiding chocolate in the bathroom",
            "Pretending to be on a work call",
            "A car ride to nowhere",
            "Fish sticks for the third night this week",
            "Lying about bedtime to get one hour back",
            "Wine in a coffee mug",
            "A meltdown in the parking lot of Target",
            "An expensive playroom Pinterest board",
            "A toddler tantrum during a Zoom call",
            "The PTA Karen",
            "A 401k drained by daycare costs",
            "An impossible breastfeeding consultation",
            "The « organic » lunch from Trader Joe's",
            "A toy that screams nursery rhymes at 6 AM",
            "Sliding tablets under the door",
            "The screen time alarm I ignore",
            "A divorce attorney's business card",
            "The pediatrician's judgmental face",
            "Crying in the school pickup line",
            "Existential dread at the playground",
            "A Mommy and Me class I dropped out of",
            "A mom blog I secretly hate-read",
            "An expired daycare deposit",
            "The neighbor's emotional support llama",
            "A 200-hour gentle parenting course",
            "Pinterest mom guilt at 2 AM",
            "A spreadsheet of childcare options",
            "A wine subscription nobody knows about",
            "A toddler with bigger anger issues than me",
        ],
    },
    "dark_humor": {
        "name": "Cliché Maximum: Pitch Black Edition",
        "tagline": "Mature 18+. Humour noir, transgressif, sans filtre. NSFW jeu de soirée pour gros adultes.",
        "language": "fr",
        "bg_prompt": "subtle dark moody black gothic decorative pattern texture background, ABSOLUTELY NO TEXT NO LETTERS",
        "mature": True,
        "questions": [
            "Mon plan pour faire face à la crise de la quarantaine : ____.",
            "Aux funérailles, j'ai décidé que la meilleure façon de rendre hommage c'était ____.",
            "Mon thérapeute m'a interdit de parler de ____.",
            "Ma dernière relation s'est terminée le jour où elle a découvert ____.",
            "Au scanner, le radiologue a trouvé ____ dans mon corps.",
            "Le pire moment de mon mariage : on a échangé nos vœux pendant ____.",
            "J'ai démissionné en envoyant à toute l'entreprise ____.",
            "Le jour où j'ai compris que j'étais en burn-out, je faisais ____ dans les toilettes du bureau.",
            "Pour fêter mon divorce, j'ai immédiatement ____.",
            "L'huissier est venu saisir ____ pour rembourser ma dette de ____.",
            "À la fin de la fête, mes amis ont retrouvé ____ dans le frigo.",
            "Mon dernier rencard Tinder s'est terminé par ____.",
            "Ma mère a vu ____ sur mon historique de navigation.",
            "Au réveillon de famille, je leur ai annoncé ____.",
            "Mon psy a noté dans mon dossier : « patient présente ____ ».",
            "Mon ex m'a envoyé ____ trois ans après notre rupture.",
            "Le test ADN familial a révélé que ____.",
            "Lors de l'autopsie, le légiste a trouvé ____.",
            "À l'EHPAD, mes grands-parents jouent secrètement à ____.",
            "Ce matin j'ai compris que ma vie c'était ____.",
            "Mon ex m'a quitté en me disant que ____.",
            "La psychologue scolaire a appelé mes parents parce que ____.",
            "Quand on m'a viré, le RH a précisé que ____.",
            "L'apocalypse aurait pu être évitée si quelqu'un avait pensé à ____.",
            "Lors de la rentrée des classes, le proviseur a annoncé ____.",
        ],
        "answers": [
            "Une dépression majeure", "L'envie de tout brûler",
            "Un divorce mal géré", "Trois bouteilles de vodka avant midi",
            "Une tentative de suicide ratée", "L'alcoolisme",
            "Un crédit conso de 12000€ pour des Pokemon", "Mon ex et son nouveau partenaire",
            "Un cancer du pancréas stade 4", "Une crise d'angoisse en public",
            "L'achat impulsif d'une voiture rouge décapotable",
            "Un mariage avec une plante d'intérieur",
            "Une thérapie de groupe pour ex-mari",
            "Un dernier mail à 2h du mat", "Un boomer sur Facebook",
            "Une crise existentielle au supermarché",
            "Une révélation traumatisante au repas de Noël",
            "L'envie de devenir berger en Mongolie",
            "L'addiction aux jeux de grattage", "Une lettre de licenciement",
            "Une hospitalisation préventive", "Une découverte ADN gênante",
            "Un voisin qui appelle la police", "Le chien du voisin",
            "Un cadavre dans le congélateur",
            "Un fœtus en formaldéhyde", "Un compte OnlyFans pour payer le loyer",
            "Un dossier MDPH en cours", "Une caution pour un crime non commis",
            "Une vie médiocre et confortable", "Le décès du chat",
            "Une avocate spécialisée en garde alternée",
            "Un rendez-vous chez l'oncologue", "Une crise de tétanie",
            "Une thérapie par électrochocs", "Un compte épargne vidé",
            "Une procédure de divorce", "L'addiction au porno",
            "Une dette URSSAF de 47 000€", "Des antidépresseurs périmés",
            "Une lettre de démission par SMS",
            "Trois ans de procédure aux Prudhommes",
        ],
    },
    "burnout_corporate": {
        "name": "Cliché Maximum: Burnout Edition",
        "tagline": "Mature 16+. Le jeu pour ceux qui ont vraiment touché le fond corporate.",
        "language": "fr",
        "bg_prompt": "subtle corporate dystopia office cubicle fluorescent lighting dark background ABSOLUTELY NO TEXT",
        "mature": True,
        "questions": [
            "Ma réunion 14h s'est terminée quand j'ai sorti ____.",
            "L'open space a été évacué après que Jean-Marc ait ____.",
            "Le CEO a annoncé en all-hands que ____.",
            "Pour mon premier jour de télétravail, j'ai célébré en ____.",
            "Mon entretien annuel a viré au cauchemar quand RH a sorti ____.",
            "Le séminaire team-building s'est terminé par ____.",
            "À la machine à café, on parle uniquement de ____.",
            "Mon dernier email au CEO contenait ____.",
            "Pour faire baisser le burn rate, le CFO a proposé ____.",
            "Le team meeting du vendredi 17h a duré 4h parce que ____.",
            "Mon arrêt maladie était justifié par ____.",
            "Lors du plan social, on a appris que ____.",
            "Mon manager m'a demandé de ____ avant de partir en vacances.",
            "La direction a remplacé l'expresso gratuit par ____.",
            "À mon pot de départ, on m'a offert ____.",
        ],
        "answers": [
            "Une démission par cris", "Un brown-out diagnostiqué",
            "Une lettre ouverte à toute la boîte", "Un plan social cantonné aux seniors",
            "Une bouteille de gin sous le bureau", "Une LinkedIn rage-quit poste",
            "Une crise de larmes en visio", "Une dépression masquée 18 mois",
            "Un licenciement pour faute grave", "L'absence d'avenir collectif",
            "Le marché tendu sur le marché", "Une fusion-absorption hostile",
            "Un PowerPoint de 87 slides", "Une équipe internalisée à Madagascar",
            "Un rachat par fonds vautour", "Un open space sans bureau",
            "Une convention collective pourrie", "Un dirigeant gourou",
            "Un MBA à 90 000 €", "Une thérapie par le travail",
            "Une mise à pied conservatoire", "Un télétravail de 80 heures",
            "Un café Nespresso périmé", "Une montre Mickey honoraire",
            "Un licenciement déguisé", "Une rupture conventionnelle moisie",
            "Un open space climatisé à 17 °C", "Un manager en burn-out depuis 6 mois",
            "Trois ans de procédure aux Prudhommes", "Une médecine du travail négligente",
        ],
    },
    "devops": {
        "name": "Cliché Maximum: DevOps Edition",
        "tagline": "Le jeu pour ceux qui parlent Kubernetes au déjeuner",
        "language": "fr",
        "bg_prompt": "subtle server rack data center cyberpunk background blue tones, ABSOLUTELY NO TEXT NO LETTERS, decorative texture only",
        "questions": [
            "Vendredi 17h : ____ explose en prod.",
            "Mon manager pense que mon job c'est ____.",
            "À chaque review du code de mon collègue, je découvre ____.",
            "L'astreinte du week-end m'a appris que ____.",
            "Notre stratégie de backup est basée sur ____.",
            "La doc interne décrit le système comme ____, en réalité c'est ____.",
            "Le stagiaire a poussé en prod ____ et personne ne s'en est rendu compte pendant ____.",
            "Mon CTO a banni Kubernetes parce que ____.",
            "Les meetings stand-up de 9h consistent à parler de ____.",
            "Notre incident report explique tout par ____.",
            "Le CEO veut que tout passe en ____ d'ici lundi.",
            "Pour passer un message au sysadmin, le meilleur moyen c'est ____.",
            "La dernière fois qu'on a touché à ____, le serveur a survécu.",
            "Le client trouve normal que ça ____ après 3 ans de service.",
            "Notre slogan de team devrait être ____.",
            "L'équipe sécu nous a interdit ____ depuis qu'on a découvert ____.",
            "Pour fêter une bonne release on commande ____.",
            "Notre monitoring nous alerte uniquement quand ____.",
            "Les standups commencent toujours par ____.",
            "Le pire endroit pour debugger est ____.",
        ],
        "answers": [
            "Le serveur principal", "Une mise à jour mineure de Linux",
            "Un certificat SSL expiré depuis 6 mois",
            "Un fichier .env oublié sur GitHub", "Un cron qui tourne depuis 2007",
            "La voiture personnelle de l'admin sys", "Un printf debug oublié",
            "Une variable nommée X dans le code", "L'API undocumented du legacy",
            "DROP TABLE users", "Un git push --force sur main",
            "Lol pourquoi pas", "Une page HTML faite à la main",
            "Le syndrome de Schrödinger", "Boire un café et prier",
            "Restart everything", "Reposer la question à ChatGPT",
            "Demander à Roger", "Hello World", "Demander à Slack",
            "L'apocalypse", "Une pizza froide", "Le télétravail forcé",
            "Trois écrans à la fois", "L'analyse de logs",
            "Le mode incognito du navigateur", "L'algorithme de tri à bulles",
            "Une démo PowerPoint qui plante", "Trois cafés et un Red Bull",
            "Pleurer en silence", "Refactoriser tout sans review",
            "Migrer vers Rust", "Faire un PR à 23h59",
            "Un dump complet de la BDD", "Une excuse Slack inventive",
            "Le service du voisin qui plante d'abord",
        ],
    },
    "pompiers": {
        "name": "Cliché Maximum: Sapeurs-Pompiers Edition",
        "tagline": "Le jeu pour ceux qui rentrent à 7h avec encore l'odeur de fumée",
        "language": "fr",
        "bg_prompt": "subtle red firefighter rescue equipment background warm tones, ABSOLUTELY NO TEXT NO LETTERS, decorative texture only",
        "questions": [
            "Garde de nuit : à 3h du mat on est appelés pour ____.",
            "Le chef de garde panique uniquement quand ____.",
            "Le pire repas qu'on ait mangé en caserne c'était ____.",
            "Pour réveiller un collègue endormi, on utilise ____.",
            "Notre intervention la plus absurde concernait ____.",
            "La salle de muscu de la caserne sert surtout à ____.",
            "Quand un nouveau arrive, on le fait stresser avec ____.",
            "Le casier de Roger contient secrètement ____.",
            "Les voisins de la caserne nous détestent à cause de ____.",
            "Notre devise officieuse est ____.",
            "Le mess de la caserne a interdit ____ après l'incident de ____.",
            "Pour qu'une intervention soit officiellement « tranquille », il manque seulement ____.",
            "L'inspection de l'an dernier a découvert ____ dans le frigo.",
            "Le chien de la caserne est expert en ____.",
            "Mon premier jour, on m'a appris à reconnaître ____.",
            "Quand on entend l'alarme, on pense d'abord à ____.",
            "Les pompiers volontaires nous appellent en panique pour ____.",
            "Pour faire baisser la tension après une grosse intervention : ____.",
            "Le médecin du SDIS nous a recommandé d'arrêter ____.",
            "L'arme préférée du chef de centre c'est ____.",
        ],
        "answers": [
            "Un chat coincé sur un arbre", "Une casserole qui crame",
            "Un faux appel après match de foot", "La porte d'entrée d'un voisin curieux",
            "Une fuite d'eau dans la salle de garde", "La machine à café qui explose",
            "Le frigo de la caserne resté ouvert", "Un perroquet qui imite l'alarme",
            "Un cambriolage par voie d'égouts", "L'odeur de la lasagne ratée",
            "Un nouveau qui dort encore", "Le canapé défoncé du salon",
            "Le chien de la caserne", "L'application Tinder du chef adjoint",
            "Une fausse alerte d'un capteur défectueux", "Une réunion budgétaire",
            "Trois pizzas froides", "Une partie de babyfoot", "La sieste du soir",
            "Le karaoké de minuit", "Le café du matin", "Une vieille couverture isolante",
            "Un thermomètre cassé", "Un grand verre d'eau froide",
            "Boire un café et prier", "Faire des burpees jusqu'à l'effondrement",
            "Crier plus fort que l'alarme", "Acheter une nouvelle cafetière",
            "Une réunion debout interminable",
        ],
    },
    "profs": {
        "name": "Cliché Maximum: Profs de Lycée Edition",
        "tagline": "Le jeu pour ceux qui ont vu passer 30 ans d'élèves",
        "language": "fr",
        "bg_prompt": "subtle vintage classroom blackboard with chalk marks decorative background ABSOLUTELY NO TEXT NO LETTERS texture only",
        "questions": [
            "Le pire mot d'excuse parent que j'ai reçu : ____.",
            "Lors du conseil de classe, le plus gros débat concerne ____.",
            "Mon élève le plus surprenant a rendu ____ pour son DM.",
            "Pour gérer une classe difficile, ma technique secrète est ____.",
            "Le proviseur me convoque chaque trimestre pour ____.",
            "Pendant la pause, en salle des profs, on débat surtout de ____.",
            "Les copies que je corrige le dimanche soir contiennent toujours ____.",
            "Mon inspection académique a porté sur ____ et s'est terminée par ____.",
            "Le sujet d'EPI qu'on m'a imposé cette année : ____.",
            "Les parents d'élèves veulent absolument ____.",
            "La photocopieuse de la salle des profs est fâchée avec ____.",
            "Le délégué de classe a proposé ____ au conseil.",
            "Un élève m'a expliqué que son devoir est manquant parce que ____.",
            "L'AED s'est officiellement plainte de ____ ce matin.",
            "Le sujet du bac que je redoute le plus est ____.",
            "Mon prochain achat de fournitures perso : ____.",
            "Le CPE m'a annoncé que ____ avait encore ____.",
            "Les portes ouvertes ont été un succès uniquement grâce à ____.",
            "L'IA Inspection a noté la classe parce que ____.",
            "Pendant les conseils de classe, ma phrase préférée est ____.",
        ],
        "answers": [
            "Mon élève s'est cassé un ongle", "Une photo de TikTok comme exposé",
            "Confisquer le téléphone définitivement", "Avoir manqué d'élèves",
            "Le café est cassé", "Le retraité absent depuis 3 ans",
            "Une faute de français du proviseur", "Distribuer trop de bonbons",
            "L'avenir incertain de la dictée", "Une réunion sans pause",
            "Un yaourt oublié dans le frigo", "Réformer l'orthographe",
            "Un pigeon a déchiré son cahier", "La photocopieuse du collège",
            "Un sujet sur Marcel Proust", "Des Post-it",
            "Le délégué", "écrasé ses lunettes", "Le baby-foot acheté en kermesse",
            "Personne ne savait répondre", "Élève brillant mais nonchalant",
            "ChatGPT a tout copié-collé", "La photocopieuse",
            "Mes propres feutres", "Le proviseur en short", "Une absence motivée",
            "Un tableau effaçable cassé", "Un mot d'excuse écrit par l'élève lui-même",
            "Trois minutes de retard généralisé",
        ],
    },
    "peche": {
        "name": "Cliché Maximum: Pêche Édition",
        "tagline": "Le jeu pour ceux qui partent à 4h du matin un dimanche",
        "language": "fr",
        "bg_prompt": "subtle vintage fishing tackle lures fly fishing pattern decorative background ABSOLUTELY NO TEXT NO LETTERS texture only",
        "questions": [
            "Mon plus gros poisson, c'est ____ et personne ne me croit.",
            "Ce que j'oublie systématiquement en partant pêcher : ____.",
            "La carpe que je n'ai jamais attrapée s'appelle ____.",
            "Pour rater une touche, le meilleur moyen est ____.",
            "Mon coffre à leurres contient secrètement ____.",
            "La femme/mari de mon pote a banni la pêche après ____.",
            "Pour expliquer un retour bredouille, j'invente ____.",
            "Le meilleur moment au bord de l'eau c'est ____.",
            "Mon collègue de pêche se vante de ____ à chaque sortie.",
            "Le caillou que j'utilise comme plomb depuis 10 ans s'appelle ____.",
            "Pour pêcher de nuit, j'emporte toujours ____.",
            "La technique secrète de mon grand-père impliquait ____.",
            "L'application météo m'a menti sur ____.",
            "L'eau du lac contient ____ selon les rumeurs.",
            "Le pire moment d'une partie de pêche est ____.",
            "Mon record absolu c'est ____.",
            "Pour calmer un brochet capturé : ____.",
            "Le voisin d'à côté a planté son hameçon dans ____.",
            "L'odeur dominante de mon vivier c'est ____.",
            "À la pause déjeuner sur la berge, je sors toujours ____.",
        ],
        "answers": [
            "Une botte d'égout", "Une vieille godasse à l'effigie de Mitterrand",
            "Un sandwich pâté oublié depuis 3 jours", "Le bouchon préféré de mon grand-père",
            "Trois canettes vides", "Une pluie torrentielle de 8h",
            "Une touche manquée à la 7e minute", "Une querelle avec un Castor",
            "Un selfie avec un poisson trop petit", "Trois cafés et un Red Bull",
            "La grenouille en silicone fluo", "Un nœud de pêcheur expert raté",
            "Un brochet de 12kg fantôme", "Le moustique du coin",
            "Une vieille radio FM", "Trois lignes emmêlées",
            "Une appli météo bidon", "L'orage soudain",
            "Une thermos de café froid", "Mon pote qui parle trop fort",
            "Le sandwich jambon-beurre", "La pluie surprise",
            "Une chaise pliante cassée", "Un pneu de voiture immergé",
            "Une canne à pêche cassée", "Le vent qui change toutes les 3 min",
            "Une plante aquatique inconnue", "Une carpe imaginaire",
            "Le silence du lever du jour", "La bière fraîche de 14h",
        ],
    },
    "nurses": {
        "name": "Cliché Maximum: Nurses Edition",
        "tagline": "The game for those who survive 12-hour shifts",
        "language": "en",
        "bg_prompt": "subtle medical scrubs stethoscope hospital decorative pattern background ABSOLUTELY NO TEXT NO LETTERS texture only",
        "questions": [
            "The patient in Room 12 today asked me about ____.",
            "Night shift discovery : ____ in the supply closet.",
            "My pager went off 17 times because of ____.",
            "The senior nurse warned me about ____ on my first day.",
            "Doctor's handwriting interpreted as ____.",
            "Cafeteria food at 3 AM tastes like ____.",
            "The newbie just learned that ____ is NOT optional.",
            "Family member arguing at the bedside about ____.",
            "Best stress relief after a 12h shift : ____.",
            "Charting at midnight reads suspiciously like ____.",
            "The morning huddle started with ____.",
            "Patient said « I'm allergic to » followed by ____.",
            "The pharmacy ran out of ____ again.",
            "My favorite drug to draw up is ____.",
            "Hospital cafeteria mystery meat resembles ____.",
            "Most common question from family : ____.",
            "Code blue at 2 AM caused by ____.",
            "Best gift for a nurse : ____.",
            "Patient discharge plan written as ____.",
            "What nurses actually need : ____.",
        ],
        "answers": [
            "A 95-year-old patient's TikTok account", "Three expired Snickers",
            "Someone's spilled coffee in the meds room", "A patient hiding their meds in their socks",
            "Doctor wrote « stat » then went to lunch", "Cardboard with mayonnaise",
            "The patient's emotional support iguana", "The Wi-Fi password",
            "A 30-minute nap in the supply closet", "A novel written by Stephen King",
            "Someone forgot to bring donuts", "Oxygen",
            "Coffee", "Saline", "Old leather",
            "When is the doctor coming ?", "A patient trying to escape",
            "More coffee and a raise", "Take 2 of literally everything",
            "Coffee, snacks, and a magic eraser", "Three more nurses",
            "A handwritten note nobody can read", "The night shift miracle",
            "A code brown at the worst time", "An IV pole that's missing wheels",
        ],
    },
}


# ============================================================
# Chargement de decks externes (data/specs_decks/*.cliche.json)
# Additif et non-destructif : si un fichier de stock existe, ses decks
# enrichissent ou remplacent ceux en dur (clés identiques = override).
# Permet d'ajouter du stock sans toucher au code. Format attendu :
# { "decks": { "<key>": {name, tagline, language, bg_prompt, mature,
#                         questions:[...], answers:[...]} } }
# ============================================================
def _load_external_decks() -> None:
    ext_dir = Path(__file__).resolve().parents[1] / "data" / "specs_decks"
    if not ext_dir.is_dir():
        return
    for path in sorted(ext_dir.glob("*.cliche.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  ⚠ deck externe ignoré ({path.name}) : {exc}")
            continue
        for key, deck in payload.get("decks", {}).items():
            if {"questions", "answers", "name"} <= deck.keys():
                NICHE_DECKS[key] = deck
            else:
                print(f"  ⚠ deck '{key}' incomplet dans {path.name}, ignoré")


_load_external_decks()


def pollinations_url(prompt: str, seed: int, w: int = 1024, h: int = 1280) -> str:
    encoded = urllib.parse.quote(prompt, safe="")
    return (f"https://image.pollinations.ai/prompt/{encoded}"
            f"?model=flux&width={w}&height={h}"
            f"&seed={seed}&nologo=true&private=true&enhance=true")


def http_get(url: str, dest: Path, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read()
            if len(data) < 5000:
                raise ValueError(f"too short {len(data)}")
            dest.write_bytes(data)
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"    retry {attempt+1}/{retries} : {exc}")
            time.sleep(6 + attempt * 6)
    return False


def produce_card(deck_key: str, deck: dict, card_type: str, idx: int,
                  text: str, bg_path: Path | None) -> dict:
    layout = LAYOUT_QUESTION_CARD if card_type == "question" else LAYOUT_ANSWER_CARD
    out_dir = OUTPUT_DIR / deck_key / card_type
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"card_{idx:03d}.png"

    compose_design(
        layout=layout,
        illustration_path=None,
        text_values={
            "text": text,
            "deck_label": deck["name"],
        },
        output_path=out_path,
        background_override=bg_path if card_type == "question" else None,
    )

    return {
        "deck_key": deck_key,
        "deck_name": deck["name"],
        "card_type": card_type,
        "card_id": f"{deck_key}_{card_type}_{idx:03d}",
        "text": text,
        "image_file": str(out_path.relative_to(OUTPUT_DIR.parent)),
        "width_px": CARD_W,
        "height_px": CARD_H,
    }


def produce_deck(deck_key: str, deck: dict, max_cards: int) -> int:
    print(f"\n=== {deck['name']} ===")
    questions = deck["questions"][:max_cards]
    answers = deck["answers"][:max_cards * 2]

    # Génère 1 background partagé par tous (économie Pollinations)
    bg_path = OUTPUT_DIR / deck_key / "shared_bg.png"
    bg_path.parent.mkdir(parents=True, exist_ok=True)
    seed = hash(deck_key) % 99999
    print(f"  → Background niche : {deck['bg_prompt'][:60]}...")
    if not http_get(pollinations_url(deck["bg_prompt"], seed, CARD_W, CARD_H),
                     bg_path):
        print(f"  ✗ Pas de background — utilisera fond uni")
        bg_path = None

    manifest = []
    for i, q in enumerate(questions, 1):
        print(f"  Q[{i:>2}] {q[:60]}")
        manifest.append(produce_card(deck_key, deck, "question", i, q, bg_path))

    for i, a in enumerate(answers, 1):
        print(f"  A[{i:>2}] {a[:60]}")
        manifest.append(produce_card(deck_key, deck, "answer", i, a, None))

    # CSV manifest pour TGC bulk upload
    csv_path = OUTPUT_DIR / deck_key / "tgc_upload.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["card_id", "card_type", "deck_name",
                        "text", "image_file"],
            extrasaction="ignore",
        )
        w.writeheader()
        w.writerows(manifest)

    metadata = {
        "deck_id": deck_key,
        "deck_name": deck["name"],
        "tagline": deck["tagline"],
        "total_cards": len(manifest),
        "questions": len(questions),
        "answers": len(answers),
        "card_format": f"Poker {CARD_W}x{CARD_H} (2.75x3.75 bleed)",
        "platform_target": "The Game Crafter + BoardGamesMaker",
        "price_suggested_eur": 19.99,
        "production_method": "Pollinations bg + Pillow text overlay (gibberish-proof)",
    }
    (OUTPUT_DIR / deck_key / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))

    print(f"  → {len(manifest)} cartes produites dans {OUTPUT_DIR / deck_key}")
    return len(manifest)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    niche = os.environ.get("NICHE", "").strip().lower()
    max_cards = int(os.environ.get("MAX_CARDS") or "0") or 25

    if niche and niche not in NICHE_DECKS:
        print(f"Niche inconnue. Choix : {list(NICHE_DECKS)}")
        return 2

    decks = {niche: NICHE_DECKS[niche]} if niche else NICHE_DECKS
    print(f"=== CARD GAME PRODUCER — {len(decks)} deck(s) × {max_cards} cards max ===")

    total = 0
    for k, d in decks.items():
        total += produce_deck(k, d, max_cards)

    print(f"\n  TOTAL : {total} cartes produites → {OUTPUT_DIR}")
    print(f"  Upload sur The Game Crafter : import CSV par deck")
    return 0


if __name__ == "__main__":
    sys.exit(main())
