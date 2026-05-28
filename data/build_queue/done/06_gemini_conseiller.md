# Briefing 06 — agent_gemini_conseiller.py

## OBJECTIF
Créer `scripts/agent_gemini_conseiller.py` — un script qui soumet un contexte de projet à Gemini et récupère des conseils structurés sur l'amélioration, l'expansion, ou de nouveaux projets potentiels.

## ENTRÉE
- `GEMINI_API_KEY` (env)
- `CONSEIL_SUJET` (env) : texte libre décrivant le sujet de la consultation (ex: "améliorer la qualité du livre de coloriage Mushroom Hollow", "idées de nouveaux produits numériques à vendre sur Etsy", "comment mieux orchestrer la génération de roman par IA")
- `CONSEIL_CONTEXTE` (env, optionnel) : contexte supplémentaire (ex: données de vente, feedback client)
- `CONSEIL_OUTPUT` (env, optionnel) : chemin du fichier de sortie JSON (défaut: `data/conseils/<timestamp>_conseil.json`)

## SORTIE
Fichier JSON avec structure :
```json
{
  "sujet": "...",
  "date": "ISO8601",
  "conseils": [
    {
      "titre": "...",
      "priorite": "haute|moyenne|basse",
      "type": "amelioration|expansion|nouveau_projet|risque",
      "description": "...",
      "actions_concrets": ["action 1", "action 2", ...],
      "effort_estime": "1j|1semaine|1mois",
      "potentiel_revenu": "faible|moyen|fort|tres_fort"
    }
  ],
  "synthese": "...",
  "priorite_absolue": "titre du conseil le plus urgent"
}
```

## PROMPT GEMINI
Systeme: "Tu es un conseiller business expert en produits numériques, e-commerce, KDP Amazon, Etsy, et monétisation d'IA. Tu donnes des conseils concrets, actionnables et pragmatiques. Tu évites le jargon et les généralités. Chaque conseil doit avoir des étapes concrètes."

Utilisateur: "[CONSEIL_SUJET]\n\nContexte supplémentaire:\n[CONSEIL_CONTEXTE]"

Modèle: `gemini-2.0-flash-exp`, `temperature: 0.7`

## EXTRACTION
- Appeler Gemini en mode texte plain (PAS application/json pour éviter l'échec sur caractères spéciaux)
- Parser la réponse avec regex pour extraire un JSON entre ```json``` et ```
- Si parsing échoue : wrapper la réponse raw dans un champ `raw_response`

## WORKFLOW GITHUB ACTIONS
Créer `.github/workflows/gemini_conseil.yml` :
- Trigger: push sur `.triggers/gemini_conseil` ou `workflow_dispatch` avec inputs: `sujet`, `contexte`
- Lit `sujet` et `contexte` depuis trigger file si push event
- Exécute `agent_gemini_conseiller.py`
- Commit le JSON résultant dans `data/conseils/`
- Variables d'env: `GEMINI_API_KEY` depuis secrets

## FORMAT TRIGGER FILE
```
sujet=améliorer qualité coloriage et passer à Runware
contexte=Pipeline Pollinations opérationnel, 30 pages générées, score audit 88/100
2026-05-27T11:00:00Z
```

## STDLIB ONLY
- `urllib.request`, `json`, `pathlib`, `os`, `re`, `datetime`
- PAS de `requests`, `openai`, `anthropic`

## CONTRAINTES
- Idempotent : ne réécrit pas un conseil existant pour le même sujet+date
- Crée `data/conseils/` si inexistant
- Exit 0 toujours (ne pas bloquer CI)
- Logs clairs : print("[CONSEIL] Sujet: ..."), print("[CONSEIL] Fichier: ...")
