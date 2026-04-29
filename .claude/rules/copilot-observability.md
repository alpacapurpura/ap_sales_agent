---
globs: "backend/src/modules/copilot/observability/**/*.py"
description: Stub — invoca copilot-expert skill
---

# Copilot Observability

Detalle (recording/pricing/cost/persistence/reporting/workers, tablas `copilot_llm_call`+`model_pricing_snapshot`, retention, PII redaction, best-effort writes) en `copilot-expert` skill → `references/copilot-observability.md`.

Trigger: tocas `backend/src/modules/copilot/observability/**` o queries de costo/billing/cycle.

**No-skip:** toda escritura observability `try/except + structlog warning` (no rompe turn). PII via `sanitize_payload(...)`.
