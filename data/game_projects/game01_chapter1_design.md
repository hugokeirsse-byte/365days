# 🕯️ Hollow Hours — Game Design : Chapitre 1 « La Pièce Sans Heure »

**Jeu** : game01, point-and-click / escape-room, **horreur atmosphérique** (style Rusty Lake).
**Moteur** : Godot 4 (from scratch, mix autorisé).
**Statut** : design chapitre 1 (API-free) — prêt à implémenter dès build Godot.

> Univers **autonome** (pas de cryptides — décision Hugo). Thème central : le **temps figé**.
> Pas de jumpscares cheap : un malaise lent, des objets qui n'ont pas leur place,
> une narration qu'on reconstitue par fragments.

---

## 🎭 1. Ton & ambiance

- **Palette** : désaturée, sépia froid, ombres profondes, une seule source de lumière chaude.
- **Son** : tic-tac d'horloge omniprésent mais **désaccordé** ; drones graves ; silences soudains.
- **Règle d'or** : tout est trop calme. L'horreur vient de ce qui **manque** (pas de reflet dans le miroir, une chaise qui a bougé entre 2 visites).

---

## 🧩 2. Le core loop (rappel)

Observer → tap pour zoomer → collecter objets → combiner/utiliser → débloquer → fragment narratif.

---

## 🗺️ 3. Structure du chapitre 1 — 4 scènes

```
[Scène A] La Chambre        → trouver comment ouvrir l'armoire et le tiroir
       ↓ (clé d'armoire)
[Scène B] L'Armoire/Couloir → réparer l'horloge murale (énigme des aiguilles)
       ↓ (horloge à la bonne heure)
[Scène C] L'Atelier d'horloger → assembler la clé-pendule
       ↓ (clé-pendule)
[Scène D] La Porte Sans Heure → énigme finale, sortie + révélation
```

---

## 🔍 4. Détail des scènes

### Scène A — La Chambre
**Hotspots** : lit défait, armoire (verrouillée), tiroir de chevet (coincé), tableau de travers, fenêtre (rideaux fermés).

| Action | Résultat |
|---|---|
| Redresser le tableau | révèle un **chiffre gravé** au mur : `3` |
| Forcer le tiroir (avec coupe-papier trouvé sous le lit) | obtient une **petite clé rouillée** |
| Ouvrir les rideaux | dehors : **pas de paysage**, juste du blanc. (1er malaise) |
| Petite clé → armoire | ouvre l'armoire → **Scène B** |

**Objets collectés** : coupe-papier, petite clé rouillée.
**Fragment narratif** (sur un mot griffonné dans le tiroir) : *« Elle a arrêté l'horloge pour m'arrêter, moi. »*

### Scène B — L'Armoire / Couloir
Dans l'armoire : un passage. Au mur, une **horloge à 3 aiguilles** bloquée. Une porte au fond (verrouillée par l'horloge).

**Énigme des aiguilles** : il faut régler l'heure. Indices disséminés :
- Mur Scène A : `3`
- Sous le tapis (à soulever) : `:` puis `4`
- Au dos du tableau : `1` (donc heure cible **3:41**)

| Action | Résultat |
|---|---|
| Régler l'horloge sur **3:41** | la porte du fond se déverrouille → **Scène C** |
| Mauvaise heure 3× | l'écran clignote, le tic-tac s'accélère (tension, pas de game-over) |

