# CAHIER DES CHARGES — Livre de coloriage

**ID :** `brief_2026-05-22_coloring_kawaii_mushroom_hollow`
**Statut :** GATE 1 — en attente de TA validation (rien ne part en production avant ton OK)
**Décidé par :** l'IA (sur trends) — *generation_strategy : mono_trend*

> Comment décider : lis ce document, regarde les 6 images de référence dans `ref_candidates/`, puis dis-moi :
> **« OK, prends la réf n°X, on envoie »** — ou — **« non / modifie ceci / change la réf »**.

---

## 1. Le livre
**Titre (proposé) :** *Mushroom Hollow*
**Sous-titre :** *30 Cute Cottagecore Mushroom Coloring Pages for Relaxation*
**Concept :** un village de champignons enchanté, kawaii et cottagecore (maisonnettes-champignons, fées, petits animaux). Coloriage **adulte détente**, style mignon et apaisant.

**Pourquoi ce projet (trends) :** trend *« kawaii cute »* (score 550) croisée à l'esthétique *cottagecore* (evergreen fort). Le créneau coloriage cute/cottagecore est noté **88,5**, ROI estimé **70-350 €/mois**, marchés **Etsy + KDP**. Choisi comme **premier projet de preuve** : faible risque (aucun texte intérieur), style déjà éprouvé par le pipeline, demande stable toute l'année.

## 2. Style visuel
**À respecter :** trait noir **épais, net, fermé**, fond **blanc pur**, formes simples prêtes à colorier, kawaii (formes rondes, grands yeux), ambiance cottagecore. Complexité **moyenne** (ni vide, ni surchargé).
**À bannir (anti-dérive) :** couleur, gris, ombrage, hachures, croquis, texture crayon, remplissage, **texte/lettres**, watermark, contours ouverts/cassés, micro-détails inutilisables.

## 3. Format (KDP, prêt à imprimer)
- Trim **8,5 × 11"**, fond perdu 0,125", **reliure (gutter) 0,75"**, marges 0,5"
- **30 pages** intérieures **N&B**, rotation recto/verso
- Export **PDF/X-1a** (intérieur) + **couverture séparée**

## 4. Les 30 pages (sujets définis)
1. Fly agaric aux étoiles et lunes flottantes · 2. Ronde de fées avec petite porte · 3. Maisonnette-champignon avec cheminée fumante · 4. Champignons empilés en tour · 5. Champignon sous un parapluie sous la pluie · 6. Couple de champignons prenant le thé · 7. Hibou perché sur un champignon géant · 8. Escargot avec chapeau-champignon · 9. Champignon à chapeau de sorcière · 10. Jardin de champignons avec abeilles et papillons · 11. Champignon portant une lanterne la nuit · 12. Champignon lisant à la bougie · 13. Champignon-maison de fée (porte + fenêtres) · 14. Champignon dansant avec des feuilles · 15. Champignon chevauchant un escargot · 16. Champignon et sa coccinelle · 17. Champ de champignons sous croissant de lune · 18. Champignon dans une boule de cristal · 19. Champignon à ailes de papillon · 20. Champignon endormi sous une feuille · 21. Champignon à motif de constellation · 22. Vieux champignon sage à barbe et canne · 23. Champignon-boulanger avec tablier et pain · 24. Champignon tenant une clé magique · 25. Champignon et son tournesol · 26. Chaton lové entre les champignons · 27. Grenouille sur champignon jouant de la flûte · 28. Champignon couvert de vignes et raisins · 29. Champignon d'hiver sous la neige · 30. Champignon émergeant des pages d'un livre

## 5. Couverture (clé-en-main)
- **En couleur** (contrairement à l'intérieur) : une scène phare du village colorée pastel doux
- **Titre** en haut, lisible en miniature · **nom d'auteur** en bas · doit ressortir en vignette Amazon/Etsy

## 6. Identité commerciale
- **Nom d'auteur (de plume) :** *Maple Briarwood* — ⚠️ **PAS encore vérifié comme libre**
- **Titre :** *Mushroom Hollow* — ⚠️ **PAS encore vérifié comme libre**
- *(Rappel : un nom d'auteur différent par livre → un flop ne contamine pas le catalogue)*
- **Collection :** Vol. 1, à décliner si succès (Vol. 2 Fairy Cottages, Vol. 3 Cozy Forest Animals, Vol. 4 Mystical Mushrooms intriqué)

## 7. Garde-fous budget images
- **Plafond DUR : 50 images** pour tout le livre (candidates + 30 pages + couverture + regénérations). Au-delà → STOP + alerte.
- Objectif **« 1 image générée = 1 image intégrée »** (prompts/négatifs/réf assez précis pour éviter les regénérations).

## 8. Grille d'audit (10 critères — 9 bloquants)
Trait noir pur (pas de gris) · cohérence stylistique entre TOUTES les pages · formes fermées coloriables · sujet conforme à la page · zéro texte parasite · format KDP correct · couverture conforme · complétude clé-en-main (titre+auteur+metadata) · titre & auteur vérifiés uniques · *(non bloquant)* composition équilibrée.

## 9. Boucle & validation
- **2 GATES :** GATE 1 = cette validation (toi) · GATE 2 = produit fini présenté → tu décides publication.
- Boucle auto-correction bornée : max 5 itérations, escalade vers toi si insoluble (jamais de boucle infinie).

---

## 10. Images de référence — À CHOISIR
6 candidates dans le dossier `ref_candidates/` (`cand_1.png` … `cand_6.png`).
**Sujet testé :** *fly agaric mushroom with stars and moons* (sujet représentatif du style).
**⚠️ Simulation gratuite (Pollinations)** — qualité variable, juste pour valider le **mécanisme** et te laisser choisir une **direction de style**. Le rendu **définitif** sera généré avec **Runware / FLUX schnell** (payant, propre) une fois cette réf verrouillée.

**Ta décision attendue :** quelle candidate (ou « aucune, regénère avec tel ajustement ») → elle deviendra la référence qui verrouille le style des 30 pages.
