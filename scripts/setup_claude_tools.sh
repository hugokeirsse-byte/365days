#!/usr/bin/env bash
# Réinstalle l'outillage "boost Claude Code" (famille A) sur un environnement neuf.
# Idempotent : relançable sans casse. Voir CLAUDE_TOOLS.md pour le détail.
# Usage : bash scripts/setup_claude_tools.sh
set -uo pipefail

log() { printf '\n=== %s ===\n' "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }

# --- 1. Plugins via marketplaces officiels -------------------------------
if have claude; then
  log "Marketplaces"
  claude plugin marketplace add obra/superpowers   2>&1 | tail -1 || true
  claude plugin marketplace add wshobson/agents     2>&1 | tail -1 || true

  log "Plugins (superpowers + noyau wshobson trié)"
  for p in \
    "superpowers@superpowers-dev" \
    "python-development@claude-code-workflows" \
    "debugging-toolkit@claude-code-workflows" \
    "security-scanning@claude-code-workflows"; do
    claude plugin install "$p" 2>&1 | tail -1 || true
  done
else
  echo "claude CLI absent — plugins non installés"
fi

# --- 2. Skills Apache-2.0 (catalogue ComposioHQ) -------------------------
log "Skills (Apache-2.0, copie depuis awesome-claude-skills)"
SK_SRC="$HOME/claude_tools/awesome-claude-skills"
[ -d "$SK_SRC" ] || git clone --depth 1 https://github.com/ComposioHQ/awesome-claude-skills.git "$SK_SRC" 2>&1 | tail -1
mkdir -p "$HOME/.claude/skills"
for s in skill-creator mcp-builder webapp-testing content-research-writer image-enhancer; do
  [ -d "$SK_SRC/$s" ] && cp -r "$SK_SRC/$s" "$HOME/.claude/skills/$s" && echo "  skill: $s"
done

# --- 3. Outils d'économie de tokens / analyse ----------------------------
log "rtk (proxy compression sortie commandes)"
if have cargo; then
  have rtk || cargo install --git https://github.com/rtk-ai/rtk 2>&1 | tail -2
else
  echo "cargo absent — rtk non installé"
fi

log "code-review-graph (graphe de code, MCP désactivé par défaut)"
if have uv; then
  have code-review-graph || uv tool install code-review-graph 2>&1 | tail -2
else
  echo "uv absent — code-review-graph non installé"
fi

# --- 4. claude-mem (mémoire persistante) — long, peut requérir un TTY ----
log "claude-mem (optionnel ; long, setup chroma DB)"
if have npx; then
  npx -y claude-mem@latest install 2>&1 | tail -5 || echo "claude-mem : à finir manuellement si interrompu"
fi

# --- 5. Catalogue de veille (consultation seule) -------------------------
log "Catalogues clonés dans ~/claude_tools (consultation)"
mkdir -p "$HOME/claude_tools"
# awesome-claude-code = CC BY-NC-ND : ANNUAIRE SEULEMENT, ne rien copier en prod
[ -d "$HOME/claude_tools/awesome-claude-code" ] || \
  git clone --depth 1 https://github.com/hesreallyhim/awesome-claude-code.git "$HOME/claude_tools/awesome-claude-code" 2>&1 | tail -1
[ -d "$HOME/claude_tools/Github-Ranking-AI" ] || \
  git clone --depth 1 https://github.com/yuxiaopeng/Github-Ranking-AI.git "$HOME/claude_tools/Github-Ranking-AI" 2>&1 | tail -1

log "Terminé. Vérifie avec : claude plugin list"
