# 🏛️ EMPIRE HUGO — Mode d'emploi opérationnel

**Mise à jour** : 2026-05-15
**Statut** : Phase 1 (déploiement multi-pipelines)
**Objectif** : 1500-5000 €/mois passifs à 12 mois, 4000-10 000 €/mois à 24 mois

---

## 🎯 La stratégie en une phrase

**Create Once, Distribute Everywhere** (COPE) : 1 design IA → 8 formats → 5 plateformes → autant de produits commercialisables qu'il y a de combinaisons.

Pipeline IA central (GitHub Actions + Pollinations + Pillow) qui tourne en automatique. Hugo fait uniquement la **distribution finale** (upload sur Etsy/Pinterest/Redbubble) pour un total de **10-30 min/jour**.

---

## 📦 Les 5 pipelines actifs ou planifiés

| # | Pipeline | Marque/Branding | Statut |
|---|---|---|---|
| 1 | **SVG Packs Cricut/Silhouette** | shop Etsy générique | ✓ Code déployé (`scripts/produce_svg_pack.py`) |
| 2 | **COPE Designs multi-niches** (Witchy, Coffee, Mountain, Pet Mom, Faith) | shop Etsy par niche | ✓ Code déployé (`scripts/produce_cope_pack.py`) |
| 3 | **Pinterest SEO Empire** | account business Hugo | À coder (script `pinterest_publisher.py`) |
| 4 | **Romance Ebooks KDP** série | sous-pseudo auteur | À coder (`produce_romance_ebook.py`) |
| 5 | **Faceless YouTube Kids** | chaîne YT dédiée | À coder (vague 2) |

**Backlog en standby** (à reprendre après cash flow stabilisé) :
- Mirabilia Éditions (Chess Puzzles Vol I, Plantes médicinales, etc.)
- Inkwell & Hush (Mandalas — saturé)
- Daystone Press (Sudoku Mastery)
- Tiny Curio Co. (Cryptids cute — nécessite IA image-to-image type Ideogram)

---

## ✅ CHECKLIST HUGO — Setup initial (à faire en 1 soirée)

### 1. Comptes plateformes (gratuits, 5-10 min chacun)

- [ ] **Etsy Seller** — https://www.etsy.com/sell — boutique digitale "SVG packs + Designs"
- [ ] **Printful** — https://www.printful.com — pour POD physique (mugs, t-shirts, posters)
- [ ] **Connecter Printful → Etsy** (intégration native, 2 min)
- [ ] **Pinterest Business** — https://business.pinterest.com — pour pousser le trafic
- [ ] **Redbubble** (optionnel, marges plus faibles mais diversification) — https://www.redbubble.com
- [ ] **Society6** (optionnel) — https://society6.com

### 2. Comptes IA pour pipelines avancés (gratuits)

- [ ] **Hugging Face** — https://huggingface.co — clé API gratuite pour fallback Pollinations et image-to-image (besoin pour Tiny Curio Co. plus tard)
- [ ] **Google AI Studio (Gemini)** — https://aistudio.google.com — clé API gratuite (1500 req/jour) pour rédaction de masse
- [ ] **Pinterest Developer** — https://developers.pinterest.com — accès API pour upload auto

### 3. Statut administratif (Hugo France)

- [ ] **Auto-entrepreneur** — https://autoentrepreneur.urssaf.fr — déclaration obligatoire pour encaisser légalement (gratuit, 5 min)
- [ ] **Compte Stripe / PayPal pro** — pour recevoir les paiements Etsy
- [ ] **Compte bancaire dédié** (optionnel mais recommandé)

---

## 🔄 Routine opérationnelle quotidienne (10-30 min)

### Le matin (10 min)

1. **Check GitHub Actions** : un nouveau run a-t-il produit du contenu cette nuit ?
   - Va sur https://github.com/hugokeirsse-byte/365days/actions
   - Si vert → nouveaux ZIPs / designs dans `products/`
   - Si rouge → screenshot et envoyer à Claude

2. **Récupère les nouveaux assets** du repo
   - Sur ton tél, ouvre `products/[niche]/etsy_bulk_upload.csv`
   - Télécharge le ZIP du jour si tu veux uploader

### Le soir (20 min)

3. **Upload sur Etsy** (10 min)
   - Va sur ta boutique Etsy → Listings → Manage Listings
   - Drag-drop les images Pinterest preview
   - Copie-colle titre, description, tags depuis le CSV
   - Publie 5-10 listings par soir → 35-70 listings/semaine

4. **Pousse 10 pins Pinterest** (5 min) — quand le robot Pinterest sera codé, ce sera 0 min
   - Manuellement : poste 10 pins/jour pointant vers tes Etsy listings
   - Compte automatisé : un cron poste pour toi

5. **Check métriques** (5 min)
   - Etsy Stats → vues, ventes, mots-clés qui marchent
   - Pinterest Analytics → quels pins ont du trafic

### Le week-end (1h)

6. **Décide la niche prochaine** semaine
7. **Lance le workflow** GitHub Actions pour produire la production de la semaine
8. **Analyse les ventes** : qu'est-ce qui marche, qu'est-ce qui flop

---

## 🚀 Lancer une nouvelle production (1 clic)

### Via GitHub Actions (depuis ton téléphone)

