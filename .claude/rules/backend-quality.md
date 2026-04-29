---
globs: "backend/src/**/*.py,backend/tests/**/*.py"
description: Stub — invoca backend-expert skill
---

# Backend Quality

- Ruff 70+ rules, 0 errors. Config `backend/pyproject.toml`. Line 120, py311.
- 10 arch fitness gates en `backend/tests/architecture/` (DDD boundaries ratchet ~95, API contracts, conventions, currency, ETL, master-data, Meta invariants, naming, domain purity).
- Pytest asyncio auto, fail_under=43%. Markers: `integration`, `verify`.
- Native commands (NUNCA docker exec).

Detalle (rules list completa, per-file overrides, jscpd/interrogate, naming conventions, todos los arch tests) en `backend-expert` skill → `references/backend-quality.md`.
