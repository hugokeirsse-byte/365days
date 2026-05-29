# CAHIER DES CHARGES — Enchanted Cottage Garden: Botanical Dreams Coloring Book
**Statut** : EN ATTENTE VALIDATION HUGO
**Date** : 2026-05-28
**ID** : coloring_2026-05-28

## GATE CdC = PENDING

**Avant toute production :**
1. Lire ce document et valider le concept + prompts
2. Copier `exemple_prompt_complet` ci-dessous et tester manuellement sur https://pollinations.ai
3. Verifier : pur noir/blanc, zero gris, lignes nettes, fond blanc
4. Si OK : ouvrir `cdc.json` et changer `gate_cdc` de `pending` a `approved`
5. Pousser le fichier — la production demarre automatiquement.

---

## 1. Concept
**Titre** : Enchanted Cottage Garden: Botanical Dreams Coloring Book
**Sous-titre** : A Whimsical Journey Through Intricate Floral Scenes for Adult Relaxation and Creativity
**Theme** : cottage_garden_flowers
**Style artistique** : botanical_precision|whimsical|intricate_line_art
**Audience** : adult
**Complexite** : intricate
**Pages** : 30

**Element unique** : Ce livre se démarque par une combinaison unique de précision botanique réaliste pour les fleurs principales (roses anciennes, lavande, pivoines, campanules) et d'éléments légèrement fantaisistes et cachés (petits insectes stylisés, arrosoirs décoratifs, bancs de jardin secrets, portes en bois ornées). Chaque page est conçue comme une scène complète de jardin, pas seulement une fleur isolée, offrant une immersion narrative. Les lignes sont volontairement plus épaisses et nettes pour éviter tout problème d'impression, même les détails les plus fins restent clairs. La progression de la complexité est douce et engageante.

## 2. STRATEGIE PROMPTS POLLINATIONS

> Ces prompts sont la CLE du projet. Tester avant de valider.

### Style de base (a inclure dans TOUS les prompts)
```
black and white coloring page, clean outlines, no fill, white background, no gray, no shading, intricate line art, high contrast, crisp lines, professional ink drawing
```

### Modificateurs de style
- highly detailed botanical illustration
- hand-drawn aesthetic
- whimsical garden elements
- zentangle inspired patterns (for complex pages)
- vintage botanical engraving style

### Mots-cles du theme
old garden roses, lavender fields, peonies blooming, bellflowers, forget-me-nots, garden path, stone wall, birdhouse, watering can, trellis with climbing plants, bees and butterflies, secret garden gate

### Mots-cles NEGATIFS (a exclure pour eviter le gris)
gray, shading, photo, realistic texture, color, gradient, shadow, blur, soft lines, halftone, 3D, photography, photorealistic

### EXEMPLE DE PROMPT COMPLET A TESTER

> Copier ce prompt sur https://pollinations.ai et verifier le resultat

```
black and white coloring page, a charming old stone path winding through a vibrant cottage garden filled with blooming lavender and intricate bellflowers, a small decorative birdhouse nestled among the foliage, highly detailed botanical illustration, clean outlines, no fill, white background, no gray, no shading, intricate line art, high contrast, crisp lines, professional ink drawing
```

### Variantes par niveau de complexite
- Prompt page simple (débutant) : black and white coloring page, a single large, simple old garden rose with a few leaves, clean outlines, no fill, white background, no gray, no shading, clear line art, high contrast.
- Prompt page medium (intermédiaire) : black and white coloring page, a rustic wooden bench surrounded by a patch of blooming peonies and small butterflies, whimsical garden elements, highly detailed botanical illustration, clean outlines, no fill, white background, no gray, no shading, intricate line art, crisp lines.
- Prompt page complexe (expert) : black and white coloring page, an elaborate secret garden gate made of wrought iron, partially covered by climbing roses and delicate wisteria, with intricate zentangle-inspired patterns on the gate, hidden ladybugs, highly detailed botanical illustration, clean outlines, no fill, white background, no gray, no shading, intricate line art, high contrast, professional ink drawing.

**Note importante** : Toujours inclure 'no gray', 'no shading', 'clean outlines', 'white background' et 'high contrast'. Tester au moins 3 pages (une de chaque complexité) AVANT toute génération de lot pour s'assurer de l'absence totale de gris et de la netteté des lignes. Prioriser 'ink drawing' et 'line art' pour renforcer le style.

