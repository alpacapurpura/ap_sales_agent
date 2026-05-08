"""Unit tests for GoldenScenarioModel v1 schema (Story D — T-1 + T-4).

T-1 scope: schema-only assertions (serialization, Literal types, ConfigDict).
T-4 scope (EXTENDED here): referential integrity tests — actor_profile_id ∈ Story C
YAMLs, tenant_slug ∈ 5 Story A seeds, dialect_code matches dialect_catalog,
tenant isolation invariant, defense-in-depth PII gate on synthetic fixtures.

# voseo-allowed: test fixtures may contain es-AR dialect samples (dialect_code=es-AR)
"""

from __future__ import annotations

import subprocess
import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.no_eval

# ---------------------------------------------------------------------------
# Path constants (T-4 additions)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[4]
_STORY_C_PERSONAS_DIR = _REPO_ROOT / "docs" / "specs" / "personas" / "archetype-aware"
_STORY_A_DIALECT_CATALOG = _REPO_ROOT / "backend" / "tests" / "fixtures" / "eval" / "tenants" / "dialect_catalog.yaml"
_GOLDENS_TEST_FIXTURES_DIR = _REPO_ROOT / "backend" / "tests" / "_goldens_test_fixtures"
_SCRIPTS_DIR = _REPO_ROOT / "backend" / "scripts"


# ════════════════════════════════════════════════════════════════════════
# Minimal valid fixture factory
# ════════════════════════════════════════════════════════════════════════


def _make_valid_turn(role: str = "customer", turn_number: int = 0) -> dict:
    """Return a minimal valid GoldenTurnModel dict."""
    return {
        "role": role,
        "content": "Hola, me interesa saber más sobre el servicio.",
        "turn_number": turn_number,
    }


def _make_valid_metadata() -> dict:
    """Return a minimal valid GoldenMetadataModel dict."""
    return {
        "generated_from_simulation_id": str(uuid.uuid4()),
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "curated_by": "chris",
        "curated_at": datetime.now(tz=timezone.utc).isoformat(),
        "generation_run_id": str(uuid.uuid4()),
        "seed": 42,
        "cost_usd_at_generation": "0.0123",
        "notes": "",
    }


def _make_valid_golden(**overrides) -> dict:
    """Return a minimal valid GoldenScenarioModel dict."""
    base = {
        "schema_version": 1,
        "id": "test-golden-001",
        "tenant_slug": "tenant_coach_lat",
        "persona_kind": "happy",
        "actor_profile_id": "coach-lat-happy-v2",
        "actor_profile_schema_version": 2,
        "dialect_code": "es-419",
        "transcript": [
            _make_valid_turn("customer", 0),
            _make_valid_turn("agent", 1),
        ],
        "expected_termination_reason": "GOAL_COMPLETION",
        "expected_voice_attributes": ["empathy", "clarity"],
        "metadata": _make_valid_metadata(),
    }
    base.update(overrides)
    return base


# ════════════════════════════════════════════════════════════════════════
# A1 — Round-trip deserialization
# ════════════════════════════════════════════════════════════════════════


def test_golden_scenario_model_round_trip() -> None:
    """GoldenScenarioModel deserializes + reserializes minimal valid fixture."""
    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    raw = _make_valid_golden()
    model = GoldenScenarioModel.model_validate(raw)

    assert model.schema_version == 1
    assert model.id == "test-golden-001"
    assert model.tenant_slug == "tenant_coach_lat"
    assert model.persona_kind == "happy"
    assert model.actor_profile_schema_version == 2
    assert len(model.transcript) == 2
    assert model.expected_termination_reason == "GOAL_COMPLETION"
    assert model.metadata.curated_by == "chris"
    assert model.metadata.cost_usd_at_generation == Decimal("0.0123")


