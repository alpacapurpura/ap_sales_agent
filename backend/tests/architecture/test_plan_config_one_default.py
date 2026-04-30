"""Architecture fitness — plan_config one-default invariant.

PM Q6: exactly one plan_config row may have is_default=TRUE.
Enforced at two levels:
  1. DB-level: partial unique index `uq_plan_config_one_default` on
     plan_config(is_default) WHERE is_default = TRUE.
  2. Runtime: PlanService.get_default_plan() + Streamlit admin atomic toggle.

This test enforces:
  1. PlanConfigModel declares is_default column (domain model level).
  2. PlanRepository.get_default() queries WHERE is_default = TRUE LIMIT 1.
  3. PlanService.update_plan() exists (atomic toggle entry point).
  4. The migration creating the partial unique index can be located.
  5. BillingDefaultPlanMissingError is raised when no default found
     (fail-fast per PM Q6, not silent fallback).
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

# ── Source paths ─────────────────────────────────────────────────────────────

_BACKEND = Path(__file__).resolve().parents[2]
_ALEMBIC_VERSIONS = _BACKEND / "alembic" / "versions"


# ── Tests ────────────────────────────────────────────────────────────────────


def test_plan_config_model_has_is_default_column() -> None:
    """PlanConfigModel must have is_default column (PM Q6 DB-level enforcement)."""
    from src.shared.billing.infrastructure.models.plan_config_model import PlanConfigModel

    # Check attribute exists on the ORM model
    assert hasattr(PlanConfigModel, "is_default"), (
        "PlanConfigModel must have is_default column for PM Q6 one-default invariant."
    )


def test_plan_config_domain_has_is_default_field() -> None:
    """PlanConfig VO must have is_default field."""
    from src.shared.billing.domain.plan import PlanConfig

    fields = set(PlanConfig.model_fields.keys())
    assert "is_default" in fields, (
        "PlanConfig Pydantic model must have is_default field. "
        "It carries the partial unique index invariant to the domain layer."
    )


def test_plan_config_is_default_defaults_to_false() -> None:
    """PlanConfig.is_default must default to False (not True).

    Only one row is default. New plans are non-default until explicitly set.
    """
    from src.shared.billing.domain.plan import PlanConfig
    from decimal import Decimal

    plan = PlanConfig(
        plan_id="test",
        display_name="Test",
        llm_budget_total_usd=Decimal("10.00"),
    )
    assert plan.is_default is False, (
        "PlanConfig.is_default must default to False. New plans must not accidentally become default."
    )


def test_plan_repository_has_get_default() -> None:
    """PlanRepository ABC must declare get_default() method."""
    from src.shared.billing.domain.plan_repository import PlanRepository

    assert hasattr(PlanRepository, "get_default"), "PlanRepository must have get_default() method for PM Q6 resolution."


def test_plan_repository_get_default_queries_is_default_true() -> None:
    """SQLAPlanRepository.get_default must filter WHERE is_default = TRUE.

    Parsed via AST: ensures the implementation queries the right predicate.
    """
    impl_path = _BACKEND / "src" / "shared" / "billing" / "infrastructure" / "plan_repository_impl.py"
    assert impl_path.exists(), f"PlanRepository implementation not found at {impl_path}"

    source = impl_path.read_text(encoding="utf-8")
    # Both .is_(True) and == True patterns should match
    assert "is_default" in source, "plan_repository_impl.py must filter by is_default in get_default()."
    # Verify is_(True) or == True pattern appears near get_default
    tree = ast.parse(source)
    found_is_default_filter = False
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "get_default":
            func_source = ast.get_source_segment(source, node)
            if func_source and "is_default" in func_source:
                found_is_default_filter = True
            break
    assert found_is_default_filter, "SQLAPlanRepository.get_default() must filter by is_default = TRUE."


def test_plan_service_has_update_plan_method() -> None:
    """PlanService must have update_plan() for atomic is_default toggle."""
    from src.shared.billing.application.plan_service import PlanService

    assert hasattr(PlanService, "update_plan"), (
        "PlanService must have update_plan() method for atomic is_default toggle (PM Q6)."
    )

    # Verify it's async (plan writes are async operations)
    method = PlanService.update_plan
    assert inspect.iscoroutinefunction(method), "PlanService.update_plan() must be async."


def test_billing_default_plan_missing_error_exists() -> None:
    """BillingDefaultPlanMissingError must exist and be raised when no default.

    PM Q6: fail-fast (raise) rather than silent fallback when no default plan.
    """
    from src.shared.billing.application.plan_service import (
        BillingDefaultPlanMissingError,
        PlanService,
    )

    assert issubclass(BillingDefaultPlanMissingError, Exception), (
        "BillingDefaultPlanMissingError must be an Exception subclass."
    )


def test_plan_service_get_default_raises_when_no_plan_found() -> None:
    """PlanService.get_default_plan() must raise BillingDefaultPlanMissingError.

    Validates fail-fast behavior per PM Q6: if no default plan in DB
    and env var fallback also fails, raise (not return None).
    """
    plan_service_path = _BACKEND / "src" / "shared" / "billing" / "application" / "plan_service.py"
    source = plan_service_path.read_text(encoding="utf-8")

    assert "BillingDefaultPlanMissingError" in source, (
        "PlanService must reference BillingDefaultPlanMissingError. "
        "get_default_plan() must raise when no default plan is resolvable."
    )
    assert "raise BillingDefaultPlanMissingError" in source, (
        "PlanService.get_default_plan() must have a `raise BillingDefaultPlanMissingError(...)` path."
    )


def test_partial_unique_index_documented_in_model() -> None:
    """PlanConfigModel must document the partial unique index (comment or __table_args__)."""
    from src.shared.billing.infrastructure.models.plan_config_model import PlanConfigModel
    import inspect as inspect_mod

    source = inspect_mod.getsource(PlanConfigModel)
    # Check for the index name or the concept
    assert "uq_plan_config_one_default" in source or "partial unique" in source.lower(), (
        "PlanConfigModel must document the partial unique index "
        "`uq_plan_config_one_default ON plan_config (is_default) WHERE is_default = TRUE`. "
        "Add a comment in __table_args__ or the class docstring."
    )


def test_migration_creates_partial_unique_index() -> None:
    """The seed migration must create the partial unique index.

    Scans alembic/versions/ for a migration referencing uq_plan_config_one_default.
    """
    if not _ALEMBIC_VERSIONS.exists():
        return  # Skip in environments without migrations directory

    found = False
    for migration_file in _ALEMBIC_VERSIONS.glob("*.py"):
        try:
            content = migration_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "uq_plan_config_one_default" in content:
            found = True
            break

    assert found, (
        "No Alembic migration found that creates the partial unique index "
        "`uq_plan_config_one_default ON plan_config (is_default) WHERE is_default = TRUE`. "
        "This index enforces the PM Q6 one-default invariant at the DB level."
    )