1. Va sur https://github.com/hugokeirsse-byte/365days/actions
2. Clique sur **"Produce COPE pack"**
3. **Run workflow** → choisis la branche `claude/review-project-briefing-galq7`
4. Paramètres :
   - `niche` : `witchy_cottagecore` (ou autre dans la liste)
   - `max_designs` : `5` (test) ou `20` (production complète)
5. Run

### Via trigger fichier (Claude peut le faire pour toi)

Demande à Claude : *"lance le pipeline COPE sur la niche [X]"* → Claude commit `.triggers/cope_pack` et ça part.

---

## 💰 Modèle économique cible (estimations honnêtes)

### Niche moyenne, 50 designs commercialisés, 6 mois après lancement

| Source | Vente moyenne | Marge | Ventes/mois | **Total mois** |
|---|---|---|---|---|
| **Etsy digital download** (SVG, prints) | 4,99 € | 4,40 € | 30 | **132 €** |
| **Etsy POD mug** (via Printful) | 22,99 € | 8,50 € | 8 | **68 €** |
| **Etsy POD t-shirt** | 24,99 € | 9,20 € | 6 | **55 €** |
| **Etsy POD poster** | 19,99 € | 9,80 € | 5 | **49 €** |
| **Redbubble (secondaire)** | - | - | 15 ventes × 2 € | **30 €** |
| **Affiliation Amazon via Pinterest** | - | - | 50 clics × 0,5 € | **25 €** |
| | | | **Total/niche/mois** | **~360 €** |

À **5 niches en production** : **~1800 €/mois**.
À **15 niches** (1 an) : **~5400 €/mois**.

**C'est honnête, pas survendu.** Beaucoup d'éditeurs Etsy + Printful font ces chiffres.

---

## ⚠️ Erreurs à ne PAS faire

- ❌ **Ouvrir 10 boutiques Etsy** : tu te dilues. **1 boutique = 1 univers visuel cohérent**. Tu peux par contre faire **plusieurs niches dans la même boutique** si elles partagent une esthétique.
- ❌ **Spammer Pinterest** avec 100 pins/jour identiques : Pinterest shadow-ban. Max 30-50 pins/jour, espacés.
- ❌ **Vendre la même image partout au même prix** : Etsy a un public payeur, Redbubble un public économique. Adapte.
- ❌ **Faire du print-on-demand sur Redbubble en priorité** : marges trop faibles. Etsy + Printful d'abord.
- ❌ **Sous-estimer le SEO Etsy** : pas de mots-clés = invisible. Le CSV qu'on génère t'aide mais tu peux affiner.
- ❌ **Oublier de déclarer** : sans auto-entrepreneur tu encaisses au noir = illégal.

---

## 📞 Quand contacter Claude

- **Tu veux lancer une nouvelle niche** → dis-le, je l'ajoute dans le code
- **Un workflow plante** → screenshot du run, je creuse
- **Tu veux pivoter** (abandonner Etsy, attaquer YouTube Kids…) → on en parle
- **Tu vois quelque chose qui marche très bien** sur Etsy d'un concurrent → envoie-moi, je copie la stratégie
- **Tu as une idée bizarre** → propose, on évalue

---

## 🗂️ Structure repo (où trouver quoi)

```
365days/
├── EMPIRE_HUGO.md                ← ce fichier (mémoire externe)
├── .github/workflows/            ← les robots GitHub Actions
│   ├── produce_svg_pack.yml      → SVG packs Cricut
│   └── produce_cope_pack.yml     → COPE multi-formats
├── scripts/                       ← les robots Python
│   ├── produce_svg_pack.py
│   ├── produce_cope_pack.py
│   ├── generate_images.py
│   ├── upscale_images.py
│   ├── mandala_finalize.py
│   └── score_images.py
├── products/                      ← OUTPUT : tes designs à uploader
│   ├── svg_packs/
│   │   └── [niche]/*.zip + etsy_listings.csv
│   └── [niche]/
│       └── design_NN/
│           ├── source.png
│           ├── pinterest_pin.jpg
│           ├── etsy_preview.jpg
│           ├── society6_poster.jpg
│           ├── wallpaper_hd.jpg
│           └── metadata.json
└── _shared/                       ← chartes, logos, ressources de marque
    └── (par marque future)
```

---

## 🔮 Roadmap 90 jours

### Semaines 1-2 (en cours)
- ✓ Pipeline SVG Packs (production)
- ✓ Pipeline COPE multi-niches (production)
- ✓ Création boutique Etsy + Printful + Pinterest Business (à faire par Hugo)
- ✓ Upload des 5 premières niches Etsy (=250 designs live)

### Semaines 3-4
- Pinterest auto-publisher (Claude code le robot)
- Romance Ebooks KDP pipeline (Claude code)
- 1ère série romance (5 livres en cross-promotion)

### Semaines 5-8
- Faceless YouTube Kids pipeline (Claude code)
- Première chaîne YT Kids active
- 30 vidéos en queue

### Semaines 9-12
- Analyse des données réelles
- Doublage des niches qui marchent
- Pivot/abandon des niches qui flopent

### Cible à 90 jours
- **5 pipelines actifs** en parallèle
- **300-500 produits commercialisés** sur 4-5 plateformes
- **150-800 €/mois** de revenus passifs
- **Roadmap claire** pour scaler à 1500-3000 €/mois à 6 mois

---

**Ce document est la mémoire externe de Claude. Quand on parle d'un projet, Claude relit ce fichier pour se remettre dans le contexte. Mets-le à jour quand des décisions stratégiques changent.**
