# Briefing 14 — scripts/lib/brain_utils.py

## OBJECTIF
Bibliothèque partagée utilisée par TOUS les agents Brain (Stratège, Prospecteur,
Architecte, Conseillers). Résout deux problèmes fondamentaux :

1. **Quota** : ne pas brider sur un seul provider. Chaque agent utilise
   le provider le mieux adapté à sa tâche (Gemini/Groq/Mistral/Cohere).

2. **Variété** : forcer des réponses différentes à chaque run en injectant
   un angle de réflexion différent + en interdisant de répéter les rapports
   précédents. Un LLM sans stimulation revient toujours aux mêmes réponses.

## FICHIER PRODUIT
`scripts/lib/brain_utils.py`

## CONTENU DU MODULE

### 1. LLM Router

Lit `data/config/llm_routing.json` (créer si inexistant avec defaults).

```python
DEFAULT_ROUTING = {
    "prospecteur": {
        "primary": "gemini",         # créativité, exploration large
        "fallback": ["groq", "mistral"]
    },
    "architecte": {
        "primary": "mistral",        # analyse technique, raisonnement
        "fallback": ["gemini", "groq"]
    },
    "stratege": {
        "primary": "gemini",         # synthèse + scoring
        "fallback": ["mistral", "groq"]
    },
    "roman_planner": {
        "primary": "gemini",         # narration + structure
        "fallback": ["groq"]
    },
    "roman_writer": {
        "primary": "groq",           # Llama 70B, rapide, créatif, pas de quota
        "fallback": ["gemini", "mistral"]
    },
    "cdc_generator": {
        "primary": "gemini",
        "fallback": ["mistral"]
    },
    "conseil": {
        "primary": "gemini",
        "fallback": ["mistral"]
    }
}
```

Fonction principale :
```python
def llm_call(agent_type: str, system: str, user: str,
             temperature: float = 0.7, max_tokens: int = 4000) -> str:
    """
    Tente le provider primaire, bascule sur les fallbacks si erreur.
    Retourne le texte brut de la réponse.
    Logue le provider utilisé et les tokens consommés dans data/logs/quota.jsonl
    """
```

Endpoints à implémenter (stdlib urllib uniquement) :
- **Gemini Flash** : `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent`
  - Auth: `?key=GEMINI_API_KEY`
- **Groq** : `https://api.groq.com/openai/v1/chat/completions`
  - Model: `llama-3.3-70b-versatile`
  - Auth: Bearer `GROQ_API_KEY`
- **Mistral** : `https://api.mistral.ai/v1/chat/completions`
  - Model: `mistral-small-latest`
  - Auth: Bearer `MISTRAL_API_KEY`

Tous en format JSON POST avec urllib.request.urlopen.
Timeout : 30s. Retry 1 fois si timeout. Si échec total : retourner `""`.

### 2. Angle Rotator

Sélectionne un angle de réflexion différent à chaque run.
Déterministe : `angle_index = week_number % len(angles)`
Sans appel API supplémentaire.