**Fragment** (gravé sous l'horloge) : *« 3h41. L'heure où tout s'est arrêté. »*

### Scène C — L'Atelier d'horloger
Établi couvert d'engrenages. Un **étau**, un **pendule sans poids**, un **moule** vide.

**Énigme d'assemblage (craft)** :
1. Récupérer un **engrenage doré** (dans une boîte fermée par un cadenas à molette → code = `341`, réutilise l'heure).
2. Fondre la **petite clé rouillée** (Scène A) dans le moule → un **poids de pendule**.
3. Engrenage + poids + pendule → **clé-pendule** (objet final).

| Action | Résultat |
|---|---|
| Cadenas molette `341` | obtient l'engrenage doré |
| Clé rouillée → moule (près de la bougie) | obtient le poids |
| Assembler les 3 | obtient la **clé-pendule** → **Scène D** |

**Fragment** (note sur l'établi) : *« Si tu remontes le temps, ne le laisse pas te voir. »*

### Scène D — La Porte Sans Heure
Une grande porte avec une serrure en forme de cadran. Un **miroir** à côté (le joueur **n'a pas de reflet**).

| Action | Résultat |
|---|---|
| Insérer la clé-pendule dans le cadran | la porte s'ouvre lentement |
| Regarder le miroir avant de sortir | **révélation** : une silhouette derrière le joueur, qui n'était pas là. Écran noir. |
| Franchir la porte | fin du chapitre 1 → teaser chapitre 2 |

**Fragment final** : *« L'horloge est repartie. Quelque chose d'autre aussi. »*

---

## 🎒 5. Inventaire & combinaisons (récap pour l'implémentation)

| Objet | Trouvé en | Utilisé pour |
|---|---|---|
| Coupe-papier | Scène A (sous le lit) | forcer le tiroir |
| Petite clé rouillée | Scène A (tiroir) | armoire, puis fondue en poids |
| Engrenage doré | Scène C (cadenas 341) | clé-pendule |
| Poids de pendule | Scène C (moule) | clé-pendule |
| Clé-pendule | Scène C (assemblage) | porte finale |

**Codes** : `3:41` (horloge), `341` (cadenas) — volontairement liés pour récompenser l'attention.

---

## 🏗️ 6. Implémentation Godot (structure)

```
scenes/
├── Room.tscn        (Scène A)
├── Corridor.tscn    (Scène B)
├── Workshop.tscn    (Scène C)
├── FinalDoor.tscn   (Scène D)
└── UI/Inventory.tscn
scripts/
├── hotspot.gd       (Area2D cliquable : signal "interacted")
├── inventory.gd     (singleton autoload : items, combine())
├── puzzle_clock.gd  (énigme aiguilles)
├── puzzle_lock.gd   (cadenas à molette)
└── game_state.gd    (autoload : flags de progression, save/load JSON)
```

→ Mécaniques génériques (hotspot, inventaire, save) : candidats au **MIX** via
l'Agent #28 Skeleton Scout (chercher "godot point and click inventory MIT").

---

## 🎨 7. Assets à produire

| Type | Source |
|---|---|
| 4 décors de scène (sombres, détaillés) | FLUX/SDXL prompt "dark eerie {room}, dim candlelight, surreal, muted sepia, no text" + retouche |
| Objets d'inventaire (icônes) | génération + rembg détourage |
| Ambiance sonore (tic-tac désaccordé, drones) | Freesound CC0 |
| SFX (clic, déverrouillage, malaise) | Kenney audio CC0 |
| UI (inventaire, zoom) | Kenney UI CC0 |

### Prompt-type décor
```
"dark eerie {room_name}, dim warm candlelight, surreal unsettling atmosphere,
muted cold sepia palette, deep shadows, point-and-click adventure background,
detailed, no text, no people" — FLUX/SDXL.
```

---

## 💰 8. Monétisation

- Chapitre 1 **gratuit** (hook).
- Chapitres 2+ : **pub récompensée** pour débloquer, OU achat unique (déblocage all chapters ~2.99 €).
- Pas de pub intrusive pendant la résolution d'énigme (casserait l'ambiance).

---

## ✅ Prochaine étape (quand build Godot dispo)

1. Init projet Godot 4, autoloads `inventory.gd` + `game_state.gd`
2. (Optionnel) Skeleton Scout → chercher un système d'inventaire/hotspot MIT à mixer
3. Construire les 4 scènes + énigmes selon ce doc
4. Générer les 4 décors + objets via pipeline image
5. Brancher son + ambiance
6. Build APK → test Amazon Appstore → validation Hugo
