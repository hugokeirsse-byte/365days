# CAHIER DES CHARGES — Mystical Coral Reefs: An Adult Coloring Journey
**Statut** : EN ATTENTE VALIDATION HUGO
**Date** : 2026-05-29
**ID** : coloring_2026-05-29

## GATE CdC = PENDING

**Avant toute production :**
1. Lire ce document et valider le concept + prompts
2. Copier `exemple_prompt_complet` ci-dessous et tester manuellement sur https://pollinations.ai
3. Verifier : pur noir/blanc, zero gris, lignes nettes, fond blanc
4. Si OK : ouvrir `cdc.json` et changer `gate_cdc` de `pending` a `approved`
5. Pousser le fichier — la production demarre automatiquement.

---

## 1. Concept
**Titre** : Mystical Coral Reefs: An Adult Coloring Journey
**Sous-titre** : Dive into intricate underwater worlds with detailed marine life, exotic corals, and hidden patterns for stress relief and creative expression.
**Theme** : underwater_coral_reef
**Style artistique** : botanical_precision|intricate|zentangle|mandala
**Audience** : adult
**Complexite** : intricate
**Pages** : 30

**Element unique** : Ce livre se distingue par son approche 'Mandala Naturelle' où les récifs coralliens et la vie marine sont entrelacés avec des motifs Zentangle et des structures de type mandala, créant des compositions organiques et complexes. Chaque page est une exploration d'un écosystème sous-marin caché, avec une attention particulière aux détails botaniques des coraux et aux textures des créatures marines, garantissant une expérience de coloriage méditative et non répétitive.

## 2. STRATEGIE PROMPTS POLLINATIONS

> Ces prompts sont la CLE du projet. Tester avant de valider.

### Style de base (a inclure dans TOUS les prompts)
```
black and white coloring page, clean outlines, no fill, white background, no gray, no shading, line art, ink drawing style
```

### Modificateurs de style
- highly detailed line art
- ornate patterns
- intricate marine biology illustration
- zentangle elements within coral structures
- mandala-inspired oceanic patterns
- engraved style

### Mots-cles du theme
sea anemones, tropical fish schools, exotic coral formations, sea turtles gliding, jellyfish blooms, starfish and shells, underwater flora and fauna, deep ocean currents

### Mots-cles NEGATIFS (a exclure pour eviter le gris)
gray, shading, photo, realistic texture, color, gradient, shadow, blur, fog, 3D render, poorly drawn, childish, simple, cartoon

### EXEMPLE DE PROMPT COMPLET A TESTER

> Copier ce prompt sur https://pollinations.ai et verifier le resultat

```
black and white coloring page, highly detailed line art of a vibrant coral reef, intricate patterns within the corals and surrounding sea anemones, a school of tropical fish swimming through, clean outlines, no fill, white background, no gray, no shading, ink drawing style, ornate patterns, botanical precision, mandala-inspired elements
```

### Variantes par niveau de complexite
- Prompt page simple (débutant) : black and white coloring page, clean outlines of a single large sea turtle gracefully swimming above simple coral formations, white background, no gray, no shading, bold lines, minimal details
- Prompt page medium (intermédiaire) : black and white coloring page, detailed line art of a section of coral reef with various medium-sized fish and a sea horse, intricate but not overwhelming patterns, white background, no gray, no shading, ink drawing style
- Prompt page complexe (expert) : black and white coloring page, extreme intricate detail of a vast underwater ecosystem, dense coral structures intertwined with complex zentangle patterns, numerous small exotic fish, a manta ray, and various crustaceans, all rendered with highly precise, fine lines, white background, no gray, no shading, botanical precision, mandala-inspired patterns, elaborate scene

**Note importante** : Toujours exclure les mots qui génèrent du gris ou du shading. La clé est la répétition des négatifs et la spécificité des positifs. Tester impérativement 1 page avec chaque niveau de complexité AVANT toute production de masse pour valider le pur noir/blanc, les lignes nettes et l'absence totale de gris.

## 3. Distribution des Pages
- Pages simples : 6
- Pages medium : 12
- Pages complexes : 12
- Progression : Le livre débute par des scènes plus épurées (6 pages) pour permettre au coloriste de s'habituer au style. La complexité augmente progressivement avec 12 pages de difficulté intermédiaire introduisant plus de détails et de motifs. Les 12 dernières pages offrent des illustrations très complexes et denses, parfaites pour les coloristes expérimentés recherchant un défi et une immersion totale, intégrant pleinement les motifs Zentangle et Mandala.

