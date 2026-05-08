---
story_id: eval-foundation-simulator-homologation
surface: BE
sub_architect: /architect-be (skill backend-expert + tessl__fastapi)
arch_version: 1
last_modified: 2026-05-07T22:00:00Z
links:
  spec: 01-spec.md
  consolidated: 03-arch.md
  story_yaml: 00-story.md
  agentic_arch: 03-arch-agentic.md
  rules:
    - .claude/rules/anti-duplication.md
    - .claude/rules/backend-ddd.md
    - .claude/rules/backend-migrations.md
    - .claude/rules/architectural-fitness.md
    - .claude/rules/auditor-downstream-regression.md
    - .claude/rules/tenant-isolation.md
    - .claude/rules/master-data.md
---

## Decisión arquitectónica clave

Story B introduce **una surface BE production-code de superficie mínima**
(1 migration Alembic + 4 SQLAlchemy mirror models + 1 `register_agent_observability`
spec) que crea un **bucket de cost separado** `eval_simulator` siguiendo el
**precedente exacto del módulo `campaigns`** (PI-1 S0 PR-1 / Alembic 083), y
**una surface BE test-infrastructure** (DB-seed fixture `eval_tenant_seeded`
+ 5 arch fitness gates nuevos + entry en tabla SSoT downstream regression)
que materializa los `TenantContext` de Story A en filas DB mínimas con flag
aislante `is_eval_synthetic=True`. Cero `agent_kind` enum en DB (NO existe —
es discriminador de registry; verificación grep §2.4). Cero deuda futura:
schema mirror exact al patrón `campaign_llm_call`, una sola migration
idempotente, separación de tablas garantiza `WHERE eval_run_kind IS NULL`
NO requerido en queries de prod (las tablas de prod NO contienen tráfico
synthetic — separación física por tabla supera "filtro por metadata jsonb").

## Existing systems audit (NO NEW LAYER rule)

### Source of evidence

- [x] Self-run greps Path B (CONTEXT-BRIEF Haiku skipped — service-story con scope acotado tras 5 commits previos discovery)
- [x] Re-validación spec D1-D11 + H1-H10 + skill `sales-agent-expert` § "Surfaces compartidas con copilot"

### Audit cross-module ejecutado

```bash
# 1. agent_kind como enum DB (CRÍTICO — spec H6 lo asume "ALTER TYPE ADD VALUE")
grep -rn "agent_kind.*VARCHAR\|agent_kind ENUM\|TYPE.*agent_kind" backend/alembic --include="*.py"
# → cero resultados. agent_kind NO es enum DB; es literal en MV (`'sales_agent'::VARCHAR(32)`)
#   + str field en AgentObservabilitySpec dataclass + str discriminator en registry.

# 2. Patrón existente para nuevo bucket de cost
find backend/src/modules -name "observability" -type d
# → modules/{copilot,sales_agent,campaigns}/observability/. Cada uno: tabla propia + register_agent_observability.

# 3. Fixture DB-seed pattern existente
find backend/tests/agentic_evals/sales_agent/fixtures -name "*.py"
# → tenant.py (Visionarias real) + synthetic_tenant.py (T2 deterministic upsert) + entrypoint.py
#   Patrón precedente exacto para fixture B `eval_tenant_seeded`.

# 4. UUID5 deterministic uso previo
grep -rn "uuid5(NAMESPACE_DNS\|uuid.NAMESPACE_DNS" backend/src --include="*.py"
# → cero en src/ (solo en libs vendoreadas). NEW pattern justificado: idempotency H2 spec.

# 5. is_eval_synthetic / extra_metadata column existente
grep -rn "is_eval_synthetic\|is_synthetic\|extra_metadata" backend/src --include="*.py"
# → cero. NEW marker required.

# 6. ActorProfile / SimulationState / TerminationReason existing
grep -rn "class ActorProfile\b\|class SimulationState\b\|class TerminationReason\b" backend/src --include="*.py"
# → cero. NEW types — son test-infra (no production code), bajo backend/tests/.

# 7. EVAL_USER_SIMULATOR / SPECIALIST_TO_ROLE
grep -rn "EVAL_USER_SIMULATOR" backend/src --include="*.py"
# → cero. NEW — la decisión §2.5 (abajo) lo coloca en eval-only registry NO en LLM_ROLE_BY_SITE.
```

### Sistemas existentes encontrados

