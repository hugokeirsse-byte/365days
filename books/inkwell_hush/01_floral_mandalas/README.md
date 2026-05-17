# Inkwell & Hush · The Mandala Collection · Vol. I

## Floral Mandalas — 100 Pages to Color

**Marque** : Inkwell & Hush
**Collection** : The Mandala Collection
**Volume** : I
**Statut** : en démarrage (Phase 1 / 5)

## Concept

100 mandalas floraux à colorier, chacun centré sur une fleur emblématique : roses, lotus, pivoines, tournesols, lavandes, hibiscus, etc. Symétrie radiale 8 ou 12, line art noir pur sur fond blanc.

## Pipeline de production

1. **Génération via Pollinations.ai (Flux)** : 100 prompts mandalas floraux
2. **Sélection / scoring** : si nécessaire, Gemini Vision pour pré-noter
3. **Upscale Real-ESRGAN ×4** : 1024×1024 → 4096×4096 pour impression
4. **Post-processing optionnel** : threshold Pillow pour garantir noir-blanc pur
5. **Mise en page** : 1 mandala par page, single-sided (verso blanc → 200 pages)
6. **Couverture** : 1 mandala emblématique sur fond terracotta

## Cible commerciale

- **Format** : 8,5 × 8,5", softcover, 200 pages (100 mandalas single-sided)
- **Prix de vente** : 10-14 €
- **Marge nette estimée** : 5-7 € par exemplaire
- **Public** : adultes 30-65 ans, public féminin majoritaire, anti-stress, méditation, cadeau bien-être

## Avancement

- [ ] Rédiger les 100 prompts mandalas floraux (catégorisés par espèce)
- [ ] Adapter le robot Pollinations pour le ratio carré 2048×2048
- [ ] Générer les 100 mandalas (~30-60 min)
- [ ] Upscaler les 100 mandalas (~1-2 h)
- [ ] Sélection visuelle (garde les 100 meilleurs)
- [ ] Mise en page automatique
- [ ] Couverture
- [ ] Upload KDP

## Notes éditoriales

- Prompt-maître constant : `intricate floral mandala, [FLEUR], black ink line art on white background, perfectly symmetric, [N]-fold radial symmetry, clean thick outlines, no shading, no color, coloring book page, high contrast, vector-style precision`
- Variations : symétrie 6/8/12/16, complexité easy/medium/intricate, fleur centrale différente
- Index final : 100 noms de fleurs en anglais
