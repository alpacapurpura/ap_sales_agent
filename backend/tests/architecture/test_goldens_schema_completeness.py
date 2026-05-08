"""Architecture fitness gate — GoldenScenarioModel v1 schema completeness.

Asserts structural invariants of the goldens schema layer (Story D — T-1):
  1. schema_version Literal[1] cement (D6)
  2. ConfigDict(extra='forbid', frozen=True) on all 3 model classes
  3. Literal type coverage: GoldenTenantSlug (5), GoldenPersonaKind (3),
     GoldenTerminationReason (3)
  4. actor_profile_schema_version Literal[2] cement (D7)
  5. CURRENT_GOLDEN_SCHEMA_VERSIONS['GoldenScenarioModel'] == 1 cement
  6. If CURRENT_GOLDEN_SCHEMA_VERSIONS[X] > 1, migrators registered

Ratchet pattern: allowlists empty, shrink-only. Any violation = build fail.

# voseo-allowed: arch fitness docstrings may cite test dialect examples
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.no_eval


# ════════════════════════════════════════════════════════════════════════
# Importability
# ════════════════════════════════════════════════════════════════════════


def test_golden_schema_module_importable() -> None:
    """goldens._schema module is importable without errors."""
    from tests.agentic_evals.sales_agent.goldens import _schema

    assert _schema is not None


def test_golden_schema_migrations_module_importable() -> None:
    """goldens._schema_migrations module is importable without errors."""
    from tests.agentic_evals.sales_agent.goldens import _schema_migrations

    assert _schema_migrations is not None


def test_golden_scenario_model_importable() -> None:
    """GoldenScenarioModel importable from goldens._schema."""
    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    assert GoldenScenarioModel is not None


# ════════════════════════════════════════════════════════════════════════
# schema_version Literal[1] cement (D6)
# ════════════════════════════════════════════════════════════════════════


def test_schema_version_field_is_literal_1() -> None:
    """GoldenScenarioModel.schema_version field type is Literal[1]."""
    from typing import Literal, get_args, get_origin

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    fields = GoldenScenarioModel.model_fields
    assert "schema_version" in fields, "GoldenScenarioModel missing 'schema_version' field"

    # Pydantic stores the annotation — check it's Literal[1]
    annotation = fields["schema_version"].annotation
    assert get_origin(annotation) is Literal or annotation == Literal[1], (
        f"schema_version annotation expected Literal[1], got {annotation!r}"
    )
    args = get_args(annotation)
    assert args == (1,), f"Literal args expected (1,), got {args!r}"


def test_schema_version_default_is_1() -> None:
    """GoldenScenarioModel.schema_version defaults to 1."""
    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    field_info = GoldenScenarioModel.model_fields["schema_version"]
    assert field_info.default == 1, f"schema_version default expected 1, got {field_info.default!r}"


# ════════════════════════════════════════════════════════════════════════
# ConfigDict(extra='forbid', frozen=True) on all model classes
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "model_name",
    ["GoldenScenarioModel", "GoldenTurnModel", "GoldenMetadataModel"],
)
def test_model_config_extra_forbid(model_name: str) -> None:
    """All golden models have ConfigDict(extra='forbid')."""
    import importlib

    schema_module = importlib.import_module("tests.agentic_evals.sales_agent.goldens._schema")
    model_class = getattr(schema_module, model_name)
    config = model_class.model_config

    assert config.get("extra") == "forbid", (
        f"{model_name} ConfigDict extra expected 'forbid', got {config.get('extra')!r}"
    )


@pytest.mark.parametrize(
    "model_name",
    ["GoldenScenarioModel", "GoldenTurnModel", "GoldenMetadataModel"],
)
def test_model_config_frozen(model_name: str) -> None:
    """All golden models have ConfigDict(frozen=True) — immutable artifacts."""
    import importlib

    schema_module = importlib.import_module("tests.agentic_evals.sales_agent.goldens._schema")
    model_class = getattr(schema_module, model_name)
    config = model_class.model_config

    assert config.get("frozen") is True, f"{model_name} ConfigDict frozen expected True, got {config.get('frozen')!r}"


# ════════════════════════════════════════════════════════════════════════
# Literal type coverage
# ════════════════════════════════════════════════════════════════════════


def test_golden_tenant_slug_has_5_values() -> None:
    """GoldenTenantSlug Literal covers exactly 5 Story A tenant seeds."""
    from typing import get_args

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenTenantSlug

    args = get_args(GoldenTenantSlug)
    assert len(args) == 5, f"GoldenTenantSlug expected 5 values, got {len(args)}: {args!r}"

    expected_slugs = {
        "tenant_coach_lat",
        "tenant_medicina_estetica",
        "tenant_clinica_dental",
        "tenant_agencia_growth_video",
        "tenant_agencia_automatizacion_ia",
    }
    assert set(args) == expected_slugs, (
        f"GoldenTenantSlug values mismatch.\nExpected: {expected_slugs}\nGot: {set(args)}"
    )


def test_golden_persona_kind_has_3_values() -> None:
    """GoldenPersonaKind Literal covers exactly 3 values (adversarial = Story I, D3)."""
    from typing import get_args

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenPersonaKind

    args = get_args(GoldenPersonaKind)
    assert len(args) == 3, f"GoldenPersonaKind expected 3 values, got {len(args)}: {args!r}"

    expected_kinds = {"happy", "nurture", "unqualified"}
    assert set(args) == expected_kinds, (
        f"GoldenPersonaKind values mismatch.\nExpected: {expected_kinds}\nGot: {set(args)}"
    )

    # adversarial is Story I — must NOT be in Story D schema
    assert "adversarial" not in args, "adversarial persona kind must NOT be in Story D schema (D3 scope)"


def test_golden_termination_reason_has_3_values() -> None:
    """GoldenTerminationReason Literal covers 3 success outcomes (excludes AGENT_ERROR)."""
    from typing import get_args

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenTerminationReason

    args = get_args(GoldenTerminationReason)
    assert len(args) == 3, f"GoldenTerminationReason expected 3 values, got {len(args)}: {args!r}"

    expected_reasons = {"GOAL_COMPLETION", "MAX_TURNS", "CUSTOMER_EXIT"}
    assert set(args) == expected_reasons, (
        f"GoldenTerminationReason mismatch.\nExpected: {expected_reasons}\nGot: {set(args)}"
    )

    # AGENT_ERROR = failure mode, must NOT be in golden schema
    assert "AGENT_ERROR" not in args, "AGENT_ERROR must NOT be in GoldenTerminationReason (failure mode)"


# ════════════════════════════════════════════════════════════════════════
# actor_profile_schema_version Literal[2] cement (D7)
# ════════════════════════════════════════════════════════════════════════


def test_actor_profile_schema_version_is_literal_2() -> None:
    """actor_profile_schema_version field is Literal[2] — frozen at Story C v2 (D7)."""
    from typing import Literal, get_args, get_origin

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    fields = GoldenScenarioModel.model_fields
    assert "actor_profile_schema_version" in fields, "Missing actor_profile_schema_version field"

    annotation = fields["actor_profile_schema_version"].annotation
    assert get_origin(annotation) is Literal or annotation == Literal[2], (
        f"actor_profile_schema_version expected Literal[2], got {annotation!r}"
    )
    args = get_args(annotation)
    assert args == (2,), f"Literal args expected (2,), got {args!r}"


# ════════════════════════════════════════════════════════════════════════
# CURRENT_GOLDEN_SCHEMA_VERSIONS cement
# ════════════════════════════════════════════════════════════════════════


def test_current_golden_schema_versions_has_golden_scenario_model() -> None:
    """CURRENT_GOLDEN_SCHEMA_VERSIONS['GoldenScenarioModel'] == 1."""
    from tests.agentic_evals.sales_agent.goldens._schema_migrations import (
        CURRENT_GOLDEN_SCHEMA_VERSIONS,
    )

    assert "GoldenScenarioModel" in CURRENT_GOLDEN_SCHEMA_VERSIONS, (
        "CURRENT_GOLDEN_SCHEMA_VERSIONS missing 'GoldenScenarioModel' entry"
    )
    assert CURRENT_GOLDEN_SCHEMA_VERSIONS["GoldenScenarioModel"] == 1, (
        f"GoldenScenarioModel version cement: expected 1, got {CURRENT_GOLDEN_SCHEMA_VERSIONS['GoldenScenarioModel']!r}"
    )


def test_golden_schema_migrations_registry_exhaustive_if_bumped() -> None:
    """If any CURRENT_GOLDEN_SCHEMA_VERSIONS > 1, migration chain MUST be registered."""
    from tests.agentic_evals.sales_agent.goldens._schema_migrations import (
        CURRENT_GOLDEN_SCHEMA_VERSIONS,
        GOLDEN_SCHEMA_MIGRATIONS,
    )

    for model_name, curr_v in CURRENT_GOLDEN_SCHEMA_VERSIONS.items():
        if curr_v == 1:
            continue  # v1 baseline — no migrations needed
        for prev in range(1, curr_v):
            key = (model_name, prev, prev + 1)
            assert key in GOLDEN_SCHEMA_MIGRATIONS, (
                f"Missing golden migration: {model_name} {prev} → {prev + 1}. "
                f"Register via @register_golden_migration in _schema_migrations.py."
            )


# ════════════════════════════════════════════════════════════════════════
# __all__ completeness
# ════════════════════════════════════════════════════════════════════════


def test_schema_all_exports_complete() -> None:
    """_schema.__all__ exports all public symbols required by downstream Stories."""
    from tests.agentic_evals.sales_agent.goldens import _schema

    exported = set(_schema.__all__)
    required = {
        "GoldenScenarioModel",
        "GoldenTurnModel",
        "GoldenMetadataModel",
        "GoldenTenantSlug",
        "GoldenPersonaKind",
        "GoldenTerminationReason",
    }
    missing = required - exported
    assert not missing, f"_schema.__all__ missing exports: {missing}"


def test_schema_migrations_all_exports_complete() -> None:
    """_schema_migrations.__all__ exports required public symbols."""
    from tests.agentic_evals.sales_agent.goldens import _schema_migrations

    exported = set(_schema_migrations.__all__)
    required = {
        "CURRENT_GOLDEN_SCHEMA_VERSIONS",
        "GOLDEN_SCHEMA_MIGRATIONS",
        "GoldenMigrator",
        "apply_golden_migrations",
        "register_golden_migration",
    }
    missing = required - exported
    assert not missing, f"_schema_migrations.__all__ missing exports: {missing}"
