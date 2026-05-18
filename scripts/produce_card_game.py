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
    "devops": {
        "name": "Cliché Maximum: DevOps Edition",
        "tagline": "Le jeu pour ceux qui parlent Kubernetes au déjeuner",
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
