# Modèles économiques annexes — Mirabilia Éditions
*Analyse stratégique, mai 2026*

> Contexte : pipeline GitHub Actions + IA gratuites (Pollinations, Gemini) + pilotage Android, zéro budget, contrainte d'autopilote ≥ 80%.

---

## Idée N°1 — Livres KDP multilingues et multi-niches

**Pitch en une phrase** : Répliquer le pipeline exact du livre plantes médicinales sur d'autres niches à fort volume Amazon (cristaux, constellations, champignons, oiseaux, recettes ancestrales) et dans d'autres langues (anglais, espagnol), sans rien reconstruire.

**Modèle économique** : Royalties KDP (35-70% selon le prix). Vente directe, pas d'abonnement.

**Plateforme de vente** : Amazon KDP (disponible dans tous les marchés mondiaux depuis le même compte).

**Setup nécessaire** (≤ 2 semaines) :
1. Forker le repo existant, modifier `meta_livre.py` (titre, niche, palette, mots-clés ISBN).
2. Générer de nouveaux `prompts.py` via Gemini (brief copy-paste existant, swap "plantes" → "champignons" ou autre).
3. Lancer les GitHub Actions : robot images + juge IA → sélectionner les 100 meilleures → book cover via Canva mobile.
4. Pour la version anglaise : Gemini traduit le corpus texte, même pipeline.

**Briques du pipeline réutilisées** : Robot images IA (Pollinations), Juge IA (Gemini Vision), Config centralisée (`meta_livre.py`), Gemini rédacteur — **tout le pipeline, fork complet**.

**Effort opérationnel mensuel après setup** : ~1h/mois (vérifier les ventes, republier si changement de règles KDP).

**Revenu réaliste à 6 mois** :
- 1 livre anglophone bien ciblé : 10-50 ventes/mois × 3-5 € royalty = **30-250 €/mois**
- Avec 4-5 titres en portefeuille (niches + langues) : **150-800 €/mois**
- Comparable : les "low-content book" publishers KDP actifs avec 5-10 titres reportent 200-600 €/mois en passif stable.

**Risques principaux** :
- KDP peut modifier ses règles sur le contenu IA généré (risque réel, surveiller).
- La concurrence est haute sur les niches génériques en anglais. Cibler des niches précises (ex. "plantes médicinales bretonnes", "champignons de France") réduit ce risque.
- Les cover mal foutus tuent les ventes : seul vrai filtre humain nécessaire.

**Verdict honnête** : **À lancer en priorité absolue.** C'est le clone parfait de ce qui existe déjà. Coût marginal quasi nul. La version anglophone d'un livre de plantes médicinales a un marché 8x plus grand que le marché français. La niche "champignons comestibles de France" est peu couverte en livres-objets KDP de qualité.

---

## Idée N°2 — Designs print-on-demand (Redbubble / Society6 / Displate)

**Pitch en une phrase** : Alimenter des boutiques Redbubble/Society6 avec les illustrations botaniques générées par le robot d'images, vendues en posters, T-shirts, tote bags, coussins — sans jamais toucher à une imprimante.