def test_golden_turn_model_round_trip() -> None:
    """GoldenTurnModel with optional fields round-trips cleanly."""
    from tests.agentic_evals.sales_agent.goldens._schema import GoldenTurnModel

    turn = GoldenTurnModel.model_validate(
        {
            "role": "agent",
            "content": "Perfecto, te explico cómo funciona nuestro programa.",
            "turn_number": 1,
            "tool_calls": ["list_public_editions"],
            "latency_ms": 342,
        }
    )
    assert turn.role == "agent"
    assert turn.tool_calls == ["list_public_editions"]
    assert turn.latency_ms == 342


def test_golden_metadata_model_default_notes() -> None:
    """GoldenMetadataModel notes defaults to empty string."""
    from tests.agentic_evals.sales_agent.goldens._schema import GoldenMetadataModel

    meta = GoldenMetadataModel.model_validate(_make_valid_metadata())
    assert meta.notes == ""


# ════════════════════════════════════════════════════════════════════════
# A1 — extra='forbid' rejection
# ════════════════════════════════════════════════════════════════════════


def test_extra_forbid_rejects_unknown_field() -> None:
    """ConfigDict(extra='forbid') rejects unknown fields in GoldenScenarioModel."""
    from pydantic import ValidationError

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    raw = _make_valid_golden(unknown_extra_field="should_be_rejected")
    with pytest.raises(ValidationError, match="extra_forbidden"):
        GoldenScenarioModel.model_validate(raw)


def test_extra_forbid_rejects_unknown_field_in_turn() -> None:
    """ConfigDict(extra='forbid') rejects unknown fields in GoldenTurnModel."""
    from pydantic import ValidationError

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenTurnModel

    with pytest.raises(ValidationError, match="extra_forbidden"):
        GoldenTurnModel.model_validate({"role": "customer", "content": "x", "turn_number": 0, "surprise": "reject"})


def test_extra_forbid_rejects_unknown_field_in_metadata() -> None:
    """ConfigDict(extra='forbid') rejects unknown fields in GoldenMetadataModel."""
    from pydantic import ValidationError

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenMetadataModel

    meta = _make_valid_metadata()
    meta["extra_key"] = "rejected"
    with pytest.raises(ValidationError, match="extra_forbidden"):
        GoldenMetadataModel.model_validate(meta)


# ════════════════════════════════════════════════════════════════════════
# A1 — frozen model mutation rejection
# ════════════════════════════════════════════════════════════════════════


def test_frozen_blocks_mutation() -> None:
    """ConfigDict(frozen=True) raises ValidationError or TypeError on attribute mutation."""
    from pydantic import ValidationError

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    model = GoldenScenarioModel.model_validate(_make_valid_golden())
    # Pydantic v2 frozen raises ValidationError; dataclasses raise TypeError.
    # Accept either — both represent correct frozen behavior.
    with pytest.raises((ValidationError, TypeError)):
        model.id = "mutated"  # type: ignore[misc]


def test_frozen_turn_blocks_mutation() -> None:
    """GoldenTurnModel frozen=True blocks mutation."""
    from pydantic import ValidationError

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenTurnModel

    turn = GoldenTurnModel.model_validate(_make_valid_turn())
    with pytest.raises((ValidationError, TypeError)):
        turn.content = "mutated"  # type: ignore[misc]


def test_frozen_metadata_blocks_mutation() -> None:
    """GoldenMetadataModel frozen=True blocks mutation."""
    from pydantic import ValidationError

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenMetadataModel

    meta = GoldenMetadataModel.model_validate(_make_valid_metadata())
    with pytest.raises((ValidationError, TypeError)):
        meta.notes = "mutated"  # type: ignore[misc]


# ════════════════════════════════════════════════════════════════════════
# Literal type constraints
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "persona_kind",
    ["happy", "nurture", "unqualified"],
)
def test_persona_kind_literal_3_values_only_valid(persona_kind: str) -> None:
    """GoldenPersonaKind accepts exactly 3 valid values."""
    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    model = GoldenScenarioModel.model_validate(_make_valid_golden(persona_kind=persona_kind))
    assert model.persona_kind == persona_kind