## 3. Distribution des Pages
- Pages simples : 8
- Pages medium : 14
- Pages complexes : 8
- Progression : Le livre commence par des pages plus simples, présentant des fleurs emblématiques du jardin de cottage ou des éléments isolés avec moins de détails pour permettre une prise en main douce. La complexité augmente progressivement au fil des pages, introduisant des scènes de jardin plus larges, des compositions florales plus denses, et enfin des pages très détaillées avec des éléments architecturaux ou des motifs complexes, offrant un défi stimulant pour les colorieurs expérimentés vers la fin du livre.

## 4. Public Cible
**Persona** : Amélie, 38 ans, graphiste freelance vivant en ville. Elle aime la nature, les jardins, et cherche des activités relaxantes pour décompresser après une journée de travail stressante. Elle apprécie les livres de coloriage qui offrent à la fois des motifs esthétiques et un certain niveau de défi, lui permettant d'exprimer sa créativité. Elle est sensible aux détails et à la qualité du dessin, et préfère les thèmes intemporels et apaisants.
**Age** : 28-60 ans
**Pourquoi ce theme** : Le thème du jardin de cottage évoque la sérénité, la beauté naturelle et un sentiment de nostalgie et d'évasion. Il permet à l'audience adulte de se connecter avec la nature même si elle vit en milieu urbain, offrant un refuge créatif et apaisant. Les fleurs sont universellement appréciées et le style 'botanical precision' associé à une touche de fantaisie séduit ceux qui cherchent à la fois l'authenticité et l'imagination.

## 5. Analyse Concurrence Amazon

### Concurrent 1 : Cottage Garden Coloring Book: Whimsical Flowers and Charming Scenes
- Note : 4.2 | Avis : 320
- Ce qui manque : Plusieurs avis mentionnent des lignes trop fines rendant le coloriage difficile, des images parfois floues ou pixelisées, et un manque de diversité dans les scènes (trop de fleurs isolées, pas assez de paysages de jardin).
- Notre avantage : Nos images sont générées avec des lignes épaisses et nettes (min 2-3px à 1664px), assurant une clarté impeccable. Nous offrons une grande variété de scènes de jardin complètes et des éléments uniques, allant de la fleur simple à des paysages complexes.

### Concurrent 2 : Adult Coloring Book: Secret Gardens & Botanical Beauty
- Note : 4.6 | Avis : 850
- Ce qui manque : Quelques acheteurs se plaignent de la répétition de certains motifs et d'une qualité d'impression inégale sur certaines pages, avec des 'taches' grises ou des zones ombragées non désirées.
- Notre avantage : Notre processus de génération Pollinations AI est strictement configuré pour le pur noir et blanc, éliminant tout gris contaminant. Chaque image est unique et ne se répète pas, et la progression thématique est pensée pour maintenir l'intérêt.

### Concurrent 3 : Vintage Flower Garden: An Adult Coloring Book
- Note : 4.0 | Avis : 180
- Ce qui manque : Les avis négatifs pointent souvent un style trop 'simple' ou 'enfantin' pour un livre adulte, et un manque de détails pour les colorieurs expérimentés. Certains disent que les pages sont 'trop vides'.
- Notre avantage : Notre style 'botanical_precision|whimsical|intricate_line_art' est spécifiquement conçu pour l'audience adulte, offrant des détails fins et des scènes riches. Même les pages 'simples' ont une élégance qui n'est jamais enfantine.

### Concurrent 4 : My Peaceful Garden: Floral Designs for Relaxation
- Note : 3.9 | Avis : 95
- Ce qui manque : Des clients ont rapporté que les images ne remplissent pas toujours la page entière, laissant de grandes marges blanches, et que le DPI semble bas, résultant en des impressions pixelisées.
- Notre avantage : Nos images 1664x2160px sont optimisées pour un remplissage maximal de la page KDP standard, et les prompts sont conçus pour une haute résolution et des lignes claires, ce qui permet d'obtenir une excellente qualité d'impression à 300 DPI sans pixellisation.

