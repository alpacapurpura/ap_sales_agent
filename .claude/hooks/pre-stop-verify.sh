#!/usr/bin/env bash
# Hook Stop: warning si tree dirty con artefactos sin commitear
# v4 paradigma post 2026-05-06 — docs/projects/ removed, stories en docs/product/stories/

set -u

REPO_ROOT="/home/chris/AISALESHT"
cd "$REPO_ROOT" || exit 0

# Si hay archivos modificados/untracked en docs/product/stories/ → warn
DIRTY=$(git status --porcelain docs/product/stories/ 2>/dev/null | head -5)

if [ -n "$DIRTY" ]; then
  echo "[harness] WARN: docs/product/stories/ tiene cambios sin commitear:"
  echo "$DIRTY"
  echo "[harness] Considerá: stage by name + conventional commit antes cerrar."
fi

# Si hay checkpoint.md con state in {refining,refined,ready,developing,developed,reviewing} → recordatorio
WIP_CHECKPOINTS=$(grep -rl "^state:[[:space:]]*\(refining\|refined\|ready\|developing\|developed\|reviewing\)\b" docs/product/stories/ 2>/dev/null | head -3)

if [ -n "$WIP_CHECKPOINTS" ]; then
  echo "[harness] Stories WIP (next session lee estos):"
  echo "$WIP_CHECKPOINTS"
fi

exit 0
