# 🦶 Cryptid Cove — Game Design : économie idle

**Jeu** : game02, idle tycoon, zoo de cryptides **mignons**.
**Moteur** : Godot 4 (from scratch, mix autorisé).
**Statut** : design économique (API-free) — prêt à implémenter dès build Godot.

> Ce doc définit les **nombres** qui rendent un idle satisfaisant : courbes de coût,
> revenus, paliers, offline-earnings, prestige. Tout est paramétrable dans un
> futur `data/game_projects/game02_balance.json`.

---

## 💰 1. Monnaies

| Monnaie | Symbole | Rôle | Gagnée par |
|---|---|---|---|
| **Cryptocoins** | CC | monnaie soft principale | revenus passifs des enclos |
| **Cryptid Essence** | ✨ | monnaie de prestige | reset "Migration" (prestige) |
| **Gems** | 💎 | monnaie premium | pub récompensée + achat optionnel |

---

## 🏞️ 2. Les générateurs = enclos de cryptides

Chaque cryptide est un **générateur** (à la AdventureCapitalist). On l'achète,
on le monte en niveau, il produit des CC. L'ordre de déblocage suit les tiers de
`cryptids_public_domain.json`.

### Table de déblocage (coût du 1er achat, revenu de base)

| Ordre | Cryptide | Tier | Coût 1er achat (CC) | Revenu base / cycle | Durée cycle (s) |
|---|---|---|---|---|---|
| 1 | Bigfoot | common | 10 | 1 | 1.0 |
| 2 | Jackalope | common | 120 | 8 | 1.5 |
| 3 | Chupacabra | uncommon | 1 400 | 47 | 2.5 |
| 4 | Jersey Devil | uncommon | 12 000 | 260 | 4 |
| 5 | Ogopogo | uncommon | 130 000 | 1 400 | 6 |
| 6 | Yeti | uncommon | 1 400 000 | 7 800 | 9 |
| 7 | Ahool | uncommon | 15 000 000 | 44 000 | 13 |
| 8 | Dover Demon | rare | 170 000 000 | 260 000 | 18 |
| 9 | Mothman | rare | 2 000 000 000 | 1 600 000 | 24 |
| 10 | Nessie | rare | 24 000 000 000 | 10 000 000 | 30 |
| 11 | Kelpie | rare | 290 000 000 000 | 65 000 000 | 38 |
| 12 | Mokele-mbembe | rare | 3 500 000 000 000 | 430 000 000 | 48 |
| 13 | Thunderbird | rare | 43 000 000 000 000 | 2 900 000 000 | 60 |
| 14 | Wendigo | legendary | 530 000 000 000 000 | 20 000 000 000 | 80 |
| 15 | Kraken | legendary | 6 600 000 000 000 000 | 140 000 000 000 | 100 |
| 16 | Flatwoods Monster | legendary | 82 000 000 000 000 000 | 1 000 000 000 000 | 120 |

> Ratio coût ≈ ×12 par cryptide, revenu ≈ ×6.5 : progression classique qui garde
> chaque nouveau cryptide désirable sans rendre les précédents inutiles.

---

## 📈 3. Courbe de coût d'amélioration (niveaux)

Formule standard idle pour le coût du niveau suivant d'un enclos :

```
cost(level) = base_cost × growth^(level - 1)
growth = 1.07   (commun) | 1.08 (uncommon) | 1.09 (rare) | 1.10 (legendary)
```

→ Plus le tier est haut, plus la montée en niveau est coûteuse (rareté = prestige).

### Paliers de multiplicateur (milestones)

Tous les **25 niveaux**, le revenu de l'enclos est **×2** (effet "milestone").
Niveaux clés : 25, 50, 100, 200, 300, 400, 500, 750, 1000.
→ Donne des objectifs courts ("plus que 6 niveaux pour le ×2").

---

## ⏱️ 4. Offline earnings (le cœur d'un idle)

```
offline_cc = revenu_par_seconde_total × secondes_hors_ligne × taux_offline
taux_offline = 0.50   (50% du rythme actif, classique et équilibré)
cap_offline  = 8 heures par défaut
```

