# 🔍 AUDIT DU SYSTÈME — forces, faiblesses, optimisations

**Date** : 2026-05-17
**Méthode** : audit honnête (Opus 4.7), sans complaisance.

---

## 💪 FORCES (à renforcer)

### 1. Architecture en cascade DETECT → CREATE → PUBLISH
- ✅ Agents de détection découplés (`trend_explosion`, `niche_gap`, `trend_design_matcher`, `seasonal_calendar`)
- ✅ Cerveau intermédiaire (`opportunity_hunter`, `ideator_offline`) qui croise tout
- ✅ Pipelines de production indépendants (10+ pipelines)
- ✅ Aucun composant n'est SPOF : si un agent tombe, le reste fonctionne
- **Comment renforcer** : ajouter un `agent_evolution` qui mesure ce qui vend réellement (via input manuel de Hugo) et propose des ré-allocations.

### 2. 100% gratuit + 100% légal
- ✅ Pollinations.ai (génération image, gratuit illimité)
- ✅ Reddit JSON public (scraping autorisé)
- ✅ Etsy HTML public (data publique, scraping légal)
- ✅ GitHub Actions free tier (2000 min/mois privé, illimité public)
- ✅ Aucun bypass, aucun fake account, aucun CAPTCHA hacking
- **Comment renforcer** : ajouter de la diversification (HuggingFace pour image2image, SDXL Lightning pour style transfer) quand tu auras la clé HF.

### 3. Multi-marché géo + multi-langue
- ✅ Cultural arbitrage exploite 12+ langues
- ✅ Literal idioms exploite 14+ langues
- ✅ Audiences multi-pays (BookTok, polyglots, expats)
- **Comment renforcer** : ajouter des versions en espagnol/français/allemand des viral formats les plus performants.

### 4. Production parallélisable massive
- ✅ Chaque pipeline génère 50-500 designs en 1 run
- ✅ Pollinations supporte la parallélisation (avec rate limit raisonnable)
- ✅ COPE (Create Once Publish Everywhere) : 1 image → 8 formats
- **Comment renforcer** : ajouter un coordinateur qui décide quoi produire en fonction des opportunités détectées (`agent_orchestrator` à coder).

---

## ⚠️ FAIBLESSES (à corriger en priorité)

### 1. ❌ **Pas de boucle de feedback réelle (RÉEL ↔ SYSTÈME)**
**Problème** : le système produit aveuglément. Il ne SAIT PAS ce qui vend vraiment sur Etsy.
**Impact** : risque de saturer une niche qui ne convertit pas, ou rater une niche qui décolle.
**Solution** :
- Hugo entre les ventes hebdomadaires dans un fichier simple (`data/sales_feedback.csv`)
- Un nouvel agent `agent_winner_amplifier` lit ce CSV, identifie les designs qui vendent, et ordonne 10 variantes du même thème pour multiplier le hit
- À coder cette semaine ou dès qu'il y a des ventes

### 2. ❌ **Risque de pattern-detection par les plateformes**
**Problème** : si on uploade 200 listings avec la même structure de tags, Etsy peut nous flag spammeur.
**Solution** :
- ✅ Tags varient déjà par design (varient les 5 derniers tags)
- ⚠️ Description : actuellement TEMPLATE → trop répétitif si 100 produits du même pipeline. À varier.
- **À faire** : pool de 3-5 templates de description par pipeline, alternés aléatoirement.
- **Bonus humain** : c'est toi qui uploades, ajoute un détail unique sur 1 listing sur 3 (preset Etsy "tags qui ont marché ailleurs").
- **Rotation** : tous les 30 jours, on permute les templates dominants.

### 3. ❌ **Pas de mockups produits physiques**
**Problème** : sur Etsy POD, sans mockup en scène (t-shirt porté, mug sur table), conversion -50%.
**Solution** :
- Pollinations peut générer des scènes mockup
- À coder : `produce_mockups.py` qui prend chaque design et le compose sur 3-5 scènes lifestyle
- Pas critique pour les designs digital download, mais blocker pour POD.

### 4. ❌ **STL paramétriques sans texte gravé**
**Problème** : la v1 du pipeline STL ne grave PAS le texte sur le STL (texte uniquement dans le titre). Limitation technique : font rendering en 3D est complexe.
**Solution** :
- v2 : intégrer FreeCAD ou OpenSCAD (CLI) sur le runner GitHub Actions pour graver le texte
- Ou : générer en SVG le contour du texte puis extrude
- À planifier sprint 3 (semaine 3-4)

