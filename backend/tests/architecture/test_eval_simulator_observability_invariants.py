"""Architecture fitness gate — eval_simulator observability invariants.

Story B: eval-foundation-simulator-homologation.
T-2 deliverable (test-infrastructure, production_code=false).

Five invariant classes (ratchet pattern — no allowlists, shrink-only):

1. **Spec registration** — ``get_spec('eval_simulator')`` returns spec after
   bootstrap import (validates T-1 spec.py + bootstrap edit together).

2. **ORM models exist** — the 3 SQLAlchemy models land in the correct paths
   (importable + __tablename__ matches migration 125 table names).

3. **eval_metadata jsonb column** — both tables carry the mandatory JSONB
   column declared in H5 (eval_run_kind, archetype_slug, actor_profile_id,
   trial_n, simulation_id, run_id tags will be written there at runtime).

4. **Tenant isolation** — all 3 ORM models expose a ``tenant_id`` column
   (UUID, nullable=False for the two cost-bucket tables; PK for lookup table).

5. **Timestamp columns timezone-aware** — DateTime columns use
   ``timezone=True`` (or TIMESTAMPTZ in migration DDL) to prevent naive
   datetime misinterpretation per ``.claude/rules/master-data.md``.

6. **campaigns parity fields** — ``eval_simulator_llm_call`` matches the
   campaigns LLM call field contract that external cost consumers expect.

Pattern precedent: ``tests/architecture/test_sales_agent_observability_invariants.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

# ── Paths to the ORM model files (T-1 deliverables) ──────────────────────

EVAL_SIMULATOR_LLM_CALL_MODEL = (
    REPO
    / "src"
    / "modules"
    / "sales_agent"
    / "observability"
    / "eval_simulator"
    / "persistence"
    / "models"
    / "eval_simulator_llm_call.py"
)
EVAL_SIMULATOR_TRACE_EVENT_MODEL = (
    REPO
    / "src"
    / "modules"
    / "sales_agent"
    / "observability"
    / "eval_simulator"
    / "persistence"
    / "models"
    / "eval_simulator_trace_event.py"
)
EVAL_SYNTHETIC_TENANTS_MODEL = (
    REPO
    / "src"
    / "modules"
    / "sales_agent"
    / "observability"
    / "eval_simulator"
    / "persistence"
    / "models"
    / "eval_synthetic_tenants.py"
)
SPEC_FILE = REPO / "src" / "modules" / "sales_agent" / "observability" / "eval_simulator" / "spec.py"
BOOTSTRAP_FILE = REPO / "src" / "shared" / "infrastructure" / "agent_observability_bootstrap.py"
MIGRATION_125 = REPO / "alembic" / "versions" / "125_add_eval_simulator_observability_tables.py"


def _read(p: Path) -> str:
    """Read file content with UTF-8 encoding."""
    return p.read_text(encoding="utf-8")


# ── 1. Spec registration ───────────────────────────────────────────────────


class TestSpecRegistration:
    """Validates T-1 spec.py + bootstrap bootstrap edit together (Invariant 1)."""

    def test_spec_file_exists(self) -> None:
        """spec.py exists at the expected path."""
        assert SPEC_FILE.exists(), f"spec.py not found at {SPEC_FILE}"

    def test_bootstrap_imports_eval_simulator_spec(self) -> None:
        """agent_observability_bootstrap.py imports eval_simulator spec (T-1 1-line edit)."""
        src = _read(BOOTSTRAP_FILE)
        assert "eval_simulator" in src, (
            "agent_observability_bootstrap.py must import eval_simulator spec "
            "(T-1 deliverable: 1-line edit). "
            f"Missing eval_simulator import in {BOOTSTRAP_FILE}"
        )

    def test_spec_calls_register_agent_observability(self) -> None:
        """spec.py calls register_agent_observability with agent_kind='eval_simulator'."""
        src = _read(SPEC_FILE)
        assert "register_agent_observability" in src, (
            "spec.py must call register_agent_observability to push spec into the registry."
        )
        assert "eval_simulator" in src, "spec.py must use agent_kind='eval_simulator'."

    def test_get_spec_returns_spec_after_bootstrap_import(self) -> None:
        """get_spec('eval_simulator') returns a non-None spec after bootstrap import (runtime check)."""
        from luana_core_platform.infrastructure import agent_observability_bootstrap
        from luana_core_observability.registry import get_spec

        spec = get_spec("eval_simulator")
        assert spec is not None, (
            "get_spec('eval_simulator') returned None. "
            "Ensure bootstrap.py imports eval_simulator/spec.py and that "
            "register_agent_observability is called at import time."
        )
        assert spec.agent_kind == "eval_simulator"

    def test_spec_llm_call_model_matches_migration_table(self) -> None:
        """Spec.llm_call_table == 'eval_simulator_llm_call' (matches migration 125 DDL)."""
        from luana_core_platform.infrastructure import agent_observability_bootstrap
        from luana_core_observability.registry import get_spec

        spec = get_spec("eval_simulator")
        assert spec.llm_call_table == "eval_simulator_llm_call"

    def test_spec_trace_event_table_matches_migration_table(self) -> None:
        """Spec.trace_event_table == 'eval_simulator_trace_event' (matches migration 125 DDL)."""
        from luana_core_platform.infrastructure import agent_observability_bootstrap
        from luana_core_observability.registry import get_spec

        spec = get_spec("eval_simulator")
        assert spec.trace_event_table == "eval_simulator_trace_event"


# ── 2. ORM model files exist ───────────────────────────────────────────────


class TestOrmModelsExist:
    """Validates that all 3 SQLAlchemy model files exist (T-1 deliverables)."""

    def test_eval_simulator_llm_call_model_file_exists(self) -> None:
        """eval_simulator_llm_call.py exists at expected path."""
        assert EVAL_SIMULATOR_LLM_CALL_MODEL.exists(), f"Missing ORM model file: {EVAL_SIMULATOR_LLM_CALL_MODEL}"

    def test_eval_simulator_trace_event_model_file_exists(self) -> None:
        """eval_simulator_trace_event.py exists at expected path."""
        assert EVAL_SIMULATOR_TRACE_EVENT_MODEL.exists(), f"Missing ORM model file: {EVAL_SIMULATOR_TRACE_EVENT_MODEL}"

    def test_eval_synthetic_tenants_model_file_exists(self) -> None:
        """eval_synthetic_tenants.py exists at expected path."""
        assert EVAL_SYNTHETIC_TENANTS_MODEL.exists(), f"Missing ORM model file: {EVAL_SYNTHETIC_TENANTS_MODEL}"

    def test_llm_call_model_tablename_matches_migration(self) -> None:
        """EvalSimulatorLlmCallModel.__tablename__ == 'eval_simulator_llm_call'."""
        src = _read(EVAL_SIMULATOR_LLM_CALL_MODEL)
        assert '__tablename__ = "eval_simulator_llm_call"' in src or (
            "__tablename__ = 'eval_simulator_llm_call'" in src
        ), "LlmCallModel.__tablename__ must be 'eval_simulator_llm_call'"

    def test_trace_event_model_tablename_matches_migration(self) -> None:
        """EvalSimulatorTraceEventModel.__tablename__ == 'eval_simulator_trace_event'."""
        src = _read(EVAL_SIMULATOR_TRACE_EVENT_MODEL)
        assert '__tablename__ = "eval_simulator_trace_event"' in src or (
            "__tablename__ = 'eval_simulator_trace_event'" in src
        ), "TraceEventModel.__tablename__ must be 'eval_simulator_trace_event'"

    def test_synthetic_tenants_model_tablename_matches_migration(self) -> None:
        """EvalSyntheticTenantModel.__tablename__ == 'eval_synthetic_tenants'."""
        src = _read(EVAL_SYNTHETIC_TENANTS_MODEL)
        assert '__tablename__ = "eval_synthetic_tenants"' in src or (
            "__tablename__ = 'eval_synthetic_tenants'" in src
        ), "SyntheticTenantModel.__tablename__ must be 'eval_synthetic_tenants'"


# ── 3. eval_metadata JSONB column ─────────────────────────────────────────


class TestEvalMetadataJsonbColumn:
    """Validates H5 mandatory eval_metadata JSONB column on both cost-bucket tables.

    Mandatory tags written at runtime: eval_run_kind, archetype_slug,
    actor_profile_id, trial_n, simulation_id, run_id.
    """

    def test_llm_call_model_has_eval_metadata_column(self) -> None:
        """EvalSimulatorLlmCallModel declares eval_metadata JSONB column."""
        src = _read(EVAL_SIMULATOR_LLM_CALL_MODEL)
        assert "eval_metadata" in src, (
            "eval_simulator_llm_call ORM model must have eval_metadata column (H5 — mandatory tags)."
        )
        assert "JSONB" in src, "eval_metadata must use JSONB type for tag queries."

    def test_trace_event_model_has_eval_metadata_column(self) -> None:
        """EvalSimulatorTraceEventModel declares eval_metadata JSONB column."""
        src = _read(EVAL_SIMULATOR_TRACE_EVENT_MODEL)
        assert "eval_metadata" in src, (
            "eval_simulator_trace_event ORM model must have eval_metadata column (H5 — mandatory tags)."
        )
        assert "JSONB" in src, "eval_metadata must use JSONB type for tag queries."

    def test_migration_llm_call_eval_metadata_not_null(self) -> None:
        """Migration DDL declares eval_metadata JSONB NOT NULL on eval_simulator_llm_call."""
        src = _read(MIGRATION_125)
        # Check the llm_call CREATE TABLE block
        llm_call_block_start = src.find("CREATE TABLE IF NOT EXISTS eval_simulator_llm_call")
        llm_call_block_end = src.find("CREATE TABLE IF NOT EXISTS eval_simulator_trace_event")
        assert llm_call_block_start != -1, "eval_simulator_llm_call DDL not found in migration"
        llm_call_block = src[llm_call_block_start:llm_call_block_end]
        assert "eval_metadata JSONB NOT NULL" in llm_call_block, (
            "Migration must declare eval_metadata JSONB NOT NULL in eval_simulator_llm_call"
        )

    def test_migration_trace_event_eval_metadata_not_null(self) -> None:
        """Migration DDL declares eval_metadata JSONB NOT NULL on eval_simulator_trace_event."""
        src = _read(MIGRATION_125)
        trace_block_start = src.find("CREATE TABLE IF NOT EXISTS eval_simulator_trace_event")
        trace_block_end = src.find("CREATE TABLE IF NOT EXISTS eval_synthetic_tenants")
        assert trace_block_start != -1, "eval_simulator_trace_event DDL not found in migration"
        trace_block = src[trace_block_start:trace_block_end]
        assert "eval_metadata JSONB NOT NULL" in trace_block, (
            "Migration must declare eval_metadata JSONB NOT NULL in eval_simulator_trace_event"
        )


# ── 4. Tenant isolation ────────────────────────────────────────────────────


class TestTenantIsolation:
    """Validates tenant_id column on all 3 ORM models (tenant-isolation rule).

    Per `.claude/rules/tenant-isolation.md`: every entity carries tenant_id.
    """

    def test_llm_call_model_has_tenant_id_column(self) -> None:
        """EvalSimulatorLlmCallModel carries tenant_id column."""
        src = _read(EVAL_SIMULATOR_LLM_CALL_MODEL)
        assert "tenant_id" in src, (
            "eval_simulator_llm_call ORM model must have tenant_id column "
            "(.claude/rules/tenant-isolation.md — every entity carries tenant_id)."
        )

    def test_trace_event_model_has_tenant_id_column(self) -> None:
        """EvalSimulatorTraceEventModel carries tenant_id column."""
        src = _read(EVAL_SIMULATOR_TRACE_EVENT_MODEL)
        assert "tenant_id" in src, "eval_simulator_trace_event ORM model must have tenant_id column."

    def test_synthetic_tenants_model_has_tenant_id_column(self) -> None:
        """EvalSyntheticTenantModel carries tenant_id column (PK)."""
        src = _read(EVAL_SYNTHETIC_TENANTS_MODEL)
        assert "tenant_id" in src, "eval_synthetic_tenants ORM model must have tenant_id column (PK per D2/D4)."

    def test_migration_llm_call_tenant_id_not_null(self) -> None:
        """Migration DDL declares tenant_id UUID NOT NULL on eval_simulator_llm_call."""
        src = _read(MIGRATION_125)
        llm_call_block_start = src.find("CREATE TABLE IF NOT EXISTS eval_simulator_llm_call")
        llm_call_block_end = src.find("CREATE TABLE IF NOT EXISTS eval_simulator_trace_event")
        llm_call_block = src[llm_call_block_start:llm_call_block_end]
        assert "tenant_id UUID NOT NULL" in llm_call_block, (
            "eval_simulator_llm_call must have tenant_id UUID NOT NULL (tenant isolation)."
        )

    def test_migration_trace_event_tenant_id_not_null(self) -> None:
        """Migration DDL declares tenant_id UUID NOT NULL on eval_simulator_trace_event."""
        src = _read(MIGRATION_125)
        trace_block_start = src.find("CREATE TABLE IF NOT EXISTS eval_simulator_trace_event")
        trace_block_end = src.find("CREATE TABLE IF NOT EXISTS eval_synthetic_tenants")
        trace_block = src[trace_block_start:trace_block_end]
        assert "tenant_id UUID NOT NULL" in trace_block, (
            "eval_simulator_trace_event must have tenant_id UUID NOT NULL (tenant isolation)."
        )


# ── 5. Timestamp columns timezone-aware ───────────────────────────────────


class TestTimestampColumnsTimezoneAware:
    """Validates DateTime(timezone=True) on all timestamp columns.

    Per `.claude/rules/master-data.md`: UTC store always.
    Forbidden: ``DateTime()`` without timezone=True.
    """

    def test_llm_call_started_at_uses_timezone_datetime(self) -> None:
        """EvalSimulatorLlmCallModel.started_at uses DateTime(timezone=True)."""
        src = _read(EVAL_SIMULATOR_LLM_CALL_MODEL)
        assert "DateTime(timezone=True)" in src, (
            "eval_simulator_llm_call ORM model must use DateTime(timezone=True) for started_at. "
            "Plain DateTime() without timezone=True is forbidden (.claude/rules/master-data.md)."
        )

    def test_trace_event_created_at_uses_timezone_datetime(self) -> None:
        """EvalSimulatorTraceEventModel.created_at uses DateTime(timezone=True)."""
        src = _read(EVAL_SIMULATOR_TRACE_EVENT_MODEL)
        assert "DateTime(timezone=True)" in src, (
            "eval_simulator_trace_event ORM model must use DateTime(timezone=True) for created_at."
        )

    def test_synthetic_tenants_seeded_at_uses_timezone_datetime(self) -> None:
        """EvalSyntheticTenantModel.seeded_at uses DateTime(timezone=True)."""
        src = _read(EVAL_SYNTHETIC_TENANTS_MODEL)
        assert "DateTime(timezone=True)" in src, (
            "eval_synthetic_tenants ORM model must use DateTime(timezone=True) for seeded_at."
        )

    def test_migration_uses_timestamptz_for_started_at(self) -> None:
        """Migration DDL uses TIMESTAMPTZ (not TIMESTAMP) for started_at."""
        src = _read(MIGRATION_125)
        # The migration should NOT use bare TIMESTAMP (without TZ) for these columns.
        assert "started_at TIMESTAMPTZ NOT NULL" in src, (
            "Migration must declare started_at as TIMESTAMPTZ for timezone-aware storage."
        )

    def test_migration_uses_timestamptz_for_created_at(self) -> None:
        """Migration DDL uses TIMESTAMPTZ for created_at in trace_event."""
        src = _read(MIGRATION_125)
        assert "created_at TIMESTAMPTZ NOT NULL" in src, (
            "Migration must declare created_at as TIMESTAMPTZ for timezone-aware storage."
        )


# ── 6. campaigns parity fields ─────────────────────────────────────────────


class TestCampaignParityFields:
    """Validates eval_simulator_llm_call field parity with campaigns (D-BE-2).

    The deliverable spec (03-arch-be.md §1 D-BE-2) states: mirror campaigns
    schema verbatim. These 10 fields are consumed by external cost consumers
    (cost_aggregator, budget_guard, admin Streamlit) that iterate all
    LLM call tables via the shared registry.
    """

    _REQUIRED_FIELDS = [
        "cost_usd",
        "input_tokens",
        "output_tokens",
        "cached_read_tokens",
        "cached_write_tokens",
        "model_requested",
        "provider",
        "started_at",
        "duration_ms",
        "tenant_id",
    ]

    @pytest.mark.parametrize("field_name", _REQUIRED_FIELDS)
    def test_llm_call_model_has_parity_field(self, field_name: str) -> None:
        """EvalSimulatorLlmCallModel has field '{field_name}' (campaigns parity)."""
        src = _read(EVAL_SIMULATOR_LLM_CALL_MODEL)
        assert field_name in src, (
            f"eval_simulator_llm_call ORM model missing field '{field_name}'. "
            "This field is required for parity with campaign_llm_call (D-BE-2 arch spec). "
            "Cost consumers iterate all LLM call tables via registry and expect these fields."
        )

    def test_llm_call_model_has_litellm_call_id_field(self) -> None:
        """EvalSimulatorLlmCallModel has litellm_call_id OR equivalent span tracking field.

        The callback handler (T-5) writes litellm_call_id for dedup and cost reconciliation.
        The model must accept this field (may be named litellm_call_id or span_id as surrogate).
        """
        src = _read(EVAL_SIMULATOR_LLM_CALL_MODEL)
        has_litellm_id = "litellm_call_id" in src
        has_span_id = "span_id" in src
        assert has_litellm_id or has_span_id, (
            "eval_simulator_llm_call ORM model must have litellm_call_id or span_id "
            "for call deduplication in the callback handler (T-5 dependency)."
        )

    def test_llm_call_model_has_reasoning_tokens(self) -> None:
        """EvalSimulatorLlmCallModel has reasoning_tokens (added in S11A)."""
        src = _read(EVAL_SIMULATOR_LLM_CALL_MODEL)
        assert "reasoning_tokens" in src, (
            "eval_simulator_llm_call must include reasoning_tokens column "
            "(parity with latest campaigns/sales_agent schema after S11A)."
        )

    def test_llm_call_model_has_error_type_field(self) -> None:
        """EvalSimulatorLlmCallModel has error_type for AgentErrorSubtype enum storage (H7)."""
        src = _read(EVAL_SIMULATOR_LLM_CALL_MODEL)
        assert "error_type" in src, (
            "eval_simulator_llm_call must have error_type field for "
            "AgentErrorSubtype enum (H7 failure taxonomy, T-4/T-5 dependency)."
        )


# ── 7. Schema mirror follows R5 exception ─────────────────────────────────


class TestR5SchemaMirrorException:
    """Validates R5 schema-mirror exception boundaries are respected.

    R5 allows builder-backend to touch persistence/models/ ONLY for schema
    mirror from migration. The ORM files must NOT import from or reference
    domain/application/api layers of sales_agent.
    """

    def test_llm_call_model_does_not_import_sales_agent_domain(self) -> None:
        """LlmCallModel does not import from sales_agent domain (R5 boundary)."""
        src = _read(EVAL_SIMULATOR_LLM_CALL_MODEL)
        assert "from src.modules.sales_agent.domain" not in src, (
            "eval_simulator_llm_call model must NOT import from sales_agent.domain "
            "(R5 schema-mirror exception: persistence/models/ only, not domain)."
        )
        assert "from src.modules.sales_agent.application" not in src, (
            "eval_simulator_llm_call model must NOT import from sales_agent.application."
        )

    def test_trace_event_model_does_not_import_sales_agent_domain(self) -> None:
        """TraceEventModel does not import from sales_agent domain (R5 boundary)."""
        src = _read(EVAL_SIMULATOR_TRACE_EVENT_MODEL)
        assert "from src.modules.sales_agent.domain" not in src, (
            "eval_simulator_trace_event model must NOT import from sales_agent.domain."
        )

    def test_llm_call_model_imports_from_shared_base_entity(self) -> None:
        """LlmCallModel imports Base from shared.domain.base_entity (correct DDD layer).

        Post-luana-nicolify migration: Base may come from luana_core_platform.domain.base_entity
        (P6 unified singleton) or legacy src.shared.domain.base_entity re-export stub.
        Both are valid during the Story 10 migration window.
        """
        src = _read(EVAL_SIMULATOR_LLM_CALL_MODEL)
        assert (
            "from src.shared.domain.base_entity import Base" in src
            or "from luana_core_platform.domain.base_entity import Base" in src
        ), (
            "eval_simulator_llm_call model must import Base from shared.domain.base_entity "
            "or luana_core_platform.domain.base_entity "
            "(correct DDD pattern — all SQLAlchemy models share the same declarative Base)."
        )

    def test_spec_imports_eval_simulator_llm_call_model(self) -> None:
        """spec.py imports EvalSimulatorLlmCallModel to register it with the registry."""
        src = _read(SPEC_FILE)
        assert "EvalSimulatorLlmCallModel" in src, (
            "spec.py must import EvalSimulatorLlmCallModel to pass it to "
            "AgentObservabilitySpec(llm_call_model=EvalSimulatorLlmCallModel, ...)."
        )