def test_persona_kind_literal_3_values_only() -> None:
    """GoldenPersonaKind rejects values outside [happy, nurture, unqualified]."""
    from pydantic import ValidationError

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    # 'adversarial' is Story I scope — NOT in Story D per D3
    for invalid_kind in ["adversarial", "edge", "negative", "angry"]:
        with pytest.raises(ValidationError):
            GoldenScenarioModel.model_validate(_make_valid_golden(persona_kind=invalid_kind))


@pytest.mark.parametrize(
    "tenant_slug",
    [
        "tenant_coach_lat",
        "tenant_medicina_estetica",
        "tenant_clinica_dental",
        "tenant_agencia_growth_video",
        "tenant_agencia_automatizacion_ia",
    ],
)
def test_tenant_slug_literal_5_values_only_valid(tenant_slug: str) -> None:
    """GoldenTenantSlug accepts all 5 Story A tenant seeds."""
    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    model = GoldenScenarioModel.model_validate(_make_valid_golden(tenant_slug=tenant_slug))
    assert model.tenant_slug == tenant_slug


def test_tenant_slug_literal_5_values_only() -> None:
    """GoldenTenantSlug rejects unknown tenant slugs."""
    from pydantic import ValidationError

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    for invalid_slug in ["tenant_unknown", "visionarias", "test_tenant", "any_tenant"]:
        with pytest.raises(ValidationError):
            GoldenScenarioModel.model_validate(_make_valid_golden(tenant_slug=invalid_slug))


@pytest.mark.parametrize(
    "termination_reason",
    ["GOAL_COMPLETION", "MAX_TURNS", "CUSTOMER_EXIT"],
)
def test_termination_reason_literal_3_values_only_valid(termination_reason: str) -> None:
    """GoldenTerminationReason accepts all 3 valid values."""
    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    model = GoldenScenarioModel.model_validate(_make_valid_golden(expected_termination_reason=termination_reason))
    assert model.expected_termination_reason == termination_reason


def test_termination_reason_literal_3_values_only() -> None:
    """GoldenTerminationReason rejects AGENT_ERROR (failure mode — not a golden)."""
    from pydantic import ValidationError

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    for invalid_reason in ["AGENT_ERROR", "TIMEOUT", "unknown_reason"]:
        with pytest.raises(ValidationError):
            GoldenScenarioModel.model_validate(_make_valid_golden(expected_termination_reason=invalid_reason))


def test_actor_profile_schema_version_literal_2() -> None:
    """actor_profile_schema_version must be Literal[2] — rejects other values."""
    from pydantic import ValidationError

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    # Valid
    model = GoldenScenarioModel.model_validate(_make_valid_golden(actor_profile_schema_version=2))
    assert model.actor_profile_schema_version == 2

    # Invalid
    for invalid_version in [1, 3, 0]:
        with pytest.raises(ValidationError):
            GoldenScenarioModel.model_validate(_make_valid_golden(actor_profile_schema_version=invalid_version))


# ════════════════════════════════════════════════════════════════════════
# Field constraints
# ════════════════════════════════════════════════════════════════════════


def test_transcript_min_length_2() -> None:
    """transcript must have at least 2 turns."""
    from pydantic import ValidationError

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    # 1 turn — invalid
    with pytest.raises(ValidationError):
        GoldenScenarioModel.model_validate(_make_valid_golden(transcript=[_make_valid_turn()]))

    # 2 turns — valid
    model = GoldenScenarioModel.model_validate(
        _make_valid_golden(transcript=[_make_valid_turn("customer", 0), _make_valid_turn("agent", 1)])
    )
    assert len(model.transcript) == 2


def test_expected_voice_attributes_min_length_1() -> None:
    """expected_voice_attributes must have at least 1 element."""
    from pydantic import ValidationError

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    with pytest.raises(ValidationError):
        GoldenScenarioModel.model_validate(_make_valid_golden(expected_voice_attributes=[]))


def test_expected_tools_invoked_defaults_empty() -> None:
    """expected_tools_invoked defaults to empty list when not provided."""
    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    raw = _make_valid_golden()
    raw.pop("expected_tools_invoked", None)
    model = GoldenScenarioModel.model_validate(raw)
    assert model.expected_tools_invoked == []


