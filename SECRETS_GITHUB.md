# 🔐 Configuration des secrets GitHub Actions

Pour activer les pipelines IA (Hugging Face, Gemini, etc.), tu dois ajouter
tes clés API en tant que **secrets GitHub**. Ces clés sont **chiffrées**
et invisibles dans le code public.

---

## 📱 Étapes (depuis ton téléphone ou PC)

### 1. Va sur la page Secrets du repo

🔗 https://github.com/hugokeirsse-byte/365days/settings/secrets/actions

(Tu dois être connecté à ton compte GitHub propriétaire du repo.)

### 2. Clique sur **« New repository secret »**

Bouton vert en haut à droite.

### 3. Remplis 2 champs

| Champ | Valeur |
|---|---|
| **Name** | nom exact attendu par le code (voir liste ci-dessous) |
| **Secret** | colle ta clé API ici |

Puis clique **« Add secret »**. Tu ne pourras plus jamais voir la valeur après
(seul le code y a accès) → **sauvegarde-la dans Bitwarden en parallèle**.

---

## 🔑 Liste des secrets attendus par notre système

| Secret name | À récupérer sur | Active quoi ? |
|---|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/app/apikey | Les 5 cerveaux perpétuels + analyse vision coloring books + QC visuel des designs |
| `HF_API_KEY` | https://huggingface.co/settings/tokens (token type "Read") | Génération images SDXL/FLUX avec image de référence (IP-Adapter) + ControlNet line-art pour coloring books |
| `OPENAI_API_KEY` *(optionnel)* | https://platform.openai.com/api-keys | DALL-E 3 si tu paies (0.04$/image) — pas obligatoire, HF couvre |
| `PINTEREST_API_KEY` *(plus tard)* | https://developers.pinterest.com | Auto-publisher Pinterest (Sprint 3) |
| `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` *(plus tard)* | https://www.reddit.com/prefs/apps | Scraping Reddit amélioré (le système fonctionne déjà sans, via JSON public) |

---

## ⚡ Ordre de priorité

1. **GEMINI_API_KEY** (CRITIQUE) — gratuit 1500 req/jour. Active immédiatement les 5 brains 24/7.
2. **HF_API_KEY** (TRÈS IMPORTANT) — gratuit. Débloque la génération qualité supérieure des illustrations (i❤️X, coloring books premium).
3. Les autres : à la demande, plus tard.

---

## ✅ Comment vérifier que ça marche

Après avoir ajouté `GEMINI_API_KEY` :

1. Va sur https://github.com/hugokeirsse-byte/365days/actions
2. Clique sur le workflow **« Agent Brain Meta »**
3. Clique **« Run workflow »** → laisse les défauts → **Run workflow**
4. Attends 2-3 min. Tu dois voir **5 jobs verts** (un par cerveau).
5. Va dans `data/brain/` sur le repo → tu vois 5 fichiers JSON avec leurs propositions.

Si les 5 jobs sont gris ou affichent « PAUSED until GEMINI_API_KEY » → le secret n'est pas configuré correctement (vérifie l'orthographe exacte : `GEMINI_API_KEY` en majuscules avec underscores).

---

## 🛡️ Sécurité

- Les secrets GitHub sont **chiffrés au repos** et accessibles uniquement aux workflows du repo.
- Si tu rends ton repo public, **le code est visible** mais **les secrets restent privés**.
- Ne jamais coller une clé API dans le code Python ou les commits — toujours via `os.environ["GEMINI_API_KEY"]`.
- Si tu suspectes qu'une clé fuite : régénère-la immédiatement sur le service d'origine.

---

## 🆘 Tu as un souci ?

- Le bouton « New repository secret » n'apparaît pas ?
  → Tu n'es peut-être pas connecté avec le compte propriétaire du repo (`hugokeirsse-byte`). Reconnecte-toi.
- Le job échoue après ajout ?
  → Vérifie le nom EXACT (sensible à la casse) et qu'il n'y a pas d'espaces.
- Quota épuisé (429) ?
  → Le brain attend automatiquement et réessaie. Si récurrent, vérifie ta clé sur le dashboard Google AI Studio.
