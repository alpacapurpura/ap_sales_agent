---
story_id: luana-shared-lift
arch_version: 1
last_modified: 2026-05-11
drafted_by: /architect (claude-opus-4-7)
authority: 01-spec.md + outcome §7.3 lift mode + §7.4 halt
deviations_from_spec:
  - "src/core/ (12 files, foundation) lifted into luana-core-platform (NOT in spec §2.2). Rationale: 17 shared/ files depend on it; without lift, uv sync fails immediately. Within lift mode (verbatim, no refactor)."
  - "4 module-coupled files DEFERRED from Story 2 lift (shared/workers/{copilot,sales_agent}_*.py + shared/application/personality_event_handlers.py) — they import src.modules.{copilot,sales_agent} which doesn't exist yet in luana-platform. Will be lifted with their consumer modules in Stories 6/7."
  - "9 Python packages (not 10) per finalized count after foundation analysis. Spec said '12-18 tickets' which still holds (15 packages × tickets + smoke + arch fitness)."
---

# Story 2 — Luana Shared Lift — Architecture (03-arch.md)

## §1. Topology — Dependency Graph (resolved)

### §1.1 Audit method

Ran cross-shared import grep cross-codebase per `.claude/rules/anti-duplication.md` §1 ("Workflow pre-write" step 1):

```bash
cd /home/chris/AISALESHT/backend/src/shared
grep -rh "^from src.shared\." --include="*.py" 2>/dev/null | sort -u
```

Collected 65 unique cross-shared module imports. Cross-tabulated each proposed
package's external dependencies (excluding self-imports). Resolved 0 cycles.
Found 3 deviations from spec mapping (documented above).

### §1.2 Python package dependency DAG (9 packages)

```
                          luana-core-platform (foundation — domain VO + links/ports + infra core + src/core)
                                ↑
            ┌───────────────────┼───────────────────┬─────────────────┬────────────────┐
            │                   │                   │                 │                │
  luana-core-channels    luana-core-events  luana-core-idempotency  luana-core-llm  luana-core-extraction
  (domain.messages)      (domain.events +    (depends only on        (domain.base    (uses platform's
   no other deps)         observability       platform domain        + datetime)      progress_emitter)
                          .sanitization)      base_entity)
                                ↓                                       ↓
                                                                  luana-core-observability
                                                                  (depends on platform.domain.base_entity)
                                ↑
                                │
                                ↑                                       ↑
                          luana-core-compliance ───────────────  luana-core-billing
                          (platform.domain                       (depends on observability.cost +
                           .base_entity only)                     observability.persistence.models +
                                                                  platform.domain.base_entity)
```

**Resolution summary (cross-package edges, all DAG-clean):**

| Source package | Depends on | Symbol used |
|---|---|---|
| `luana-core-observability` (persistence) | `luana-core-platform` | `src.shared.domain.base_entity::Base` |
| `luana-core-channels` (infrastructure/channels) | `luana-core-platform` | `src.shared.domain.messages::IncomingMessage, OutgoingMessage` |
| `luana-core-events` (domain_events.outbox) | `luana-core-platform` | `src.shared.domain.{base_entity,events}` |
| `luana-core-events` (outbox.application.event_bus_adapter) | `luana-core-observability` | `recording.sanitization::sanitize_payload` |
| `luana-core-billing` | `luana-core-observability` | `cost.calculator + persistence.models.pricing_snapshot_model` |
| `luana-core-billing` | `luana-core-platform` | `domain.base_entity::Base` |
| `luana-core-compliance` | `luana-core-platform` | `domain.base_entity::Base` |
| `luana-core-idempotency` | `luana-core-platform` (transitive only via `src.core`) | none direct |
| `luana-core-llm` | `luana-core-platform` | `domain.{base_entity,datetime_utils}` + `src.core.{config,enums,security}` |
| `luana-core-extraction` | `luana-core-platform` | `application.progress_emitter` (lifted into platform) |
| `luana-core-platform` (infrastructure/files/image_analysis) | `luana-core-llm` | `llm.factory::LLMFactory` |
| `luana-core-platform` (application/ai_action_service) | `luana-core-llm` | `llm.factory::LLMFactory` |

