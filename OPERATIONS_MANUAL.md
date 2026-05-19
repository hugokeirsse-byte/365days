# 🛠️ OPERATIONS MANUAL — guide d'exploitation jour-à-jour

**Date** : 2026-05-19
**Public** : Hugo, sur Android Termux + GitHub Mobile, en condition réelle.

Ce manuel répond à : *« Qu'est-ce que je fais maintenant, là, tout de suite ? »*

---

## 🔌 1. ARCHITECTURE TECHNIQUE EN 1 SCHÉMA

```
┌──────────────────────────────────────────┐
│  TON TÉLÉPHONE ANDROID                   │
│  ├── Termux (terminal Linux portable)    │
│  │   ├── ~/empire/secrets/  (privé 600)  │
│  │   ├── ~/empire/orchestrator/          │
│  │   └── ~/empire/stage_local/           │
│  ├── Telegram (validation 1-clic)        │
│  ├── GitHub Mobile (suivi workflows)     │
│  └── Bitwarden (mots de passe)           │
└────────────┬─────────────────────────────┘
             │ SSH (clé privée)
             ↓
┌──────────────────────────────────────────┐
│  GITHUB (public, code + Actions cron)    │
│  ├── Secrets (clés API injectées run.)   │
│  ├── 27 workflows (en cron espacé)       │
│  ├── staging/<brand>/ (assets en attente)│
│  └── products/ (publié validé)           │
└────────────┬─────────────────────────────┘
             │ API calls outbound
             ↓
┌──────────────────────────────────────────┐
│  10 LLM-MINIONS gratuits (cloud)         │
│  Gemini, Groq, Mistral, HF, Replicate... │
└──────────────────────────────────────────┘
             │ génère assets
             ↓
┌──────────────────────────────────────────┐
│  STAGING + notif Telegram                │
│  → Hugo clique ✅/❌                       │
└──────────────────────────────────────────┘
             │ upload manuel ou via API
             ↓
┌──────────────────────────────────────────┐
│  PLATEFORMES (KDP, Redbubble, TGC...)    │
└──────────────────────────────────────────┘
```

---

## 📱 2. INSTALLATION TERMUX (Vague 0.3)

### 2.1 Packages essentiels (5 min)

```bash
# Dans Termux :
pkg update && pkg upgrade -y
pkg install -y python git openssh nano cronie jq curl wget rsync
pip install --upgrade pip
pip install requests beautifulsoup4 lxml fake-useragent jsonschema
```

### 2.2 Génération clé SSH pour GitHub (1 min)

```bash
ssh-keygen -t ed25519 -C "termux-hugo" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
# Copier la sortie → GitHub Settings > SSH Keys > New SSH key
```

### 2.3 Clone du repo en mode privé (2 min)

```bash
mkdir -p ~/empire && cd ~/empire
git clone git@github.com:hugokeirsse-byte/365days.git
cd 365days
# Le secret reste local :
mkdir -p ~/empire/secrets && chmod 700 ~/empire/secrets
touch ~/empire/secrets/api_keys.env && chmod 600 ~/empire/secrets/api_keys.env
```

### 2.4 Stockage des clés API (au fur et à mesure des inscriptions)

```bash
nano ~/empire/secrets/api_keys.env
# Coller, ligne par ligne :
# GEMINI_API_KEY=...
# GROQ_API_KEY=...
# MISTRAL_API_KEY=...
# (etc.)
```

Pour charger automatiquement :
```bash
echo 'set -a; source ~/empire/secrets/api_keys.env; set +a' >> ~/.bashrc
```

### 2.5 (Optionnel, avancé) Mini-LLM local via llama.cpp

Seulement si tu veux faire tourner un LLM **directement sur le téléphone** sans cloud :

```bash
pkg install -y cmake clang
git clone https://github.com/ggerganov/llama.cpp ~/empire/llama.cpp
cd ~/empire/llama.cpp && make -j
# Télécharger un modèle 1-3B léger en GGUF (ex: Llama 3.2 1B ou Phi-3.5 mini)
# Place le .gguf dans models/
./main -m models/llama-3.2-1b.gguf -p "résumé : ..."
```

→ Branché comme provider `"local"` dans `data/config/llm_routing.json`.
→ **Conseil** : ne pas l'utiliser pour de la production sérieuse, juste pour
tester ou pour des résumés courts si tu veux 0 dépendance cloud.

---

## 🤖 3. LE BOT TELEGRAM (Vague 8)

### 3.1 Création (5 min)

1. Sur Telegram, cherche `@BotFather` → `/newbot` → nom + username
2. Récupère le **bot token** (chaîne du genre `123456789:ABCdef...`)
3. Ajoute le bot à un canal privé (toi seul) ou conversation directe
4. Récupère ton **chat_id** : envoie un message au bot, puis va sur
   `https://api.telegram.org/bot<TOKEN>/getUpdates` → `chat.id`

### 3.2 Stockage des secrets

Dans Termux :
```bash
echo "TELEGRAM_BOT_TOKEN=<token>" >> ~/empire/secrets/api_keys.env
echo "TELEGRAM_CHAT_ID=<chat_id>" >> ~/empire/secrets/api_keys.env
```

Dans GitHub Secrets (Settings > Secrets > Actions) :
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 3.3 Types de notifs reçues

| Émoji prefix | Type | Boutons inline |
|---|---|---|
| 🆕 | Asset prêt à valider | ✅ Publier · ❌ Rejeter · 🔍 Voir détails |
| 🚨 | Score opportunité > 8/10 | 🚀 Lancer prod · 📌 File · ❌ Ignorer |
| ⚠️ | Décision LLM ambiguë | A · B · C · ❓ Demander Claude |
| 💔 | Bug critique (workflow failed 3×) | 🩹 Patch Gemini · 🧠 Claude · ⏸️ Pause |
| 📊 | Rapport hebdo (dim 23h) | (lecture seule) |