| Sistema | Path | Discriminador / Tabla | Factory / Spec | Providers / Adapters | Estado |
|---|---|---|---|---|---|
| **Cost bucket separation** | `shared/agent_observability/registry.py` + `modules/{copilot,sales_agent,campaigns}/observability/__init__.py` | `agent_kind: str` (registry) + `{prefix}_llm_call` table | `register_agent_observability(spec)` + `agent_observability_registry()` | 3 specs registered: `copilot`, `sales_agent`, `campaign` | active |
| **Cross-agent MV rollup** | Alembic 079 + Alembic 083 (campaigns extension) | `mv_daily_llm_cost_per_tenant_v2(agent_kind, tenant_id, occurred_on)` | UNION ALL en migration body | sales_agent + copilot rows | active. campaigns added en 083 sin tocar 079 (cross-agent MV refactor pending future migration) |
| **Bootstrap registration** | `shared/infrastructure/agent_observability_bootstrap.py` | imports trigger `register_agent_observability` side-effect | bootstrap module | sales_agent + copilot + campaigns | active |
| **Shared abstraction inventory** | `.claude/rules/anti-duplication.md` § "Inventario shared" | tabla SSoT 21 patterns | — | TurnEnvelope, FXResolver, PricingResolver, sanitize_payload, BaseAgentCallbackHandler, BaseTraceEventRepoProtocol, BaseLLMCallRepoProtocol, etc. | active. CADA UNO REUSADO (cero mirror) |
| **Eval test fixtures** | `backend/tests/agentic_evals/sales_agent/fixtures/{tenant,synthetic_tenant,entrypoint}.py` | DB-seed pattern + sales_agent_entrypoint closure | `pytest.fixture` | Visionarias real + T2 deterministic | active. Patrón base para `eval_tenant_seeded` |
| **TenantContext loader (Story A)** | `backend/tests/fixtures/eval/tenants/loader.py::load_eval_tenant` | dataclass(frozen=True) test-infra ONLY | `load_eval_tenant(slug) → TenantContext` | 5 archetype seeds YAML | done 2026-05-07 |
| **agent_app entrypoint** | `backend/src/modules/sales_agent/application/orchestrator/graph.py::agent_app` | LangGraph compiled StateGraph | `agent_app.ainvoke(state, config)` | supervisor → sales_agent_node | active. **NO TOCAR** §3 sales-agent-expert |
| **MultiRoleLLMRouter** | `backend/src/shared/infrastructure/llm/router.py` | `ModelRole` enum + `LLM_ROLE_BY_SITE` | `LLMFactory.get_service().generate_response(role=...)` | LiteLLMService (proxy único post T-4) | active. EXTEND read-only (consumir, no modificar SSoT) |

### Decisión por sistema

- **Cost bucket separation** (`shared/agent_observability/registry.py`): **EXTEND**. Patrón cementado: módulo nuevo con observability tiene su propia tabla + spec registrada. Story B introduce **NEW módulo de test-infra**, NO production module — pero el patrón se aplica idéntico para `eval_simulator` con caveat: el "módulo" registrante vive en `backend/tests/agentic_evals/sales_agent/simulator/` (test-infra), NO en `backend/src/modules/`. El código de SQLAlchemy models + register call vive en `backend/src/modules/sales_agent/observability/eval_simulator/` (production_code=true bajo R5 schema-mirror exception escalado: tabla `eval_simulator_llm_call` es business-module change normal, sigue el precedente de campaigns). **Justificación bucket separation**: H6 spec — separa cost queries de prod. Si compartiéramos `sales_agent_llm_call` con metadata jsonb filter, queries Streamlit existentes leen tráfico synthetic + degradan dashboards prod. Tabla aparte = filtro físico = cero pollution forward.

- **Cross-agent MV rollup** (Alembic 079): **EXTEND**. Migration nueva (124+) extiende MV con UNION ALL para `eval_simulator_llm_call`. Idempotente (`DROP MV IF EXISTS` + `CREATE MV IF NOT EXISTS`). Re-uses concurrent refresh pattern.

- **Bootstrap registration** (`shared/infrastructure/agent_observability_bootstrap.py`): **EXTEND**. Append `from src.modules.sales_agent.observability.eval_simulator import _eval_simulator_observability` (side-effect import).

- **Shared abstraction inventory** (`anti-duplication.md`): **REUSE verbatim**. NO mirror. Customer LLM call rows escritas via composición:
  - `BaseObservabilityContext` subclass `EvalSimulatorObservabilityContext` (nuevo, hereda de `BaseObservabilityContext`)
  - `BaseAgentCallbackHandler` subclass `EvalSimulatorCallbackHandler` (nuevo, hereda de `BaseAgentCallbackHandler`)
  - `FXResolver.default()` REUSED
  - `PricingResolver` REUSED
  - `sanitize_payload` REUSED
  - `BaseTraceEventRepoProtocol` + `BaseLLMCallRepoProtocol` REUSED structurally

- **Eval test fixtures**: **EXTEND**. Story B agrega `simulator/fixtures/tenant_seeded.py` (story-local — opción A elegida abajo §2.7) que reusa el patrón `synthetic_tenant.py` (upsert idempotente + soft-delete teardown).

- **TenantContext loader Story A**: **CONSUMIR read-only**. `load_eval_tenant(slug)` retorna inmutable TenantContext; fixture B lo usa para construir DB rows.

- **agent_app entrypoint**: **CONSUMIR read-only**. agent_bridge invoca `agent_app.ainvoke` + `ConversationPipeline.{build_identity, build_brand_voice, create_initial_state}` heredando observability completa.

- **MultiRoleLLMRouter**: **CONSUMIR read-only**. Customer node invoca `LLMFactory.get_service().generate_response(model_type=...)` con role de eval-only registry (decisión §2.5).

### Por qué el sistema cost-bucket-separation requiere NEW table (justificación NO-NEW-LAYER)

