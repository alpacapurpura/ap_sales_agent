---
globs: "backend/src/modules/copilot/**/*.py"
description: Stub — invoca copilot-expert skill
---

# Copilot Resilience

Detalle (field discovery, module/route registration, debug via trazas, subagentes deepagents `task`) en `copilot-expert` skill → `references/copilot-resilience.md`.

Trigger: tocas `backend/src/modules/copilot/**` o user reporta bug copilot. Invoca skill antes coding.

**No-skip rule:** diagnóstico copilot SIEMPRE empieza con query a `copilot_trace_event`. Sin trace = bug observabilidad, fix recorder primero.
