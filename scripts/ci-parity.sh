#!/usr/bin/env bash
# CI Parity — reproduce the GitHub Actions ``quality-gates`` job locally.
#
# Why this exists
# ===============
# ``/test-all`` runs natively in WSL for fast iteration (CLAUDE.md rule #2).
# Native runs differ from CI in three ways that have produced 5+ failed
# deploys this month alone:
#
#   1. ``backend/.env`` (84 keys, prod-mirror routing) vs the CI image's
#      baked-in ``backend/.env.test`` (~38 keys after sync).
#   2. Host TZ (UTC-3..-5) vs CI runner TZ=UTC. Date-boundary tests
#      (Lima locale, ISO week resets) flip outcome at midnight UTC.
#   3. Host RAM 16GB+ with no Node heap limit vs container ~1GB default.
#      ``tsc --noEmit`` and ``vitest run --coverage`` OOM only in CI.
#
# This script builds the SAME Docker test images CI builds (``test``
# stage of each Dockerfile) and runs the SAME steps with the SAME
# environment constraints. It is the deterministic gate we MUST pass
# before pushing to ``main`` — the workflow itself is just a remote
# replay of what runs here.
#
# Usage
# =====
#   scripts/ci-parity.sh              # full sweep (~5-8 min cold, ~2 min warm)
#   scripts/ci-parity.sh --skip-fe    # only backend (faster iteration)
#   scripts/ci-parity.sh --skip-be    # only frontend
#
# The first run is slow because Docker BuildKit fetches base images and
# installs deps. Subsequent runs reuse layer cache and complete in <2
# min unless ``requirements*.txt`` / ``package*.json`` changed.

set -euo pipefail

cd "$(dirname "$0")/.."

SKIP_BE=0
SKIP_FE=0
for arg in "$@"; do
  case "$arg" in
    --skip-be) SKIP_BE=1 ;;
    --skip-fe) SKIP_FE=1 ;;
    -h|--help)
      sed -n '2,30p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown flag: $arg" >&2
      echo "Usage: $0 [--skip-be] [--skip-fe]" >&2
      exit 2
      ;;
  esac
done

# ANSI colour helpers — kept inline so the script has no external deps.
red()    { printf "\033[31m%s\033[0m\n" "$*"; }
green()  { printf "\033[32m%s\033[0m\n" "$*"; }
blue()   { printf "\033[34m%s\033[0m\n" "$*"; }

step() {
  blue "── $* ──"
}

# Single shared env block — mirrors deploy-prod.yml ``env`` keys plus
# the heap bump that unblocks tsc/vitest in container-constrained RAM.
DOCKER_RUN_ENV=(
  -e TZ=UTC
  -e NODE_OPTIONS=--max-old-space-size=4096
)

if [ "$SKIP_BE" -eq 0 ]; then
  step "Building backend test image (Dockerfile target=test)"
  docker build \
    --target test \
    -f backend/Dockerfile \
    -t local-be-ci \
    backend/

  step "BE: ruff check"
  docker run --rm "${DOCKER_RUN_ENV[@]}" local-be-ci ruff check src

  step "BE: ruff format --check"
  docker run --rm "${DOCKER_RUN_ENV[@]}" local-be-ci ruff format --check src

  step "BE: pytest with coverage"
  # Mirrors deploy-prod.yml line 50-52. ``meta_provider`` excluded because
  # CI excludes it (live API integration not safe in CI sandbox).
  docker run --rm "${DOCKER_RUN_ENV[@]}" local-be-ci \
    pytest --cov=src/modules --cov=src/shared --cov-report=term -q \
    --ignore=tests/modules/analytics/test_meta_provider.py

  step "BE: pip-audit (security, advisory — matches deploy-prod.yml continue-on-error)"
  docker run --rm "${DOCKER_RUN_ENV[@]}" local-be-ci pip-audit --strict --desc || \
    printf "\033[33m  (advisory: pip-audit reported issues; CI has continue-on-error: true on this step)\033[0m\n"
fi

if [ "$SKIP_FE" -eq 0 ]; then
  step "Building frontend test image (Dockerfile target=test)"
  docker build \
    --target test \
    -f frontend/Dockerfile \
    -t local-fe-ci \
    frontend/

  step "FE: ESLint"
  docker run --rm "${DOCKER_RUN_ENV[@]}" local-fe-ci npm run lint

  step "FE: TypeScript (tsc --noEmit)"
  # Heap bump matches deploy-prod.yml — without it tsc OOMs at ~1GB.
  docker run --rm "${DOCKER_RUN_ENV[@]}" local-fe-ci npx tsc --noEmit

  step "FE: Vitest with coverage"
  docker run --rm "${DOCKER_RUN_ENV[@]}" local-fe-ci \
    npx vitest run --coverage

  step "FE: npm audit (security, advisory — matches deploy-prod.yml continue-on-error)"
  docker run --rm "${DOCKER_RUN_ENV[@]}" local-fe-ci npm audit --audit-level=high || \
    printf "\033[33m  (advisory: npm audit reported issues; CI has continue-on-error: true on this step)\033[0m\n"
fi

green "✓ CI Parity passed locally — safe to push to main."