El patrón canónico (`campaigns`) prueba que `agent_kind` se introduce **siempre** con tabla propia + spec registrada. NO hay precedente de "agent_kind compartido en tabla mixta + filtro por metadata". Forzarlo violaría:
1. Cross-agent MV (`mv_daily_llm_cost_per_tenant_v2`) que GROUP BY tenant_id sin filtro `eval_run_kind` → pollution garantizada
2. `mv_refresh_log.get_last_refresh` budget guards (PI-1 S0 PR-2 § 7.2 soft cap 105% si MV stale > 1h) → soft cap aplicado a tenant si simulator quema budget synthetic
3. Streamlit `/sales-agent-quality` + `/sales-routing` queries `sales_agent_llm_call` sin filtro
4. Retention worker `shared/agent_observability/workers/retention_task.py` aplica window per-table; eval-simulator wants 7-day retention (synthetic), no 365 días audit

NEW tabla `eval_simulator_llm_call` + `eval_simulator_trace_event` es la única forma cost-zero-deuda. Spec H6 cement.

## Surface diff (BE)

### 1. Migration Alembic — `124_add_eval_simulator_observability_tables.py`

Path: `backend/alembic/versions/124_add_eval_simulator_observability_tables.py`

**Idempotente raw SQL** (no `op.create_table`, no `sa.Enum`). Mirror exacto schema `campaigns_llm_call` (Alembic 083) con dos diferencias:
- `lead_id UUID NOT NULL` → `lead_id UUID NULL` (eval-simulator NO escribe per-lead audit; el field queda como mirror schema con NULL admitido para preservar compat con BaseLLMCallRepoProtocol)
- Retención default 30 días (eval is synthetic, no audit obligation)

```sql
-- Migration body (full content in ticket T-1 implementation):

-- 1. eval_simulator_llm_call
CREATE TABLE IF NOT EXISTS eval_simulator_llm_call (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,                          -- el `tenant_id = uuid5(NS_DNS, f"eval-{slug}")` deterministic
  lead_id UUID NULL,                                -- eval simulator no usa lead audit
  channel_type VARCHAR(32) NOT NULL DEFAULT 'eval_simulator',
  turn_id UUID NOT NULL,
  span_id UUID NOT NULL,
  parent_span_id UUID,
  role VARCHAR(32) NOT NULL,                        -- 'customer' siempre (custom LLM persona)
  provider VARCHAR(32) NOT NULL,
  model_requested VARCHAR(128) NOT NULL,
  model_responded VARCHAR(128) NOT NULL,
  input_tokens INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  cached_read_tokens INTEGER NOT NULL DEFAULT 0,
  cached_write_tokens INTEGER NOT NULL DEFAULT 0,
  reasoning_tokens INTEGER NOT NULL DEFAULT 0,
  pricing_version_id UUID NOT NULL,
  input_unit_cost_usd NUMERIC(14,12) NOT NULL,
  output_unit_cost_usd NUMERIC(14,12) NOT NULL,
  cached_read_unit_cost_usd NUMERIC(14,12) NOT NULL DEFAULT 0,
  cost_usd NUMERIC(16,10) NULL,                     -- NULL admitido per T-1 cost_recorder canonicalization
  tenant_currency CHAR(3) NULL,
  fx_rate_to_tenant NUMERIC(16,8) NULL,
  fx_rate_source VARCHAR(32) NULL,
  cost_tenant_currency NUMERIC(16,8) NULL,
  started_at TIMESTAMPTZ NOT NULL,
  duration_ms INTEGER NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'ok',
  error_type VARCHAR(64) NULL,
  -- Eval-specific metadata jsonb (H5 — eval-vs-prod separation tags)
  eval_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  -- Generated columns (mirror campaigns):
  occurred_on DATE GENERATED ALWAYS AS ((started_at AT TIME ZONE 'UTC')::date) STORED,
  occurred_year_month VARCHAR(7) GENERATED ALWAYS AS (
    EXTRACT(YEAR FROM started_at AT TIME ZONE 'UTC')::INT::TEXT
    || '-'
    || LPAD(EXTRACT(MONTH FROM started_at AT TIME ZONE 'UTC')::INT::TEXT, 2, '0')
  ) STORED
);

CREATE INDEX IF NOT EXISTS ix_eval_simulator_llm_call_tenant_day
  ON eval_simulator_llm_call (tenant_id, occurred_on);
CREATE INDEX IF NOT EXISTS ix_eval_simulator_llm_call_turn
  ON eval_simulator_llm_call (turn_id);
-- Index sobre simulation_id (extracted from JSONB) para query downstream:
CREATE INDEX IF NOT EXISTS ix_eval_simulator_llm_call_sim_id
  ON eval_simulator_llm_call ((eval_metadata->>'simulation_id'));
CREATE INDEX IF NOT EXISTS ix_eval_simulator_llm_call_run_id
  ON eval_simulator_llm_call ((eval_metadata->>'run_id'));

-- 2. eval_simulator_trace_event (mirror trace_event con eval_metadata)
CREATE TABLE IF NOT EXISTS eval_simulator_trace_event (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  lead_id UUID NULL,
  channel_type VARCHAR(32) NOT NULL DEFAULT 'eval_simulator',
  turn_id UUID NOT NULL,
  span_id UUID NOT NULL,
  parent_span_id UUID,
  event_type VARCHAR(32) NOT NULL,
  name VARCHAR(128),
  data JSONB NOT NULL DEFAULT '{}'::jsonb,
  duration_ms INTEGER,
  status VARCHAR(16) NOT NULL DEFAULT 'ok',
  -- Eval-specific metadata jsonb
  eval_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_eval_simulator_trace_event_tenant_turn
  ON eval_simulator_trace_event (tenant_id, turn_id, created_at);
CREATE INDEX IF NOT EXISTS ix_eval_simulator_trace_event_sim_id
  ON eval_simulator_trace_event ((eval_metadata->>'simulation_id'));

-- 3. Marker is_eval_synthetic en tablas TOCADAS por fixture seed
-- DECISIÓN §2.6: NO agregar columna a 5+ tablas (tenants, brand,
-- personality_profile, products, buyer_personas, pricing). En su lugar usar
-- naming convention deterministic (Opción B spec): tenant_id = uuid5(NS_DNS,
-- f"eval-{slug}") + Streamlit prod filtra `WHERE tenant_id NOT IN (SELECT tenant_id
-- FROM eval_synthetic_tenants)`. Lookup table:
CREATE TABLE IF NOT EXISTS eval_synthetic_tenants (
  tenant_id UUID PRIMARY KEY,
  archetype_slug VARCHAR(64) NOT NULL,
  seeded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ NULL                       -- soft-delete idempotency teardown
);
CREATE INDEX IF NOT EXISTS ix_eval_synthetic_tenants_slug
  ON eval_synthetic_tenants (archetype_slug) WHERE deleted_at IS NULL;
```

