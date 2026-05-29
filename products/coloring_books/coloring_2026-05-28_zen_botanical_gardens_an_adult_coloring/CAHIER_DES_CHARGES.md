# CAHIER DES CHARGES — Zen Botanical Gardens: An Adult Coloring Journey
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
**Titre** : Zen Botanical Gardens: An Adult Coloring Journey
**Sous-titre** : Discover Tranquility with Intricate Flora and Fauna Designs – A Stress-Relief Coloring Book for Grown-Ups
**Theme** : botanical_garden
**Style artistique** : intricate botanical precision|zentangle|mandala
**Audience** : adult
**Complexite** : intricate
**Pages** : 30

**Element unique** : Ce livre se distingue par son alliance unique de la précision botanique et de motifs relaxants inspirés du Zentangle et du Mandala, créant un voyage artistique méditatif. Chaque illustration est conçue pour être purement en noir et blanc, avec des lignes nettes et aucun gris contaminant, garantissant une expérience de coloriage immaculée et professionnelle. Les pages présentent une progression de complexité, invitant à la découverte de jardins luxuriants, de fleurs exotiques, de feuillages détaillés et d'animaux cachés, offrant une immersion totale et une évasion créative sans la frustration des images de mauvaise qualité.

## 2. STRATEGIE PROMPTS POLLINATIONS

> Ces prompts sont la CLE du projet. Tester avant de valider.

### Style de base (a inclure dans TOUS les prompts)
```
black and white coloring page, clean outlines, no fill, white background, no gray, no shading, line art, high contrast
```

### Modificateurs de style
- intricate details
- fine line art
- zentangle patterns
- mandala elements
- botanical precision
- hand-drawn aesthetic

### Mots-cles du theme
tropical plants, exotic flowers, lush foliage, secret garden, water features, hidden creatures, garden path, vines, succulents

### Mots-cles NEGATIFS (a exclure pour eviter le gris)
gray, shading, photo, realistic texture, color, gradient, shadow, blur, pixelated, 3d, render, photograph, painting, low detail, simple

### EXEMPLE DE PROMPT COMPLET A TESTER

> Copier ce prompt sur https://pollinations.ai et verifier le resultat

```
black and white coloring page, intricate details, fine line art, clean outlines, no fill, white background, no gray, no shading, high contrast, lush tropical botanical garden scene with exotic flowers like orchids and bromeliads, winding path, hidden hummingbird, zentangle patterns on leaves, mandala elements in flower centers, hand-drawn aesthetic
```

### Variantes par niveau de complexite
- Prompt page simple (débutant) : black and white coloring page, clean outlines, no fill, white background, no gray, no shading, bold lines, simple botanical scene with a large single lotus flower, some surrounding leaves, clear boundaries.
- Prompt page medium (intermédiaire) : black and white coloring page, clean outlines, no fill, white background, no gray, no shading, medium intricate details, fine line art, a section of a botanical garden with various flowering plants, a small butterfly, subtle zentangle motifs on petals.
- Prompt page complexe (expert) : black and white coloring page, intricate details, fine line art, clean outlines, no fill, white background, no gray, no shading, high contrast, full page, highly detailed secret garden scene with overflowing vines, exotic birds, hidden intricate patterns within leaves and flowers, tiny insects, delicate mandala elements woven into the foliage.

**Note importante** : Toujours exclure les mots qui génèrent du gris ou du shading. La clé est d'utiliser 'no gray', 'no shading', 'white background', 'black and white coloring page', 'clean outlines', 'no fill'. Tester 1 page avec l'exemple_prompt_complet et valider par Hugo AVANT toute production en masse pour s'assurer de l'absence totale de gris.

## 3. Distribution des Pages
- Pages simples : 8
- Pages medium : 14
- Pages complexes : 8
- Progression : Le livre débute avec des illustrations plus simples, idéales pour se familiariser avec le style et les outils de coloriage, offrant une entrée en matière douce. La difficulté augmente progressivement avec les pages medium, introduisant plus de détails et de motifs. Les dernières pages sont les plus complexes, présentant des scènes riches et très détaillées, parfaites pour les coloristes expérimentés cherchant un défi et une immersion profonde, créant un sentiment d'accomplissement au fil du livre.

