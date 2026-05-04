#!/usr/bin/env bash
# Hook PostToolUse Edit|Write: actualiza checkpoint.md del story/sprint/PI tocado
# Find checkpoint.md más cercano al archivo editado y touchea last_modified

set -u

# El hook recibe info del tool call. Para simplicidad, escaneamos el cwd
# y actualizamos cualquier checkpoint.md modificado en últimos 5 min.

REPO_ROOT="/home/chris/AISALESHT"
NOW_ISO=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Find checkpoint.md files dentro de docs/projects/active/ recientes
find "${REPO_ROOT}/docs/projects/active" -name "checkpoint.md" -mmin -5 2>/dev/null | while read -r checkpoint; do
  # Update last_modified timestamp inline (preservar el resto)
  if grep -q "^last_modified:" "$checkpoint"; then
    sed -i "s/^last_modified:.*/last_modified: ${NOW_ISO}/" "$checkpoint"
  fi
done

exit 0