**Verificación idempotencia**: ejecutar `alembic upgrade head` 2x sin error.
Test pre-prod clone DB workflow per `.claude/rules/backend-migrations.md`:

```bash
# Steps from migrations rule:
docker exec visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test_eval_simulator;"
docker exec visionarias_postgres pg_dump -U postgres -s visionarias_logs > /tmp/schema.sql
docker exec visionarias_postgres psql -U postgres -d migration_test_eval_simulator < /tmp/schema.sql
docker exec visionarias_brain_dev bash -c "ALEMBIC_DATABASE_URL=postgresql://postgres:postgres@postgres/migration_test_eval_simulator alembic stamp <prod_rev>"
docker exec visionarias_brain_dev bash -c "ALEMBIC_DATABASE_URL=postgresql://postgres:postgres@postgres/migration_test_eval_simulator alembic upgrade head"  # Run 1
docker exec visionarias_brain_dev bash -c "ALEMBIC_DATABASE_URL=postgresql://postgres:postgres@postgres/migration_test_eval_simulator alembic upgrade head"  # Run 2 — must be no-op
docker exec visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test_eval_simulator;"
```

### 2. SQLAlchemy mirror models — production code under R5 schema-mirror exception

Path: `backend/src/modules/sales_agent/observability/eval_simulator/`

```
modules/sales_agent/observability/eval_simulator/
├── __init__.py                                     # registers spec via register_agent_observability
└── persistence/
    ├── __init__.py
    ├── models/
    │   ├── __init__.py
    │   ├── llm_call_model.py                       # EvalSimulatorLlmCallModel
    │   ├── trace_event_model.py                    # EvalSimulatorTraceEventModel
    │   └── synthetic_tenant_model.py               # EvalSyntheticTenantModel (lookup)
    ├── llm_call_repository.py                      # impl BaseLLMCallRepoProtocol
    └── trace_event_repository.py                   # impl BaseTraceEventRepoProtocol
```

**Justificación R5 schema-mirror exception** (`.claude/rules/backend-ddd.md` §
"Schema-mirror exception"): builder-backend MAY touch
`modules/sales_agent/persistence/models/` SOLO para schema mirror desde
shared/migration. Caso eval_simulator: tabla nace por migration (business
module change normal — campaigns precedent), SQLAlchemy model class debe
vivir en módulo consumer. Builder-backend genera/modifica
`modules/sales_agent/observability/eval_simulator/persistence/models/*.py`
para reflejar DDL nuevo SIN tocar `modules/sales_agent/{domain,application,api}/`.

**Spec registration** (`__init__.py`):

```python
"""Eval simulator observability — bucket separation cost tracking.

Registers agent_kind="eval_simulator" en shared/agent_observability/registry.
Tables eval_simulator_llm_call + eval_simulator_trace_event creadas en migration 124.

Origen: PI-12 Story B eval-foundation-simulator-homologation (2026-05-07).
Pattern paridad campaigns/observability/__init__.py (PI-1 S0 PR-1 / Alembic 083).
"""

from __future__ import annotations

from src.modules.sales_agent.observability.eval_simulator.persistence.models.llm_call_model import (
    EvalSimulatorLlmCallModel,
)
from src.shared.agent_observability.registry import (
    AgentObservabilitySpec,
    register_agent_observability,
)

register_agent_observability(
    AgentObservabilitySpec(
        agent_kind="eval_simulator",
        llm_call_model=EvalSimulatorLlmCallModel,
        trace_event_table="eval_simulator_trace_event",
        llm_call_table="eval_simulator_llm_call",
        trace_retention_env_var="EVAL_SIMULATOR_TRACE_RETENTION_DAYS",
        llm_call_retention_env_var="EVAL_SIMULATOR_LLM_CALL_RETENTION_DAYS",
        trace_default_days=30,                       # synthetic, short retention
        llm_call_default_days=30,
        has_lead_id=False,                            # eval-simulator no usa lead audit
    ),
)
```