## 4. Public Cible
**Persona** : Sarah, 38 ans, graphiste freelance. Elle cherche une activité relaxante et créative pour décompresser après une journée de travail stressante. Amoureuse de la nature et du design, elle apprécie les livres de coloriage aux illustrations détaillées et élégantes. Elle est frustrée par les livres de mauvaise qualité avec des gris ou des lignes floues. Elle utilise le coloriage comme une forme de méditation et pour stimuler sa créativité.
**Age** : 25-65 ans
**Pourquoi ce theme** : Le thème du jardin botanique résonne avec cette audience par son lien avec la nature, la beauté et la tranquillité. Il offre une évasion visuelle et une opportunité de se connecter avec le monde végétal, connu pour ses vertus apaisantes. Les motifs complexes de style Zentangle/Mandala ajoutent une dimension méditative, aidant à la concentration et à la réduction du stress, ce qui est très recherché par les adultes actifs.

## 5. Analyse Concurrence Amazon

### Concurrent 1 : Botanical Wonderland Coloring Book for Adults
- Note : 4.4 | Avis : 720
- Ce qui manque : Certains avis mentionnent que les illustrations sont parfois trop simples ou répétitives, et que le papier est trop fin pour les feutres. Quelques plaintes sur des images un peu floues ou avec des zones grises non intentionnelles.
- Notre avantage : Nos images sont garanties 100% noir et blanc pur, avec des lignes nettes et une variété de complexité. Nous recommandons l'impression sur un papier plus épais ou l'utilisation de crayons de couleur pour une meilleure expérience, ou de se procurer la version numérique pour imprimer sur le papier de son choix.

### Concurrent 2 : Secret Garden: An Inky Treasure Hunt and Coloring Book
- Note : 4.7 | Avis : 15000
- Ce qui manque : Bien que très populaire, certains utilisateurs trouvent que le style de Johanna Basford est parfois trop chargé et manque d'espaces pour laisser libre cours à l'imagination. D'autres déplorent le fait que les images soient recto-verso, rendant l'utilisation de feutres difficile.
- Notre avantage : Notre livre propose des designs complexes mais avec une meilleure gestion de l'espace, permettant à l'utilisateur de s'approprier l'œuvre. Toutes nos pages sont imprimées en recto seul pour éviter tout problème de transperçage, et chaque page offre une nouvelle scène unique.

### Concurrent 3 : Beautiful Botanicals: A Flower and Plant Coloring Book for Adults
- Note : 4.2 | Avis : 380
- Ce qui manque : Plusieurs commentaires indiquent que les dessins manquent de finesse, les lignes sont épaisses et le style est jugé enfantin pour un livre 'adulte'. Des images générées par IA avec des artefacts ou des zones légèrement grisées sont parfois signalées.
- Notre avantage : Nous nous concentrons sur la 'botanical precision' avec des lignes fines et détaillées, un style clairement adulte, et une validation rigoureuse pour garantir l'absence totale de gris ou d'artefacts, assurant une qualité d'image supérieure pour une expérience de coloriage gratifiante.

### Concurrent 4 : Tropical Botanical Gardens: Adult Coloring Book
- Note : 4.3 | Avis : 250
- Ce qui manque : Certains acheteurs trouvent que la variété des plantes est limitée et que les pages se ressemblent un peu. La qualité d'impression est décrite comme inégale, avec des noirs parfois pâles.
- Notre avantage : Notre cahier des charges inclut une grande diversité de plantes tropicales et exotiques, avec des éléments uniques (animaux cachés, éléments architecturaux de jardin) pour chaque page. Nous mettons l'accent sur un contraste élevé et des noirs profonds pour une impression impeccable.

