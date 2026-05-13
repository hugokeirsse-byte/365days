# Mode d'emploi : robot de génération d'images IA

Ce robot génère 365 images en une seule commande, sans rien télécharger sur ton téléphone. Tout se passe sur les serveurs GitHub Actions et les images atterrissent directement dans le repo.

---

## Vue d'ensemble

```
Toi (téléphone Android)
    │
    │  1. Tu pousses un fichier prompts.py (les 365 consignes)
    ▼
Repo GitHub
    │
    │  2. Tu cliques "Run workflow" depuis l'app GitHub ou la page web
    ▼
GitHub Actions (gratuit, illimité sur repo public)
    │
    │  3. Le script appelle Pollinations.ai (gratuit) pour chaque prompt
    │     Les images sont commit dans le repo toutes les 20 réussites
    ▼
Dossier generated_images/ rempli avec 365 fichiers .jpg
```

Tu n'as **jamais** à stocker une image sur ton téléphone. Tu visualises les résultats directement depuis l'interface GitHub ou tu les télécharges au moment d'imprimer le livre.

---

## Étape par étape

### 1. Préparer la liste des prompts

À la racine du repo, crée un fichier `prompts.py` en t'inspirant de `prompts.example.py`.

Chaque entrée a cette forme :

```python
{
    "id": "1",
    "filename": "kappa",
    "prompt": "A traditional Japanese kappa yokai, ... ukiyo-e style ...",
    "seed": 1,   # optionnel
}
```

C'est ici que tu peux te faire aider de Gemini : tu lui demandes de te fabriquer les 365 prompts à partir d'un thème (« 365 cryptides du Japon »). Voir le **cahier des charges Gemini** (`CAHIER_CHARGES_GEMINI.md`) pour le briefing à lui donner.

### 2. Pousser `prompts.py` sur GitHub

Depuis ton téléphone, tu peux soit :
- l'envoyer à Claude qui le push automatiquement,
- ou ajouter le fichier directement via l'éditeur web GitHub (icône crayon sur la page du fichier),
- ou via une app comme Working Copy si tu manipules git en local.

### 3. Déclencher le workflow

Depuis ton téléphone :
1. Va sur https://github.com/hugokeirsse-byte/365days/actions
2. Clique sur **Generate AI images** dans la liste de gauche
3. En haut à droite, **Run workflow** → choisis la branche → **Run workflow**

Trois paramètres optionnels apparaissent (tu peux les laisser par défaut) :
- `model` : `flux` (qualité maximale, recommandé), `flux-realism` (style photo), ou `turbo` (rapide, moins beau)
- `width` / `height` : par défaut 1024×1024. Tu peux mettre 1536 ou 2048 si tu veux du grand format.

### 4. Surveiller l'avancée

Le workflow s'exécute pendant 30 min à 2h selon le nombre de prompts.

- Toutes les 20 images réussies, un commit "Checkpoint images IA : 20 images générées" apparaît dans l'historique du repo. Donc même si le workflow timeoute, tu ne perds jamais plus de 19 images.
- Les images apparaissent au fur et à mesure dans le dossier `generated_images/`. Tu peux les visualiser directement depuis l'app GitHub.

### 5. Relances et corrections

Le script est **idempotent** : il saute les images déjà présentes. Si une image te déplaît :
1. Supprime le fichier `001_kappa.jpg` correspondant dans `generated_images/` (depuis l'éditeur GitHub).
2. Modifie le prompt ou la seed dans `prompts.py`.
3. Relance le workflow : seule cette image sera régénérée.

---

## Astuces qualité

### Cohérence visuelle de la collection

Pour qu'un livre ait une identité, **tous les prompts doivent partager un même suffixe stylistique**. Exemple pour un livre sur les cryptides japonais :

```
… (description du sujet) …, traditional Japanese ukiyo-e woodblock print
style, muted earth tones, parchment paper texture, ink linework, highly
detailed mythological bestiary illustration
```

Gemini saura répliquer ce suffixe sur les 365 entrées si tu le précises dans le briefing.

### Format à viser

- Pour une page intérieure A5/A4 : 1024×1024 ou 1536×1536 suffit.
- Pour la couverture : génère plus grand (2048×2048) et garde plusieurs variantes (change la seed).
- Évite les formats non carrés au début : ça complique le cadrage final.

### Limites

- Pollinations.ai (Flux) **écrit mal le texte**. Ne demande jamais "with the word X written on it". Tu rajouteras tes typos avec le générateur de page.
- Sur sujets très précis (espèces réelles, monuments historiques), l'IA hallucine. Réserve l'IA aux thèmes fantastiques, symboliques, ou abstraits.
- Si plusieurs images de suite échouent : c'est probablement un soucis Pollinations temporaire, relance le workflow 10 min plus tard.

---

## Variantes pour les futurs livres

Quand tu attaqueras le livre suivant :

**Option A — repo dédié (recommandé)** : tu forke ce repo, tu vides `generated_images/` et `prompts.py`, tu remplis avec le nouveau thème. Chaque livre a son histoire git propre.

**Option B — sous-dossiers** : tu adaptes le workflow pour qu'il prenne un paramètre `book_slug` et écrive dans `livres/{book_slug}/images/`. Plus pratique si tu veux centraliser, mais le repo grossit vite.

Dis-moi quand tu en seras là, j'adapte.