**Bootstrap registration** — extend `backend/src/shared/infrastructure/agent_observability_bootstrap.py`:

```python
# Add the eval_simulator import (side-effect — register_agent_observability invoked)
from src.modules.sales_agent.observability.eval_simulator import (  # noqa: F401
    eval_simulator as _eval_simulator_observability,
)
```

### 3. DB-seed fixture `eval_tenant_seeded(archetype_slug)`

**Decisión §2.7 — directorio**: **story-local** (`backend/tests/agentic_evals/sales_agent/simulator/fixtures/tenant_seeded.py`).

Justificación SoC + future consumers (C/D/E/F/G/H/I):
- C (personas-instrumented-runtime): consume `ActorProfile` + extends loader, NO seeded DB rows directos
- D (goldens-3-tenants-dataset): consume `run_simulation()` directamente, ya cubierto
- E (voice-fidelity-grader): grader contra transcript artifact, NO seeded fixture
- F (eval-pass-k-tracking): wraps `run_simulation(..., trial_n=k)`, ya cubierto
- G/H (CI gate / cost cap): leen `_artifacts/` + queries DB, ya cubierto
- I (adversarial-jailbreak): `register_termination_policy()` extension, NO seeded fixture

**Conclusion**: fixture es story-B-only consumer. Story-local evita cross-story coupling. Si una story futura necesita seed → lift a `simulator/fixtures/` cross-story, NO al `agentic_evals/sales_agent/fixtures/` general (que tiene Visionarias + T2 hard-coded — distinto patrón).

```python
# backend/tests/agentic_evals/sales_agent/simulator/fixtures/tenant_seeded.py

"""DB-seed fixture for eval simulator runs.

Materializes a Story-A `TenantContext` (loaded from
`backend/tests/fixtures/eval/tenants/`) into Postgres rows with
deterministic UUID5 + soft-delete teardown. Reusable across the 5
archetypes via `archetype_slug` parametrize.

Decisiones:
- D2 (spec): tenant_id = uuid5(NAMESPACE_DNS, f"eval-{slug}") deterministic
- §2.6 (arch): is_eval_synthetic marker via `eval_synthetic_tenants` lookup
  table (Opción B-derived spec). NO column `is_eval_synthetic` en tablas
  business — costo migration de >5 tablas sin ROI; lookup table escala.

Tenant isolation (`.claude/rules/tenant-isolation.md`):
- Cada query filter tenant_id explícito.
- TenantContext de Story A es read-only — fixture NO muta YAML.

Anti-duplication §0:
- Reusa `TenantModel`, `BrandRepository.save_settings`, `PersonalityProfileModel`,
  `ProductModel`, `BuyerPersonaModel`, `Pricing*` desde producción paths.
- NO mirror DDL, NO test-only ORM models.

Spanish neutro: log/error/warning strings en español neutro (`.claude/rules/spanish-text.md`).
"""

import uuid
from contextlib import contextmanager
from typing import Iterator
from uuid import UUID

import pytest
import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.fixtures.eval.tenants.loader import (
    ARCHETYPE_SLUGS,
    TenantContext,
    load_eval_tenant,
)

logger = structlog.get_logger()

# Decisión D2 — UUID5 deterministic per archetype slug.
EVAL_TENANT_NAMESPACE = uuid.NAMESPACE_DNS


def _eval_tenant_id(archetype_slug: str) -> UUID:
    """Deterministic tenant_id derivation. Idempotent across runs."""
    return uuid.uuid5(EVAL_TENANT_NAMESPACE, f"eval-{archetype_slug}")


@pytest.fixture
def eval_tenant_seeded(
    visionarias_tenant_session,                       # reuses real DB session
):
    """Yield a callable `seed(slug) → (tenant_id, TenantContext)` that
    inserts DB rows + records in `eval_synthetic_tenants` lookup.

    Teardown soft-deletes via `eval_synthetic_tenants.deleted_at = utc_now()`
    so concurrent eval runs don't collide + Streamlit prod queries can
    filter `WHERE tenant_id NOT IN (SELECT tenant_id FROM eval_synthetic_tenants
    WHERE deleted_at IS NULL)`.

    Returns:
        Callable[[str], tuple[UUID, TenantContext]] que carga + sembrá +
        retorna ids para use en `run_simulation(...)`.

    Raises:
        ValueError: si archetype_slug no en ARCHETYPE_SLUGS.
        FileNotFoundError: si seed YAML faltante (Story A precondition).
    """
    db: Session = visionarias_tenant_session["db_session"]
    seeded_ids: list[UUID] = []

    def _seed(archetype_slug: str) -> tuple[UUID, TenantContext]:
        if archetype_slug not in ARCHETYPE_SLUGS:
            msg = (
                f"archetype_slug {archetype_slug!r} no encontrado. "
                f"Validos: {list(ARCHETYPE_SLUGS)}"
            )
            raise ValueError(msg)

        ctx = load_eval_tenant(archetype_slug)
        tenant_id = _eval_tenant_id(archetype_slug)

        # 1. Upsert lookup
        from src.modules.sales_agent.observability.eval_simulator.persistence.models.synthetic_tenant_model import (
            EvalSyntheticTenantModel,
        )
        lookup = db.execute(
            select(EvalSyntheticTenantModel).where(
                EvalSyntheticTenantModel.tenant_id == tenant_id
            )
        ).scalar_one_or_none()
        if lookup is None:
            lookup = EvalSyntheticTenantModel(
                tenant_id=tenant_id,
                archetype_slug=archetype_slug,
            )
            db.add(lookup)
        else:
            lookup.deleted_at = None  # restore from prior teardown
        db.flush()

        # 2. Upsert TenantModel
        from src.modules.iam.infrastructure.models.tenant_model import TenantModel
        tenant = db.execute(
            select(TenantModel).where(TenantModel.id == tenant_id)
        ).scalar_one_or_none()
        if tenant is None:
            tenant = TenantModel(
                id=tenant_id,
                name=f"eval-{archetype_slug}",
                slug=f"eval-{archetype_slug}",
                config_json={"brand_settings": ctx.brand},
                default_currency=ctx.pricing.get("currency", "USD"),
                timezone="UTC",
            )
            db.add(tenant)
        else:
            tenant.config_json = {"brand_settings": ctx.brand}
        db.flush()

        # 3. Upsert PersonalityProfileModel — minimal fields for compiler v2
        from src.modules.brand.infrastructure.models.personality_model import (
            PersonalityProfileModel,
        )
        # ... build minimum required fields from ctx.personality_profile YAML
        # (system_instruction es el campo critical para slot 5 cache prefix)

        # 4. Upsert ProductModel(s) from ctx.offer_ladder.raw["offers"]
        # 5. Upsert BuyerPersonaModel(s) from ctx.buyer_personas

        db.commit()
        seeded_ids.append(tenant_id)
        logger.info(
            "eval_tenant_seeded",
            tenant_id=str(tenant_id),
            archetype_slug=archetype_slug,
        )
        return tenant_id, ctx

    yield _seed

    # Teardown: soft-delete idempotente
    from datetime import UTC, datetime
    from src.modules.sales_agent.observability.eval_simulator.persistence.models.synthetic_tenant_model import (
        EvalSyntheticTenantModel,
    )
    for tid in seeded_ids:
        try:
            row = db.execute(
                select(EvalSyntheticTenantModel).where(
                    EvalSyntheticTenantModel.tenant_id == tid
                )
            ).scalar_one_or_none()
            if row and row.deleted_at is None:
                row.deleted_at = datetime.now(tz=UTC)
            db.commit()
        except Exception as exc:  # noqa: BLE001 — teardown is best-effort
            logger.warning("eval_tenant_teardown_failed", tenant_id=str(tid), error=str(exc))
            db.rollback()
```