### Concurrent 5 : Nature's Elegance: Intricate Botanical Designs Coloring Book
- Note : 4.6 | Avis : 610
- Ce qui manque : Les avis négatifs pointent souvent du doigt des illustrations qui semblent avoir été 'étirées' ou mal proportionnées, et un manque d'originalité dans les compositions. Parfois, le fond n'est pas parfaitement blanc, laissant des traces de gris clair.
- Notre avantage : Nous garantissons des proportions naturelles et des compositions originales grâce à des prompts précis. Notre processus de validation strict assure un fond blanc pur et des lignes parfaitement nettes, éliminant tout risque de gris ou d'images mal formatées.

## 6. Listing KDP
**Titre Amazon** : Zen Botanical Gardens: Adult Coloring Book – Intricate Flora & Fauna Designs for Relaxation, Stress Relief & Creativity | A Detailed Line Art Coloring Journey
**Sous-titre** : Mindful Coloring with Exotic Flowers, Lush Foliage & Secret Garden Scenes | High-Quality, Pure Black & White Illustrations for Adults
**Prix** : $9.99

**Description** :
Découvrez la sérénité et la beauté de la nature avec <b>Zen Botanical Gardens</b>, votre nouveau livre de coloriage adulte préféré. Plongez dans un monde luxuriant de fleurs exotiques, de feuillages complexes et de jardins secrets, méticuleusement conçus pour offrir des heures de détente et d'évasion.<br><br>🎨 <b>Illustrations d'une Qualité Exceptionnelle :</b> Chaque page est une œuvre d'art unique, garantie <b>purement en noir et blanc</b>, avec des lignes nettes et précises. Dites adieu aux gris indésirables et aux images floues !<br>🌸 <b>Thème Botanique Envoûtant :</b> Explorez 30 scènes détaillées inspirées des plus beaux jardins botaniques, mêlant la précision florale à des motifs apaisants de style Zentangle et Mandala.<br>🧘‍♀️ <b>Parfait pour la Relaxation & la Méditation :</b> Le coloriage est une forme prouvée de réduction du stress. Laissez votre esprit vagabonder et retrouvez votre calme intérieur en donnant vie à ces magnifiques illustrations.<br>✨ <b>Progression de la Complexité :</b> Que vous soyez débutant ou coloriste expérimenté, ce livre offre un défi adapté avec des pages allant du simple au très complexe.<br>🎁 <b>Le Cadeau Idéal :</b> Offrez le cadeau de la créativité et de la relaxation à vos amis, votre famille ou à vous-même.<br><br>Chaque illustration est imprimée sur une seule face pour éviter les bavures et vous permettre d'utiliser une variété de médiums. Préparez vos crayons de couleur, feutres ou pastels et commencez votre voyage artistique dès aujourd'hui !

**Mots-cles** : adult coloring book, botanical garden, zentangle coloring, mandala flowers, stress relief, intricate designs, nature coloring
**Categories** : Books > Arts & Photography > Drawing > Coloring Books, Books > Self-Help > Stress Management

## 7. Checklist de Validation

Avant de changer gate_cdc a `approved` :

- [ ] **Test style** : Générer 1 page test avec 'exemple_prompt_complet'. Vérifier visuellement et numériquement (avec un outil d'analyse d'image si possible) : pur noir/blanc sans aucun niveau de gris (RVB 0,0,0 et 255,255,255 uniquement), lignes parfaitement nettes, fond blanc immaculé.
- [ ] **Test complexite** : L'image générée correspond-elle au niveau de difficulté 'intricate' attendu pour une audience adulte ? Les détails sont-ils suffisants pour maintenir l'intérêt sans être surchargés ?
- [ ] **Test impression** : Les lignes sont-elles suffisamment épaisses et bien définies pour une impression laser à 300 DPI ? À la résolution de 1664px de large, les lignes les plus fines doivent être au minimum de 2-3 pixels d'épaisseur pour garantir une bonne restitution sans cassure ni disparition à l'impression.
- [ ] **Test marche** : Effectuer une recherche Amazon ('botanical garden coloring book adult', 'zentangle botanical coloring book'). Le concept et le style sont-ils suffisamment distincts pour se démarquer des best-sellers actuels ? Y a-t-il une demande non satisfaite pour des livres de haute qualité sans gris ?

---

*CdC genere le 2026-05-28 — GATE: pending*