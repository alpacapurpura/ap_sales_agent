---
story_id: luana-shared-lift
spec_version: 1
po_version: 1                                   # ★ self-drafted by /pm per autonomous batch §7.2 pre-auth 2026-05-11 ★
last_modified: 2026-05-11
ratified_by_chris: true                         # pre-auth §7.2 — auto-ratify if stays within ADR-001 + lift mode §7.3
drafted_by: /pm (claude-opus-4-7) lift mode self-draft
authority: SESSION-RESUME-AUTONOMOUS.md §5 Phase B + outcome §7.2 + §7.3
---

# Story 2 — Luana Shared Lift

## 1. Why

`backend/src/shared/` ya cumple la función de Luana core (~20k LOC). Lift mecánico
a packages versionados dentro del monorepo `luana-platform` previene el "lasagna de
condicionales" cuando Brand #2 (Vitalia) o #3 (Comunify) bootstraps en Stories 11-13.

## 2. Scope — lift mode (NO refactor)

### 2.1 Constraint: lift mode (per outcome §7.3)

**MUST DO:**
- Lift verbatim los archivos source desde AISALESHT a `~/luana-platform/core/`
- Preservar DDD boundaries (domain → infrastructure → application → api)
- Preservar nombres de classes, funciones, módulos
- Preservar APIs públicos sin cambios
- Preservar tests existentes (lift en mismo commit)
- Agregar per-package `pyproject.toml` / `package.json` (version `0.0.1-alpha`)
- Actualizar import paths INTERNOS dentro de luana-platform según nueva estructura

**MUST NOT DO:**
- ❌ Scope expansion (agregar features, refactor lógica)
- ❌ Renombrar módulos o classes (preservar names)
- ❌ Refactor boundaries DDD
- ❌ Cambiar tech stack o patterns
- ❌ Schema migration changes (DB stays in AISALESHT, Story 4 territory)
- ❌ Cross-brand decisions
- ❌ Publishing packages (Story 9)
- ❌ Modificar AISALESHT (Story 10 swaps imports)

### 2.2 Source → Destination mapping (per 00-story.md)

| Source AISALESHT path | Destination luana-platform path | Package name |
|---|---|---|
| `backend/src/shared/agent_observability/{recording,persistence,cost,pricing,application,workers,reporting}` | `core/luana-core-observability/src/luana_core_observability/` | `luana-core-observability` |
| `backend/src/shared/agent_observability/channels` + `backend/src/shared/infrastructure/channels` | `core/luana-core-channels/src/luana_core_channels/` | `luana-core-channels` |
| `backend/src/shared/domain_events` | `core/luana-core-events/src/luana_core_events/` | `luana-core-events` |
| `backend/src/shared/billing` | `core/luana-core-billing/src/luana_core_billing/` | `luana-core-billing` |
| `backend/src/shared/compliance` | `core/luana-core-compliance/src/luana_core_compliance/` | `luana-core-compliance` |
| `backend/src/shared/idempotency` | `core/luana-core-idempotency/src/luana_core_idempotency/` | `luana-core-idempotency` |
| `backend/src/shared/infrastructure/llm` | `core/luana-core-llm/src/luana_core_llm/` | `luana-core-llm` |
| `backend/src/shared/application/extraction` | `core/luana-core-extraction/src/luana_core_extraction/` | `luana-core-extraction` |
| `backend/src/shared/{links/ports,domain,infrastructure/{files,prompts,database,external,web,models},workers,api}` | `core/luana-core-platform/src/luana_core_platform/` | `luana-core-platform` |

**FE primitives:**

| Source AISALESHT path | Destination luana-platform path | Package name |
|---|---|---|
| `frontend/src/components/ui/` | `core/@luana/ui-kit/src/` | `@luana/ui-kit` |
| `frontend/src/lib/tokens/` | `core/@luana/design-tokens/src/` | `@luana/design-tokens` |
| `frontend/src/lib/format/` + `format-date.ts` + `format-money.ts` | `core/@luana/format/src/` | `@luana/format` |
| `frontend/src/lib/api/` + `http-client.ts` | `core/@luana/api-client/src/` | `@luana/api-client` |
| `frontend/src/lib/zod-schemas/` (if exists) + form schemas | `core/@luana/schemas/src/` | `@luana/schemas` |
| `frontend/src/hooks/` | `core/@luana/hooks/src/` | `@luana/hooks` |

Total: **9 Python + 6 TS = 15 packages** (architect resolves exact 10th Python package or confirms 9).

### 2.3 Tests lifting

Tests lift en mismo commit que su source code:
- `backend/tests/shared/agent_observability/` → `core/luana-core-observability/tests/`
- `backend/tests/shared/billing/` → `core/luana-core-billing/tests/`
- etc.
- `frontend/src/__tests__/components/ui/` → `core/@luana/ui-kit/tests/`
- etc.

Arch fitness tests (relevantes a shared/) → `core/tests/architecture/`.

### 2.4 Internal import path updates

Imports DENTRO de luana-platform usan paths nuevos:
- `from luana_core_observability.recording import TurnEnvelope` (NOT `from src.shared.agent_observability.recording...`)
- `import { Button } from '@luana/ui-kit'` (NOT `import { Button } from '@/components/ui/button'`)

Imports en AISALESHT NO se tocan (Story 10).

## 3. Acceptance criteria

### 3.1 Estructura