> **Implementation note for builder**: el listado exacto de tablas + campos a sembrar
> SE DERIVA del recorrido de `ConversationPipeline.{build_identity, build_brand_voice,
> create_initial_state}` (paths citados en §0). Builder ejecuta:
> `grep -rn "tenant_id\|self\..*_repo\|_port\." backend/src/modules/sales_agent/application/services/knowledge_builder.py`
> + traza dependencies hasta `BrandRepository`, `OfferRepository`, `PersonalityProfileRepository`,
> `BuyerPersonaRepository`, `Pricing*`. Las tablas mínimas son: `tenants` (config_json brand_settings),
> `personality_profiles` (system_instruction), `products` (al menos 1 active offer), `buyer_personas`.
> Detalle exhaustivo en T-3 implementation.

### 4. Tests requeridos (BE-side)

| Test | Path | Type | Cobertura |
|---|---|---|---|
| Migration apply + rollback + idempotency | `backend/tests/migrations/test_124_eval_simulator_observability_tables.py` | integration | Capa 0 — migration funciona en DB clone |
| Migration columns + indexes match contract | `backend/tests/migrations/test_124_columns_indexes.py` | integration | DDL paridad campaigns precedent |
| Fixture seed + teardown + cross-tenant isolation | `backend/tests/agentic_evals/sales_agent/simulator/fixtures/test_tenant_seeded.py` | integration | UUID5 idempotency, soft-delete, isolation |
| Spec registered (registry has eval_simulator entry) | `backend/tests/architecture/test_eval_simulator_observability_invariants.py` | architecture | EXTEND `register_agent_observability` count + spec fields |
| `EvalSimulatorLlmCallModel` schema mirror campaigns | `backend/tests/architecture/test_eval_simulator_schema_mirror.py` | architecture | Column count + types vs campaigns |
| Coverage minimum: 60% del módulo `modules/sales_agent/observability/eval_simulator/` | — | — | No bajar |

### 5. Arch fitness gates nuevos (allowlists vacías inicial — shrink-only)

