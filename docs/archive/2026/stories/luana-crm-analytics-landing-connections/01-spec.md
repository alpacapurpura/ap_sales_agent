---
story_id: luana-crm-analytics-landing-connections
spec_version: 1
po_version: 1                                   # ★ self-drafted by /pm per autonomous batch §7.2 pre-auth 2026-05-11 ★
last_modified: 2026-05-11
ratified_by_chris: true                         # pre-auth §7.2 — auto-ratify if stays within ADR-001 + lift mode §7.3
drafted_by: /pm (claude-opus-4-7) lift mode self-draft
authority: SESSION-RESUME-AUTONOMOUS.md §5 Phase D + outcome §7.2 + §7.3
---

# Story 4 — Luana CRM + Analytics + Landing + Connections lift

## 1. Why

4 módulos densos que constituyen el data + integration backbone. Lift mecánico habilita
Vitalia/Comunify/Lupulo bootstraps Stories 11-13 con misma ETL framework + connections
engine + landing generator.

## 2. Scope — lift mode (per outcome §7.3)

### 2.1 Constraint

**MUST DO:** lift verbatim, preserve DDD boundaries + names + APIs + tests, add per-package
pyproject.toml at 0.0.1-alpha, update import paths INTERNOS.

**MUST NOT DO:** scope expansion, rename, refactor ETL pipeline architecture, schema migration
changes, publishing, AISALESHT mutation, brand-specific adapter decisions.

### 2.2 Source → Destination mapping (per 00-story.md)

| Source AISALESHT | Destination luana-platform | Package |
|---|---|---|
| `backend/src/modules/crm/` | `core/luana-core-crm/src/luana_core_crm/` | `luana-core-crm` |
| `backend/src/modules/analytics/` | `core/luana-core-analytics-engine/src/luana_core_analytics_engine/` | `luana-core-analytics-engine` |
| `backend/src/modules/landing/` | `core/luana-core-landing/src/luana_core_landing/` | `luana-core-landing` |
| `backend/src/modules/connections/` | `core/luana-core-connections/src/luana_core_connections/` | `luana-core-connections` |

**Total: 4 Python packages.** (Lift `copilot_provider/` subfolders → DEFERRED Story 6 per Story 2+3 pattern.)

### 2.3 Tests lifting

- `backend/tests/modules/{crm,analytics,landing,connections}/` → `core/luana-core-{name}/tests/`
- Test mock paths updated to new module locations
- Existing test count preserved

### 2.4 ETL extraction-contract SSoT (analytics-specific)

Analytics module owns `make extraction-contract` workflow. Per `.claude/rules/etl-extraction-contract.md`:
- 2 source-of-truth files: `analytics/domain/extraction_contract.py` + `analytics/domain/metric_catalog.py`
- Auto-gen MD: `docs/etl/extraction-contract.md`

Story 4 MUST verify post-lift:
- `make extraction-contract` smoke runs OK in luana-platform (or equivalent invocation against `core/luana-core-analytics-engine/`)
- Architect resolves: where does `make` Makefile target live? (likely lift Makefile snippet too, or create local equivalent in `core/luana-core-analytics-engine/`)

### 2.5 Connections engine (NOT adapters)

Brand-specific channel adapters (Lupulo POS, Vitalia payment gateway, etc.) DO NOT migrate to core.
Story 4 lifts ONLY the engine:
- `connections/domain/` (channel base classes, adapter port abstractions)
- `connections/application/` (OAuth flow, registration patterns)
- `connections/infrastructure/` (registry, factory)
- `connections/api/` (REST endpoints generic)

Brand-specific adapters remain in AISALESHT until Stories 11-13 lift each to `vertical-{niche}/connections/`.

Architect identifies + lists any brand-specific files to DEFER (e.g., `connections/infrastructure/adapters/manychat_adapter.py` if such exists).

### 2.6 Internal import path updates

- `from src.modules.crm` → `from luana_core_crm`
- `from src.modules.analytics` → `from luana_core_analytics_engine`
- `from src.modules.landing` → `from luana_core_landing`
- `from src.modules.connections` → `from luana_core_connections`
- Cross-module Story 2+3 imports adjusted per pattern

AISALESHT NO se toca.

## 3. Acceptance criteria

### 3.1 Estructura

- [ ] 4 Python packages en `~/luana-platform/core/luana-core-{crm,analytics-engine,landing,connections}/` con pyproject.toml 0.0.1-alpha
- [ ] Cada registrado en root pyproject.toml workspace members
- [ ] `cd ~/luana-platform && uv sync --all-packages` GREEN
- [ ] Cross-package imports work (consumes Story 2+3 packages OK)

### 3.2 Tests

- [ ] Cada package: `uv run pytest core/luana-core-<name>/tests/` GREEN
- [ ] Aggregate run: `uv run pytest core/` GREEN (Stories 2+3+4 todos)
- [ ] Mock paths updated, no `monkeypatch.setattr('src.modules.X')` legacy

### 3.3 ETL contract regen smoke