def test_forbidden_tools_defaults_empty() -> None:
    """forbidden_tools defaults to empty list when not provided."""
    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    raw = _make_valid_golden()
    raw.pop("forbidden_tools", None)
    model = GoldenScenarioModel.model_validate(raw)
    assert model.forbidden_tools == []


def test_expected_min_distinct_objections_handled_optional() -> None:
    """expected_min_distinct_objections_handled is None by default (nurture only per D17)."""
    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    model = GoldenScenarioModel.model_validate(_make_valid_golden())
    assert model.expected_min_distinct_objections_handled is None


def test_expected_min_distinct_objections_handled_ge_1_when_set() -> None:
    """expected_min_distinct_objections_handled must be >= 1 when provided."""
    from pydantic import ValidationError

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    # Valid: 1, 2, 3
    for n in [1, 2, 5]:
        model = GoldenScenarioModel.model_validate(
            _make_valid_golden(
                persona_kind="nurture",
                expected_min_distinct_objections_handled=n,
            )
        )
        assert model.expected_min_distinct_objections_handled == n

    # Invalid: 0 (must be >= 1)
    with pytest.raises(ValidationError):
        GoldenScenarioModel.model_validate(_make_valid_golden(expected_min_distinct_objections_handled=0))


def test_id_slug_pattern() -> None:
    """id field must match slug pattern [a-z0-9][a-z0-9_-]+."""
    from pydantic import ValidationError

    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    # Valid slugs
    for valid_id in ["golden-001", "test_golden_v1", "a1b2c3"]:
        model = GoldenScenarioModel.model_validate(_make_valid_golden(id=valid_id))
        assert model.id == valid_id

    # Invalid slugs
    for invalid_id in ["", "AB", "_starts_underscore", "-starts-dash", "has space"]:
        with pytest.raises(ValidationError):
            GoldenScenarioModel.model_validate(_make_valid_golden(id=invalid_id))


# ════════════════════════════════════════════════════════════════════════
# __all__ exports
# ════════════════════════════════════════════════════════════════════════


def test_schema_module_exports_all() -> None:
    """_schema.py __all__ exports required public symbols for downstream Stories E/F/G/H/I."""
    import importlib

    module = importlib.import_module("tests.agentic_evals.sales_agent.goldens._schema")
    exported = set(module.__all__)
    required = {
        "GoldenScenarioModel",
        "GoldenTurnModel",
        "GoldenMetadataModel",
        "GoldenTenantSlug",
        "GoldenPersonaKind",
        "GoldenTerminationReason",
    }
    missing = required - exported
    assert not missing, f"_schema.__all__ missing required exports: {missing}"


# ════════════════════════════════════════════════════════════════════════
# T-4 — Referential integrity tests
# (uses synthetic test fixtures from `_goldens_test_fixtures/`)
# ════════════════════════════════════════════════════════════════════════


def _load_story_c_ids() -> set[str]:
    """Return set of `id` values from all Story C archetype-aware persona YAMLs."""
    ids: set[str] = set()
    if not _STORY_C_PERSONAS_DIR.exists():
        return ids
    for yaml_file in _STORY_C_PERSONAS_DIR.glob("*.yaml"):
        raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "id" in raw:
            ids.add(str(raw["id"]))
    return ids


def _load_story_a_dialect_map() -> dict[str, str]:
    """Return {tenant_slug: dialect_code} from Story A dialect_catalog + ARCHETYPE_DIALECT_MAP hardcode."""
    # Hardcoded from loader.py::ARCHETYPE_DIALECT_MAP (Story A cement)
    return {
        "tenant_coach_lat": "es-PE",
        "tenant_medicina_estetica": "es-MX",
        "tenant_clinica_dental": "es-CO",
        "tenant_agencia_growth_video": "es-AR",
        "tenant_agencia_automatizacion_ia": "es-419",
    }


