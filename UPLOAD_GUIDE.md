# 📤 GUIDE D'UPLOAD — comment uploader chaque produit sur chaque plateforme

**Préalable** : tu as fini les inscriptions (Etsy Seller, Printful, KDP, Redbubble si voulu). Si pas encore : voir `INSCRIPTIONS_HUGO.md`.

---

## 🎯 Pour chaque pipeline : quoi uploader, où, comment

### 1. Cultural Arbitrage (mots intraduisibles)

**Fichiers générés** dans `products/cultural_arbitrage/{mot}/{format}/` :
- `etsy_preview.jpg` — image carrée 1080×1080 pour l'aperçu Etsy
- `print_3000.png` — fichier haute résolution à vendre (3000×3000 @ 300 DPI)
- `metadata.json` — titre, tags, prix recommandé

**Où uploader** :

#### Etsy (priorité 1)
1. Etsy → Shop Manager → Listings → Add a Listing
2. Type : **Digital download**
3. Upload : `print_3000.png` (le fichier client) + `etsy_preview.jpg` (l'aperçu visible)
4. Copie-colle depuis `metadata.json` :
   - `title`
   - `tags_etsy` (max 13 tags séparés par virgules)
   - Description : prends le pattern dans `EMPIRE_HUGO.md` ou écris :
     > « Beautiful [language] word "[word]" — meaning [meaning]. Instant digital download, print at home or local shop. High-resolution 3000×3000px @ 300dpi. Personal use included. »
5. Prix : 4,50 €
6. Catégorie : Art & Collectibles → Prints

#### Redbubble (priorité 2 — passe le même fichier sur produits physiques)
1. Redbubble → Sell → Add new work
2. Upload : `print_3000.png`
3. Active les produits : t-shirt, mug, poster, tote bag (par défaut tout)
4. Titre + tags : pareil depuis `metadata.json`
5. Prix : utilise les marges Redbubble par défaut (~20%)

**Astuce** : pour 30 expressions × 4 formats = 120 designs, fais des batches de 5-10 par soir.

---

### 2. I ❤️ X (avec illustration de fond)

**Fichiers générés** dans `products/iheart/{niche}/{variant}/` :
- `etsy_preview.jpg` — 1080×1080
- `print_3000.png` — 3000×3000
- `tshirt_2400x3000.png` — format Printful t-shirt portrait

**Où uploader** :

#### Etsy POD via Printful (priorité 1 — physique)
1. Va sur Printful → Stores → Connect Etsy store (déjà fait à l'inscription)
2. Printful Dashboard → Add Product → **T-shirt**
3. Upload `tshirt_2400x3000.png`
4. Configure : couleur (white/heather), tailles (S à 3XL)
5. Publish to Etsy → titre + tags depuis `metadata.json`
6. Prix Etsy : auto-calculé par Printful (cible 24,99 €, marge ~9 €)

#### Etsy digital download (priorité 2 — instant)
1. Listing digital download (idem cultural arbitrage)
2. Upload `print_3000.png`
3. Prix : 3,50 €

#### Redbubble (priorité 3)
1. Upload `print_3000.png`
2. Active surtout : t-shirt, mug, sticker

**Reco** : commence par les 5 niches les plus généralistes (Reading, My Cat, My Dog, Coffee, Crochet). Stats Etsy disent qu'elles vendent même sans budget pub.

---

### 3. Literal Idioms (humour polyglotte)

**Fichiers générés** dans `products/literal_idioms/{lang}/{idiom_slug}/` :
- `etsy_preview.jpg`, `print_3000.png`

**Où uploader** :

#### Etsy (priorité 1)
- Listing digital download
- Prix : 4,99 €
- Description : explique la blague linguistique :
  > « In [language], "[original]" literally translates to "[literal]" — but it actually means "[meaning]". The perfect gift for [language] learners, polyglots, or anyone who loves the weird charm of idioms. »

#### Pinterest (priorité 2 — gros trafic potentiel)
- Crée 1 pin par idiome
- Description SEO : pleine d'hashtags langues #germanlanguage #frenchidiom #polyglot #languagelearning
- Link out vers ton Etsy listing
- Pinterest viralise les sujets éducatifs/funny — c'est exactement ton angle

#### Redbubble (priorité 3)
- Active t-shirt + sticker (le format humour marche bien sur stickers)

---

### 4. Tumbler Wraps

**Fichiers générés** dans `products/tumbler_wraps/{niche}/design_NN/` :
- `wrap.png` (2790×2490 px @ 300 DPI — format Etsy sublimation standard)
- `etsy_preview.jpg`

**Où uploader** :

#### Etsy SUBLIMATION digital (priorité 1)
- Listing digital download
- **Important** : précise « 20oz straight tumbler wrap, sublimation PNG »
- Inclut dans la description :
  > « Compatible with 20oz straight tumblers. PNG format with transparent background where needed. Instant download. »
- Prix : 3,99 €
- Catégorie : Craft Supplies & Tools → Sublimation

**Pas de versions physiques** sur Printful pour les tumbler wraps (Printful ne fait pas).

---

### 5. Coloring Books KDP

**Fichiers générés** dans `products/coloring_books/{niche_key}/` :
- `{niche_key}.pdf` — le livre complet KDP-ready
- `pages/page_NN.png` — pages individuelles si besoin retouche
- `metadata.json` — titre, sous-titre, keywords KDP, prix, catégories

**Où uploader** :

#### KDP (priorité 1)
1. KDP → Bookshelf → Create new paperback
2. Title + Subtitle : depuis `metadata.json`
3. Series : laisse vide ou crée une série « Mystical Coloring Collection »
4. Author : ton nom ou pseudo
5. Description : écris ~150 mots, intègre les `kdp_keywords`
6. **Categories** : choisis 2 dans `metadata.json["categories"]`
7. **Keywords** : 7 mots-clés depuis `metadata.json["kdp_keywords"]`
8. Print : Paperback → 8.5×11 inch → **Black and white** interior → White paper
9. Upload `{niche_key}.pdf`
10. Cover : à créer (KDP Cover Creator gratuit, ou Canva)
11. Pricing : 7,99 € (marge ~3 €/livre vendu)
12. Publish

⚠️ **Cover obligatoire** — KDP refuse sans. Pour la première version :
- Utilise KDP Cover Creator (gratuit)
- Ou Canva template "KDP book cover 8.5×11"
- Ou demande à Claude de générer une cover via Pollinations (script à coder en v2)

#### Etsy digital download (priorité 2 — version PDF instant)
- Listing digital download du PDF
- Prix : 9,99 €
- Public : crafters qui veulent imprimer chez eux

---

### 6. SVG Packs (Cricut)

**Fichiers générés** dans `products/svg_packs/{niche}/` :
- `{niche}_pack.zip` — ZIP contenant les SVG
- `etsy_listings.csv` — pré-rempli

**Où uploader** :

#### Etsy (la seule plateforme pertinente)
- Listing digital download
- Upload : le ZIP
- Description : insiste sur « compatible Cricut Design Space, Silhouette Studio, Glowforge »
- Prix : 4,99 €

---

## 🎨 Workflow optimal (10 produits/jour, ~30 min)

### Matin (15 min)
1. Ouvre Etsy Shop Manager
2. **Add a Listing** → upload 3-5 designs depuis `products/`
3. Copie-colle titre + tags depuis `metadata.json`
4. Publish

### Midi (10 min)
1. Pinterest Business
2. Crée 5-10 pins liés aux listings du matin
3. Description SEO + 5-8 hashtags + lien vers Etsy

### Soir (5 min)
1. Check Etsy Stats (vues, favoris, ventes)
2. Si un listing a 0 vues après 3 jours → modifie 3 tags
3. Si un listing vend → screenshot pour Claude, on en fait des variantes

---

## ⚠️ Erreurs typiques à ÉVITER

- ❌ **Copier-coller exact 13 tags identiques** entre tous tes listings → Etsy te marque comme spam. Varie au moins 5 tags entre listings d'une même niche.
- ❌ **Trop de mots dans le titre** → Etsy coupe au-delà de 140 caractères. Mots-clés en début.
- ❌ **Description en bullet points uniquement** → Etsy aime les descriptions humaines, pas que des listes.
- ❌ **Oublier les images de scène** sur les listings POD → Printful génère des mockups, mais ajoute aussi une image de scène (le t-shirt sur quelqu'un, le mug sur une table cosy).
- ❌ **Vendre les SVG comme libres de droits commerciaux** → précise « personal use only, small commercial OK up to 100 items ». Sinon les revendeurs Etsy te volent.

---

## 💡 Quand les ventes commenceront

**Plus tu uploads, plus tu apprends ce qui marche.** En général :
- Les **3-7 premiers jours** : 0 vente (normal, Etsy index lentement)
- **Semaine 2** : 1-3 ventes si les tags sont bons
- **Mois 2** : 10-30 ventes/mois
- **Mois 6** : 50-200 ventes/mois si tu uploades 5-10 produits/semaine

**Quand un design vend** → screenshot pour Claude, on crée 5-10 variantes du même thème pour multiplier le hit.

---

## 🆘 Si tu bloques

- Listing refusé Etsy ? Screenshot du motif → Claude
- Prix qui ne se calcule pas sur Printful ? Vérifie que tu as bien connecté ta boutique Etsy
- KDP demande une cover ? Crée-en une basique via KDP Cover Creator (gratuit, 5 min)
- Pas de ventes après 1 mois ? Pas de panique, on analyse les tags et la concurrence