```python
ANGLES = {
    "prospecteur": [
        "Explore UNIQUEMENT les marchés B2B : vendre nos capacités à d'autres créateurs/entreprises, pas directement au consommateur final.",
        "Explore UNIQUEMENT les niches ultra-spécialisées que les grandes plateformes ignorent : trop petites pour elles, parfaites pour nous.",
        "Pense comme un investisseur qui cherche le x10 : qu'est-ce qui n'existe pas encore mais sera évident dans 12 mois ?",
        "Explore UNIQUEMENT les formats apparus ou explosés après 2024. Nouveaux formats, nouvelles plateformes, nouveaux comportements d'achat.",
        "Cherche les business qu'UNE SEULE personne fait discrètement et gagne bien. Invisible aux algorithmes, visible aux observateurs attentifs.",
        "Explore les opportunités de TRADUCTION ou d'ADAPTATION culturelle : un produit qui marche en anglais et qui n'existe pas dans d'autres langues.",
        "Challenge nos certitudes : qu'est-ce qu'on croit impossible ou hors de portée mais qui en réalité ne l'est pas avec notre stack actuelle ?",
        "Explore UNIQUEMENT les marchés à forte saisonnalité : rentrée, Noël, Saint-Valentin, été. Comment les anticiper 3 mois en avance ?",
        "Pense en HYBRIDES : croise deux de nos domaines existants pour créer quelque chose qu'aucun concurrent ne fait.",
        "Explore les marchés DISGRÂCIÉS : domaines que tout le monde évite en ce moment parce qu'il y a eu trop de spammeurs, mais qui ont encore une demande réelle.",
        "Explore ce qu'on peut faire avec SEULEMENT du texte et du code, zéro image. Marchés entièrement pilotables par LLM.",
        "Pense à l'AFFILIATION avancée : pas juste des liens, mais des systèmes de recommandation automatisés ultra-ciblés."
    ],
    "architecte": [
        "Perspective du client final qui reçoit notre produit : qu'est-ce qui lui semble médiocre ou incomplet ?",
        "Perspective de l'ingénieur DevOps : où est le risque de crash silencieux ? Qu'est-ce qui peut tomber sans qu'on le sache ?",
        "Perspective de la scalabilité : qu'est-ce qui casse ou se dégrade si on multiplie le volume par 10 ?",
        "Perspective du CFO : où perdons-nous de l'argent ou du temps sans le savoir ? Quelles inefficiences coûtent cher ?",
        "Perspective de quelqu'un qui reprend le système dans 6 mois sans documentation : où se perd-il ?",
        "Perspective de la sécurité et de la résilience : comment ce système pourrait-il être dégradé ou bloqué (ban plateformes, API morte, repo corrompu) ?",
        "Perspective de l'automatisation maximale : quelles actions Hugo fait encore manuellement qui pourraient être automatisées sans risque ?"
    ],
    "stratege": [
        "Maximise le potentiel de revenu à court terme (1-3 mois) avec ce qu'on peut produire AUJOURD'HUI sans clé image.",
        "Maximise la diversification : propose des produits dans des catégories qu'on n'a pas encore testées.",
        "Cherche l'angle COLLECTION : quel produit, s'il explose, ouvre une série de 10+ volumes ?",
        "Cherche le REFONTE gagnante : quel bestseller est mal noté pour une raison simple à corriger ?",
        "Maximise la VITESSE : quel produit peut être en vente dans 48h avec notre stack actuelle ?",
        "Cherche le CROSS-TREND : deux tendances qui ne se sont pas encore croisées mais dont le croisement ferait sens."
    ]
}

def get_angle(agent_type: str) -> str:
    """Retourne l'angle de la semaine courante pour cet agent."""
    from datetime import date
    week = date.today().isocalendar()[1]
    angles = ANGLES.get(agent_type, ["Explore de nouveaux angles."])
    return angles[week % len(angles)]
```

### 3. Report Memory

Empêche les répétitions en lisant les rapports précédents.

```python
def get_previous_propositions(reports_dir: str, agent_type: str,
                               max_reports: int = 4) -> str:
    """
    Lit les N derniers rapports JSON de cet agent.
    Extrait les titres/noms des propositions déjà faites.
    Retourne une chaîne à injecter dans le prompt :
    "INTERDIT de répéter ou paraphraser ces propositions déjà faites : [liste]"
    """
```

### 4. Temperature Schedule

```python
TEMPERATURE_SCHEDULE = {
    "prospecteur": lambda week: [0.9, 1.0, 0.85, 0.95, 1.0, 0.8][week % 6],
    "architecte":  lambda week: [0.6, 0.7, 0.65, 0.75][week % 4],
    "stratege":    lambda week: [0.7, 0.8, 0.75, 0.85][week % 4],
    "roman_writer": lambda week: 0.92,  # toujours élevé pour la créativité
}

def get_temperature(agent_type: str) -> float:
    from datetime import date
    week = date.today().isocalendar()[1]
    fn = TEMPERATURE_SCHEDULE.get(agent_type, lambda w: 0.7)
    return fn(week)
```

### 5. Quota Logger

```python
def log_api_call(agent_type: str, provider: str,
                 tokens_in: int, tokens_out: int, success: bool):
    """
    Ajoute une ligne dans data/logs/quota.jsonl :
    {"ts": ISO, "agent": ..., "provider": ..., "tokens_in": ...,
     "tokens_out": ..., "success": ..., "date": "YYYY-MM-DD"}
    Crée data/logs/ si inexistant.
    """
```

Fonction bonus :
```python
def check_daily_budget(provider: str, max_calls_today: int = 200) -> bool:
    """
    Lit quota.jsonl et vérifie que ce provider n'a pas dépassé
    max_calls_today aujourd'hui. Retourne False si dépassé.
    """
```

## FICHIER DE CONFIG À CRÉER
`data/config/llm_routing.json` : avec le contenu DEFAULT_ROUTING ci-dessus.

## SECRETS GITHUB NÉCESSAIRES
Le module lit ces env vars (optionnelles, basculement automatique si absentes) :
- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- `MISTRAL_API_KEY`

Si un provider n'a pas de clé, il est sauté automatiquement.

## CONTRAINTES
- STDLIB ONLY (`urllib.request`, `json`, `pathlib`, `os`, `datetime`)
- Pas de `requests`, `httpx`, `openai`
- Toutes les fonctions loguent clairement ce qu'elles font
- Import propre : `from scripts.lib.brain_utils import llm_call, get_angle, get_previous_propositions`