- À l'ouverture : popup "Pendant ton absence, le zoo a gagné X CC 🦶"
- **Pub récompensée** : "Double tes gains hors-ligne" (×2) → levier monétisation #1
- **Gems** : étendre le cap offline de 8h → 24h (achat premium)

---

## 👷 5. Automatisation (managers)

Au début, le joueur **tap** pour collecter chaque enclos. Puis il débloque des
**Gardiens** (managers) qui auto-collectent.

| Gardien | Débloque l'auto-collecte de | Coût (CC) |
|---|---|---|
| Apprenti gardien | Bigfoot | 1 000 |
| Soigneur | Jackalope | 15 000 |
| Crypto-vétérinaire | Chupacabra | 200 000 |
| ... | (1 par cryptide) | ×~14 par palier |

→ Le passage de "tap actif" à "100% idle" est la 1re grande satisfaction.

---

## 🔄 6. Prestige — "La Grande Migration"

Quand la progression ralentit, le joueur peut **migrer** : reset des CC et enclos,
contre de la **Cryptid Essence ✨** permanente.

```
essence_gagnée = floor( sqrt( total_CC_gagnés_cette_run / 1e12 ) )
bonus_permanent = +2% revenus globaux par point d'Essence
```

- L'Essence ne se reset jamais.
- Débloque un arbre de talents permanents (ex: "+offline cap", "coût enclos -5%",
  "tap ×10", "chance de cryptide doré").
- **Cryptide doré** : version brillante d'un cryptide (×10 revenus), chance rare à
  chaque migration → collectionnite.

---

## 🎯 7. Boucles de rétention

| Levier | Mécanique |
|---|---|
| **Quêtes journalières** | "Collecte 3 cryptides", "fais 1 migration" → récompense Gems |
| **Expéditions** | envoyer un gardien en expédition (timer 30min-4h) → ramène un cryptide rare ou des Gems |
| **Événements saisonniers** | cryptide spécial Halloween (Jack-o-Bigfoot), Noël (Yeti festif) → cross avec seasonal_calendar |
| **Collection** | "Cryptid-dex" : compléter la collection (common→legendary→dorés) = succès + bonus |

---

## 💎 8. Monétisation (F2P éthique)

| Offre | Type | Prix indicatif |
|---|---|---|
| Double offline earnings | pub récompensée | gratuit (pub) |
| Boost ×2 revenus 4h | pub récompensée | gratuit (pub) |
| Skip timer expédition | pub OU Gems | — |
| Pack de Gems | achat IAP | 0.99–4.99 € |
| Retrait des pubs interstitielles | achat IAP unique | 2.99 € |
| Starter pack (1 cryptide rare + Gems) | achat IAP | 2.99 € |

> Règle : **jamais de pay-to-win bloquant**. Le jeu est finissable sans payer ;
> l'argent achète du **temps** (skip) et du **confort** (no ads), pas la victoire.

---

## 🗂️ 9. Fichiers à produire pour l'implémentation

```
game02_balance.json     ← toutes les tables ci-dessus en données (à générer)
sprites/cryptids/*.png  ← 16 cryptides cute (FLUX prompt "cute kawaii chibi <cryptid>")
sprites/enclosures/*.png
ui/                     ← Kenney UI pack CC0 (boutons arrondis cozy)
audio/                  ← loop cozy (BandLab/Freesound CC0) + SFX collecte (Kenney)
```

### Prompt-type génération sprite (réutilisable)
```
"cute kawaii chibi {cryptid_name}, big sparkly eyes, soft pastel colors,
rounded shapes, adorable mascot, simple flat vector style, white background,
no text" — via FLUX-schnell ou SDXL, puis rembg pour le détourage.
```

---

## ✅ Prochaine étape (quand build Godot dispo)

1. Générer `game02_balance.json` depuis ces tables
2. Implémenter : currency manager (BigNumber), générateurs, offline calc, prestige
3. Brancher le bestiaire depuis `cryptids_public_domain.json`
4. Générer les 16 sprites cute via le prompt-type
5. Intégrer AdMob rewarded
6. Build APK → test Amazon Appstore → validation Hugo