def _load_synthetic_fixtures() -> list[dict]:
    """Load all 15 synthetic golden YAMLs from `_goldens_test_fixtures/`."""
    fixtures: list[dict] = []
    if not _GOLDENS_TEST_FIXTURES_DIR.exists():
        return fixtures
    for yaml_file in sorted(_GOLDENS_TEST_FIXTURES_DIR.glob("*.yaml")):
        raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            fixtures.append(raw)
    return fixtures


# ── Story A + C referential integrity ────────────────────────────────────


def test_actor_profile_id_exists_in_story_c_yamls() -> None:
    """Each synthetic fixture's actor_profile_id must correspond to a Story C YAML id.

    T-4 deliverable: referential integrity (actor_profile_id ∈ Story C archetype-aware/*.yaml).
    Validates 15-cell synthetic dataset built in this ticket.
    Spec: 03-arch.md §3.8, D7 (actor_profile_schema_version frozen at curation).
    """
    story_c_ids = _load_story_c_ids()
    assert story_c_ids, (
        f"No Story C persona YAMLs found in {_STORY_C_PERSONAS_DIR}. "
        "Ensure Story C build is done before running referential integrity tests."
    )

    fixtures = _load_synthetic_fixtures()
    assert fixtures, (
        f"No synthetic test fixtures found in {_GOLDENS_TEST_FIXTURES_DIR}. T-4 should have created 15 synthetic YAMLs."
    )

    violations: list[str] = []
    for fixture in fixtures:
        actor_id = fixture.get("actor_profile_id", "")
        golden_id = fixture.get("id", "<unknown>")
        if actor_id not in story_c_ids:
            violations.append(f"golden '{golden_id}': actor_profile_id='{actor_id}' not in Story C YAMLs")

    assert not violations, "Referential integrity violation — actor_profile_id not in Story C:\n" + "\n".join(
        f"  - {v}" for v in violations
    )


def test_tenant_slug_in_5_story_a_seeds() -> None:
    """Each synthetic fixture's tenant_slug must be one of the 5 Story A seeds.

    T-4 deliverable: referential integrity (tenant_slug ∈ 5 Story A seeds).
    Validates GoldenTenantSlug Literal[5] cement (D6).
    """
    story_a_slugs = {
        "tenant_coach_lat",
        "tenant_medicina_estetica",
        "tenant_clinica_dental",
        "tenant_agencia_growth_video",
        "tenant_agencia_automatizacion_ia",
    }

    fixtures = _load_synthetic_fixtures()
    assert fixtures, f"No synthetic fixtures in {_GOLDENS_TEST_FIXTURES_DIR}"

    violations: list[str] = []
    for fixture in fixtures:
        slug = fixture.get("tenant_slug", "")
        golden_id = fixture.get("id", "<unknown>")
        if slug not in story_a_slugs:
            violations.append(f"golden '{golden_id}': tenant_slug='{slug}' not in Story A seeds {story_a_slugs}")

    assert not violations, "Referential integrity violation — tenant_slug not in Story A seeds:\n" + "\n".join(
        f"  - {v}" for v in violations
    )


def test_dialect_code_matches_dialect_catalog_strict() -> None:
    """Each synthetic fixture's dialect_code must match Story A ARCHETYPE_DIALECT_MAP[tenant_slug].

    T-4 deliverable: referential integrity (dialect_code == dialect_catalog[tenant_slug]).
    Strict check: no golden may use a dialect_code inconsistent with its tenant's
    registered dialect (Story A loader.py ARCHETYPE_DIALECT_MAP SSoT).
    Spec: 03-arch.md §3.8.
    """
    dialect_map = _load_story_a_dialect_map()
    fixtures = _load_synthetic_fixtures()
    assert fixtures, f"No synthetic fixtures in {_GOLDENS_TEST_FIXTURES_DIR}"

    violations: list[str] = []
    for fixture in fixtures:
        slug = fixture.get("tenant_slug", "")
        dialect = fixture.get("dialect_code", "")
        golden_id = fixture.get("id", "<unknown>")

        if slug not in dialect_map:
            violations.append(f"golden '{golden_id}': unknown tenant_slug '{slug}'")
            continue

        expected_dialect = dialect_map[slug]
        if dialect != expected_dialect:
            violations.append(
                f"golden '{golden_id}': dialect_code='{dialect}' but dialect_catalog['{slug}']='{expected_dialect}'"
            )

    assert not violations, "Dialect code mismatch vs ARCHETYPE_DIALECT_MAP:\n" + "\n".join(
        f"  - {v}" for v in violations
    )


