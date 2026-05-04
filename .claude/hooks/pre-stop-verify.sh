#!/usr/bin/env bash
# Hook Stop: warning si tree dirty con artefactos sin commitear

set -u

REPO_ROOT="/home/chris/AISALESHT"
cd "$REPO_ROOT" || exit 0

# Si hay archivos modificados/untracked en docs/projects/active/ → warn
DIRTY=$(git status --porcelain docs/projects/active/ 2>/dev/null | head -5)

if [ -n "$DIRTY" ]; then
  echo "[harness] WARN: docs/projects/active/ tiene cambios sin commitear:"
  echo "$DIRTY"
  echo "[harness] Considerá: stage by name + conventional commit antes cerrar."
fi

# Si hay checkpoint.md con phase != DONE pero work-in-progress → recordatorio
WIP_CHECKPOINTS=$(grep -rl "phase: " docs/projects/active/ 2>/dev/null | xargs grep -l "status: in-progress" 2>/dev/null | head -3)

if [ -n "$WIP_CHECKPOINTS" ]; then
  echo "[harness] Stories in-progress (resume next session leyendo estos):"
  echo "$WIP_CHECKPOINTS"
fi

exit 0
