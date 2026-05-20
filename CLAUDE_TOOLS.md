# 🧰 OUTILLAGE CLAUDE CODE (famille A — boost de l'agent, ≠ libs business)

**Date** : 2026-05-20
**But** : rendre Claude (moi) plus méthodique, doté de mémoire, sobre en tokens.
À ne pas confondre avec `LIBRARIES_AND_REPOS.md` (libs qui servent les *produits*).

> Tout vit dans `~/.claude` et `~/.cargo`/`~/.local`, **hors du repo git**. Si
> l'environnement est recréé, relancer **`bash scripts/setup_claude_tools.sh`**.

---

## ✅ Installé (session 20/05)

| Outil | Type | Rôle | Licence |
|---|---|---|---|
| **superpowers** (`obra`) | plugin | Méthode dev structurée (brainstorm→plan→TDD), skills auto | MIT |
| **python-development** (`wshobson`) | plugin | Python 3.12+, FastAPI/Django, async | MIT |
| **debugging-toolkit** (`wshobson`) | plugin | Debug interactif + DX | MIT |
| **security-scanning** (`wshobson`) | plugin | SAST, secrets, OWASP — utile vu nos clés API | MIT |
| **skill-creator** | skill | Fabriquer/standardiser **nos** skills (les agents métier) | Apache-2.0 |
| **mcp-builder** | skill | Créer des serveurs MCP (intégrations : Telegram, etc.) | Apache-2.0 |
| **webapp-testing** | skill | Tester un front via Playwright (exports Godot web) | Apache-2.0 |
| **content-research-writer** | skill | Aide rédaction sourcée (listings, contenu) | Apache-2.0 |
| **image-enhancer** | skill | Upscale/sharpen images (base pipeline sprites) | Apache-2.0 |
| **claude-mem** (`thedotmack`) | MCP+daemon | Mémoire persistante entre sessions (chroma DB) | Apache-2.0 |
| **rtk** (`rtk-ai`) | binaire | Compresse la sortie des commandes (−60-90 % tokens) | MIT |
| **code-review-graph** (`tirth8205`) | CLI/MCP | Graphe AST du code, lecture ciblée. **MCP non activé** (à brancher sur gros codebase = jeux Godot) | MIT |

## 🗂️ Catalogues clonés (`~/claude_tools`)
- **ComposioHQ/awesome-claude-skills** — Apache-2.0 → ✅ exploitable, source des skills ci-dessus.
- **hesreallyhim/awesome-claude-code** — ⚠️ **CC BY-NC-ND 4.0** → **annuaire seulement**, interdit de copier/adapter en prod (NonCommercial + NoDerivatives). On l'utilise pour rebondir vers des repos sources (qui ont leurs propres licences).
- **yuxiaopeng/Github-Ranking-AI** — veille du top 100 repos IA.

## ⚙️ rtk — activation
Binaire prêt. Pour économiser réellement, préfixer les commandes verbeuses :
`rtk git diff`, `rtk log`, `rtk test`, `rtk grep`, `rtk find`. `rtk gain` montre les tokens économisés. Routing global non imposé (léger, pas intrusif).

## ❌ Écarté
- **everything-claude-code (ECC)** : trop intrusif (réécrit `~/.claude`).
- Les ~78 autres plugins wshobson : hors de notre stack (Unity, k8s, blockchain, .NET…) ou doublons (tdd, context-management).