# ── Tenant isolation invariant ───────────────────────────────────────────


def test_one_tenant_per_golden() -> None:
    """Each synthetic fixture contains data from exactly one tenant.

    T-4 deliverable: tenant isolation invariant.
    D6 schema cement: GoldenScenarioModel has a single `tenant_slug` binding —
    there is no multi-tenant field. This test verifies the schema enforces
    the one-tenant-per-golden contract (no cross-tenant data leakage).
    Spec: tenant-isolation.md + 03-arch.md §3.8.
    """
    from tests.agentic_evals.sales_agent.goldens._schema import GoldenScenarioModel

    fixtures = _load_synthetic_fixtures()
    assert fixtures, f"No synthetic fixtures in {_GOLDENS_TEST_FIXTURES_DIR}"

    for fixture in fixtures:
        golden_id = fixture.get("id", "<unknown>")
        # Schema validation will reject any golden with multiple tenant references
        # (extra='forbid' blocks unknown fields; tenant_slug is a single Literal)
        model = GoldenScenarioModel.model_validate(fixture)

        # Single tenant: model.tenant_slug is exactly one Literal value
        assert isinstance(model.tenant_slug, str), (
            f"golden '{golden_id}': tenant_slug is not a string: {model.tenant_slug!r}"
        )
        assert model.tenant_slug in {
            "tenant_coach_lat",
            "tenant_medicina_estetica",
            "tenant_clinica_dental",
            "tenant_agencia_growth_video",
            "tenant_agencia_automatizacion_ia",
        }, f"golden '{golden_id}': tenant_slug '{model.tenant_slug}' not in 5 known tenants"


# ── Defense-in-depth PII gate (synthetic fixtures) ──────────────────────


def test_no_pii_in_committed_goldens() -> None:
    """Defense-in-depth: scan_goldens_pii.py must exit 0 on synthetic test fixtures.

    T-4 deliverable: defense-in-depth PII arch gate (spec §Scenario_4).
    Runs scan_goldens_pii.py against `_goldens_test_fixtures/` (synthetic dataset).
    Expected exit code 0 — synthetic-first invariant guarantees zero PII.

    Gate is also replicated as architecture fitness test in
    `tests/architecture/test_goldens_no_committed_pii.py` which scans the
    REAL `goldens/` directory. This test covers the synthetic fixtures
    used during builder phase (before Chris curates real goldens).

    Skip condition: neither synthetic fixtures dir nor real goldens dir exist.
    Spec: D10, D-A-4, 03-arch.md §3.8.
    """
    if not _GOLDENS_TEST_FIXTURES_DIR.exists() or not any(_GOLDENS_TEST_FIXTURES_DIR.glob("*.yaml")):
        pytest.skip("No synthetic fixtures to scan — builder phase fixtures not yet created")

    scanner = _SCRIPTS_DIR / "scan_goldens_pii.py"
    if not scanner.exists():
        pytest.skip(f"scan_goldens_pii.py not found at {scanner} — T-2 not yet complete")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(scanner), str(_GOLDENS_TEST_FIXTURES_DIR)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, (
        f"PII detected in synthetic test fixtures (exit {result.returncode}).\n"
        f"Scanner output:\n{result.stderr}\n"
        "Synthetic fixtures must not contain real PII (spec D10 strict block).\n"
        f"Fix: replace real PII with synthetic equivalents in {_GOLDENS_TEST_FIXTURES_DIR}"
    )
