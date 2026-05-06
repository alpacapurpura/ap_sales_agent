#!/usr/bin/env bash
# Hook PostToolUse Edit|Write: actualiza checkpoint.md del story tocado
# v4 paradigma post 2026-05-06 — stories en docs/product/stories/{id}/

set -u

REPO_ROOT="/home/chris/AISALESHT"
NOW_ISO=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Find checkpoint.md files dentro de docs/product/stories/ recientes (últimos 5 min)
find "${REPO_ROOT}/docs/product/stories" -name "checkpoint.md" -mmin -5 2>/dev/null | while read -r checkpoint; do
  # Update last_modified timestamp inline (preservar el resto)
  if grep -q "^last_modified:" "$checkpoint"; then
    sed -i "s/^last_modified:.*/last_modified: ${NOW_ISO}/" "$checkpoint"
  fi
done

exit 0
