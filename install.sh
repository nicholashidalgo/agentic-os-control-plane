#!/usr/bin/env bash
# install.sh - first-time setup for agentic-os-control-plane
# Safe to rerun: creates missing dirs, never overwrites existing config.yaml
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "==> agentic-os-control-plane: setup"
echo ""

# 1. Create required directories
DIRS=(
  vault/raw
  vault/wiki
  vault/projects
  vault/daily
  data
  logs
)
for d in "${DIRS[@]}"; do
  if [ ! -d "$REPO_ROOT/$d" ]; then
    mkdir -p "$REPO_ROOT/$d"
    echo "    created  $d/"
  else
    echo "    exists   $d/"
  fi
done

# 2. Copy config.example.yaml to config.yaml (only if config.yaml is absent)
if [ ! -f "$REPO_ROOT/config.yaml" ]; then
  cp "$REPO_ROOT/config.example.yaml" "$REPO_ROOT/config.yaml"
  echo ""
  echo "    created  config.yaml (copied from config.example.yaml)"
else
  echo ""
  echo "    exists   config.yaml, not overwritten"
fi

# 3. Install Python dependencies
if [ -f "$REPO_ROOT/requirements.txt" ]; then
  echo ""
  echo "==> Installing Python dependencies..."
  python -m pip install -r "$REPO_ROOT/requirements.txt" --quiet
  python -m pip install -e "$REPO_ROOT" --quiet
  echo "    done"
fi

# 4. Done
echo ""
echo "==> Setup complete."
echo ""
echo "Next steps:"
echo "  1. Edit config.yaml to set your vault path (default: vault/)"
echo "  2. Run a demo skill:"
echo "       agentic-os list"
echo "       agentic-os run morning_brief"
echo "       agentic-os run research_digest --input vault/raw/sample_note.md"
echo "       agentic-os run policy_simulator --input vault/raw/sample_action_manifest.json"
echo "  3. Run tests:"
echo "       python -m pytest tests/ -v"
echo ""
