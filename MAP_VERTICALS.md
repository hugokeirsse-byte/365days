# MAP DES VERTICALES — Architecture par domaine

> Chaque vertical est **100% indépendant** : ses propres outils, sa propre IA, son propre audit.
> Principe universel : **CdC → Gate Hugo → Production → Audit → Publication par Hugo**

---

## RÔLES

| Qui | Quoi |
|-----|------|
| **Hugo** | Lire le CdC → Valider (gate=approved) ou Rejeter (gate=rejected) → Publier sur les plateformes |
| **Système** | Tout le reste : veille marché, génération CdC, production, audit, préparation listing |

---

## FLUX UNIVERSEL

```
Cerveau perpétuel (cron hebdo)         Optimizer (cron lundi)
       ↓                                        ↓
       └──────────── Queue Manager (cron 4h) ──┘
                            ↓
              Génère CdC jusqu'à 10 pending/vertical
                            ↓ gate=pending
                ┌───────────────────────────┐
                │  HUGO : lit + valide      │  < 5 min/semaine
                │  approve / reject         │
                └───────────────────────────┘
                   ↓ gate=approved    ↓ gate=rejected
            Production (auto)    Queue Manager remplace
                   ↓              automatiquement
                 Audit
                   ↓
            Hugo publie (plateforme)
                   ↓
            Queue Manager détecte le manque
                   ↓
            Nouveau CdC généré auto
```

**Invariant garanti : 10 CdC pending par vertical à tout moment.**
 Hugo publie sur la plateforme