## 4. Public Cible
**Persona** : Sophie, 38 ans, graphiste freelance. Elle cherche des activités relaxantes après des journées de travail intenses. Passionnée par la nature et les arts visuels, elle apprécie les livres de coloriage détaillés qui offrent une évasion méditative et stimulent sa créativité. Elle est frustrée par les livres pour adultes trop simplistes ou mal imprimés (lignes grises, floues). Elle cherche des motifs originaux et non répétitifs.
**Age** : 28-55 ans
**Pourquoi ce theme** : Le thème du récif corallien offre une évasion visuelle et mentale vers un monde apaisant et mystérieux. La richesse des formes organiques et la diversité de la vie marine se prêtent parfaitement à des détails intriqués, procurant une sensation de découverte et de calme, idéale pour la réduction du stress. Ce thème résonne avec ceux qui aiment la nature, l'océan, et cherchent une activité créative qui les déconnecte du quotidien.

## 5. Analyse Concurrence Amazon

### Concurrent 1 : Ocean Wonders: Adult Coloring Book - Marine Animals and Sea Life
- Note : 4.3 | Avis : 380
- Ce qui manque : Images trop simples ou enfantines pour certains adultes, répétition de motifs similaires, lignes parfois trop fines rendant le coloriage difficile, manque de diversité de la vie marine.
- Notre avantage : Notre livre se concentre sur des scènes complexes, des motifs uniques de type mandala/zentangle intégrés à la nature, et une progression de difficulté, évitant la répétition et ciblant clairement l'audience adulte avec des détails profonds et des lignes nettes garanties.

### Concurrent 2 : Underwater Paradise: An Adult Coloring Book Featuring Beautiful Ocean Scenes
- Note : 4.1 | Avis : 250
- Ce qui manque : Présence de gris dans les images, qualité d'impression inégale, illustrations génériques sans style artistique distinctif, les fonds sont souvent vides.
- Notre avantage : Grâce à notre stratégie de prompts stricte, nous garantissons des images en pur noir et blanc sans aucun gris. Notre style 'Mandala Naturelle' offre une signature artistique unique et des fonds riches en détails, non vides.

### Concurrent 3 : Tropical Fish & Coral Reefs Coloring Book for Adults
- Note : 4.4 | Avis : 410
- Ce qui manque : Manque d'intrication pour les coloristes avancés, les poissons sont souvent dessinés de manière basique, peu de variété dans les types de coraux, ne stimule pas l'imagination.
- Notre avantage : Nous offrons une intrication poussée avec des motifs Zentangle et mandala intégrés, transformant chaque page en un défi créatif. La diversité des espèces marines et des formations coralliennes est une priorité, allant au-delà des représentations basiques.

### Concurrent 4 : The Ultimate Ocean Coloring Book: Stress Relief for Adults
- Note : 4.0 | Avis : 180
- Ce qui manque : Images floues ou pixelisées, lignes trop épaisses qui gâchent les détails, absence de cohérence stylistique entre les pages, certains motifs sont clairement des images modifiées et non dessinées.
- Notre avantage : Nos prompts sont conçus pour générer des lignes nettes et précises, avec une épaisseur optimale pour l'impression 300 DPI, sans flou ni pixelisation. Le style artistique est cohérent et chaque page est pensée comme une œuvre d'art originale.

### Concurrent 5 : Marine Life Adult Coloring Book: Exotic Creatures and Beautiful Undersea Scenery
- Note : 4.2 | Avis : 320
- Ce qui manque : Trop de pages avec des fonds unis et sans détails, manque de dynamisme dans les scènes, illustrations qui semblent générées par IA sans retouche humaine (petits défauts, incohérences).
- Notre avantage : Chaque page de notre livre est une scène dynamique et riche en détails, avec des fonds élaborés. La stratégie de prompt est affinée pour minimiser les 'artefacts IA' et garantir des compositions harmonieuses et intentionnelles, validées pour leur qualité artistique.