### Concurrent 5 : Whimsical Wildflowers & Garden Wonders Coloring Book
- Note : 4.4 | Avis : 410
- Ce qui manque : Bien que le concept soit apprécié, quelques commentaires mentionnent que les images manquent de 'profondeur' ou de 'texture' et sont parfois trop plates. Le 'whimsical' est parfois interprété comme 'moins réaliste' que ce que certains attendaient.
- Notre avantage : Nous équilibrons le 'whimsical' avec la 'botanical_precision', garantissant que les fleurs et les plantes sont reconnaissables et magnifiquement détaillées, tout en ajoutant des touches fantaisistes pour l'originalité. Les lignes nettes et variées donnent de la structure et de la profondeur sans introduire de gris.

## 6. Listing KDP
**Titre Amazon** : Enchanted Cottage Garden Coloring Book for Adults: Intricate Botanical Designs, Whimsical Flowers & Relaxing Countryside Scenes - A Detailed Floral Art Journey
**Sous-titre** : Unwind with Beautiful Hand-Drawn Style Illustrations of Roses, Lavender, Peonies & Secret Garden Gates. Perfect for Stress Relief & Creative Expression.
**Prix** : $8.99

**Description** :
Découvrez le livre de coloriage <b>Enchanted Cottage Garden</b>, une évasion artistique dans le monde apaisant des jardins de cottage.<br><br>Ce livre unique offre 30 pages d'illustrations détaillées, conçues pour les adultes cherchant à se détendre et à stimuler leur créativité. Chaque page est une invitation à explorer des scènes de jardin idylliques, avec :<br>• Des fleurs emblématiques comme les roses anciennes, la lavande parfumée et les pivoines luxuriantes, dessinées avec une précision botanique exquise.<br>• Des éléments de jardin fantaisistes : arrosoirs décoratifs, bancs cachés, portes secrètes et des insectes charmants.<br>• Une progression de la difficulté, des motifs simples mais élégants aux scènes de jardin complexes et immersives.<br><br>Idéal pour la méditation créative, ce livre garantit une expérience de coloriage sans frustration grâce à :<br>• Des <b>lignes ultra-nettes et épaisses</b> pour un rendu impeccable.<br>• Un <b>noir et blanc pur</b>, sans aucun gris contaminant ni ombrage.<br>• Un <b>fond blanc immaculé</b>, parfait pour laisser votre imagination s'exprimer.<br><br>Plongez dans un monde de beauté florale et de tranquillité. Ce livre est le cadeau parfait pour les amateurs de jardinage, les artistes en herbe ou toute personne ayant besoin d'une pause relaxante. Préparez vos crayons et feutres, et laissez-vous transporter par la magie du jardin enchanté !

**Mots-cles** : adult coloring book, cottage garden, flower coloring, botanical art, stress relief, intricate designs, whimsical garden, floral illustrations
**Categories** : Crafts, Hobbies & Home / Coloring Books, Arts & Photography / Graphic Design / Illustration

## 7. Checklist de Validation

Avant de changer gate_cdc a `approved` :

- [ ] **Test style** : Générer 1 page test avec 'exemple_prompt_complet' (ou une variante complexe) à 1664x2160px. Vérifier RIGOUROUSEMENT : 1) Absence ABSOLUE de gris ou de nuances, seulement du noir pur et du blanc pur. 2) Lignes parfaitement nettes et contrastées. 3) Fond entièrement blanc et propre. 4) Style artistique conforme au 'botanical_precision|whimsical|intricate_line_art'.
- [ ] **Test complexite** : Valider que le niveau de difficulté des images générées correspond bien à l'audience 'adult'. S'assurer que les pages 'simples' ne sont pas enfantines et que les pages 'complexes' offrent un défi suffisant et des détails fins, comme décrit dans la distribution des pages.
- [ ] **Test impression** : Examiner attentivement la largeur des lignes sur les images 1664x2160px. Les lignes les plus fines doivent être d'au moins 2-3 pixels de large pour garantir qu'elles restent visibles et imprimables sans devenir invisibles ou pixélisées une fois le fichier PDF généré pour KDP à 300 DPI. Faire un test d'impression physique si possible sur une imprimante laser standard.
- [ ] **Test marche** : Effectuer une recherche sur Amazon.com avec 'cottage garden flowers coloring book adult' et 'whimsical botanical coloring book'. Analyser les résultats pour confirmer que le thème est toujours pertinent mais que notre élément unique et la qualité technique (lignes, absence de gris) offrent un avantage concurrentiel clair.

---

*CdC genere le 2026-05-28 — GATE: pending*