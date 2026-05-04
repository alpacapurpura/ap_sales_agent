# PI-11 — Backend Quality Guardrails

> Tipo: **maintenance transversal** (técnico). No es feature de negocio; es infraestructura de calidad de código.
> Owner: /pm
> Estado: **active, S1 not-started**
> Prioridad: **alta** (candidato a subir a Now cuando PI-5 S3 cierre o PI-9 se pause)

## Problema

El backend tiene **~10 tests fallidos** y **brechas de cobertura críticas** en módulos core que gestionan leads, citas y conversaciones de ventas. Esto genera:
- **Riesgo de regresión**: cambios en `sales_agent`, `copilot`, `brand` rompen CI sin detectarse.
- **Ceguera en módulos revenue-critical**: `crm` (59.3%) y `scheduling` (59.9%) tienen cobertura insuficiente para operar con confianza.
- **Drift arquitectónico**: tests de arquitectura (DDD boundaries, naming, anchors) rotos = normas no se enforcean.

## Outcome esperado

- **0 tests fallidos** en suite principal (`pytest` sin `--deselect`).
- **Cobertura ≥75%** en módulos P0 (`crm`, `scheduling`) y ≥80% en P1 (`sales_agent`, `copilot` orquestación).
- **Arch fitness 78/78 pasando** (sin allowlist creciente sin justificación).
- `/test-backend` verde como gate real (no solo aspiracional).

## Scope

### In scope
- Fix 10+ tests rotos (brand, copilot, sales_agent, shared, arch fitness).
- Aumentar cobertura P0/P1 (crm, scheduling, sales_agent, copilot, shared).
- Normalizar imports cruzados DDD detectados por `test_ddd_boundaries`.
- Actualizar snapshots de arquitectura (anchors, prompt fragments, naming).
- Fix potenciales bugs detectados por tests (outbox flags, Kimi temperature clamping).

### Out of scope
- Refactor funcional de negocio (sin cambiar comportamiento user-facing).
- Nuevos endpoints o features.
- Frontend (cobertura FE es PI separado si se decide).
- Integración con PostgreSQL en vivo (los verify/integration tests ya tienen su propio gate).

## Plan macro (sprints)

| Sprint | Tema | PRs | Objetivo |
|---|---|---|---|
| **S1** | Test integrity + coverage P0 | PR-1 fix tests + arch snapshots; PR-2 coverage lift crm/scheduling | Restaurar confianza en CI |
| **S2** | Coverage P1 + shared contracts | PR-3 coverage sales_agent/copilot; PR-4 shared/links/ports tests | Cerrar brechas agentic + transversales |

## Decisiones diferidas (por resolver en sprint)

- Default outbox `True` o `False` (tests asumen `False`, código defaultea `True`).
- Imports cruzados `campaigns -> sales_agent` y `crm -> campaigns` — ¿intencionales? Si sí, agregar a `KNOWN_CROSS_MODULE_IMPORTS`.
- Endpoint legacy `/voice/transcribe` — ¿remover tests legacy o mantener `410 Gone` como esperado?

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Scope creep funcional ("aprovecho y refactorizo X") | PRs = puro fix/tests. Sin cambio de comportamiento. |
| Cross-surface (business + agentic) en mismo PR | Split builders paralelos según routing matrix. |
| Tests rotos por refactoring paralelo (otra sesión) | Claim by commit inmediato; CI verde antes de push. |

## Cierre PI

- Todos los PRs shipped + RESULT.md escritos.
- `current-state/` NO se actualiza (este PI no agrega capacidades user-facing).
- `retro.md` con learnings sobre cobertura thresholds y proceso de mantenimiento transversal.

## Historial

| Fecha | Evento |
|---|---|
| 2026-05-01 | Creado por Chris — detectados 10+ tests fallidos + cobertura baja P0/P1 en análisis de backend. |
