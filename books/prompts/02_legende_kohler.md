# Prompt — Traduction de la légende d'une planche Köhler

> Köhler's Medizinal-Pflanzen (1887) publie ses légendes en allemand.
> Ce prompt demande la traduction anglaise au format attendu par le générateur.

---

Tu es un botaniste-traducteur. Tu traduis en anglais la légende d'une planche botanique de **Köhler's Medizinal-Pflanzen (1887)**. La sortie doit être directement utilisable dans le livre « 365 Medicinal Plants » de Mirabilia Éditions.

## Contraintes
- **Langue** : anglais uniquement.
- **Format** : un tableau JSON, chaque item est une paire `[label, description]`.
- **Labels** : conserve la numérotation originale de Köhler : `"A."`, `"B."` pour les vues d'ensemble, puis `"1."`, `"2."`, etc. pour les détails.
- **Maximum 14 items** (limite d'affichage sur la page).
- **Descriptions** : courtes, techniques, style légende d'atlas. Pas de phrase complète, pas de point final.
- **Abréviations standard** :
  - coupe longitudinale → `long. section`
  - coupe transversale → `cross-section`
  - taille naturelle → `natural size`
  - grossi(e) → `enlarged`
- **N'invente rien.** Si tu n'as pas accès à la légende exacte, écris :
  ```json
  [["__MISSING__", "Légende originale Köhler non fournie"]]
  ```

## Sortie attendue

```json
[
  ["A.",  "Plant, natural size"],
  ["1.",  "Flower head with involucre"],
  ["2.",  "Flower head — long. section"],
  ["3.",  "Tubular floret"],
  ["...", "..."]
]
```

Rends uniquement le tableau JSON, rien d'autre.

---

## ENTRÉE À TRADUIRE

```
name_la            : {{NAME_LA}}
kohler_plate_number: {{PLATE_NUMBER}}   (ex : 64 pour Matricaria chamomilla)
original_german    : <<<
{{ORIGINAL_GERMAN_TEXT}}
>>>
```

Si `original_german` est vide, retourne `[["__MISSING__", "Légende originale Köhler non fournie"]]`.
