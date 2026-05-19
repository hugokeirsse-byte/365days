# 🩹 TROUBLESHOOTING — résolution des erreurs courantes

**Doctrine** : avant d'appeler Claude (coûteux), passer par cette liste.
80% des problèmes sont résolus ici sans intervention LLM.

---

## 🔐 1. CLÉS API ET SECRETS

### "Bad credentials" / "Invalid API key"

| Cause | Solution |
|---|---|
| Token expiré | Regénérer sur le dashboard du provider → update Secret GitHub |
| Token mal copié (espace, retour ligne) | Re-coller proprement, valeur sans guillemet |
| Quota dépassé pour la journée | Attendre 24h OU bascule fallback chain |
| Secret pas exposé au workflow | Vérifier `env:` dans le YAML ou `secrets.X` |
| Mauvais nom de variable | Confirmer la casse exacte (case sensitive) |

### "Permission denied (publickey)" en `git push` depuis Termux

```bash
ssh -T git@github.com
# Si "Permission denied" : la clé n'est pas chargée
ssh-add ~/.ssh/id_ed25519
# Si "command not found" : pkg install openssh
# Si la clé est correcte mais GH refuse : re-coller le .pub dans GitHub Settings
```

---

## 🤖 2. WORKFLOWS GITHUB ACTIONS

### Workflow ne se déclenche pas au cron

| Cause | Solution |
|---|---|
| Repo inactif depuis 60 jours | GitHub désactive les crons → faire 1 commit ou ré-activer dans Actions tab |
| Cron syntax invalide | Tester sur https://crontab.guru/ |
| Workflow disabled manuellement | Actions tab > clique sur le workflow > Enable |
| Branche par défaut différente de `main` | Crons ne tournent que sur la branche par défaut |

### "Resource not accessible by integration"

→ Le workflow a besoin de permissions write mais ne les déclare pas.

```yaml
permissions:
  contents: write   # pour push
  pull-requests: write  # pour PR
```

### Build sort en erreur "ImportError: No module X"

→ Manque dans `pip install`. Ajouter au step :
```yaml
- run: pip install <module>
```

Ou utiliser `requirements.txt` au root + `pip install -r requirements.txt`.

---

## 🧠 3. LLM-MINIONS

### Gemini : "RESOURCE_EXHAUSTED"

→ Quota journalier épuisé (1500 req/j).
- Bascule automatique sur Groq via fallback chain
- Si Groq aussi épuisé → Mistral
- Si toute la chaîne épuisée → attendre reset (00h UTC pour Gemini)

### Groq : "rate_limit_exceeded"

→ 30 req/min. Implémenter rate-limiter Python :
```python
import time
time.sleep(2)  # entre chaque appel
```

### HuggingFace Inference : "Model is loading"

→ Le modèle se warm-up (cold start). Retry après 30s.
- Si > 3 retries fail : utiliser Replicate en fallback (coûte du crédit trial)

### Replicate : "402 Payment Required"

→ Trial 5$ épuisé. Choix :
1. Payer (Hugo décide, généralement non-prioritaire mois 1-3)
2. Rebasculer sur HF Inference (gratuit mais plus lent)
3. Skip cette tâche et alerter Hugo via Telegram

### Mistral : "InvalidRequestError: model has expired"

→ Mistral fait des updates de modèles. Mettre à jour `llm_routing.json`
avec le nom courant (vérifier doc Mistral).

---

## 🎨 4. GÉNÉRATION D'IMAGES

### Stable Diffusion sort une image avec texte gibberish

→ SD ne sait pas écrire. Solution :
- Générer l'image **sans texte** puis ajouter le texte via PIL/ReportLab
- OU passer par FLUX (meilleur pour texte court intégré)

### Mains à 6 doigts / anatomie cassée