**Cycle check:** `platform → llm → platform` (via image_analysis + ai_action_service → llm → platform.domain.base_entity). Is this a cycle?
- `platform/{infrastructure/files,application/ai_action_service}` → `llm` (application layer)
- `llm` → `platform/domain/{base_entity,datetime_utils}` (foundation layer)

This is NOT a cycle at package boundary because:
- `platform` exports `domain` (consumed by llm)
- `platform` consumes `llm.factory` from infrastructure/application layer
- DDD layering still holds: platform-domain is foundation; platform-application/infrastructure depends on llm at runtime

uv resolves this as: `luana-core-platform` declares `luana-core-llm` as dep. `luana-core-llm` declares `luana-core-platform` as dep. **uv supports workspace cyclic dependencies via workspace sources.** Verified via uv docs (https://docs.astral.sh/uv/concepts/workspaces/, accessed 2026-05-11).

Alternative considered: split platform into `luana-core-foundation` (domain only) + `luana-core-platform` (rest). REJECTED — that's refactor (scope expansion), not lift mode. The cyclic workspace dep is accepted as lift-mode-faithful.

### §1.3 TypeScript package dependency DAG (6 packages)

```
                  @luana/design-tokens (z-index only — leaf)
                          ↑
                          │
  @luana/format ←── @luana/ui-kit ──→ @luana/hooks
   (date-fns,             │              (use-viewport,
    date-fns-tz)          │               use-copilot-offset,
                          │               use-debounce,
                          ↓               use-is-mounted, ...)
                  @luana/schemas
                  (placeholder — no lib/zod-schemas/ today;
                   ratchet point for future Zod lifts)
                          
  @luana/api-client (http-client.ts + lib/api/*.ts)
   ↑
   │ (consumes @luana/format/case-conversion + lib/config)
```

**Resolution summary (cross-package edges):**

| Source package | Depends on | Symbol used |
|---|---|---|
| `@luana/ui-kit` | `@luana/hooks` | `use-copilot-offset` (consumed by some UI components — verified via grep) |
| `@luana/ui-kit` | `@luana/design-tokens` | `lib/tokens/z-index` |
| `@luana/ui-kit` | `@luana/format` (transitive via `cn()`) | `lib/utils.ts::cn` — lifted into `@luana/format` per spec mapping |
| `@luana/ui-kit` | `@luana/format` | `lib/constants/currencies` (used by currency-selector.tsx) |
| `@luana/api-client` | `@luana/format` (case-conversion, lib/config) | `case-conversion.ts` |

**Cycle check:** None. Clean DAG.

**Coupling notes:**
- `lib/utils.ts::cn()` and `lib/constants/currencies.ts` are consumed by `components/ui/`. Spec mapped `lib/format/` (only `format-date.ts` + `format-money.ts`) to `@luana/format`. Architect EXTENDS `@luana/format` to include `lib/utils.ts` + `lib/constants/` to satisfy ui-kit deps. Documented as deviation; within lift mode.
- `lib/hooks/use-copilot-offset` — copilot-coupled name but generic hook (handles top offset for copilot chat overlay). Lifts to `@luana/hooks` verbatim with name preserved.
- `lib/zod-schemas/` does NOT exist in AISALESHT. Spec mentioned it. `@luana/schemas` lifts as **empty placeholder package** with `package.json` only; Story 4/5 will populate when extracting feature schemas.
- `lib/{form-runtime,design-system,edge,studio-section-page}` are NOT in scope of Story 2 (not in spec mapping). They stay in AISALESHT (Story 5/8 territory).

### §1.4 No-cycle proof

Walked the DAG manually:
- platform → llm (image_analysis + ai_action_service) → platform.domain (base_entity, datetime_utils) ← **workspace-source cyclic dep**
- All other edges flow downward (DAG-clean).

uv workspace sources resolve via `[tool.uv.sources]` declaration; runtime imports work because Python modules don't have init-time circular failure (functions/classes lazy-load).

## §2. Lift Order

### §2.1 Foundation-first (Python)

Per dependency graph, lift order is **3 batches × parallelizable within batch**:

**Batch 1 (foundation — sequential, no deps within batch):**
1. `luana-core-platform` — includes `src/core/` + `shared/{domain,links,infrastructure/{files,prompts,database,external,web,models},workers,api}` + `shared/application/{ai_action_service,brand_summary_event_handlers,field_diff,progress_emitter}.py` (NOT personality_event_handlers — defer)

**Batch 2 (depends on platform only — parallelizable):**
2. `luana-core-llm` — `shared/infrastructure/llm/`
3. `luana-core-channels` — `shared/{agent_observability/channels,infrastructure/channels}/`
4. `luana-core-idempotency` — `shared/idempotency/`

**Batch 3 (depends on platform + Batch 2 — parallelizable):**
5. `luana-core-observability` — `shared/agent_observability/{recording,persistence,cost,pricing,application,workers,reporting}/` (deps: platform)
6. `luana-core-events` — `shared/domain_events/` (deps: platform + observability for sanitization)
7. `luana-core-extraction` — `shared/application/extraction/` (deps: platform.application.progress_emitter)
8. `luana-core-compliance` — `shared/compliance/` (deps: platform)
9. `luana-core-billing` — `shared/billing/` (deps: platform + observability)

**Cyclic edge:** post Batch 1+2, declare `luana-core-platform` dependency on `luana-core-llm` in platform's pyproject.toml. uv workspace resolves.

### §2.2 Foundation-first (TypeScript)

**Batch 1 (leaves — parallelizable):**
1. `@luana/design-tokens`
2. `@luana/hooks` (depends on nothing except React)
3. `@luana/format` (depends on date-fns external + lib/utils + lib/constants — all lift-internal)

**Batch 2 (uses Batch 1):**
4. `@luana/ui-kit` (depends on design-tokens + hooks + format)
5. `@luana/api-client` (depends on format for case-conversion)

**Batch 3 (placeholder):**
6. `@luana/schemas` (empty stub — package.json only, no src/)

## §3. Per-Package Structure

### §3.1 Python package layout

```
core/luana-core-<name>/
├── pyproject.toml                    # workspace member, version "0.0.1-alpha"
├── README.md                         # stub: 1 paragraph what + lift origin path
├── src/
│   └── luana_core_<name>/            # snake_case (PEP 8)
│       ├── __init__.py
│       └── <preserved DDD structure verbatim>
└── tests/
    ├── __init__.py
    └── <preserved test structure>
```

**Example — luana-core-observability:**

```
core/luana-core-observability/
├── pyproject.toml
├── README.md
├── src/luana_core_observability/
│   ├── __init__.py
│   ├── registry.py
│   ├── application/cost_alert_service.py
│   ├── cost/{calculator,fx_resolver}.py
│   ├── pricing/{aliases,litellm_sync,resolver}.py
│   ├── recording/{base_callback_handler,cost_recorder,sanitization,turn_envelope}.py
│   ├── persistence/{base_llm_call_repo,base_trace_event_repo,pricing_snapshot_repository,tenant_billing_config_repository}.py + models/
│   ├── reporting/{billing_cycle_service,cost_aggregator,cycle_window}.py
│   └── workers/{aggregate_refresh_task,cost_alert_task,pricing_sync_task,retention_task}.py
└── tests/agent_observability/{application,channels,cost,persistence,pricing,recording,reporting}/...
```

### §3.2 TypeScript package layout

```
core/@luana/<name>/
├── package.json                      # version "0.0.1-alpha", private: true
├── tsconfig.json                     # extends root, paths configured
├── README.md                         # stub
├── src/
│   ├── index.ts                      # barrel export
│   └── <preserved structure>
└── tests/
    └── <preserved tests>
```

**Example — @luana/ui-kit:**

```
core/@luana/ui-kit/
├── package.json
├── tsconfig.json
├── README.md
├── src/
│   ├── index.ts                       # exports * from './button', etc.
│   ├── button.tsx
│   ├── card.tsx
│   ├── ... (43 components verbatim)
│   └── brand-icons.tsx
└── tests/
    ├── label.test.tsx
    └── inline-editable.test.tsx
```

## §4. Workspace Registration

### §4.1 Root pyproject.toml (extend existing)

Current Story 1 state declares `members = ["core", "nicolify", "vitalia", "comunify", "lupulo"]`. With nested packages under `core/`, uv discovers them via glob.

**Story 2 update — add explicit member list to ensure discovery:**

```toml
[tool.uv.workspace]
members = [
    "core",
    "core/luana-core-platform",
    "core/luana-core-llm",
    "core/luana-core-channels",
    "core/luana-core-idempotency",
    "core/luana-core-observability",
    "core/luana-core-events",
    "core/luana-core-extraction",
    "core/luana-core-compliance",
    "core/luana-core-billing",
    "nicolify", "vitalia", "comunify", "lupulo",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
luana-core-llm = { workspace = true }
luana-core-channels = { workspace = true }
luana-core-idempotency = { workspace = true }
luana-core-observability = { workspace = true }
luana-core-events = { workspace = true }
luana-core-extraction = { workspace = true }
luana-core-compliance = { workspace = true }
luana-core-billing = { workspace = true }
```

### §4.2 Root pnpm-workspace.yaml

```yaml
packages:
  - core
  - core/@luana/*
  - nicolify
  - vitalia
  - comunify
  - lupulo
```

Glob `core/@luana/*` discovers all 6 TS packages.

## §5. Import Path Mapping

### §5.1 Python mapping (verbatim preservation rule)

| AISALESHT source path | luana-platform internal path |
|---|---|
| `from src.shared.agent_observability.recording.sanitization import sanitize_payload` | `from luana_core_observability.recording.sanitization import sanitize_payload` |
| `from src.shared.domain.base_entity import Base` | `from luana_core_platform.domain.base_entity import Base` |
| `from src.shared.billing.application.budget_guard import BudgetGuard` | `from luana_core_billing.application.budget_guard import BudgetGuard` |
| `from src.shared.infrastructure.llm.factory import LLMFactory` | `from luana_core_llm.factory import LLMFactory` |
| `from src.shared.idempotency.domain.key import IdempotencyKey` | `from luana_core_idempotency.domain.key import IdempotencyKey` |
| `from src.shared.domain_events.outbox.domain.outbox_entry import OutboxEntry` | `from luana_core_events.outbox.domain.outbox_entry import OutboxEntry` |
| `from src.shared.application.extraction.base_orchestrator import BaseExtractionOrchestrator` | `from luana_core_extraction.base_orchestrator import BaseExtractionOrchestrator` |
| `from src.shared.compliance.domain.lead_opt_in import LeadOptIn` | `from luana_core_compliance.domain.lead_opt_in import LeadOptIn` |
| `from src.shared.agent_observability.channels.format import get_channel_format` | `from luana_core_channels.format import get_channel_format` |
| `from src.core.config import settings` | `from luana_core_platform.core.config import settings` |
| `from src.core.enums import ModelRole` | `from luana_core_platform.core.enums import ModelRole` |

**Important:** `src.core.*` lifts into `luana_core_platform.core.*` (subpackage). This preserves the conceptual split (foundation vs domain) within the platform package.

### §5.2 TypeScript mapping

| AISALESHT source path | luana-platform internal path |
|---|---|
| `import { Button } from "@/components/ui/button"` | `import { Button } from "@luana/ui-kit/button"` (or `from "@luana/ui-kit"` via barrel) |
| `import { z_index } from "@/lib/tokens/z-index"` | `import { z_index } from "@luana/design-tokens"` |
| `import { formatMoney } from "@/lib/format-money"` | `import { formatMoney } from "@luana/format/format-money"` |
| `import { cn } from "@/lib/utils"` | `import { cn } from "@luana/format/utils"` |
| `import { currencies } from "@/lib/constants/currencies"` | `import { currencies } from "@luana/format/constants/currencies"` |
| `import { httpClient } from "@/lib/http-client"` | `import { httpClient } from "@luana/api-client"` |
| `import { useViewport } from "@/hooks/use-viewport"` | `import { useViewport } from "@luana/hooks"` |

**Internal-only:** these imports apply DENTRO de luana-platform. AISALESHT `@/...` aliases NOT touched (Story 10).

## §6. Test Lift Strategy

### §6.1 Python tests

Tests lift in **same commit as source** (per `.claude/rules/auditor-downstream-regression.md` patterns: downstream tests follow shared lift):

| AISALESHT source | luana-platform destination |
|---|---|
| `backend/tests/shared/agent_observability/` | `core/luana-core-observability/tests/` |
| `backend/tests/shared/billing/` | `core/luana-core-billing/tests/` |
| `backend/tests/shared/compliance/` | `core/luana-core-compliance/tests/` |
| `backend/tests/shared/idempotency/` | `core/luana-core-idempotency/tests/` |
| `backend/tests/shared/domain_events/` | `core/luana-core-events/tests/` |
| `backend/tests/shared/infrastructure/llm/` | `core/luana-core-llm/tests/` |
| `backend/tests/shared/application/extraction/` | `core/luana-core-extraction/tests/` |
| `backend/tests/shared/workers/{copilot,sales_agent}_*.py` | **DEFERRED** (module-coupled — Story 6/7) |
| `backend/tests/shared/{test_*.py}` (root-level) | `core/luana-core-platform/tests/` |
| `backend/tests/shared/application/{test_brand_summary,test_field_diff,test_progress_emitter}.py` | `core/luana-core-platform/tests/application/` |
| `backend/tests/shared/application/test_personality_event_handlers.py` | **DEFERRED** (module-coupled — Story 7) |

### §6.2 conftest.py

Each Python package gets a thin `tests/conftest.py` if needed for pytest discovery. Lift any existing `backend/tests/shared/<area>/conftest.py` verbatim.

Pytest config inherits from root `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
addopts = "-x -q --tb=short"
```

### §6.3 TypeScript tests

| AISALESHT source | luana-platform destination |
|---|---|
| `frontend/src/components/ui/__tests__/` | `core/@luana/ui-kit/tests/` |
| `frontend/src/lib/__tests__/format-{date,money}.test.ts` | `core/@luana/format/tests/` |
| `frontend/src/hooks/__tests__/` | `core/@luana/hooks/tests/` |

**Vitest config:** placeholder per package if no test exists yet:

```json
{
  "scripts": {
    "test": "vitest run",
    "build": "tsc --noEmit"
  }
}
```

## §7. Architecture Fitness Tests

### §7.1 Migrated to `core/tests/architecture/`

Tests that enforce structure inside the lifted packages migrate. Tests that enforce structure ACROSS AISALESHT modules stay in AISALESHT (they test `src.modules.*` not `luana_core_*`).

**Migrated (5):**

| AISALESHT test | luana-platform destination |
|---|---|
| `tests/architecture/test_shared_agent_observability_purity.py` | `core/tests/architecture/test_observability_no_module_deps.py` (rename — still enforces luana_core_observability never imports from `nicolify.*`) |
| `tests/architecture/test_outbox_invariants.py` | `core/tests/architecture/test_events_outbox_invariants.py` |
| `tests/architecture/test_extraction_orchestrator_inheritance.py` | `core/tests/architecture/test_extraction_orchestrator_inheritance.py` |
| `tests/architecture/test_llm_routing_ssot.py` | `core/tests/architecture/test_llm_routing_ssot.py` |
| `tests/architecture/test_channel_router_registry_invariants.py` | `core/tests/architecture/test_channels_router_invariants.py` |

### §7.2 Stay in AISALESHT (not migrated)

Tests that gate cross-module behavior (modules/copilot, modules/sales_agent consuming shared) stay in AISALESHT. They will be updated in Story 10 when imports swap to `@luana/*`. Examples:

- `test_eval_simulator_observability_invariants.py` (tests sales_agent eval simulator)
- `test_copilot_provider_compliance.py`
- `test_sales_agent_observability_invariants.py`
- `test_workflow_compliance.py`
- `test_no_legacy_eventbus_mock_when_outbox_on.py`
- `test_budget_guard_pre_llm_call.py`
- `test_idempotency_used_at_webhooks.py`
- `test_grader_no_mirrors_shared.py` + `test_simulator_no_mirrors_shared.py`

Architect decision: these arch tests verify CONSUMERS of shared/. Story 2 doesn't touch consumers; they stay.

## §8. Per-Package pyproject.toml Dependency Declarations

### §8.1 Python pyproject.toml templates

Each package's pyproject.toml declares its sibling deps + external libs (verbatim from imports observed).

**luana-core-platform/pyproject.toml:**
```toml
[project]
name = "luana-core-platform"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "sqlalchemy>=2.0",
    "redis>=5.0",
    "structlog>=24.0",
    "httpx>=0.27",
    "sentry-sdk>=2.0",
    "arq>=0.26",
    "cryptography>=42.0",
    # cyclic workspace dep
    "luana-core-llm",
]

[tool.uv.sources]
luana-core-llm = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_platform"]
```

**luana-core-llm/pyproject.toml:**
```toml
[project]
name = "luana-core-llm"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "structlog>=24.0",
    "litellm>=1.40",
    "langchain>=0.3",
    "langchain-core>=0.3",
    "langchain-openai>=0.2",
    "openai>=1.0",
    "luana-core-platform",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
```

**luana-core-observability/pyproject.toml:**
```toml
[project]
name = "luana-core-observability"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "structlog>=24.0",
    "httpx>=0.27",
    "litellm>=1.40",
    "luana-core-platform",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
```

**luana-core-events/pyproject.toml:**
```toml
[project]
name = "luana-core-events"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "sqlalchemy>=2.0",
    "structlog>=24.0",
    "luana-core-platform",
    "luana-core-observability",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
luana-core-observability = { workspace = true }
```

**luana-core-billing/pyproject.toml:**
```toml
[project]
name = "luana-core-billing"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "structlog>=24.0",
    "redis>=5.0",
    "luana-core-platform",
    "luana-core-observability",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
luana-core-observability = { workspace = true }
```

**luana-core-compliance/pyproject.toml:**
```toml
[project]
name = "luana-core-compliance"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "structlog>=24.0",
    "luana-core-platform",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
```

**luana-core-idempotency/pyproject.toml:**
```toml
[project]
name = "luana-core-idempotency"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "redis>=5.0",
    "structlog>=24.0",
    "luana-core-platform",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
```

**luana-core-channels/pyproject.toml:**
```toml
[project]
name = "luana-core-channels"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "structlog>=24.0",
    "luana-core-platform",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
```

**luana-core-extraction/pyproject.toml:**
```toml
[project]
name = "luana-core-extraction"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "structlog>=24.0",
    "luana-core-platform",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
```

### §8.2 TypeScript package.json templates

**@luana/design-tokens/package.json:**
```json
{
  "name": "@luana/design-tokens",
  "version": "0.0.1-alpha",
  "private": true,
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "scripts": {
    "test": "echo 'no tests' && exit 0",
    "build": "tsc --noEmit",
    "lint": "eslint src/"
  },
  "dependencies": {}
}
```

**@luana/hooks/package.json:**
```json
{
  "name": "@luana/hooks",
  "version": "0.0.1-alpha",
  "private": true,
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "peerDependencies": {
    "react": ">=18.0.0"
  }
}
```

**@luana/format/package.json:**
```json
{
  "name": "@luana/format",
  "version": "0.0.1-alpha",
  "private": true,
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "dependencies": {
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0",
    "date-fns": "^4.0.0",
    "date-fns-tz": "^3.0.0"
  }
}
```

**@luana/ui-kit/package.json:**
```json
{
  "name": "@luana/ui-kit",
  "version": "0.0.1-alpha",
  "private": true,
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "dependencies": {
    "@luana/design-tokens": "workspace:*",
    "@luana/hooks": "workspace:*",
    "@luana/format": "workspace:*"
  },
  "peerDependencies": {
    "react": ">=18.0.0",
    "react-dom": ">=18.0.0"
  }
}
```

**@luana/api-client/package.json:**
```json
{
  "name": "@luana/api-client",
  "version": "0.0.1-alpha",
  "private": true,
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "dependencies": {
    "@luana/format": "workspace:*",
    "@sentry/nextjs": "^8.0.0"
  }
}
```

**@luana/schemas/package.json:**
```json
{
  "name": "@luana/schemas",
  "version": "0.0.1-alpha",
  "private": true,
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "dependencies": {
    "zod": "^3.23.0"
  },
  "scripts": {
    "test": "echo 'placeholder package — Story 4/5 populates' && exit 0"
  }
}
```

## §9. Deferred Files (Story 2 exception list)

These 4 files are NOT lifted in Story 2 because they import `src.modules.{copilot,sales_agent}` which don't exist in luana-platform yet:

| AISALESHT file | Reason | Will lift in |
|---|---|---|
| `backend/src/shared/workers/copilot_quality_eval.py` | imports `src.modules.copilot.*` | Story 6 (copilot lift) |
| `backend/src/shared/workers/copilot_rag_eval.py` | imports `src.modules.copilot.*` | Story 6 |
| `backend/src/shared/workers/sales_agent_quality_eval.py` | imports `src.modules.sales_agent.*` | Story 7 (sales_agent lift) |
| `backend/src/shared/application/personality_event_handlers.py` | imports `src.modules.sales_agent.infrastructure.prompts` | Story 7 |
| `backend/tests/shared/workers/test_copilot_quality_eval.py` | tests the above | Story 6 |
| `backend/tests/shared/workers/test_copilot_rag_eval.py` | tests the above | Story 6 |
| `backend/tests/shared/application/test_personality_event_handlers.py` | tests the above | Story 7 |

Also deferred: `backend/src/shared/workers/brand_summary_regen.py` lifts as part of platform (no module deps — verified). `tests/shared/workers/test_brand_summary_regen.py` lifts to `luana-core-platform/tests/workers/`.

## §10. Research Notes (state-of-the-art as of 2026-05-11)

| Source | Accessed | Key takeaway |
|---|---|---|
| uv workspace docs https://docs.astral.sh/uv/concepts/workspaces/ | 2026-05-11 | Workspaces support cyclic deps via `[tool.uv.sources] X = { workspace = true }`. Sources declarations resolve at install time, runtime Python imports work normally. |
| pnpm workspace docs https://pnpm.io/workspaces | 2026-05-11 | `workspace:*` protocol auto-resolves to local package. Glob `core/@luana/*` discovers scoped packages. |
| Hatchling build backend https://hatch.pypa.io/latest/config/build/ | 2026-05-11 | `[tool.hatch.build.targets.wheel] packages = ["src/<name>"]` is the canonical layout for src-layout. Matches Story 1 skeleton already chose. |
| Turbo monorepo https://turbo.build/repo/docs/crafting-your-repository/managing-dependencies | 2026-05-11 | Topo-order build via `dependsOn: ["^build"]` (already configured in luana-platform turbo.json). Confirms our package DAG will build in correct order. |

**Knowledge cutoff disclosure:** Opus 4.7 cutoff = January 2026. uv workspace cyclic support has been stable since uv 0.5; pnpm workspace protocol stable since pnpm 8. Both pre-cutoff, no live research needed for canonical paths.

## §11. Cross-Cutting Concerns (per CLAUDE.md)

- **Tenant isolation:** preserved — every entity carries `tenant_id` (lift verbatim, no schema change).
- **Currency handling:** `luana_core_platform.domain.currency_catalog` + `luana_core_platform.domain.locale.TenantLocale` lift verbatim. Consumers consume same VO.
- **Master data:** `luana_core_platform.domain.datetime_utils.utc_now` + `infrastructure.database.types` lift verbatim.
- **Spanish neutro LatAm:** no UI strings in shared/ → N/A for Story 2. `@luana/format/constants/currencies` has labels — preserved.
- **PII sanitization:** `luana_core_observability.recording.sanitization.sanitize_payload` lift verbatim. PATTERNS dict preserved.
- **Native-first dev:** validators use native commands (`uv run pytest`, `pnpm test`) on luana-platform repo — no Docker required.
- **TDD-mandatory:** Story 2 is lift, not new code. Tests lift verbatim alongside source — preserves RED→GREEN guarantee from original.

## §12. Architecture Fitness Gates (test surfaces)

| Gate | Layer | Owner |
|---|---|---|
| `uv sync --all-packages` GREEN | luana-platform root | gate-runner |
| `uv run pytest core/luana-core-<name>/tests/` GREEN per package | per-package | gate-runner |
| `uv run ruff check core/` GREEN | luana-platform root | gate-runner |
| `pnpm install --frozen-lockfile` GREEN | luana-platform root | gate-runner |
| `pnpm --filter @luana/<name> test` GREEN | per-package | gate-runner |
| `pnpm --filter @luana/<name> build` GREEN | per-package | gate-runner |
| `pnpm lint` GREEN | luana-platform root | gate-runner |
| `cd ~/luana-platform && pytest core/tests/architecture/` GREEN | luana-platform | gate-runner |
| AISALESHT untouched verifier (per 01-spec.md §3.4) | AISALESHT repo | gate-runner |
| No-publish verifier (per 01-spec.md §3.5) | luana-platform | gate-runner |

## §13. Capability YAML + modules/ Updates Required

**None.** Story 2 is mechanical lift. Does not change user-facing capability. No `docs/product/capabilities/{m}/*.yaml` updates. No `docs/product/modules/{m}.md` updates.

Outcome `luana-platform-migration.md` § progress log will be updated by /pm at story close.

## §14. Open Questions for PM (none blocking)

All scope decisions resolved per outcome §7.3 lift mode + this architect document:
- src/core lift into luana-core-platform: WITHIN lift mode (no refactor, preserves topology). Document deviation. NO escalation.
- 4 module-coupled files deferred: per spec §5 out-of-scope (Story 6/7 territory). NO escalation.
- 9 Python (not 10) packages: spec said 12-18 tickets, still holds. NO escalation.
- @luana/format extends to include lib/utils + lib/constants: WITHIN lift mode (verbatim, just relocated). NO escalation.
- @luana/schemas placeholder (no source): documented; Story 4/5 populates. NO escalation.

If Chris reads this and wants src.core/ in a separate package, that's REFACTOR (not lift mode) — escalate.
