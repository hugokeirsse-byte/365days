# Prompt — Ré-ordonner les 365 entrées en index alphabétique

> À utiliser une seule fois en fin de production, quand toutes les fiches sont rédigées.

---

Tu reçois un tableau JSON de fiches plantes pour le livre « 365 Medicinal Plants ».

Ta tâche :
1. **Trie** les entrées par `name_en` (ordre alphabétique anglais, insensible à la casse).
2. **Réattribue** les champs `id` (1 à N) et `day` selon l'ordre obtenu, en partant de `January 1` et en avançant d'un jour par entrée (le calendrier est non bissextile, 365 jours).
3. **Vérifie** qu'il n'y a pas de doublon de `name_la`.
4. **Renvoie** le tableau JSON re-numéroté.

## Calendrier de référence (non bissextile)

```
Jan 31 + Feb 28 + Mar 31 + Apr 30 + May 31 + Jun 30 +
Jul 31 + Aug 31 + Sep 30 + Oct 31 + Nov 30 + Dec 31 = 365
```

## Sortie

Un tableau JSON complet, prêt à écraser `plants.json`.
Rends uniquement le JSON, rien d'autre.

---

## ENTRÉE

```json
{{PLANTS_JSON_ARRAY}}
```