→ Anti-Slop visuel (#21) score < 7 → boucle de correction.
- Ajouter au prompt négatif : "extra fingers, deformed hands, mutated fingers"
- OU utiliser ControlNet avec un input "main propre" en référence

### Coloring book : lignes non fermées (peinture déborde)

→ Pain point classique des bestsellers (cf. pain_points/<niche>.json).
- Augmenter le poids ControlNet lineart (1.2 → 1.4)
- Post-process OpenCV : `cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)` pour fermer les gaps
- Si toujours raté : passer en re-roll avec seed différente

---

## 📦 5. STAGING ET QA

### `qa_verdict: FAIL` sur 3 itérations consécutives

→ La niche/prompt est probablement faux.
1. Vérifier `winning_formula/<niche>.json` (la formule extraite est-elle saine ?)
2. Vérifier `pain_points/<niche>.json` (les pain points captés sont-ils pertinents ?)
3. Si formule saine mais output mauvais : escalade Telegram ⚠️ Hugo décide

### Asset existe mais `metadata.json` manquant

→ Producteur a planté à mi-chemin. Le validateur de schéma (#22) le détecte.
- Soit re-lancer le producteur (idempotent par design)
- Soit déplacer manuellement vers `archive/incomplete/`

### `validate_schemas.py` retourne erreur sur un fichier valide

→ Vérifier la version `jsonschema` :
```bash
pip install --upgrade jsonschema
```
Schema 2020-12 demande jsonschema ≥ 4.x.

---

## 📱 6. BOT TELEGRAM

### Pas de notif reçue

| Cause | Solution |
|---|---|
| Token mal configuré | Tester `curl https://api.telegram.org/bot<TOKEN>/getMe` |
| chat_id faux | Vérifier dans `getUpdates` après envoi d'un message au bot |
| Le bot a été bloqué | Débloquer dans la conversation |
| Rate limit Telegram (30/sec) | Implémenter throttling, batcher si beaucoup d'assets |

### Boutons inline ne déclenchent rien

→ Le workflow handler n'écoute pas les `callback_query`. Vérifier que :
- Le workflow `telegram_dispatch.yml` tourne en continu (long-polling) OU
- Le bot utilise un webhook (besoin URL publique → Render free tier)

---

## 💰 7. PLATEFORMES VENTE

### KDP refuse W-8BEN

→ Vérifier le **TIN** (Tax Identification Number). Pour Français :
- Numéro fiscal de référence (13 chiffres sur l'avis d'imposition)
- Inscrire dans le champ "Foreign TIN"
- Convention France-USA = 0% retenue (case à cocher "Treaty Benefits")

### Redbubble rejette un design pour "infringement"

→ Cf. SECURITE_ET_LEGAL.md §7.2 :
1. Retirer le design
2. Lire la raison (souvent : ressemblance avec marque déposée)
3. Ajouter pattern à `data/whitelists/blacklist_copyright.json`
4. Si certain du fair use : contester via leur form

### Etsy review étendue / suspension nouveau compte

→ Probablement trigger antifraude (compte récent + volume).
- Ralentir les listings (max 5/jour)
- Activer la photo de profil + bio complète
- Si suspendu : ticket support, joindre justificatifs identité

---

## 🐍 8. PYTHON / TERMUX

### "ModuleNotFoundError" malgré `pip install`

→ Termux a parfois 2 Python (python3 + python). Vérifier :
```bash
which python
python -c "import sys; print(sys.executable)"
pip --version
# Si conflits : pkg uninstall python && pkg install python
```

### "OSError: [Errno 28] No space left on device"

→ Termux espace plein. Nettoyer :
```bash
pkg autoclean
rm -rf ~/.cache/pip
df -h ~
# Si toujours plein : déplacer stage_local/ vers la carte SD
```

### Cron Termux ne se déclenche pas

```bash
# Vérifier que cronie tourne :
sv-enable crond
crond
# Ou alternative simpler : Termux:Tasker (app séparée) pour scheduler
```

---

## 🧹 9. GIT

### "rejected non-fast-forward"

→ Le remote a des commits que tu n'as pas en local.
```bash
git fetch origin
git pull --rebase origin <branch>
# Résoudre conflits si besoin, puis :
git push
```

### Branch désynchronisée avec main

```bash
git fetch origin main
git rebase origin/main
# Si conflits, fix puis :
git rebase --continue
```

---

## 🆘 10. QUAND VRAIMENT TOUT EST CASSÉ

1. **Snapshot local du repo** : `cp -r ~/empire/365days ~/empire/365days_backup_$(date +%s)`
2. **Rollback au dernier commit qui marchait** : `git log --oneline` puis `git checkout <sha>`
3. **Si même ça casse** : clone neuf dans un autre dossier, copier manuellement les changements utiles
4. **Notif Telegram 🧠 Claude** avec contexte précis : qu'est-ce qui marchait, qu'est-ce qui ne marche plus, dernière étape connue

→ Claude n'a pas le contexte de la session locale, donc fournir :
- Le log d'erreur exact (screenshot ou copie)
- Le dernier commit qui marchait (sha)
- Ce que tu as essayé
