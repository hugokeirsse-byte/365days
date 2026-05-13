# Prompt — Rédaction d'une fiche encyclopédique (série « 365 Medicinal Plants »)

> À copier-coller tel quel dans Gemini ou ChatGPT, en remplaçant uniquement le bloc « ENTRÉE À RÉDIGER ».
> Tu peux enchaîner plusieurs plantes dans la même conversation pour gagner du temps.

---

Tu rédiges une fiche encyclopédique en anglais pour le livre « **365 Medicinal Plants** » de Mirabilia Éditions. Le ton est celui d'une encyclopédie de référence : précis, sobre, scientifiquement rigoureux mais accessible. Pas de fioritures, pas de marketing, pas d'avertissement médical générique en plus de la rubrique `precautions`.

## Contraintes strictes
- **Langue** : anglais uniquement.
- **Format de sortie** : un unique bloc JSON valide, copiable directement, sans texte autour.
- **Longueurs maximales** (caractères, espaces compris) :
  - `origin`, `parts_used`, `harvest`, `habitat`, `regions` → 220
  - `active_compounds`, `properties`, `precautions`, `interactions` → 320
  - `traditional_uses`, `how_to_use`, `cultural_note` → 420
- **Pas de listes à puces** dans les rubriques : texte rédigé en 1 à 3 phrases.
- **Pas de duplication** entre rubriques (chaque info une seule fois).
- **`precautions`** doit mentionner la toxicité, la grossesse/allaitement, et tout effet indésirable connu — factuel, pas alarmiste.
- **Sources** : appuie-toi sur la littérature ethnobotanique et pharmacologique de référence (Mrs. Grieve, WHO monographs, Commission E, ESCOP, USDA…). N'invente rien : si une donnée n'est pas connue, écris simplement « Not documented. »

## Schéma de sortie attendu

```json
{
  "id": <int 1-365>,
  "day": "<Month D>",
  "name_en": "<nom commun anglais>",
  "name_la": "<nom latin>",
  "family": "<famille botanique>",
  "origin": "<...>",
  "parts_used": "<...>",
  "harvest": "<...>",
  "habitat": "<...>",
  "active_compounds": "<...>",
  "properties": "<...>",
  "traditional_uses": "<...>",
  "how_to_use": "<...>",
  "precautions": "<...>",
  "interactions": "<...>",
  "cultural_note": "<...>",
  "regions": "<...>",
  "legend": [],
  "image_url": "<URL fournie>",
  "image_source": "Köhler's Medizinal-Pflanzen, 1887"
}
```

> Laisse `legend` vide `[]` : elle est rédigée séparément via le prompt 02.

---

## ENTRÉE À RÉDIGER

```
id        : {{ID}}
day       : {{DAY}}            (ex : "January 1")
name_en   : {{NAME_EN}}
name_la   : {{NAME_LA}}
image_url : {{IMAGE_URL}}
```

Rends uniquement le JSON, rien d'autre.
