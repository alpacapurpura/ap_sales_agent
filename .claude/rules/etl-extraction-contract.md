---
globs: "backend/src/modules/analytics/**/*.py"
description: Stub — invoca metrics-expert skill
---

# ETL Extraction Contract

SSoT 2 archivos:
- `backend/src/modules/analytics/domain/extraction_contract.py` — docs+test enforcement
- `backend/src/modules/analytics/domain/metric_catalog.py` — runtime semantics
- Auto-gen MD: `docs/etl/extraction-contract.md` (NUNCA edit manual)

**Antes ETL question:** leer `docs/etl/extraction-contract.md` PRIMERO.

**Después modificar** providers/pipeline/etl_service/scheduler/workers/catalog: 5-step → implement → update contract → re-check catalog → `make extraction-contract` → arch test.

Detalle (best practices reliability/correctness/observability, multi-stage, anti-patterns, queries prod) en `metrics-expert` skill → `references/etl-extraction-contract.md`.

**No-skip:** todo cambio analytics dispara los 5 pasos. Sin excepciones.