- [ ] 9 Python packages en `~/luana-platform/core/luana-core-*` con pyproject.toml at `version = "0.0.1-alpha"`
- [ ] 6 TS packages en `~/luana-platform/core/@luana/*` con package.json at `"version": "0.0.1-alpha"`, `"private": true`
- [ ] Cada package registrado en root `pyproject.toml` (`[tool.uv.workspace] members`) o `pnpm-workspace.yaml` (`packages: [...]`)
- [ ] `cd ~/luana-platform && uv sync --all-packages` GREEN
- [ ] `cd ~/luana-platform && pnpm install --frozen-lockfile` GREEN

### 3.2 Tests

- [ ] Cada Python package: `cd ~/luana-platform && uv run pytest core/luana-core-<name>/tests/` GREEN
- [ ] Cada TS package: `cd ~/luana-platform && pnpm --filter @luana/<name> test` GREEN (placeholder OK si no había tests originales)
- [ ] Arch fitness tests para boundaries GREEN

### 3.3 Lint + format

- [ ] `uv run ruff check core/luana-core-*` GREEN en luana-platform
- [ ] `pnpm lint` GREEN en luana-platform

### 3.4 No tocar AISALESHT

- [ ] `cd /home/chris/AISALESHT && git diff HEAD~1 HEAD --name-only | grep -E '^(backend/src/shared|frontend/src/(components/ui|lib|hooks))'` → empty (no AISALESHT files modified in Story 2)

### 3.5 No publishing

- [ ] No package has `publishConfig` in package.json
- [ ] No `.releaserc.json`
- [ ] No `release.yml` workflow

## 4. Halt criteria (auto-stop + escalate Chris)

1. Coupling oculto detectado entre packages (ej. `luana-core-observability` necesita symbol de `luana-core-platform` que aún no se lifteó) — escalate, /architect re-evalúa orden lift
2. Tests acoplados a paths viejos no resolubles en 3 fix iter — escalate
3. Auditor REJECTED + 3 auto-fix Opus iter fail — escalate (per §7.4)
4. Scope expansion needed — escalate
5. Cumulative cost > $1500 (cumulative incl Phase A) — soft check-in
6. Cross-brand architecture decision discovered — escalate

## 5. Out of scope

- iam/, tenant_profile/, tenant_domains/, commercial_calendar/, social_proof/, assets/ (Story 3)
- crm/, analytics/, advertising/, social_media/, landing/, connections/ (Story 4)
- brand/, offer/ (Story 5)
- copilot/ (Story 6)
- sales_agent/ (Story 7)
- campaigns/, scheduling/, extension SDK (Story 8)
- GH Packages publishing (Story 9)
- AISALESHT import swap to `@luana/*` (Story 10)

## 6. Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | Coupling oculto entre `shared/` sub-packages | High | Architect produce dependency-graph audit ANTES tickets. Si cycle → re-evaluar package boundaries. |
| 2 | Tests con paths viejos en mocks (`monkeypatch.setattr('src.shared...')`) | Medium | Lift tests + update mock paths en mismo commit |
| 3 | FE primitives con `@/...` aliases en imports | Medium | Update `tsconfig.json` paths en luana-platform + update package internal imports |
| 4 | Workspace member resolution (uv + pnpm) | Low | Story 1 already proved skeleton works; Story 2 just adds members |
| 5 | Duplicación temporal con AISALESHT (durante Story 2-9 ventana) | Low (accepted) | Story 10 cierra ventana lift import swap |

## 7. Scenario coverage (Gherkin-light per autonomous batch)

```gherkin
Scenario A — Python package lift
  Given backend/src/shared/billing/ exists in AISALESHT
  When /dev-team lifts to core/luana-core-billing/src/luana_core_billing/
  And pyproject.toml is created at core/luana-core-billing/pyproject.toml with version 0.0.1-alpha
  And tests lifted to core/luana-core-billing/tests/
  Then cd ~/luana-platform && uv sync --all-packages exits 0
  And cd ~/luana-platform && uv run pytest core/luana-core-billing/tests/ exits 0

Scenario B — TS package lift
  Given frontend/src/lib/format/ exists in AISALESHT
  When /dev-team lifts to core/@luana/format/src/
  And package.json created with version 0.0.1-alpha, private true
  Then cd ~/luana-platform && pnpm install --frozen-lockfile exits 0
  And cd ~/luana-platform && pnpm --filter @luana/format build exits 0

Scenario C — No AISALESHT mutation
  Given /dev-team finishes all tickets
  When git diff in AISALESHT
  Then NO file under backend/src/shared/ modified
  And NO file under frontend/src/{components/ui,lib,hooks}/ modified

Scenario D — Cross-package import works
  Given luana-core-observability lifted with import "from luana_core_platform.X import Y"
  When luana-core-platform also lifted
  Then uv sync resolves dependency
  And import works at runtime in test fixture

Scenario E — Arch fitness ratchet preserved
  Given lifted code with arch fitness tests
  When running pytest core/tests/architecture/
  Then 0 new violations
```

## 8. Notes for /architect

- Order matters: lift `luana-core-platform` (foundation) FIRST, then `luana-core-{observability,billing,...}` depending on it
- Per-package dependency graph: emit before tickets DAG. Architect produces it as 03-arch.md §X.
- Granularity per ticket: 1 package per ticket OR 1 dependency layer per ticket (architect decides based on coupling analysis)
- Validator pattern: per-package "uv sync + uv run pytest" GREEN; cross-package "import works" smoke
- 05-guidelines.md: must explicitly list AISALESHT paths as READ-ONLY (no modifications)