### 5. ❌ **Crons indépendants peuvent se télescoper**
**Problème** : si 3 workflows pushent en même temps, conflict git push.
**Solution actuelle** : retry+rebase 5x avec exponential backoff (déjà en place).
**Renforcement** : utiliser `concurrency` group au niveau workflow (déjà fait).
**Audit OK** sur ce point.

### 6. ❌ **Pas de monitoring/alerting**
**Problème** : si Pollinations bloque, ou Reddit change son JSON, on ne le sait pas.
**Solution** :
- Ajouter dans chaque agent un seuil "si <X% de succès, créer issue GitHub"
- À coder : `agent_health_check` qui audit les runs hebdomadairement

---

## 🎯 OPTIMISATIONS PRIORITAIRES (ordre)

### Sprint 1 (cette nuit / dès activation crons)
- ✅ Pousser workflows sur main (en cours)
- ✅ Déclencher production nocturne via `.triggers/` (en cours)
- ⚠️ Coder l'agent winner amplifier (besoin données ventes Hugo)

### Sprint 2 (semaine 2-3 après inscriptions Hugo)
- 📝 Coder `produce_mockups.py` pour POD
- 📝 Pool de templates description (anti-pattern detection)
- 📝 Pinterest auto-publisher (besoin clé API)
- 📝 Romance ebook pipeline (besoin Gemini)

### Sprint 3 (mois 2)
- 📝 STL texte gravé v2
- 📝 Bot IDEATOR LLM augmenté (Groq + Gemini)
- 📝 YouTube Kids faceless
- 📝 Agent winner amplifier qui ré-injecte les hits

---

## 🔁 BOUCLE D'ÉVOLUTION CONTINUE — comment le système s'auto-améliore

```
┌──────────────────────────────────────────────────────────┐
│  Lundi  : agent_trend_explosion + agent_niche_gap        │
│  Mardi  : agent_trend_design_matcher (scrape Etsy)       │
│  Merc.  : agent_ideator_offline (brainstorm 200 idées)   │
│  Jeudi  : opportunity_hunter (croise tout)               │
│  Hugo   : décide 3-5 productions de la semaine           │
│  Vendr. : pipelines de production lancés                 │
│  Samedi : Hugo uploade les designs sur les plateformes   │
│  Dim.   : Hugo entre les ventes dans sales_feedback.csv  │
│  → Lundi suivant : agent_winner_amplifier ré-prio       │
└──────────────────────────────────────────────────────────┘
```

**Auto-amplification** : 1 design qui vend → 10 variantes du même thème.
**Auto-élimination** : 0 ventes en 60 jours → le format/niche est descoré.
**Évolution exogène** : Trend Design Matcher découvre de nouvelles structures virales tous les mardis.

---

## 🛡️ ANTI-FRAGILITÉ — comment le système résiste aux chocs

| Choc | Mitigation |
|---|---|
| Pollinations bloque | HF SDXL en backup (à activer après clé HF) |
| Reddit change API | Mode dégradé fallback données antérieures |
| Etsy bloque scraping | Mode dégradé local data |
| Hugo prend des vacances 1 mois | Le système continue à produire en stock — pas critique |
| GitHub Actions limit dépassé | Réduire `MAX_DESIGNS` par run, prioriser Top 10 opportunités |
| Compte Etsy/Printful banni | Diversification multi-plateformes (Redbubble, Society6, Cults3D, KDP en parallèle) |

---

## 📈 INDICATEURS DE SANTÉ DU SYSTÈME (à tracker)

- **Production hebdomadaire** : combien de designs/livres/STL produits/semaine ?
- **Uploads hebdomadaire** : combien sur Etsy/Printful/Cults3D ?
- **Vues moyennes Etsy** par listing à J+7
- **Conversion** : ventes / vues
- **Revenus mensuels** : par pipeline, par plateforme
- **Coût** : 0 € (sauf si on prend Etsy Plus à 10$/mois ou Printful Pro à 25$/mois — à décider quand on aura 50+ ventes/mois)

---

## 🎓 LEÇONS APPRISES

1. **Spécialiser > Généraliser** : remplacer le Trendhunter générique (polluait avec HN/Wiki) par 2 agents spécialisés a multiplié la pertinence
2. **Le COPE est roi** : 1 image source → 8 formats = ROI ×8
3. **Les concepts viraux > la qualité visuelle** : un format texte fort se vend même avec une illustration moyenne
4. **L'évolution > le perfectionnisme** : sortir 100 designs imparfaits >> attendre 10 designs parfaits