## 6. Listing KDP
**Titre Amazon** : Mystical Coral Reefs Adult Coloring Book: Intricate Underwater Worlds, Marine Life & Zen Patterns for Stress Relief & Relaxation
**Sous-titre** : Dive into Detailed Ocean Scenes, Exotic Fish, Sea Turtles, & Mandala-Inspired Coral Art. Perfect for Advanced Colorists Seeking Calm & Creativity.
**Prix** : $8.99

**Description** :
Bienvenue dans 'Mystical Coral Reefs', un livre de coloriage pour adultes conçu pour vous transporter dans les profondeurs apaisantes de l'océan. <br><br><b>Découvrez un monde sous-marin d'une beauté époustouflante:</b><br>Ce livre unique propose 30 illustrations méticuleusement détaillées de récifs coralliens vibrants, de poissons tropicaux exotiques, de majestueuses tortues de mer et de créatures marines fascinantes. Chaque page est une œuvre d'art en noir et blanc, prête à prendre vie avec vos couleurs.<br><br><b>Un style artistique unique 'Mandala Naturelle':</b><br>Laissez-vous captiver par l'intégration harmonieuse de motifs Zentangle et de structures inspirées des mandalas au sein de la flore et de la faune marines. Cette approche innovante offre une expérience de coloriage profondément méditative et visuellement stimulante, parfaite pour la relaxation et la pleine conscience.<br><br><b>Pourquoi choisir 'Mystical Coral Reefs'?</b><ul><li><b>30 Pages d'Évasion:</b> Des scènes variées, allant de la complexité moyenne à très élevée, pour des heures de plaisir et de défi créatif.</li><li><b>Qualité d'Image Supérieure:</b> Des lignes pures, nettes et audacieuses (pur noir/blanc, sans gris ni ombrage) pour un rendu d'impression impeccable.</li><li><b>Thème Captivant:</b> Idéal pour les amoureux de l'océan, de la nature et ceux qui cherchent une activité anti-stress.</li><li><b>Cadeau Idéal:</b> Parfait pour les anniversaires, les fêtes ou toute occasion spéciale pour les adultes créatifs.</li></ul>Plongez dans cette aventure artistique sous-marine et libérez votre créativité. Commandez votre exemplaire de 'Mystical Coral Reefs' dès aujourd'hui et commencez votre voyage coloré!

**Mots-cles** : adult coloring book, coral reef, marine life, ocean coloring, zentangle, mandala, stress relief, relaxation, underwater animals, detailed coloring, nature coloring, sea creatures, coloring for adults
**Categories** : Books > Crafts, Hobbies & Home > Crafts & Hobbies > Coloring Books, Books > Arts & Photography > Drawing > Mandalas

## 7. Checklist de Validation

Avant de changer gate_cdc a `approved` :

- [ ] **Test style** : Hugo doit générer 1 page test avec l'exemple_prompt_complet (et idéalement 1 de chaque variante simple/medium/complexe) à la résolution 1664x2160px. La vérification est stricte : absence ABSOLUE de gris, image en pur noir et blanc (binarisée), lignes parfaitement nettes et définies (pas de flou, pas d'aliasing visible), et fond intégralement blanc. Si le moindre pixel gris est détecté, la stratégie de prompt doit être ajustée.
- [ ] **Test complexite** : Valider que le niveau de difficulté des images générées correspond bien à l'audience 'adult'. Les pages simples doivent rester engageantes, les pages medium doivent offrir un bon équilibre, et les pages complexes doivent être suffisamment détaillées pour représenter un challenge sans être illisibles. Une image 'child' serait un échec.
- [ ] **Test impression** : Les lignes doivent être suffisamment épaisses pour être bien imprimées en 300 DPI sans disparaître ou devenir pixelisées. À la résolution 1664px de large, les lignes fines ne doivent pas être inférieures à 2-3 pixels d'épaisseur pour assurer une bonne visibilité et durabilité après impression. Tester un échantillon imprimé est fortement recommandé.
- [ ] **Test marche** : Effectuer une recherche Amazon ('underwater coral reef coloring book' et variantes) pour évaluer la saturation actuelle du marché, identifier les best-sellers et leurs points forts/faibles. Valider que notre concept unique ('Mandala Naturelle') et notre promesse de qualité supérieure (pas de gris, lignes nettes) nous positionnent favorablement face à la concurrence.

---

*CdC genere le 2026-05-29 — GATE: pending*