```

---

## VERTICAL 1 — LIVRES DE COLORIAGE KDP

**Plateforme** : Amazon KDP (paperback)  
**Outil production** : Pollinations AI → images PNG → Pillow/ReportLab → PDF  
**Cerveau dédié** : agent_coloring_intel.py (cron lundi)  

| Étape | Script | Workflow | Statut |
|-------|--------|----------|--------|
| Tendances marché | agent_coloring_intel.py | agent_coloring_intel.yml | ✓ |
| CdC + prompts | **agent_coloring_cdc.py** | **coloring_cdc.yml** | ✓ Nouveau |
| Production images | produce_coloring_book.py | produce_coloring_book.yml | ✓ (à connecter au CdC) |
| Audit | agent_visual_audit.py | agent_visual_audit.yml | ✓ v3 |
| Listing Amazon | Préparer manuellement via le CdC | — | Manuel Hugo |

**Ce que Hugo valide dans le CdC :**
- Thème et style artistique (ex: "botanical precision, no shading")
- Les prompts EXACTS Pollinations (testables avant validation)
- Audience cible et niveau de complexité
- Positionnement vs concurrents

**Exigences qualité (causes de REJECT) :**
- Résolution minimum 2560×3328px (300 DPI KDP 8.5×11")
- Zéro gris / shading dans les images (100% N&B pur)
- Lignes visibles à l'impression (≥ 3px à 300 DPI)
- 20-40 pages par livre

---

## VERTICAL 2 — LOW-CONTENT KDP (JOURNAUX / PLANNERS)

**Plateforme** : Amazon KDP (paperback)  
**Outil production** : ReportLab Python — 100% offline, 300 DPI garanti  
**Cerveau dédié** : à créer (agent_lowcontent_trends.py)  

| Étape | Script | Workflow | Statut |
|-------|--------|----------|--------|
| Tendances marché | (à créer) | (à créer) | ✗ Manquant |
| CdC + spec layout | agent_cdc_lowcontent.py | cdc_lowcontent.yml | ✓ |
| Production PDF | produce_lowcontent_from_cdc.py | produce_lowcontent_kdp.yml | ✗ Manquant |
| Audit PDF | agent_visual_audit.py (audit_lowcontent) | agent_visual_audit.yml | ✓ v3 |
| Listing Amazon | Préparer via CdC | — | Manuel Hugo |

**Ce que Hugo valide dans le CdC :**
- Concept du journal (thème, niche, "pourquoi maintenant?")
- Layout des pages (structure, nombre de lignes, prompts journaliers)
- Spécifications ReportLab (polices, couleurs, décorations)
- 7 mots-clés KDP + 2 catégories

**Exigences qualité :**
- 100-120 pages minimum
- Format 6×9 inches exact
- Marges KDP respectées (0.75" gutter)
- Texte vectoriel (ReportLab → PDF → pas d'image floue)

---

## VERTICAL 3 — ROMANS KDP (eBOOK + PAPERBACK)

**Plateforme** : Amazon KDP (eBook + paperback)  
**Outil production** : Groq Llama 3.3 70B (roman en anglais)  
**Cerveau dédié** : agents LLM multi-provider déjà wired dans brain_utils  

| Étape | Script | Workflow | Statut |
|-------|--------|----------|--------|
| Tendances genre | agent_eclaireur_bestsellers.py | agent_eclaireur.yml | ✓ |
| CdC 38 chapitres | agent_cdc_roman.py | cdc_roman.yml | ✓ |
| Écriture chapitres | **produce_roman_chapters.py** | **novel_factory.yml** | ✗ Manquant |
| Assemblage + mise en page | (à créer) | — | ✗ Manquant |
| Audit roman | agent_visual_audit.py (audit_novel) | agent_visual_audit.yml | ✓ v3 |
| Listing Amazon | Préparer via CdC | — | Manuel Hugo |

**Ce que Hugo valide dans le CdC :**
- Titre, logline, résumé
- Plan complet 38 chapitres
- Personnages (fiches complètes)
- Niveau de sensualité, tropes, ton
- Nom de plume et bio auteur

**Exigences qualité :**
- 60 000+ mots
- Score lisibilité ≥ 70 (Flesch-Kincaid)
- < 10 "AI tells" par 1000 mots
- Arc narratif complet en 4 actes

---

## VERTICAL 4 — IMPRESSION 3D (CULTS3D / PRINTABLES)

**Plateforme** : Cults3D (80% royalties), Printables (visibilité)  
**Outil production** : OpenSCAD (texte GRAVÉ dans géométrie), render matplotlib  
**Cerveau dédié** : agent_stl_trends.py (cron mercredi)  

| Étape | Script | Workflow | Statut |
|-------|--------|----------|--------|
| Tendances Cults3D/Printables | agent_stl_trends.py | stl_trends_brain.yml | ✓ Nouveau |
| CdC + variantes | agent_stl_cdc.py | stl_cdc.yml | ✓ Nouveau |
| Production STL | produce_stl_openscad.py | stl_production.yml | ✓ Nouveau |
| Renders PNG | render_stl_matplotlib.py | (intégré stl_production.yml) | ✓ Nouveau |
| Audit 3D | agent_stl_audit.py | (intégré stl_production.yml) | ✓ Nouveau |
| Upload Cults3D | Manuel Hugo | — | Manuel Hugo |

**Ce que Hugo valide dans le CdC :**
- Type de produit (bookmark, keychain, coaster, door_plate, plant_marker)
- Niche et thème (cottagecore, DnD, witchy, minimalist...)
- Les 15 variantes de texte
- Dimensions et paramètres d'impression

**Exigences qualité :**
- Texte réellement gravé dans la géométrie (pas juste dans le nom de fichier)
- Dimensions printables (< 300mm, > 3mm épaisseur)
- STL valide (> 100 triangles, géométrie manifold)
- Variantes physiquement distinctes (triangle counts différents)

---

## VERTICAL 5 — JEUX DE SOCIÉTÉ (ETSY / DRIVETHRURPG / ITCH.IO)

**Scope** : card games, jeux de plateau, jeux de dés, party games, jeux éducatifs, accessoires JDR  
**Plateformes** : Etsy (PDF print-and-play), DriveThruRPG (JDR), Itch.io (indie), The Game Crafter (physique)  
**Outil production** : Pillow + ReportLab (composants imprimables complets)  
**Cerveau dédié** : à créer (agent_jeux_societe_trends.py)  

| Étape | Script | Workflow | Statut |
|-------|--------|----------|--------|
| Tendances marché | (à créer) | (à créer) | ✗ Manquant |
| CdC jeu complet | agent_jeux_societe_cdc.py | jeux_societe_cdc.yml | ✓ Nouveau |
| Production card game | produce_card_game.py | produce_card_game.yml | ✓ (sans gate — à connecter) |
| Production board game | (à créer) | — | ✗ Manquant |
| Audit | agent_visual_audit.py (audit_card_game) | agent_visual_audit.yml | ✓ v3 |
| Listing plateforme | Manuel Hugo | — | Manuel Hugo |

**Types de jeux supportés dans le CdC :**

| Type | Composants | Plateforme | Prix typique |
|------|-----------|------------|-------------|
| card_game | 52-200 cartes poker | Etsy, TGC | 4.99-12.99 USD |
| board_game | plateau + cartes + pions + règles | Etsy, Itch.io | 8.99-24.99 USD |
| dice_game | étiquettes dés + score sheets | Etsy, Itch.io | 3.99-7.99 USD |
| party_game | 100-300 cartes + règles | Etsy, Amazon | 5.99-14.99 USD |
| educational | flashcards + plateau optionnel | Etsy, TPT | 3.99-9.99 USD |
| rpg_accessory | feuilles perso + cartes + tuiles | DriveThruRPG, Itch.io | 2.99-24.99 USD |

**Ce que Hugo valide dans le CdC :**
- Concept du jeu et mécanique principale
- Liste complète des composants (quoi imprimer)
- Règles de jeu complètes (cause #1 de mauvaises reviews = règles manquantes)
- Exemples de contenu (cartes, questions, textes)
- Plateforme de vente et prix

**Queue** : 10 CdC jeux_societe en attente à tout moment (20 combinaisons type × thème × mécanique)

---

## VERTICAL 6 — MERCH PRINT-ON-DEMAND

**Plateformes** : Redbubble, Merch by Amazon, Society6  
**Outil production** : Pillow (designs PNG), SVG éventuel  
**Cerveau dédié** : agent_trend_design_matcher.py  

| Étape | Script | Workflow | Statut |
|-------|--------|----------|--------|
| Tendances design | agent_trend_design_matcher.py | agent_trend_design_matcher.yml | ✓ |
| CdC design | (à créer) | (à créer) | ✗ Manquant |
| Production designs | tumbler_wraps, svg_pack... | plusieurs workflows | ✓ (sans gate) |
| Audit | agent_visual_audit.py | agent_visual_audit.yml | partiel |
| Upload plateformes | Manuel Hugo | — | Manuel Hugo |

---

## ACTIONS HUGO — CHECKLIST COMPLÈTE

### À faire une seule fois (setup)
- [ ] URSSAF: inscription auto-entrepreneur avant première vente
- [ ] Amazon KDP: compte créé et bancaire connecté
- [ ] Cults3D: compte créé (gratuit), compte Stripe connecté
- [ ] Etsy: compte créé, listing fees acceptées
- [ ] GitHub Secrets: GROQ_API_KEY, MISTRAL_API_KEY, RUNWARE_API_KEY

### Routine hebdomadaire Hugo (< 30 min)
1. Lire rapport hebdo `data/reports/rapport_hebdo_latest.md`
2. Vérifier les CdC en attente dans `products/*/` (gate=pending)
3. Approuver ou rejeter → push → production auto
4. Lire les AUDIT.txt des produits APPROVE → uploader sur la plateforme

### Ne jamais faire (automatisé)
- Générer des images (automatique)
- Écrire des chapitres de roman (automatique)
- Générer des STL (automatique)
- Auditer les produits (automatique)
- Faire la veille marché (automatique, chaque semaine)

---

## PIPELINE CdC — GESTION DE LA FILE

| Règle | Comportement |
|-------|-------------|
| File cible | **10 CdC pending** par vertical en permanence |
| Hugo approuve 1 | 1 nouveau CdC généré auto pour remplacer |
| Hugo rejette 3 | 3 nouveaux CdC générés auto |
| File < 10 | Queue Manager génère jusqu'à 5 CdC par run, refait en 4h |
| Hugo approuve / rejette via GitHub | Push `gate_cdc=approved/rejected` dans `cdc.json` → déclenche queue |

**Pour Hugo : 1 seule action par CdC — changer `gate_cdc` dans le fichier JSON, push.**

---

## CERVEAUX PERPÉTUELS ACTIFS

| Agent | Cron | Fréquence | Domaine |
|-------|------|-----------|---------|
| agent_coloring_intel.py | lundi 02h | hebdo | Livres de coloriage KDP |
| agent_eclaireur_bestsellers.py | mardi 03h | hebdo | Bestsellers KDP |
| agent_saisonnier.py | mercredi 02h | hebdo | Calendrier saisonnier |
| agent_stl_trends.py | mercredi 04h | hebdo | 3D print Cults3D/Printables |
| agent_b1_stratege.py | jeudi 04h | hebdo | Stratégie globale |
| agent_prospecteur_emergence.py | vendredi 03h | hebdo | Nouvelles niches émergentes |
| agent_architecte_systeme.py | dimanche 02h | hebdo | Gaps système auto-détectés |
| agent_rapporteur_hebdo.py | dimanche 20h | hebdo | Rapport résumé pour Hugo |

---

## SECRETS GITHUB REQUIS

| Secret | Utilisation | Fournisseur |
|--------|-------------|-------------|
| GEMINI_API_KEY | Cerveau principal (créatif) | Google AI Studio (gratuit) |
| GROQ_API_KEY | Roman writing (Llama 3.3 70B) | Groq (gratuit limité) |
| MISTRAL_API_KEY | Analyse technique | Mistral (gratuit limité) |
| RUNWARE_API_KEY | Génération images qualité | Runware.ai |
| HF_API_KEY | Images (fallback) | HuggingFace |

---

*Mis à jour : 2026-05-27*