| Gate | Path | Invariant | Allowlist |
|---|---|---|---|
| **H9 anti-mirror** | `backend/tests/architecture/test_simulator_no_mirrors_shared.py` | NINGÚN archivo bajo `tests/agentic_evals/sales_agent/simulator/_internal/` con basename que coincida con `shared/agent_observability/recording/{turn_envelope,base_callback_handler,sanitization,cost_recorder}.py` | `[]` — never mirror. |
| **H5 mandatory eval-kind tag** | `backend/tests/architecture/test_simulator_writes_eval_kind_tag.py` | Cada call site que escribe a `eval_simulator_{trace_event,llm_call}` invoca `_with_eval_metadata(...)` que inyecta `eval_run_kind: "simulator"` + `archetype_slug` + `simulation_id` + `run_id` antes del `add(...)` | `[]` |
| **H9 public API surface minimal** | `backend/tests/architecture/test_simulator_public_api_surface.py` | `simulator/__init__.py::__all__` == frozenset({"run_simulation", "SimulationResult", "SimulationState", "ActorProfile", "TerminationReason", "AgentErrorSubtype", "register_termination_policy"}). Anti-pattern: re-export `_internal/*` symbols. | `[]` |
| **H1 schema migrations registry complete** | `backend/tests/architecture/test_schema_migrations_registry_complete.py` | Cada Pydantic class `SimulationState`, `ActorProfile`, `SimulationResult`, `ConversationTurn` cuyo `schema_version > 1` tiene migration `(prev, curr)` registrada en `SCHEMA_MIGRATIONS`. Frozen golden v1 fixture present + deserializable. | `[]` |
| **H8 termination policy registry contract** | `backend/tests/architecture/test_termination_policy_registry_contract.py` | `register_termination_policy(name, predicate)` validates: name unique en registry, predicate has signature `(SimulationState) -> TerminationReason \| None`, registry frozen post-init impossible to silently mutate. | `[]` |

> **Allowlist policy** (paridad `architectural-fitness.md` ratchet pattern):
> Si gate falla cuando builder agrega legítimo nuevo case (e.g. story I agrega
> nueva termination policy `adversarial_detected`), gate test enforces que `name`
> NO en lista existente — ratchet GROWS por adicción intencional, no shrink.
> Para H9 (anti-mirror) + H5 (eval-kind tag) + H9 (public API): allowlists shrink-only.
> Para H1 + H8 (registries): cada test enforces contract, NO allowlist (registry
> appears via test discovery).

### 6. Cross-cutting BE

- **Tenant isolation** (`.claude/rules/tenant-isolation.md`):
  - Cada query DB en fixture filtra `tenant_id` explícito (incluso `get_by_id` patterns)
  - `tenant_id = uuid5(NAMESPACE_DNS, f"eval-{slug}")` deterministic — fixture rejects setup si Visionarias UUID coincide (defensive paranoia)
  - Eval rows escritas a `eval_simulator_*` tables con `tenant_id` filtrado en cada repo `add()` call
  - Scenario 4 sub-case B grader verifica `SELECT DISTINCT tenant_id FROM ...trace_event WHERE eval_metadata->>'simulation_id' = ?` retorna 1 row
- **PII sanitization** (`tessl/.../pii-sanitisation.md`): `sanitize_payload(...)` aplicado pre-write a `eval_metadata` jsonb + `data` jsonb (heredado del callback handler shared base — no re-implementar).
- **Master data + currency** (`master-data.md` + `currency-handling.md`):
  - `started_at TIMESTAMPTZ NOT NULL` — UTC store
  - `tenant_currency CHAR(3)` desde `TenantContext.pricing.currency` (NO hardcoded `'USD'`)
  - FX resolved via `FXResolver.default()` (shared, REUSED)
- **Spanish neutro** (`.claude/rules/spanish-text.md`):
  - Errors structlog en español neutro: `"archetype_slug 'X' no encontrado"`, `"directorio tenant inexistente"`
  - Voseo permitido en actor persona prompts dialect=es-AR (heredado a 03-arch-agentic) — NO aplica a este BE arch
- **PII allowlist response_model**: N/A (no FastAPI endpoints — pure test infrastructure)
- **Soft-delete only**: `eval_synthetic_tenants.deleted_at` (idempotency teardown). NO hard delete.

### 7. Auditor downstream regression (R3)

**UPDATE** `.claude/rules/auditor-downstream-regression.md` § "Tabla SSoT — surface → downstream test paths":

| Surface modified (path) | Downstream test paths que MUST run | Razón |
|---|---|---|
| `backend/src/modules/sales_agent/observability/eval_simulator/**` | `tests/migrations/test_124_*.py`<br>`tests/architecture/test_eval_simulator_*.py`<br>`tests/agentic_evals/sales_agent/simulator/**`<br>`tests/architecture/test_termination_policy_registry_contract.py` | Bucket separation + spec registration cambios afectan cross-agent reporting + retention worker + bootstrap |
| `backend/alembic/versions/124_*.py` | `tests/migrations/test_124_*.py`<br>`tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py` (per anti-default-flip pattern) | Migration idempotency + cross-agent MV |
| `backend/tests/agentic_evals/sales_agent/simulator/**` | (entry NEW added) — when consumer C/D/E/F/G/H/I introducidos | Forward-only — actualizar al introducir consumer |

