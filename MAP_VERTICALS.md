# MAP DES VERTICAUX — État du système

> **Règle universelle** : CdC (gate=pending) → Hugo valide → Production auto → Audit → Hugo publie  
> **Invariant** : 10 CdC pending par vertical en permanence  
> **Rôle Hugo** : lire CdC + approuver/rejeter + publier sur plateforme — rien d'autre

---

## FLUX UNIVERSEL

```
Cerveaux Brain (cron hebdo) + Optimizer (lundi 06h)
                    ↓
         Queue Manager (cron toutes les 4h)
         → maintient 10 CdC pending / vertical
                    ↓ gate=pending
          ┌─────────────────────────────┐
          │  HUGO : 5 min/semaine       │
          │  approve → production auto  │
          │  reject  → replacement auto │
          └─────────────────────────────┘
                    ↓ gate=approved
             Production (GitHub Actions)
                    ↓
                  Audit
                    ↓
             Hugo publie sur plateforme
```

---

## ÉTAT DES 7 VERTICAUX

| # | Vertical | Plateforme | CdC | Prod | Brain | Statut |
|---|----------|------------|-----|------|-------|--------|
| 1 | Coloring Books | Amazon KDP | ✅ | ✅ Pollinations+PDF | ✅ | **PRÊT** |
| 2 | Low-Content KDP | Amazon KDP | ✅ | ✅ ReportLab | ✅ | **PRÊT** |
| 3 | Romans KDP | Amazon KDP | ✅ | ✅ Groq Llama | ✅ | **PRÊT** |
| 4 | STL 3D print | Cults3D | ✅ | ✅ OpenSCAD | ✅ | **PRÊT** |
| 5 | Jeux de société | Etsy/Itch.io | ✅ | ✅ PDF print | ✅ | **PRÊT** |
| 6 | Merch Design | Redbubble/Amazon | ✅ | ✅ Pollinations+Pillow | ✅ | **PRÊT** |
| 7 | Godot Assets | Itch.io | ✅ | ✅ Pollinations/LLM | ✅ | **PRÊT** |

---

## VERTICAL 1 — COLORING BOOKS KDP

