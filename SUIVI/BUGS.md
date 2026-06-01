# BUGS & INCIDENTS — 365days Factory

> Format : `[DATE] [SÉVÉRITÉ] [COMPOSANT] Description → Fix appliqué`
> SÉVÉRITÉ : 🔴 BLOQUANT | 🟡 DÉGRADÉ | 🟢 MINEUR

---

## BUGS OUVERTS

_Aucun pour l'instant_

---

## BUGS RÉSOLUS

_À remplir au fil des incidents_

---

## PATTERN D'ERREURS CONNUES

| Composant | Erreur fréquente | Cause | Fix |
|-----------|-----------------|-------|-----|
| Gemini API | 429 Too Many Requests | Rate limit free tier (15 req/min) | Tempo de 5s entre appels |
| GitHub Actions | Push rejected | Concurrent commits sur même branch | Retry avec rebase |
| LLM Router | KeyError 'model' | JSON mal formé en sortie | Prompt avec `respond in JSON only` |

