# 📦 staging/ — file d'attente des assets prêts à valider

**Doctrine** : aucun asset n'est publié automatiquement. Tout passe par ce dossier,
attend la validation humaine via bot Telegram, puis est uploadé manuellement par Hugo
(ou par script API dédié quand cas le permet).

Voir : `AUTOMATION_BLUEPRINT.md` §6, `SECURITE_ET_LEGAL.md` §2.

---

## 📁 Structure par brand_id

```
staging/
├── heritage_coloring/      [Modules U, P, D — coloriages historiques + restoration]
├── iconic_offspring/       [Module W — Progeny Engine bébés crossover PD]
├── pocket_decks/           [Module A — jeux de cartes POD]
├── modern_cozy/            [Modules L, B, K — coloring stylé, merch, fiction cozy]
├── vintage_restoration/    [Module P — restauration + colorisation archives]
├── merch_batch/            [Module B — lots de designs cross-canal multi-plateforme]
└── coloring_modern/        [Module L — coloring books style moderne (ControlNet)]
```

---

## 📋 Convention de nommage

Chaque asset dans `staging/<brand>/` suit ce format :

```
<YYYY-MM-DD>_<niche-slug>_v<n>/
├── asset.<ext>             [PDF, PNG, APK, ZIP, MP4...]
├── metadata.json           [conforme à data/schemas/asset.schema.json]
├── preview.png             [aperçu basse résolution pour bot Telegram]
└── qa_report.json          [verdict Gemini Vision + pain points adressés]
```

---

## 🤖 Cycle d'un asset

```
1. Module producteur génère asset.X + métadonnées dans staging/<brand>/<niche>/
2. QA automatique (Gemini Vision) écrit qa_report.json
3. Si qa_verdict = PASS : notification Telegram avec preview + boutons
4. Hugo clique ✅ → asset migré vers products/ + entrée publish_targets remplie
5. Hugo clique ❌ → asset migré vers archive/rejected/<YYYY-MM-DD>_<niche>/
6. Si Hugo ne répond pas en 7 jours :
   - Pour brands BAS RISQUE (heritage_coloring, pocket_decks) : auto-publish
   - Pour brands MOYEN RISQUE (iconic_offspring, vintage_restoration) : 14 jours puis archive
```

---

## ⚠️ Règles d'or

1. **Ne JAMAIS** uploader un asset directement depuis staging sans valider qa_report.json
2. **Ne JAMAIS** commiter `stage_local/` (gitignore obligatoire pour HD brutes)
3. **Toujours** vérifier `copyright_check.blacklist_clean: true` avant upload
4. **Toujours** appliquer rate limit par plateforme (cf. SECURITE_ET_LEGAL.md §2.1)
5. **Limite** par brand : max 30 assets en staging simultanément (sinon = pipeline saturé, vérifier QA)

---

## 🧹 Nettoyage automatique

Une GitHub Action (à coder) tourne chaque dimanche 23h :
- Archive les assets > 30 jours non publiés
- Vérifie l'intégrité des `metadata.json` vs schéma
- Génère un rapport hebdo Telegram : combien d'assets/brand, taux publication, etc.