---

## 📅 4. ROUTINE QUOTIDIENNE D'HUGO (5-15 min/jour)

### Matin (5 min)
1. Ouvrir Telegram → voir les notifs ⚠️ et 🚨 de la nuit
2. Trancher les arbitrages (clic sur un bouton inline)
3. Valider 2-3 assets ✅ qui sont prêts en staging

### Midi (5 min, optionnel)
4. Ouvrir GitHub Mobile → onglet "Actions" → vérifier qu'aucun workflow n'est rouge
5. Si rouge ET pas déjà notifié par 💔, c'est un bug inhabituel — ping Claude via Telegram

### Soir (5 min, optionnel)
6. Lecture rapide du flux Telegram pour debriefer la journée

### Le dimanche (15 min)
7. Lire le 📊 Rapport hebdo (#24)
8. Identifier les modules à doubler ou à éteindre
9. Mettre à jour `data/whitelists/blacklist_copyright.json` si nouveaux refus plateformes
10. Faire un pull de la branche dans Termux : `cd ~/empire/365days && git pull`

---

## 🚀 5. LANCER UN NOUVEAU PIPELINE — checklist

Avant d'allumer le pipeline d'un module, valider 7 points :

- [ ] **L1** Le pipeline existe dans `.github/workflows/produce_<module>.yml`
- [ ] **L2** Les secrets GitHub nécessaires sont configurés
- [ ] **L3** Les comptes plateformes cibles sont créés (cf. INSCRIPTIONS_HUGO.md)
- [ ] **L4** W-8BEN rempli sur la plateforme US (si applicable)
- [ ] **L5** La niche est dans `whitelist_pd.json` (si Module U/V/W/P)
- [ ] **L6** Le bot Telegram fonctionne (envoyer un message test)
- [ ] **L7** Test dry-run : `gh workflow run produce_<module>.yml -f dry_run=true`

Si les 7 points sont verts → activer le cron en supprimant `if: ${{ github.event_name == 'workflow_dispatch' }}` du job principal.

---

## 🔍 6. DEBUG D'UN WORKFLOW EN ÉCHEC

```
PROBLÈME : workflow rouge
↓
ÉTAPE 1 : Lire le log dans GitHub Actions UI mobile (45 sec)
  → si "Bad credentials" : secret expiré, regénérer + update
  → si "Rate limit" : attendre 24h ou changer de provider
  → si "Permission denied" : vérifier secrets répertoire
↓
ÉTAPE 2 : Re-run le workflow (3 retry max)
↓
ÉTAPE 3 : Si toujours rouge, notif Telegram 💔 arrive auto
↓
ÉTAPE 4 : Cliquer 🩹 Patch Gemini (auto-correction tentative)
↓
ÉTAPE 5 : Si Gemini échoue, cliquer 🧠 Claude (intervention manuelle)
```

---

## 🛡️ 7. SÉCURITÉ — CE QUI NE DOIT JAMAIS ARRIVER

| Erreur | Conséquence | Prévention |
|---|---|---|
| `git push` contient un `.env` | Clés API exposées | `.gitignore` strict + `truffleHog` mensuel |
| Compte Bitwarden compromis | Tout exposé | 2FA Aegis (pas SMS) + YubiKey si possible |
| 1 seul email = compromission unique | Perte totale | 2FA partout + email secondaire de récupération |
| Bot Telegram piraté | Validations frauduleuses | Token jamais en clair, rotation annuelle |
| Push direct sur main sans review | Bug en prod | Toujours via PR (sauf docs) |

---

## 📊 8. KPI HEBDO À SURVEILLER

Le 📊 Rapport hebdo (#24) du dimanche 23h donne :

| KPI | Cible mois 1 | Cible mois 6 | Cible mois 12 |
|---|---|---|---|
| Assets produits / semaine | 20 | 80 | 200 |
| Assets validés / semaine | 15 | 60 | 150 |
| Assets uploadés / semaine | 12 | 50 | 120 |
| Tokens cloud consommés | < 5M | < 15M | < 30M |
| Tokens Claude consommés | < 200k | < 500k | < 1M |
| Revenus mensuels (€) | 0-50 | 200-800 | 1500-5000 |
| Plateformes actives | 3-5 | 7-10 | 10-12 |

---

## 🆘 9. EN CAS D'URGENCE — qui faire quoi

| Situation | Action immédiate | Ensuite |
|---|---|---|
| **Ban d'un compte** | Ne pas recréer immédiatement | Cf. SECURITE_ET_LEGAL.md §7.1 |
| **Strike copyright** | Retirer le produit | Mettre la niche en blacklist + analyser |
| **Compte bancaire gelé** | Activer le 2e compte | Réunir justificatifs URSSAF |
| **Bug bloquant > 24h** | Notif 💔 + clic 🧠 Claude | Hot-fix puis investigation |
| **Hugo malade / vacances** | Auto-publish reste actif pour brands bas risque | Modules moyen risque attendent retour |

---

## 📚 10. LIENS RAPIDES

- Strategy générale : `STRATEGY.md`
- Inscriptions actives : `INSCRIPTIONS_HUGO.md`
- Sécurité+légal : `SECURITE_ET_LEGAL.md`
- Automation : `AUTOMATION_BLUEPRINT.md`
- Reverse engineering : `REVERSE_ENGINEERING_BESTSELLERS.md`
- Triage modules : `MODULES_TRIAGE.md`
- Map business+agents : `MAP_BUSINESS_ET_AGENTS.md`
- Checklist nouvelle niche : `CHECKLIST_LANCEMENT_NICHE.md`
- Troubleshooting : `TROUBLESHOOTING.md`
