TARGET: scripts/agent_publisher.py

## Rôle
Prépare le paquet de publication KDP + Etsy après GATE 2 approuvé.
Génère metadata KDP, fiche Etsy, et PUBLICATION_READY.md lisible par Hugo.

## Variables d'environnement
- BRIEF_ID
- GEMINI_API_KEY (pour blurb + description Etsy)
- GEMINI_MODEL (défaut gemini-2.5-flash)

## Fichiers écrits dans products/coloring_books/_gate1/<BRIEF_ID>/publication/
- kdp_metadata.json : titre, auteur, description (150-200 mots Gemini), 7 keywords, categories, prix 8.99
- etsy_listing.json : titre (max 140 chars keywords-first), description (500-800 mots SEO), 13 tags
- PUBLICATION_READY.md : résumé Hugo + checklist KDP + listing Etsy

## Algorithme
1. Vérifier kdp_package.json existe avec ready_for_gate2=true
2. Appeler Gemini : blurb KDP + description Etsy + 13 tags + 7 keywords
3. Mode fallback si Gemini absent : templates statiques avec variables du brief
4. Écrire les 3 fichiers
5. Print "PRÊT POUR PUBLICATION : voir PUBLICATION_READY.md"

## Dépendances
- stdlib + urllib
- Aucune dépendance externe requise

## CLI
```
python scripts/agent_publisher.py [BRIEF_ID]
```
