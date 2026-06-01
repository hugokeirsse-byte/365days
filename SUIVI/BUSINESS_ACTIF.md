# BUSINESS ACTIF : Conformité EU AI Act (#91)

> Mis à jour : 2026-06-01
> Statut : 🔄 EN CONSTRUCTION

---

## L'OFFRE

**Produit 1 — Template d'auto-audit AI Act** (Gumroad, passif)
- Prix : €49
- Ce que c'est : un document Word/PDF de 15 pages que le client remplit lui-même pour évaluer sa conformité
- Délai de livraison : immédiat (auto)
- Ce que Hugo fait : rien (automatique après paiement)

**Produit 2 — Audit Express 48h** (Malt + direct)
- Prix : €990
- Ce que c'est : Hugo envoie un questionnaire (5 min pour le client) → Claude génère un rapport PDF de 25 pages → Hugo relit 30 min → livraison par email
- Délai : 48h
- Ce que Hugo fait : relire 30 min + envoyer

**Produit 3 — Retainer mensuel** (après 3 ventes)
- Prix : €2500/mois
- Ce que c'est : 2 audits/mois + questions illimitées + mises à jour réglementaires
- À construire plus tard

---

## ICP (CLIENT IDÉAL)

- PME française 10-200 personnes
- Utilise l'IA dans ses process (RH, marketing, finance, CRM, support)
- A entendu parler de l'AI Act mais n'a rien fait
- Décideurs : DPO, DSI, directeur juridique, CEO startup tech
- Secteurs prioritaires : RH (screening CV = haut risque), fintech (scoring), santé, assurance

---

## CANAUX D'ACQUISITION (tous gratuits)

1. **Malt.fr** — profil "Expert Conformité EU AI Act" (crédibilité instantanée)
2. **LinkedIn** — outreach "solution first" : mini-audit gratuit d'un aspect → offre
3. **Gumroad** — template à €49 comme lead magnet → upsell audit complet

---

## PIPELINE TECHNIQUE

```
[Scanner LinkedIn/web]
       ↓
[Identifie entreprise utilisant IA]
       ↓
[Claude génère mini-audit GRATUIT personnalisé pour cette entreprise]
       ↓
[Hugo envoie par email/LinkedIn (copier-coller)]
       ↓
[Client intéressé → lien Gumroad/Malt]
       ↓
[Paiement reçu → webhook → Claude génère rapport complet]
       ↓
[Hugo relit 30 min → envoie PDF par email]
```

---

## STACK TECHNIQUE (100% GRATUIT)

| Composant | Outil | Coût |
|-----------|-------|------|
| Génération texte | Gemini API free tier | €0 |
| PDF | Python fpdf2 | €0 |
| Vente templates | Gumroad | €0 + 10% commission |
| Profil service | Malt.fr | €0 + commission à la mission |
| Automation | GitHub Actions | €0 (2000 min/mois) |
| Email livraison | Gmail | €0 |

---

## ACTIONS HUGO (faire depuis téléphone)

- [ ] **PRIORITÉ 1** : S'inscrire URSSAF auto-entrepreneur → autoentrepreneur.urssaf.fr (30 min)
- [ ] **PRIORITÉ 2** : Créer compte Gumroad → gumroad.com (10 min)
- [ ] **PRIORITÉ 3** : Créer profil Malt.fr avec titre "Expert Conformité EU AI Act" (30 min)
- [ ] **PRIORITÉ 4** : Vérifier que le secret GEMINI_API_KEY est bien dans GitHub Settings > Secrets

---

## STRUCTURE DU RAPPORT D'AUDIT

1. **Executive Summary** (1 page) — verdict global + 3 risques principaux
2. **Classification du système IA** — minimal/limité/haut risque/inacceptable
3. **Analyse des obligations** — par article AI Act applicable
4. **Gap analysis** — ce qui manque vs ce qui est requis
5. **Plan d'action priorisé** — 30j / 90j / 6 mois avec responsables
6. **Documentation à produire** — liste exacte des documents requis

---

## KPIs DE SUCCÈS

| Étape | Objectif | Délai |
|-------|----------|-------|
| Profils créés (Malt + Gumroad) | 1 | J+3 |
| Premier template publié sur Gumroad | 1 | J+7 |
| Premiers prospects contactés | 10 | J+14 |
| Première vente (template ou audit) | 1 | J+30 |
| Revenu mensuel stable | €2000/mois | M+3 |
