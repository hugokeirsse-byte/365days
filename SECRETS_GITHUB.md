# 🔐 Configuration des secrets GitHub Actions

Page secrets : https://github.com/hugokeirsse-byte/365days/settings/secrets/actions

Clique **« New repository secret »**, remplis Name + Secret, clique Add.
Sauvegarde chaque clé dans Bitwarden en parallèle (tu ne peux plus la relire après).

---

## 🔑 Secrets à configurer — par priorité

### 1. GEMINI_API_KEY — CRITIQUE (gratuit)
- **Obtenir** : https://aistudio.google.com/app/apikey
- **Quota gratuit** : 1500 req/jour (Gemini Flash)
- **Active** : tous les cerveaux Brain, B1 Stratège, Prospecteur, Architecte, CdC Roman/Coloriage/Low-content, Gemini Conseil, Novel Planner

### 2. GROQ_API_KEY — IMPORTANT (gratuit)
- **Obtenir** : https://console.groq.com → API Keys → Create API key
- **Quota gratuit** : 30 req/min, modèle Llama-3.3-70B-Versatile inclus
- **Active** : Roman Writer (chapitre par chapitre, rapide), fallback Architecte
- **Pourquoi** : économise le quota Gemini sur la partie la plus gourmande (38 chapitres)

### 3. MISTRAL_API_KEY — IMPORTANT (gratuit)
- **Obtenir** : https://console.mistral.ai → API Keys
- **Quota gratuit** : 1 req/s, Mistral Small inclus
- **Active** : Architecte Système (analyse technique), fallback général
- **Pourquoi** : meilleur pour le raisonnement analytique, économise Gemini

### 4. RUNWARE_API_KEY — GÉNÉRATION D’IMAGES (payant à l’usage)
- **Obtenir** : https://runware.ai → Dashboard → API Keys
- **Tarif** : ~$0.002/image (SD 1.5) à $0.006/image (SDXL/FLUX)
- **Active** : Coloriages IA (30 images/livre), couvertures Romans, Merch designs, tous les produits visuels
- **REMPLACE** : HF_API_KEY (HuggingFace est abandonné)
- **Sans cette clé** : Pollinations (gratuit) sert de fallback pour les tests

### 5. TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID — NOTIFICATIONS (optionnel)
- **Obtenir bot** : @BotFather sur Telegram → /newbot
- **Obtenir chat_id** : envoie un message à ton bot, puis `https://api.telegram.org/bot<TOKEN>/getUpdates`
- **Active** : notifications push quand un produit est prêt à valider (agent F1 Ops)

### 6. PINTEREST_API_KEY, REDDIT_CLIENT_ID/SECRET — PLUS TARD
- Pinterest : auto-publisher (Sprint 3+)
- Reddit : scraping amélioré (le système fonctionne sans via JSON public)

---

## 📊 Budget tokens/jour estimé (en régime normal)

| Provider | Appels/jour | Sous quota ? |
|---|---|---|
| Gemini Flash | ~80-120 | ✅ (limite : 1500) |
| Groq Llama 70B | ~50-80 | ✅ (limite : ~1400/jour) |
| Mistral Small | ~20-40 | ✅ (limite : ~86400/jour) |
| Runware (images) | 0-50 selon production | Facturation à l’usage |

Règle d’or : chaque agent utilise le provider optimal pour sa tâche.
Distribution configurable dans `data/config/llm_routing.json`.

---

## ✅ Vérifier que ça marche

1. Va sur https://github.com/hugokeirsse-byte/365days/actions
2. Clique **B1 Stratège** → **Run workflow** → attends 2-3 min
3. Un rapport apparaît dans `data/strategie/` avec les propositions de la semaine

---

## 🛡️ Sécurité

- Secrets chiffrés au repos, visibles uniquement par les workflows du repo
- Si tu rends le repo public : code visible, secrets restés privés
- Ne jamais coller une clé dans le code — toujours via `os.environ["NOM_CLE"]`
- Suspectes une fuite ? Régénère immédiatement sur le dashboard du service