**Pre-commit hook freshness gate** (`.claude/rules/auditor-downstream-regression.md` §
"Pre-commit freshness gate"): nuevo `.py` bajo `backend/src/modules/sales_agent/observability/
eval_simulator/` requiere row en SSoT tabla; si self-contained (no cross-consumer) marca
`# downstream-regression-na: tabla cementada en story B; consumers C-I lift cuando entren`.

### 8. SSoT Guard — extend `contract-guard` hook

`.claude/skills/...` SSoT Guard list — add:
- Editing `backend/src/modules/sales_agent/observability/eval_simulator/__init__.py`
  → reminder: re-run `.venv/bin/pytest tests/architecture/test_eval_simulator_observability_invariants.py -v`

## Migration ordering + rollback

- Revision: `124_add_eval_simulator_observability_tables`
- Down revision: latest existing (verificar `ls backend/alembic/versions | sort | tail -1` antes commit, no asumir 123)
- Idempotente: `IF NOT EXISTS` en cada DDL statement
- Downgrade: `DROP TABLE IF EXISTS eval_simulator_trace_event CASCADE; DROP TABLE IF EXISTS eval_simulator_llm_call CASCADE; DROP TABLE IF EXISTS eval_synthetic_tenants CASCADE;` — clean rollback (no FK to other prod tables since `tenant_id` is just UUID column, no FK constraint to `tenants.id`)

## Rollout sequence (builder-backend ticket order)

| Ticket | Owner | Order | Depends on |
|---|---|---|---|
| T-1 | builder-backend (Sonnet OK — schema mirror exception R5) | 1 | Migration 124 + 4 SQLAlchemy models + register spec + bootstrap extension |
| T-2 | builder-backend | 2 | T-1 | Migration test + arch fitness gate `test_eval_simulator_observability_invariants.py` |
| T-3 | builder-backend | 3 | T-1 | Fixture `eval_tenant_seeded.py` + fixture test |

> AGENTIC tickets (T-4 onwards) cubren simulator code (state.py, customer_node.py,
> graph.py, etc.) — owner es **builder-agentic Opus 4.7** (R23 `production_code: false`
> for tests; tests/docs sobre agentic permite Sonnet). Detalle en 03-arch-agentic.md.

## Riesgos y mitigaciones

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Migration rompe MV `mv_daily_llm_cost_per_tenant_v2` | high | Migration NO toca MV existente — extension futura. Solo agrega tablas separadas. Test arch verifica MV unchanged post-migration |
| Builder confunde "agent_kind enum" del spec con DDL enum (no existe) | medium | Spec H6 corregida en este arch: NO ALTER TYPE; bucket separation via tabla nueva. T-1 prompt cita §2.4 audit verbatim |
| Fixture seed lenta (5 archetypes × N tablas) | medium | Sembrar lazy on-demand per archetype slug consumido, NO eager. Idempotent upsert post-prior-run |
| Coverage drop en `modules/sales_agent/` por nueva subdir `observability/eval_simulator/` | low | Coverage gate threshold 43% global, no per-module. Subdir nueva agrega ~150 LOC de mirror — coverage local 80%+ via fixture test + arch test |
| `EvalSyntheticTenantModel` table FK to `tenants.id` causa cascade delete issue | low | NO FK. UUID column standalone (paridad campaigns precedent: `lead_id` no es FK either) |
| Builder olvida bootstrap import → spec NO registered → MV runtime KeyError | medium | Arch test `test_eval_simulator_observability_invariants.py` ejercita `agent_observability_registry()` post-bootstrap import. CI fail si missing |

## Decisiones registradas

- **2026-05-07** — D-BE-1: `agent_kind` NO es enum DB. Spec H6 reinterpretada: bucket separation via tabla nueva (precedente campaigns/Alembic 083). NO ALTER TYPE.
- **2026-05-07** — D-BE-2: Tabla mirror campaigns schema verbatim minus `lead_id NOT NULL → NULL` + retention 30d default. Cero deuda — pattern cementado.
- **2026-05-07** — D-BE-3: Fixture story-local NO cross-eval. Future stories C/D/E/F/G/H/I no necesitan seed (consumen `run_simulation()` API). Lift a cross-story dir solo si emerge dual-consumer real.
- **2026-05-07** — D-BE-4: `is_eval_synthetic` marker via lookup table (`eval_synthetic_tenants`) NO column nueva en tablas business. Costo migration de >5 tablas sin ROI; lookup table escala + permite query Streamlit prod filtrar.
- **2026-05-07** — D-BE-5: Tenant_id UUID5 deterministic — re-run idempotency. Si run interrumpido, prox run reusa rows mediante upsert.
- **2026-05-07** — D-BE-6: SQLAlchemy models bajo `modules/sales_agent/observability/eval_simulator/persistence/models/` (no `tests/`) por R5 schema-mirror exception + paridad campaigns. Builder-backend Sonnet OK para mirror schema; resto (state, graph, customer_node) Opus per R23 agentic production code.

## Próximo paso

`done -> 03-arch-be.md` (referencia al orchestrator /architect).
