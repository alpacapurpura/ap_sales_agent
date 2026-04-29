---
globs: "backend/tests/architecture/**/*.py"
description: Stub — invoca backend-expert skill
---

# Architectural Fitness Tests

Tests `backend/tests/architecture/` enforzan reglas estructurales que linters no catch (DDD boundaries, API contracts, conventions). **Ratchet pattern** — `KNOWN_*` allowlists shrink only.

Run: `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short` o `make arch-test`. Auto en `/test-backend`, `/test-all`, `/pase-produccion`.

Common fixes (cross-module/domain framework imports/missing response_model/hard deletes/SA 1.x query) en `backend-expert` skill → `references/architectural-fitness.md`.

**No-skip:** new violation = build fail. Allowlists shrink only — fix + remove. Add to allowlist requiere justificación commit.
