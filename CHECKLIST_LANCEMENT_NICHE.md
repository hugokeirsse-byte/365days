# ✅ CHECKLIST — Lancement d'une nouvelle niche

**Doctrine** : aucune niche n'entre en production sans passer ces 4 portes.
La séquence garantit légalité + viabilité économique + alignement marque.

---

## PORTE 1 — Détection (automatique, 0 effort Hugo)

L'agent #1 (Éclaireur Bestsellers), #2 (Critique de Plaintes) ou #3 (Tendanceur)
détecte un signal. L'agent #7 (Synthétiseur) génère un fichier dans
`data/opportunities/<id>.json` conforme à `data/schemas/opportunity.schema.json`.

- [ ] **P1.1** Score normalisé ≥ 75/100 (cf. `scoring_matrix.json`)
- [ ] **P1.2** Pas de veto légal (`legalite > 0`)
- [ ] **P1.3** Evidence chiffrée présente (search volume, competition, pain points)
- [ ] **P1.4** `next_action` défini (pipeline à déclencher)

**Si toutes cases vertes → la niche passe en queue de production.**

---

## PORTE 2 — Validation copyright + brand fit (automatique, 0 effort)

Avant de lancer la production, le système vérifie :

- [ ] **P2.1** `copyright_check.check_asset()` retourne `passed=true` sur le titre + description prévus
- [ ] **P2.2** Si parents PD : tous dans `whitelist_pd.json` (Module U/V/W/P)
- [ ] **P2.3** Aucun pattern blacklist (Disney/Marvel/DC/Pokémon/Nintendo...) dans le brief
- [ ] **P2.4** `brand_id` déterminé (heritage_coloring | iconic_offspring | pocket_decks | modern_cozy)
- [ ] **P2.5** Le brand a un pipeline producteur compatible disponible

**Si une case rouge → la niche passe en `data/opportunities/rejected/` avec raison.**

---

## PORTE 3 — Production + QA (automatique, ~15-45 min/niche)

Le producteur génère l'asset, le QA inline tourne :

- [ ] **P3.1** Asset produit dans `staging/<brand>/<niche>/`
- [ ] **P3.2** `metadata.json` conforme à `asset.schema.json`
- [ ] **P3.3** Anti-Slop textuel (#20) PASS sur titre + description + bullets
- [ ] **P3.4** Anti-Slop visuel (#21) score ≥ 7/10
- [ ] **P3.5** Pain points détectés en P1 sont **explicitement adressés** dans `qa_pain_points_addressed`
- [ ] **P3.6** Format technique correct (DPI, dimensions, bleed pour print)
- [ ] **P3.7** `preview.png` généré pour notif Telegram

**Si P3.3 ou P3.4 fail → boucle de correction (max 3 itérations).**
**Si toujours fail après 3 itérations → escalade Telegram ⚠️ Hugo décide.**

---

## PORTE 4 — Validation humaine + publication (effort Hugo : 30 secondes)

- [ ] **P4.1** Notif Telegram 🆕 reçue avec preview + métadonnées
- [ ] **P4.2** Hugo clique ✅ Publier
- [ ] **P4.3** Workflow `publish_<platform>.yml` se déclenche
- [ ] **P4.4** Si plateforme accepte API (KDP API future, Gumroad API) : upload auto
- [ ] **P4.5** Sinon : asset migre vers `products/ready_to_upload/` + notif "à uploader manuellement"
- [ ] **P4.6** Hugo upload manuel quand il a 5 min (selon throttling cf. SECURITE_ET_LEGAL.md §2.1)
- [ ] **P4.7** Hugo confirme upload via bouton Telegram → asset marqué `published`

---

## 🌐 PORTE 5 — Cross-pollinisation (automatique, déclenchée à P4 ✅)

Quand un asset passe en `published`, l'agent #10 (Arbitragiste Cross-canal)
déclenche automatiquement les pipelines dérivés selon
`REVERSE_ENGINEERING_BESTSELLERS.md §4.1` :

Exemple : un coloring book Heritage passe ✅ → déclenche :
- [ ] Pipeline merch (extraire 5 visuels iconiques → t-shirt/sticker/poster/mug)
- [ ] Pipeline vidéo faceless (montrer le process coloring sur TikTok/YouTube)
- [ ] Pipeline progeny pack (si parents PD compatibles)

**Effet** : 1 validation → 3-5 produits dérivés en file de prod. **Stock toujours plein.**

---

## 📋 EXEMPLE COMPLET — niche "Köhler Medicinal Plants Coloring Book"

```
PORTE 1 ✅ Score 84/100, evidence: BHL HD scans + KDP top 50 catégorie botanique
PORTE 2 ✅ Brand: heritage_coloring · Source: kohler_medicinal_plants_1887 (whitelist)
PORTE 3 ✅ 100 pages line-art generées, anti-slop 9/10, pain points "papier épais"
         et "lignes fermées" adressés
PORTE 4 ⏳ Notif Telegram envoyée, Hugo clique ✅ → publish_kdp.yml démarre
PORTE 5 → déclenche :
         - produce_merch_batch (10 visuels iconiques de Köhler → t-shirts/stickers)
         - produce_video_faceless (vidéo "process coloring" TikTok)
         - produce_kdp_collector (livre collector édition reliée)
```

---

## 🚨 ABANDON D'UNE NICHE — quand et comment

Une niche est abandonnée si :
1. Score chute en dessous de 50/100 (3 mesures consécutives)
2. 3 strikes copyright sur des assets dérivés
3. Ratio coût-tokens / revenus négatif après 60 jours en production
4. Hugo décide manuellement (bouton 🚫 Bannir niche dans Telegram)

L'abandon écrit la niche dans `data/blacklist_niches.json` avec timestamp et raison.
Aucun pipeline ne re-produira pour cette niche pendant 6 mois (cooldown).

---

## 📅 CADENCE DE LANCEMENT — recommandation conservative

| Semaine | Nouvelles niches lancées |
|---|---|
| S1 (Vagues 0+1+2 ok) | 2 niches pilotes (Köhler + Audubon coloring) |
| S2 | +2 niches (Vésale + bébé super-héros #1) |
| S3 | +3 niches (cottagecore witch, dark academia, mystical mushrooms) |
| S4 | +3 niches |
| S5+ | +5/semaine si la machine tient, ralentir si saturation staging |

**Saturation staging** : > 30 assets en attente dans une brand → on freine
la production pour cette brand jusqu'à digérer le stock.