**Plateformes** : Amazon KDP (8.5×11" paperback)  
**Production** : Pollinations Flux → Pillow (threshold B&W) → ReportLab PDF  

| Script | Workflow | Rôle |
|--------|----------|------|
| agent_coloring_cdc.py | coloring_cdc.yml | Génère CdC avec stratégie prompts |
| produce_coloring_from_cdc.py | coloring_production.yml | Génère N pages + PDF KDP |
| agent_coloring_intel.py | agent_coloring_intel.yml | Brain tendances (lundi 02h) |

**Gate check** : Hugo valide les prompts Pollinations AVANT production (testables sur pollinations.ai)  
**Exigences** : 0% gris, lignes nettes, fond blanc pur, 20-40 pages

---

## VERTICAL 2 — LOW-CONTENT KDP

**Plateformes** : Amazon KDP (6×9" paperback)  
**Production** : ReportLab Python — 100% offline, vectoriel, 300 DPI garanti  

| Script | Workflow | Rôle |
|--------|----------|------|
| agent_cdc_lowcontent.py | cdc_lowcontent.yml | Génère CdC avec spec layout |
| produce_lowcontent_from_cdc.py | lowcontent_production.yml | Génère PDF 6×9 |
| agent_lowcontent_trends.py | lowcontent_brain.yml | Brain tendances (mardi 05h) |

**Gate check** : Hugo valide le concept + layout + palette couleur  
**Exigences** : 100-120 pages, marges KDP 0.75" gutter, texte vectoriel

---

## VERTICAL 3 — ROMANS KDP

**Plateformes** : Amazon KDP (eBook + paperback)  
**Production** : Groq Llama 3.3-70B (38 chapitres, ~65 000 mots)  

| Script | Workflow | Rôle |
|--------|----------|------|
| agent_cdc_roman.py | cdc_roman.yml | CdC : plan 38 chapitres + personnages |
| produce_roman_chapters.py | novel_production.yml | Écriture chapitres (NOVEL_DIR) |
| agent_roman_trends.py | roman_brain.yml | Brain tendances KDP (mercredi 05h) |

**Gate check** : Hugo valide plan, personnages, logline, nom de plume  
**Exigences** : 60 000+ mots, arc narratif complet, < 10 "AI tells"/1000 mots

---

## VERTICAL 4 — STL 3D PRINT

**Plateformes** : Cults3D (80% royalties), Printables (visibilité)  
**Production** : OpenSCAD headless — texte réellement gravé dans géométrie  

| Script | Workflow | Rôle |
|--------|----------|------|
| agent_stl_cdc.py | stl_cdc.yml | CdC : type + niche + N variantes texte |
| produce_stl_openscad.py | stl_production.yml | STL + renders matplotlib + audit |
| render_stl_matplotlib.py | (intégré stl_production) | PNG renders 3 angles |
| agent_stl_audit.py | (intégré stl_production) | Validation géométrie + printabilité |
| agent_stl_trends.py | stl_trends_brain.yml | Brain tendances (mercredi 04h) |

**Gate check** : Hugo valide type, niche, liste des textes variantes  
**Exigences** : texte gravé (OpenSCAD), variantes physiquement distinctes, < 300mm, > 3mm

---

## VERTICAL 5 — JEUX DE SOCIÉTÉ

**Plateformes** : Etsy (PDF P&P), DriveThruRPG (JDR), Itch.io, The Game Crafter  
**Types** : card_game, board_game, dice_game, party_game, educational, rpg_accessory  
**Production** : Pillow + ReportLab → PDF prêts à imprimer  

| Script | Workflow | Rôle |
|--------|----------|------|
| agent_jeux_societe_cdc.py | jeux_societe_cdc.yml | CdC complet avec règles + composants |
| produce_board_game.py | jeux_societe_production.yml | PDFs : cartes + règles + plateau + tokens |
| agent_jeux_societe_trends.py | jeux_societe_brain.yml | Brain tendances (jeudi 04h) |

**Gate check** : Hugo valide concept + mécaniques + règles + exemples de cartes  
**Exigences** : règles complètes (cause #1 mauvaises reviews), cartes au format imprimable

---

## VERTICAL 6 — MERCH DESIGN POD

**Plateformes** : Redbubble (20% royalty), Merch by Amazon (37%), Society6, Etsy+Printful  
**Concept** : 1 CdC = 1 thème × 30 designs (ex: "proverbes du monde illustrés")  
**Production** : Pollinations Flux 1200×1200 → Pillow overlay texte → PNG 2400×2400  

| Script | Workflow | Rôle |
|--------|----------|------|
| agent_merch_design_cdc.py | — (via queue) | CdC : 30 designs avec prompts Pollinations |
| produce_merch_designs.py | merch_production.yml | PNGs + mosaïque + checklist upload |
| agent_merch_trends.py | merch_brain.yml | Brain tendances POD (vendredi 04h) |

**Gate check** : Hugo valide concept thème + style illustration + liste des 30 designs  
**Produits générés** : t-shirt, mug, sticker, poster, tote bag, phone case, hoodie  
**Exigences** : PNG 2400×2400 fond blanc, texte lisible, style cohérent sur la collection

---

## VERTICAL 7 — GODOT ASSETS

**Plateformes** : Itch.io (4.99-19.99 USD), Godot Asset Library (gratuit → visibilité)  
**Types** : sprite_pack, ui_kit, tileset, shader_pack, addon, game_template  
**Production** : Pollinations (images) ou LLM GDScript/GLSL (code)  

| Script | Workflow | Rôle |
|--------|----------|------|
| agent_godot_cdc.py | godot_cdc.yml | CdC : type + thème + contenu pack |
| produce_godot_assets.py | godot_production.yml | Images/code + README Godot 4 |
| agent_godot_trends.py | godot_brain.yml | Brain tendances Itch.io (samedi 05h) |

**Gate check** : Hugo valide type d'asset, thème, liste des catégories de contenu  
**Exigences** : structure dossiers Godot 4, README import, compatibilité 4.2+

---

## CERVEAUX PERPÉTUELS

| Cron | Agent | Domaine |
|------|-------|---------|
| Lundi 06h | agent_vertical_optimizer.py | Feedback loop tous verticaux |
| Mardi 05h | agent_lowcontent_trends.py | Low-content KDP |
| Mercredi 04h | agent_stl_trends.py | STL 3D print |
| Mercredi 05h | agent_roman_trends.py | Romans KDP Fiction |
| Jeudi 03h | agent_coloring_intel.py | Coloriage KDP (bestsellers Amazon) |
| Jeudi 04h | agent_jeux_societe_trends.py | Jeux de société |
| Jeudi 05h | agent_prospecteur_emergence.py | Nouvelles niches émergentes |
| Vendredi 04h | agent_merch_trends.py | Merch POD |
| Samedi 05h | agent_godot_trends.py | Godot/Itch.io assets |
| Dimanche 20h | agent_rapporteur_hebdo.py | Rapport hebdo pour Hugo |
| Toutes les 4h | agent_cdc_queue_manager.py | Maintenir 10 CdC/vertical |

---

## INJECTION D'IDÉE MANUELLE

Hugo peut injecter ses propres idées via GitHub → Actions → "💡 Idée Hugo" :
- Tape une idée libre (ex: "jeu de cartes dark humor médecins urgences")
- Le système détecte automatiquement le bon vertical
- Génère un CdC → gate=pending → Hugo valide comme d'habitude

---

## FUTURS VERTICAUX (non encore implémentés)

| Vertical | Plateforme | Stack | Priorité |
|----------|------------|-------|----------|
| Wall Art printable | Etsy Digital | Pollinations + Pillow | Haute |
| Excel/Sheets templates | Etsy + Gumroad | Python openpyxl | Haute |
| Cross-stitch patterns | Etsy | Python grille + PDF | Moyenne |
| Digital Planners iPad | Etsy | ReportLab hyperliens | Moyenne |
| Tarot/Oracle cards | Etsy | Pollinations + PDF | Basse |
| Prompt Packs IA | PromptBase + Etsy | LLM pur texte | Basse |

---

## SECRETS GITHUB REQUIS

| Secret | Utilisation | Fournisseur |
|--------|-------------|-------------|
| GEMINI_API_KEY | ✅ Cerveau principal — CdC, trends | Google AI Studio (gratuit) |
| GROQ_API_KEY | Romans (Llama 3.3-70B) | Groq (gratuit limité) |
| MISTRAL_API_KEY | Analyse technique (fallback) | Mistral (gratuit limité) |

*Mis à jour : 2026-05-27*
