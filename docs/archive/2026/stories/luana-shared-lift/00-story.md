# Story 2 — Luana Shared Lift

> **Outcome:** luana-platform-migration · **Sequence:** 2/14 · **State:** refining

## Why

`backend/src/shared/` ya es la pre-Luana (~20k LOC, 50% del trabajo hecho). Mapeo 1:1 a 10 packages versionados de Luana core. Lift mecánico.

## What

Cortar `shared/` en 10 packages publicados a GH Packages:

| Origen `shared/` | Destino package |
|---|---|
| `agent_observability/{recording,persistence,cost,pricing,application,workers,reporting}` | `luana-core-observability` |
| `agent_observability/channels` + `infrastructure/channels` | `luana-core-channels` |
| `domain_events/outbox` | `luana-core-events` |
| `billing` | `luana-core-billing` |
| `compliance` | `luana-core-compliance` |
| `idempotency` | `luana-core-idempotency` |
| `infrastructure/llm` | `luana-core-llm` |
| `application/extraction` | `luana-core-extraction` |
| `links/ports` + `domain` + `infrastructure/{files,prompts,database,external,web,models}` + `workers` + `api` | `luana-core-platform` |

FE primitives:
- `frontend/src/components/ui/` → `@luana/ui-kit`
- `frontend/src/lib/tokens/` → `@luana/design-tokens`
- `frontend/src/lib/format/` → `@luana/format`
- `frontend/src/lib/api/` → `@luana/api-client`
- `frontend/src/lib/zod-schemas/` → `@luana/schemas`
- `frontend/src/hooks/` → `@luana/hooks`

## Acceptance criteria

- [ ] 10 Python packages publicados a GH Packages como `0.0.2-alpha`
- [ ] 6 TypeScript packages publicados a GH Packages como `0.0.2-alpha`
- [ ] Packages tienen tests (lift de tests existentes en `backend/tests/shared/` + `frontend/src/__tests__/`)
- [ ] Cada package tiene `pyproject.toml` / `package.json` con dependencies declaradas
- [ ] Smoke test: nuevo `nicolify` repo (Story 10 placeholder) puede `pip install luana-core-platform==0.0.2-alpha` con éxito
- [ ] Arch fitness tests migrados a `luana-core/tests/architecture/`

## Out of scope

- Lift `iam`, `tenant_profile`, etc (Story 3)
- Lift `crm`, `analytics`, etc (Story 4)
- Update Nicolify imports (Story 10)

## Risks

- Coupling oculto entre `shared/` sub-packages (ej: observability importa de domain_events) — resolver con package dependency graph
- Tests acoplados a paths viejos — refactor imports cuidadoso

## Effort: 12-18 tickets, ~5 días Opus tool-time
