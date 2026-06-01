# DÉCISIONS STRATÉGIQUES — 365days Factory

> Chaque décision importante est documentée ici pour ne jamais se reposer la même question.
> Format : `## [DATE] — [DÉCISION]` + contexte + alternatives rejetées

---

## 2026-06-01 — Architecture semi-automatique adoptée

**Décision** : Semi-auto (bot prépare, Hugo copie-colle et envoie) plutôt que full-auto.

**Raison** : Les plateformes (LinkedIn, Malt, email) détectent les bots et suspendent les comptes. Le temps économisé ne vaut pas le risque de ban.

**Rejeté** : Full automation via API/scraping (trop risqué ToS).

---

## 2026-06-01 — Un business à la fois

**Décision** : On ne lance pas le business #2 avant que le business #1 ait généré UNE vente réelle.

**Raison** : La dispersion est l'ennemi principal. On a tendance à construire sans vendre.

**Règle** : Un produit vendu = autorisation de passer au suivant.

---

## 2026-06-01 — Fal.ai remplace Pollinations pour toutes les images pro

**Décision** : Fal.ai + Flux.1 pour toute génération d'images vendables (~€0.003/image).

**Budget disponible** : €20 pour démarrer.

**Rejeté** : Pollinations (qualité insuffisante pour vente), Midjourney (trop cher pour automatisation), DALL-E (trop cher).

---

## 2026-06-01 — Nettoyage codebase

**Décision** : Suppression des scripts Tier D (jeux société, mobile apps, Godot) et de tous les scripts v2/v3/v4 obsolètes. Désactivation des crons sur tous les workflows sauf cdc_queue_manager + rapporteur_hebdo.

**Rejeté** : Garder tous les scripts "au cas où" (encombre, consomme des ressources, crée de la confusion).

---

## 2026-06-01 — Priorités business (à confirmer)

**Candidats Tier S+ :**
1. #91 Conformité AI Act — €2000-8000/mois, B2B, peu de concurrents FR
2. #92 Réponses Appels d'Offres — €3000-8000/mois, BOAMP public, besoin urgent

**Décision en attente** : Hugo choisit lequel lancer en premier.

---

## 2026-06-01 — URSSAF obligatoire avant première vente

**Décision** : Inscription auto-entrepreneur obligatoire avant toute vente.

**Lien** : autoentrepreneur.urssaf.fr (30 minutes)

**Règle** : Aucune transaction avant avoir le numéro SIRET.

---

## RÈGLES PERMANENTES

- **RGPD** : Jamais de base de données de leads personnels. B2B email légal si contact professionnel + opt-out.
- **"Solution first"** : On génère le livrable AVANT de contacter le prospect, pas après.
- **Pas de Terraform** : Risque de responsabilité légale si l'infra d'un client casse.
- **Pas de HLSL shaders** : Trop buggy, support impossible.

