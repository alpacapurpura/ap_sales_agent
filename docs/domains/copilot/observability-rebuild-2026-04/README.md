# Copilot Observability Rebuild — 2026-04

**Objetivo:** unificar observabilidad técnica + de negocio (costo LLM por tenant, ciclo billing 25-25) bajo **un único módulo cohesivo**, eliminando todo path duplicado o legacy.

**Driver:** plan anterior tendía a frankenstein (paralelo + deprecation lenta). Este rediseño impone migración total con switch atómico.

## Documentos en este folder

### Top-level (leer siempre antes de cada fase)

| Doc | Para qué |
|---|---|
| `README.md` | Este archivo. Índice y meta-info. |
| `ARCHITECTURE.md` | Estado objetivo: estructura del módulo, seams estables, schema DB. |
| `PRINCIPLES.md` | No-negociables. Reglas que no cambian fase a fase. |

### Por fase

Cada `phase-N-*/` contiene:

| Archivo | Propósito | Quién llena |
|---|---|---|
| `plan.md` | Tasks ejecutables con criterios de aceptación. | Pre-llenado por arquitecto. |
| `research-checklist.md` | Investigación SOTA Abril 2026 obligatoria al **iniciar** la fase. | Pre-llenado. Agente ejecutor verifica vigencia. |
| `completion-checklist.md` | Gates objetivos para declarar fase cerrada. | Pre-llenado. Agente verifica cada item. |
| `learnings.md` | Decisiones, sorpresas, atajos descubiertos. | Llenado por agente **durante/al final** de la fase. |
| `deferred-debt.md` | Items que NO se pudieron resolver y van a fase siguiente. | Llenado por agente al final de la fase. |

### Handoff prompts

`handoff-prompts/start-phase-N.md` — prompt literal para pegar en una conversación nueva y arrancar esa fase. Cada uno apunta a los docs que el agente debe leer y a las reglas globales del repo.

## Mapa de fases

| Fase | Objetivo en una línea | Riesgo al copilot | Duración estimada |
|---|---|---|---|
| **1 · Foundation** | Construir módulo nuevo aislado + tablas + worker pricing. NO conectado al hot path. | Cero (read-only en chat.py). | 1-2 días |
| **2 · Atomic Switch** | Un solo commit: cablear callback handler en graph, **borrar** trace_recorder/usage_tracking/llamadas dispersas. | Alto (commit grande, hot path). Requiere ventana sin WIP paralelo. | 1 día efectivo + 24h soak |
| **3 · Reporting + Hardening** | Streamlit billing dashboard, retention, PII redaction, alertas. | Bajo (read-only + workers). | 2 días |

**Estado final tras Fase 3:** un único módulo `backend/src/modules/copilot/observability/`, cero código muerto, schema OTel-compatible, reporte por tenant con ciclo configurable 25-25.

## Reglas globales (aplican a las 3 fases)

- Branch único: `development`. Nunca feature branches/worktrees salvo instrucción explícita.
- Stage por nombre: `git add path/file`. Prohibido `git add .` o `-A` (hay sesiones paralelas).
- Lint/tests/type-check NATIVE en WSL (`backend/.venv/bin/...`, `cd frontend && npx ...`). Nunca `docker exec` para esto.
- Docker SOLO runtime + migrations + DB.
- TDD obligatorio: tests primero, implementación después (ver `.claude/rules/tdd-mandatory.md`).
- Conventional Commits: `feat(copilot-obs): ...`, `chore(copilot-obs): ...`, etc.
- Migraciones idempotentes raw SQL (`IF NOT EXISTS`) — ver `.claude/rules/backend-migrations.md`.
- Tenant isolation: toda query filtra `tenant_id` (ver `.claude/rules/tenant-isolation.md`).

## Cómo se conecta con docs existentes

- `docs/domains/copilot/INDEX.md` — agregar entrada a este folder cuando Fase 3 cierre.
- `.claude/rules/copilot-resilience.md` — actualizar sección "Debug copilot" cuando schema cambie en Fase 2.
- `docs/etl/extraction-contract.md` — sin impacto (otro dominio).

## Referencia a la conversación origen

Este rediseño nace de la auditoría arquitectónica del 2026-04-26. Resumen de gaps detectados:

1. Costo+modelo guardado **agregado por turn** en JSONB (`turn_end.data`), no per-call.
2. Pricing hardcoded gpt-4o (otros providers caen a fallback incorrecto).
3. Sin snapshot pricing al call → re-cálculo retroactivo rompe billing.
4. Sin ciclo billing 25-25 modelado.
5. `event_type='llm_call'` documentado pero nunca emitido (drift schema vs realidad).
6. Sin FX rate snapshot.
7. Sin PII redaction (solo truncate).
8. Sin retention policy en `copilot_trace_event`.
9. ~10 sitios de `recorder.record(...)` esparcidos en `chat.py` = acoplamiento bidireccional copilot↔obs.

Ver `ARCHITECTURE.md` para la solución estructural.