- [ ] `cd ~/luana-platform && python -c "from luana_core_analytics_engine.domain.extraction_contract import ...; print('ok')"` succeeds
- [ ] Architect designs contract regen invocation strategy (Makefile lift OR script equivalent)
- [ ] Validator runs smoke OK

### 3.4 Connections engine (no brand adapters)

- [ ] Brand-specific adapters NOT lifted (architect lists which files defer + writes to DEFERRED-FILES.md)
- [ ] Engine packages skeleton functional (e.g., `ConnectionAdapter` ABC importable)
- [ ] Smoke test: stub adapter can register via engine

### 3.5 Lint + format

- [ ] `uv run ruff check core/luana-core-{crm,analytics-engine,landing,connections}` GREEN

### 3.6 No tocar AISALESHT

- [ ] `git diff <base SHA> HEAD --name-only` shows ZERO mutations of `backend/src/modules/{crm,analytics,landing,connections}/`

### 3.7 No publishing

- [ ] No publishConfig / .releaserc / release.yml / semantic-release

### 3.8 copilot_provider/ deferred (Story 6)

- [ ] `core/DEFERRED-FILES.md` appended with 4 new entries (one per module's copilot_provider/)

## 4. Halt criteria

1. Cross-Story coupling unresolvable (e.g., crm imports brand from Story 5)
2. ETL contract regen architecture impossible per lift mode (would require refactor)
3. Connections engine + adapter separation reveals tight coupling (would require refactor)
4. Auditor REJECTED + 3 auto-fix Opus iter fail
5. Scope expansion needed
6. Cumulative cost > $1500 — soft check-in
7. Brand-specific code in supposedly brand-agnostic engine

## 5. Out of scope

- brand/, offer/ (Story 5)
- copilot/ (Story 6)
- sales_agent/ (Story 7)
- campaigns/, scheduling/, extension SDK (Story 8)
- GH Packages publishing (Story 9)
- AISALESHT import swap (Story 10)
- Brand-specific adapters (Stories 11-13)

## 6. Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | analytics ETL pipeline reaches into other modules | High | Architect dep audit; if cycle → escalate |
| 2 | crm custom_fields system coupled to brand/offer | Medium | Architect verifies data-driven (no hardcoded brand) |
| 3 | connections OAuth flows brand-specific | Medium | Architect lists brand-specific files → defer Stories 11-13 |
| 4 | landing templates reference brand/offer | Low | Lift templates engine + verify renderer brand-agnostic |
| 5 | extraction-contract regen Makefile target | Medium | Architect designs lift strategy |
| 6 | Test count drop due to coupling-deferred tests | Low | Document in gate-output.json |

## 7. Scenario coverage

```gherkin
Scenario A — Package lift per module
  Given backend/src/modules/crm/ exists in AISALESHT
  When /dev-team lifts to core/luana-core-crm/src/luana_core_crm/
  And pyproject.toml created with version 0.0.1-alpha
  And tests lifted to core/luana-core-crm/tests/
  Then cd ~/luana-platform && uv sync --all-packages exits 0
  And cd ~/luana-platform && uv run pytest core/luana-core-crm/tests/ exits 0

Scenario B — ETL contract regen smoke
  Given luana-core-analytics-engine lifted with contract.py + metric_catalog.py
  When invoking contract regen (per architect's design)
  Then docs/etl/extraction-contract.md (or local equivalent) generated successfully
  And arch test catalog↔contract alignment passes

Scenario C — Connections engine no adapters
  Given /dev-team finishes Story 4
  When grep -r "ManyChat\|Stripe\|Lupulo\|Vitalia" ~/luana-platform/core/luana-core-connections/src/
  Then matches are limited to abstract names / docstrings, NOT concrete adapters

Scenario D — AISALESHT untouched
  Given /dev-team finishes all tickets
  When git diff in AISALESHT
  Then ZERO files under backend/src/modules/{crm,analytics,landing,connections}/ modified

Scenario E — No forward Story 5/6 imports
  Given lifted packages
  When grep -rE "from src.modules.(brand|offer|copilot|sales_agent|campaigns|scheduling)" ~/luana-platform/core/luana-core-{crm,analytics-engine,landing,connections}/src/
  Then empty

Scenario F — Arch fitness ratchet preserved
  Given lifted code with existing arch fitness tests
  When running pytest core/tests/architecture/
  Then 0 new violations, includes Story 3 brand-agnostic + no-forward-imports gates extended to Story 4 modules
```

## 8. Notes for /architect

- Order: emit dependency graph between 4 modules + Story 2+3 packages
- Granularity: 1 module per ticket (with sub-tickets if dense — analytics likely needs 3-4 sub-tickets for ETL framework / providers / scheduler / workers)
- ETL contract regen lift strategy MUST be in 03-arch.md (Makefile snippet location?)
- Connections engine vs adapter split: explicit list of deferred brand-specific files
- Validator pattern: per-package uv sync + pytest + ETL contract regen smoke
- 05-guidelines.md: brand-specific adapters in connections = DEFERRED list explicit
- copilot_provider/ subfolders DEFERRED Story 6 (pattern 4 entries to DEFERRED-FILES.md)