**Modèle économique** : Commission sur vente (Redbubble verse 20% du prix de vente sur chaque produit vendu, pas d'avance, pas de coût fixe).

**Plateforme de vente** : Redbubble (priorité : plus facile à indexer dans Google Images), Society6 (posters premium), Displate (métal prints, niche déco).

**Setup nécessaire** (≤ 2 semaines) :
1. Sélectionner 50-100 des meilleures images issues du juge IA (déjà scorées).
2. Les recadrer/exporter en 3000×3000px minimum (Canva mobile suffit).
3. Créer compte Redbubble, uploader manuellement ou par lot via le navigateur mobile (Redbubble n'a pas d'API publique, mais l'upload est simple depuis mobile).
4. Optimiser les titres/tags avec des mots-clés longs (ex. "botanical illustration chamomile art print vintage style").

**Briques du pipeline réutilisées** : Robot images IA (Pollinations), Juge IA (Gemini Vision pour sélectionner les designs les plus propres), Gemini rédacteur (pour les descriptions/tags de chaque produit en masse).

**Effort opérationnel mensuel après setup** : ~2h/mois (uploader 20-30 nouveaux designs générés en batch, regarder les stats).

**Revenu réaliste à 6 mois** :
- Avec 100 designs actifs, taux de conversion typique Redbubble : 1-3 ventes/design/mois sur les tops.
- Réaliste : 15-40 ventes/mois × 4-8 € commission = **60-320 €/mois**
- Les boutiques de botanical art sur Redbubble avec 200+ designs reportent 200-500 €/mois dans les forums dédiés.
- Displate est plus rentable par vente (commission ~30%) mais volume plus bas.

**Risques principaux** :
- Redbubble peut déréférencer les comptes avec trop de contenu IA perçu comme du spam visuel. Garder un niveau de qualité élevé (le juge IA sert exactement à ça).
- Saturation sur les niches génériques (fleurs abstraites, mandalas). Botanical illustration vintage est moins saturé.
- Long tail : les premières ventes mettent 2-4 mois à arriver.

**Verdict honnête** : **À lancer en priorité, mais en parallèle du KDP.** Setup léger (3-4 jours), coût zéro, aucune gestion client. Le vrai problème est que les revenus sont modestes et plafonnent sans diversification continue de designs. Pas un substitut au KDP, mais un excellent complément passif qui exploite le même stock d'images.

---

## Idée N°3 — Newsletter automatisée phytothérapie / santé naturelle (Beehiiv)

**Pitch en une phrase** : Une newsletter hebdomadaire en français sur les plantes médicinales — "La plante de la semaine" — rédigée à 80% par Gemini à partir du corpus `Info.py`, avec des liens d'affiliation Amazon sur les produits liés (huiles essentielles, tisanes, compléments).

**Modèle économique** : Hybride — affiliation Amazon (3-5% du panier), Beehiiv Boost (€0,50-1,50 par abonné référé à d'autres newsletters partenaires), et optionnellement une offre payante à €5/mois au-delà de 1000 abonnés.

**Plateforme de vente** : Beehiiv (free tier : 2500 abonnés, 0 € jusqu'à ce seuil). Amazon Partenaires pour les liens affiliés.

**Setup nécessaire** (≤ 2 semaines) :
1. Créer compte Beehiiv + compte Amazon Partenaires.
2. Briefer Gemini pour générer 52 éditions type (une par semaine/an) à partir du corpus `Info.py`, en format newsletter (intro, focus plante, recette/usage, produit du mois avec lien affilié).
3. Pré-charger 8-12 éditions dans la file d'attente Beehiiv (envoi programmé automatique).
4. Landing page simple Beehiiv pour capter les abonnés (formulaire embeddable).
5. Partager le lien une fois dans des groupes Facebook/Reddit phytothérapie → croissance organique lente mais constante.

**Briques du pipeline réutilisées** : Corpus `Info.py` (contenu déjà rédigé), Gemini rédacteur (reformatage newsletter), Robot images (illustrations botaniques pour enrichir les éditions).

**Effort opérationnel mensuel après setup** : ~2h/mois (relire et approuver les 4 éditions pré-générées, corriger les erreurs potentielles de Gemini sur les contre-indications médicales — critique pour la responsabilité légale).

**Revenu réaliste à 6 mois** :
- 300-600 abonnés réalistes sans budget pub sur une niche française de niche.
- Affiliation Amazon : 20-30 clics/édition × 5% × panier moyen €30 = ~15-25 €/édition = **60-100 €/mois**
- Beehiiv Boost : faible au début, €5-20/mois.
- Total réaliste à 6 mois : **70-150 €/mois**. Pas spectaculaire mais entièrement passif.

**Risques principaux** :
- **Risque légal fort** : tout contenu de santé naturelle en France doit éviter les allégations thérapeutiques sans nuances. Gemini peut halluciner des dosages ou contre-indications erronés. La relecture humaine rapide est non-négociable.
- Beehiiv peut modifier ses conditions de Boost.
- La croissance est lente sans budget pub. 300 abonnés en 6 mois est optimiste sans une stratégie de distribution active.

**Verdict honnête** : **Idée moyenne mais cohérente.** La valeur principale est de transformer le corpus `Info.py` en actif distribué (chaque édition peut être indexée par Google). Ce n'est pas une machine à revenus rapides, mais c'est un asset qui prend de la valeur lentement. À lancer seulement APRÈS les idées N°1 et N°2.

---

## Idée N°4 — Vente de packs de prompts thématiques (Gumroad / Etsy)

**Pitch en une phrase** : Vendre des packs de 200-500 prompts IA ultra-spécialisés (illustration botanique vintage, art de livres d'enfants, labels de produits artisanaux, affiche rétro naturalia) à des créateurs et petits entrepreneurs qui ne savent pas prompter efficacement.

**Modèle économique** : Vente directe de fichiers numériques (PDF ou TXT). Pas d'abonnement, pas de service.

**Plateforme de vente** : Gumroad (0 € fixe, 10% de commission), Etsy (Digital Downloads, €0,20 par listing + 6,5% par vente), ou les deux.

**Setup nécessaire** (≤ 2 semaines) :
1. Choisir 3-4 niches précises (botanical illustration, labels épicerie fine, affiche motivationnelle naturelle, papier peint cottagecore).
2. Briefer Gemini pour générer 300-500 prompts variés par niche avec des variables (style, période, couleur dominante, format).
3. Organiser en PDF bien présenté (Canva mobile, template simple).
4. Créer les listings Gumroad/Etsy avec des aperçus visuels générés par le robot images lui-même.
5. Pinterest : épingler 10-15 images-teaser par semaine (Gemini peut générer les descriptions de pins).

**Briques du pipeline réutilisées** : Gemini rédacteur (génération des prompts en masse), Robot images IA (générer des exemples visuels pour les previews), Config centralisée (un template de fiche produit réplicable).

**Effort opérationnel mensuel après setup** : ~1h/mois (regarder les ventes, répondre aux rares questions, uploader de nouveaux packs occasionnellement).

**Revenu réaliste à 6 mois** :
- Comparable Etsy/Gumroad : les packs de prompts spécialisés (non-génériques) vendent 10-50 unités/mois à €7-15 l'unité.
- Avec 3 packs actifs, scénario médian : 25 ventes × €9 = **225 €/mois**
- Scénario optimiste (bon SEO Etsy + Pinterest) : **400-600 €/mois**
- Le marché se sature vite sur les prompts génériques. La niche botanical/naturalia est encore peu couverte.

**Risques principaux** :
- Saturation rapide : le marché des prompts a explosé en 2023-2024 et beaucoup de vendeurs génériques font baisser les prix.
- Différenciation difficile sans visuels de qualité (les previews sont critiques pour vendre sur Etsy).
- Etsy peut dépublier les listings jugés "faible valeur" si les avis sont mauvais.

**Verdict honnête** : **Bonne idée à condition d'hyper-spécialiser.** Un pack "500 prompts pour illustrations botaniques façon Köhler's Medizinal-Pflanzen" ciblant les créateurs de contenus santé/bien-être est différenciant. Un pack "1000 prompts généraux Midjourney" ne vend plus. La clé est la niche + les previews visuels. Setup rapide, effort minimal après.

---

## Idée N°5 — Kit "Lancez votre livre KDP en 30 jours" (Gumroad)

**Pitch en une phrase** : Vendre le pipeline lui-même sous forme de kit documenté (templates GitHub, fichiers de config commentés, briefings Gemini, guide étape par étape) aux créateurs qui veulent lancer un livre IA sur KDP mais ne savent pas coder.

**Modèle économique** : Vente directe de produit numérique (pack ZIP + PDF guide). Optionnellement : version premium avec accès à un repo template GitHub.

**Plateforme de vente** : Gumroad (primary), eventuellement un site GitHub Pages comme vitrine.

**Setup nécessaire** (≤ 2 semaines) :
1. Documenter le pipeline existant (Gemini peut rédiger 80% du guide depuis les fichiers existants).
2. Créer un repo template GitHub public "mirabilia-kdp-starter" avec `meta_livre.py`, les workflows GitHub Actions, et un `GUIDE.md` illustré.
3. Rédiger le PDF de vente (30 pages max, Canva mobile, screenshots d'Android).
4. Créer le listing Gumroad avec une page de vente claire (Gemini rédige, tu valides).

**Briques du pipeline réutilisées** : Config centralisée (le produit vendu), GitHub Actions (démo dans le guide), Gemini rédacteur (documentation et copywriting).

**Effort opérationnel mensuel après setup** : ~30min/mois (répondre à 2-3 emails de clients, mettre à jour si KDP change ses règles).

**Revenu réaliste à 6 mois** :
- Marché cible : créateurs KDP francophones qui cherchent à automatiser. Petit marché mais acheteur.
- Prix réaliste : €29-49 pour le kit complet.
- Comparable : les "make money with KDP" guides vendent 5-30 copies/mois sur Gumroad selon la crédibilité de l'auteur.
- Avec un livre KDP publié et visible comme preuve sociale : 10-20 ventes/mois × €39 = **390-780 €/mois** en scénario optimiste.
- Réaliste sans promotion active : **100-250 €/mois**.

**Risques principaux** :
- Crédibilité : sans preuve que le pipeline fonctionne (livre publié, ventes réelles), personne n'achète.
- Ce modèle ne peut démarrer qu'APRÈS que le livre N°1 soit publié et génère des ventes visibles.
- Risque de copie : le repo template est public, quelqu'un peut le prendre sans payer. Atténuable en vendant la documentation et l'accompagnement, pas juste le code.

**Verdict honnête** : **Idée solide mais dépendante du timing.** Elle devient excellente dès que le livre N°1 est publié avec des ventes prouvées. C'est du "sell the shovels during a gold rush" — vendre l'outil plutôt que le produit. À lancer en mois 3-4, pas dès le départ.

---

## Idée N°6 — Datasets structurés à vendre (Gumroad / Hugging Face / Ko-fi)

**Pitch en une phrase** : Monétiser les bases de données déjà construites (365 plantes médicinales avec métadonnées riches, et futures bases similaires) en les vendant comme datasets à des développeurs d'apps santé, des chercheurs, ou des créateurs de contenu.

**Modèle économique** : Vente directe de fichier numérique (JSON, CSV, SQLite). Prix unique, pas d'abonnement.

**Plateforme de vente** : Gumroad (B2C), Ko-fi (B2C alternatif), ou Hugging Face Datasets (gratuit mais avec page de donation). Pour les acheteurs pro : invoice directe via Stripe.

**Setup nécessaire** (≤ 1 semaine) :
1. Exporter `Data.py` et `Info.py` en JSON/CSV bien formatés + documentation des champs.
2. Créer un listing Gumroad avec aperçu (5-10 entrées en preview).
3. Déposer une version limitée sur Hugging Face pour la visibilité/crédibilité.
4. Rédiger une description ciblant les développeurs (Gemini rédige).

**Briques du pipeline réutilisées** : Le corpus `Data.py` / `Info.py` (déjà produit), Gemini rédacteur (documentation des champs, description marketing).

**Effort opérationnel mensuel après setup** : ~0h/mois (vente entièrement automatique une fois listé). Mise à jour du dataset 1x/an max.

**Revenu réaliste à 6 mois** :
- Marché étroit : développeurs d'apps wellness, étudiants en NLP, créateurs de chatbots santé.
- Prix : €15-40 pour un dataset de 365 entrées richement annotées.
- Volume réaliste : 3-10 ventes/mois = **45-400 €/mois**.
- Scénario réaliste médian : **80-150 €/mois** passif total.
- C'est peu mais le coût de setup est minimal (les données existent déjà).

**Risques principaux** :
- Faible volume par nature (marché de niche technique).
- Les données botaniques publiques existent ailleurs gratuitement (GBIF, WikiData) — la valeur ajoutée est le formatage, les métadonnées éditoriales et la curation, pas les données brutes.
- Si Gemini a rédigé une partie des descriptions sans vérification, des erreurs factuelles peuvent affecter la réputation.

**Verdict honnête** : **Idée correcte mais revenus plafonnés.** À faire en 2 heures si les données sont déjà propres. Pas une priorité stratégique, mais un "quick win" avec quasi zéro effort. Ne pas y consacrer plus d'une demi-journée.

---

## Idée N°7 — Sites de contenu long-tail SEO + affiliation Amazon (GitHub Pages)

**Pitch en une phrase** : Créer des sites statiques GitHub Pages sur des requêtes SEO précises à faible concurrence (ex. "tisane pour le sommeil recette", "plantes médicinales pour débutants", "champignons comestibles forêt française"), alimentés par du contenu Gemini, avec des liens affiliés Amazon sur les produits recommandés.

**Modèle économique** : Affiliation Amazon (3-5% du panier), AdSense (optionnel, revenus faibles au début). Trafic organique Google.

**Plateforme de vente** : GitHub Pages (hébergement 0 €), Amazon Partenaires, Google AdSense.

**Setup nécessaire** (≤ 2 semaines) :
1. Choisir 3-5 mots-clés cibles avec Google Search Console ou Ubersuggest (gratuit).
2. Briefer Gemini pour générer 20-30 articles de 1000-2000 mots par site, structurés SEO.
3. Déployer un site Jekyll/Hugo sur GitHub Pages (template gratuit + GitHub Actions pour build automatique).
4. Ajouter les liens affiliés Amazon dans le contenu.
5. Soumettre le sitemap à Google Search Console.

**Briques du pipeline réutilisées** : Gemini rédacteur (articles SEO en masse), GitHub Actions (build et deploy automatique du site statique), Robot images (illustrations pour enrichir les articles).

**Effort opérationnel mensuel après setup** : ~2h/mois (ajouter 2-4 articles, vérifier Search Console).

**Revenu réaliste à 6 mois** :
- **À 6 mois : quasi zéro.** Le SEO organique prend 8-18 mois en France pour des sites nouveaux sans backlinks.
- À 12 mois : 500-2000 visites/mois réalistes sur une niche bien ciblée → €30-150/mois affiliation + €10-40/mois AdSense.
- À 18 mois : **100-400 €/mois** si le site continue à être alimenté.
- Ce modèle est le plus lent à démarrer de cette liste.

**Risques principaux** :
- Google peut pénaliser le contenu IA de mauvaise qualité (les mises à jour Helpful Content frappent les sites thin-content).
- Le délai de rentabilité dépasse l'horizon des 6 mois annoncé dans le brief.
- Sans backlinks (impossible à obtenir sans budget ou partenariats), le classement reste difficile.

**Verdict honnête** : **Idée viable à long terme, mauvaise à court terme.** Si l'objectif est 50-200 € dans les 6 mois, passer son tour. Si l'objectif est 200-500 € en 18 mois entièrement passif, c'est le meilleur modèle de cette liste sur le long terme. À démarrer maintenant pour récolter plus tard, pas comme source principale de revenus.

---

## Idée N°8 — Livres de coloriage botaniques (KDP Low-Content)

**Pitch en une phrase** : Générer des livres de coloriage pour adultes basés sur des illustrations botaniques en style line art, via le robot d'images avec des prompts spécifiques "coloring book style", publiés sur KDP avec un investissement de 3-4 jours.

**Modèle économique** : Royalties KDP (royalty fixe sur les livres low-content, ~2-3 € par vente pour un livre à 9,99 $).

**Plateforme de vente** : Amazon KDP (marché mondial).

**Setup nécessaire** (≤ 1 semaine) :
1. Créer des prompts spécifiques : "botanical illustration [plante], coloring book style, black and white line art, clean outlines, no shading, white background".
2. Lancer le robot images avec ces prompts (200 images), passer par le juge IA pour sélectionner 50 designs propres.
3. Assembler le PDF intérieur (1 illustration par page, format KDP standard, 8.5×8.5 pouces).
4. Créer la couverture (Canva mobile, template KDP).
5. Publier sur KDP en quelques jours.

**Briques du pipeline réutilisées** : Robot images IA (prompts spécialisés line art), Juge IA (sélection des designs les plus propres), Config centralisée (template réplicable par thème : fleurs, champignons, forêt...).

**Effort opérationnel mensuel après setup** : ~30min/mois (surveiller les ventes, aucun autre engagement).

**Revenu réaliste à 6 mois** :
- Le marché du coloriage adulte sur KDP est saturé en anglais sur les niches génériques MAIS moins sur les niches précises (plantes françaises spécifiques, mycologie, herboristerie).
- 5-20 ventes/mois × €2,50 royalty = **12-50 €/mois par titre**.
- Avec 5 titres distincts (fleurs, champignons, plantes médicinales, forêt, bord de mer) : **60-250 €/mois**.
- La qualité du line art généré par l'IA est variable : certains prompts donnent d'excellents résultats, d'autres sont inutilisables. Le juge IA filtre ça.

**Risques principaux** :
- La qualité du line art IA reste inférieure à un illustrateur humain. Les acheteurs KDP laissent de mauvais avis si le coloriage est de mauvaise qualité.
- KDP peut restreindre davantage les livres low-content générés par IA.
- Revenus unitaires très faibles : il faut un volume significatif pour atteindre 200 €/mois.

**Verdict honnête** : **Idée correcte, pas excellente.** C'est plus rapide à lancer que l'idée N°1 (moins de contenu texte), mais les royalties plus basses et la concurrence accrue en font un complément plutôt qu'une priorité. À faire après les livres illustrés complets (N°1).

---

## Classement final — Ratio revenu potentiel / effort de setup

| Rang | Idée | Revenu réaliste 6 mois | Setup | Score |
|------|------|------------------------|-------|-------|
| 🥇 1 | **N°1 — KDP multilingues/multi-niches** | 150-800 €/mois | 1-2 semaines | ★★★★★ |
| 🥈 2 | **N°4 — Packs de prompts (Gumroad/Etsy)** | 150-400 €/mois | 5-7 jours | ★★★★☆ |
| 🥉 3 | **N°2 — Print-on-demand (Redbubble)** | 60-300 €/mois | 3-5 jours | ★★★★☆ |
| 4 | N°5 — Kit autoédition KDP | 100-500 €/mois | 1-2 semaines | ★★★☆☆ |
| 5 | N°6 — Datasets (Gumroad) | 50-150 €/mois | 2-3 jours | ★★★☆☆ |
| 6 | N°8 — Livres de coloriage KDP | 60-200 €/mois | 4-6 jours | ★★★☆☆ |
| 7 | N°3 — Newsletter Beehiiv | 70-150 €/mois | 1 semaine | ★★☆☆☆ |
| 8 | N°7 — Sites SEO GitHub Pages | 0-50 €/mois à 6 mois | 1-2 semaines | ★☆☆☆☆ (long terme) |

---

## Synthèse stratégique (5 lignes)

Les trois idées qui exploitent le mieux le pipeline et qu'il serait contre-productif de ne pas tenter en priorité :

1. **KDP multilingues (N°1)** : Le pipeline est déjà construit. Forker le repo et changer `meta_livre.py` est l'action la moins risquée et la plus directement rentable. La version anglophone du livre de plantes médicinales seule peut tripler les revenus sans aucun nouveau travail d'infrastructure.

2. **Packs de prompts (N°4)** : La génération de prompts de qualité est littéralement ce que fait le pipeline. Les vendre directement transforme un intrant (les prompts) en produit. C'est une semaine de travail pour un actif passif durable.

3. **Print-on-demand (N°2)** : Le robot d'images génère déjà des centaines d'illustrations — autant les monétiser sur Redbubble en parallèle. Coût marginal quasi nul, setup en 3 jours, revenus qui s'accumulent sans aucune gestion.

---

## Les pièges à éviter — Miroirs aux alouettes

**1. YouTube / TikTok faceless automatisé** : Le marché est saturé d'outils et de vendeurs de formation. La réalité : les chaînes faceless mettent 12-18 mois à décoller sur YouTube, TikTok bannit activement le contenu IA répétitif, et la monétisation YouTube nécessite 1000 abonnés + 4000h de watch-time avant le premier euro. La promesse "5000 €/mois en passif" est omniprésente et quasi-systématiquement mensongère pour un débutant sans budget pub.

**2. Dropshipping** : Zéro rapport avec le pipeline, zéro avantage compétitif, marges écrasées par les vendeurs chinois sur Amazon et les frais Shopify. Abandonner.

**3. NFTs / tokens / crypto-adjacent** : Marché effondré, légalité complexe en France, aucun rapport avec les compétences et l'infrastructure disponibles.

**4. Cours Udemy génériques** : Udemy est une guerre de prix — les cours passent à 9,99 € lors des promos. Sans une audience préexistante et des avis 4,5 étoiles dès le lancement, un cours est invisible. La plateforme prend 50-75% des revenus si le client vient via leurs promotions. Éviter en première intention.

**5. Apps mobiles monétisées** : Le développement et la maintenance d'une app mobile, même simple, nécessitent des compétences techniques spécifiques, un compte développeur payant (99$/an Apple, 25$ Google), et des mises à jour régulières pour rester compatible avec les nouvelles versions d'OS. Incompatible avec la contrainte "Android only + zéro code de maintenance".

**6. Micro-SaaS d'API** : Séduisant sur le papier, mais attirer des clients sur une API inconnue sans budget marketing ni communauté existante est extrêmement difficile. Les marketplaces API (RapidAPI) ont des milliers d'APIs qui ne font aucune vente. À n'envisager que si un canal de distribution existe déjà (newsletter avec 1000+ abonnés, communauté active).
