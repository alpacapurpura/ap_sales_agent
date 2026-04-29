---
globs: "{backend/src/modules/analytics/**/*.py,frontend/src/features/growth-studio/**/*.{ts,tsx}}"
description: Stub — invoca metrics-expert skill
---

# Data Reliability Verification

4 layers (Growth Studio):
- 0 ETL execution — `make verify-etl provider={n}`
- 1 Source Probe (API == DB) — `make verify-probe-{p}`
- 2 Pipeline (DB == DTO) — `make verify-pipeline`
- 3 UI Fidelity (API == display) — `make verify-ui`

Trigger matrix + agregar provider workflow + anti-patterns en `metrics-expert` skill → `references/data-reliability.md`.

**No-skip:** modificar provider/stage-service/DTO/component sin layer correspondiente. Skip "small change" → no hay small data pipeline change.
