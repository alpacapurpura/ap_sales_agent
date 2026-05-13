#!/usr/bin/env bash
# install_luana_core_editable.sh — Story 10 T-1.5 mitigation Halt Trigger #1 (2026-05-12)
# Installs all luana-core-* packages editable from /home/chris/luana-platform/core/
# Idempotent — safe to re-run.
#
# Context: T-2 builder raised Halt Trigger #1 (2026-05-12): luana-core packages
# NOT installed in AISALESHT venv. Chris ratified Option A' (Session 5 Phase 2):
# editable install all luana-core packages so T-2..T-7 codemod rewrites resolve
# `from luana_core_X import Y` imports correctly.
#
# NOTE: AISALESHT venv is ephemeral pre-archive (Story 10 closes AISALESHT as
# per Decisión 3A). This install is intentionally transitional.

set -euo pipefail

LUANA_CORE_DIR="/home/chris/luana-platform/core"
VENV_PIP="/home/chris/AISALESHT/backend/.venv/bin/pip"

if [[ ! -d "$LUANA_CORE_DIR" ]]; then
  echo "ERROR: $LUANA_CORE_DIR not found" >&2
  exit 1
fi

if [[ ! -x "$VENV_PIP" ]]; then
  echo "ERROR: AISALESHT venv pip not found at $VENV_PIP" >&2
  exit 1
fi

PACKAGES=()
EDITABLE_ARGS=()
for pkg_dir in "$LUANA_CORE_DIR"/luana-core-*/; do
  pkg_name=$(basename "$pkg_dir")
  PACKAGES+=("$pkg_dir")
  EDITABLE_ARGS+=("--editable" "$pkg_dir")
  echo "Will install: $pkg_name"
done

echo ""
echo "Installing ${#PACKAGES[@]} luana-core packages editable (single invocation to resolve cross-deps)..."
echo ""

# Install all packages in a single pip call so pip can resolve cross-package deps
# (individual installs fail because luana-core-X depends on luana-core-Y which is
# also local but not yet installed at that point).
"$VENV_PIP" install --quiet "${EDITABLE_ARGS[@]}" || {
  echo "FAILED: bulk editable install" >&2
  exit 1
}

echo ""
echo "All ${#PACKAGES[@]} packages installed."
