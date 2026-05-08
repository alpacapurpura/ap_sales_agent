"""Unit tests for SimulationState / ActorProfile / SimulationResult / ConversationTurn / CostSummary.

T-4 acceptance A1: All Pydantic classes deserializable + frozen + schema_version field.

TDD RED-first per `.claude/rules/tdd-mandatory.md`.
"""

# voseo-allowed: tests reference dialect_code es-AR fixture for actor persona — magic comment escape

import operator
from datetime import UTC, datetime
from decimal import Decimal
from typing import get_args, get_origin
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel, ValidationError

from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile
from tests.agentic_evals.sales_agent.simulator.result import (
    ConversationTurn,
    CostSummary,
    SimulationResult,
)
from tests.agentic_evals.sales_agent.simulator.state import SimulationState
from tests.agentic_evals.sales_agent.simulator.termination import (
    AgentErrorSubtype,
    TerminationReason,
)


pytestmark = pytest.mark.no_eval


# ════════════════════════════════════════════════════════════════════════
# ActorProfile — frozen, schema_version, dialect default, validation
# ════════════════════════════════════════════════════════════════════════


def _make_actor() -> ActorProfile:
    return ActorProfile(
        id="lead-frio-impaciente",
        name="María Cliente Fría",
        actor_goal="Decidir si vale la pena agendar llamada",
        dialect_code="es-419",
        traits=["impaciente", "exigente"],
        pain_points=["resultados lentos"],
        objections=["precio", "tiempo"],
        budget_hint="medio",
        urgency="medium",
        communication_style="directa",
        initial_message="Hola, vi tu anuncio. ¿Cuánto cuesta?",
        persona_kind="happy",
    )


class TestActorProfile:
    def test_schema_version_field_default_matches_current_schema_versions(self) -> None:
        """Story C bump (D13) — default == CURRENT_SCHEMA_VERSIONS["ActorProfile"] (= 2).

        Renamed from `test_schema_version_field_default_1` post Story C T-1
        bump 1 → 2. Keeps assertion data-driven so future bumps fail loudly
        only at the registry source (not multiple places).
        """
        from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
            CURRENT_SCHEMA_VERSIONS,
        )

        actor = _make_actor()
        assert actor.schema_version == CURRENT_SCHEMA_VERSIONS["ActorProfile"]
        # Cement the absolute value too — catches accidental drift between
        # the registry and the model default during regression hunts.
        assert actor.schema_version == 2

    def test_frozen_immutable(self) -> None:
        actor = _make_actor()
        with pytest.raises(ValidationError):
            actor.name = "otro"

    def test_extra_forbid(self) -> None:
        with pytest.raises(ValidationError):
            ActorProfile.model_validate(
                {
                    "id": "x",
                    "name": "x",
                    "actor_goal": "x",
                    "initial_message": "x",
                    "unknown_field": "should fail",
                }
            )

    def test_dialect_code_default_es_419(self) -> None:
        actor = ActorProfile(
            id="x",
            name="x",
            actor_goal="x",
            initial_message="hola",
        )
        assert actor.dialect_code == "es-419"

    def test_persona_kind_literal_validation(self) -> None:
        with pytest.raises(ValidationError):
            ActorProfile.model_validate(
                {
                    "id": "x",
                    "name": "x",
                    "actor_goal": "x",
                    "initial_message": "hola",
                    "persona_kind": "invalid_kind",
                }
            )

    def test_urgency_literal_validation(self) -> None:
        with pytest.raises(ValidationError):
            ActorProfile.model_validate(
                {
                    "id": "x",
                    "name": "x",
                    "actor_goal": "x",
                    "initial_message": "hola",
                    "urgency": "extreme",
                }
            )

    def test_voseo_allowed_when_dialect_es_ar(self) -> None:
        # voseo-allowed: actor persona dialect injection
        actor = ActorProfile(
            id="x",
            name="Juan Argentino",
            actor_goal="comprar",
            dialect_code="es-AR",
            communication_style="vos sos directa, tenés ganas de saber",
            initial_message="hola, querés explicarme?",
            persona_kind="happy",
        )
        assert actor.dialect_code == "es-AR"
        assert "vos" in actor.communication_style

    def test_round_trip_model_dump_validate(self) -> None:
        actor = _make_actor()
        raw = actor.model_dump()
        rebuilt = ActorProfile.model_validate(raw)
        assert rebuilt == actor


# ════════════════════════════════════════════════════════════════════════
# ConversationTurn — frozen, schema_version, role literal
# ════════════════════════════════════════════════════════════════════════


class TestConversationTurn:
    def test_schema_version_field_default_1(self) -> None:
        turn = ConversationTurn(
            turn_number=0,
            role="customer",
            content="hola",
            timestamp=datetime.now(tz=UTC),
        )
        assert turn.schema_version == 1

    def test_frozen_immutable(self) -> None:
        turn = ConversationTurn(
            turn_number=0,
            role="customer",
            content="hola",
            timestamp=datetime.now(tz=UTC),
        )
        with pytest.raises(ValidationError):
            turn.content = "modified"

    def test_role_literal_customer_or_agent(self) -> None:
        ConversationTurn(turn_number=0, role="customer", content="x", timestamp=datetime.now(tz=UTC))
        ConversationTurn(turn_number=1, role="agent", content="y", timestamp=datetime.now(tz=UTC))
        with pytest.raises(ValidationError):
            ConversationTurn.model_validate(
                {
                    "turn_number": 0,
                    "role": "bot",
                    "content": "x",
                    "timestamp": datetime.now(tz=UTC),
                }
            )

    def test_content_min_length_1(self) -> None:
        with pytest.raises(ValidationError):
            ConversationTurn(turn_number=0, role="customer", content="", timestamp=datetime.now(tz=UTC))

    def test_turn_number_ge_zero(self) -> None:
        with pytest.raises(ValidationError):
            ConversationTurn(turn_number=-1, role="customer", content="x", timestamp=datetime.now(tz=UTC))

    def test_extra_forbid(self) -> None:
        with pytest.raises(ValidationError):
            ConversationTurn.model_validate(
                {
                    "turn_number": 0,
                    "role": "customer",
                    "content": "x",
                    "timestamp": datetime.now(tz=UTC),
                    "unknown": "field",
                }
            )


# ════════════════════════════════════════════════════════════════════════
# CostSummary — frozen, schema_version, default Decimal zero
# ════════════════════════════════════════════════════════════════════════


class TestCostSummary:
    def test_schema_version_default_1(self) -> None:
        cs = CostSummary()
        assert cs.schema_version == 1

    def test_frozen_immutable(self) -> None:
        cs = CostSummary()
        with pytest.raises(ValidationError):
            cs.total_cost_usd = Decimal(99)

    def test_default_decimal_zero(self) -> None:
        cs = CostSummary()
        assert cs.agent_cost_usd == Decimal(0)
        assert cs.simulator_cost_usd == Decimal(0)
        assert cs.total_cost_usd == Decimal(0)

    def test_llm_calls_count_split_default_zero(self) -> None:
        cs = CostSummary()
        assert cs.llm_calls_count_split == {"sales_agent": 0, "eval_simulator": 0}

    def test_constructed_with_values(self) -> None:
        cs = CostSummary(
            agent_cost_usd=Decimal("0.012"),
            simulator_cost_usd=Decimal("0.008"),
            total_cost_usd=Decimal("0.020"),
            llm_calls_count_split={"sales_agent": 3, "eval_simulator": 2},
        )
        assert cs.total_cost_usd == Decimal("0.020")
        assert cs.llm_calls_count_split["sales_agent"] == 3


# ════════════════════════════════════════════════════════════════════════
# SimulationResult — frozen, schema_version, references nested types
# ════════════════════════════════════════════════════════════════════════


class TestSimulationResult:
    def _make_result(self) -> SimulationResult:
        ts = datetime.now(tz=UTC)
        return SimulationResult(
            simulation_id=uuid4(),
            run_id=uuid4(),
            tenant_id=uuid4(),
            archetype_slug="tenant_coach_lat",
            actor_profile_id="lead-frio-impaciente",
            trial_n=0,
            transcript=[
                ConversationTurn(
                    turn_number=0,
                    role="customer",
                    content="hola",
                    timestamp=ts,
                ),
            ],
            termination_reason=TerminationReason.MAX_TURNS,
            error_subtype=None,
            total_turns=1,
            cost_summary=CostSummary(),
            started_at=ts,
            completed_at=ts,
            artifact_path="_artifacts/run-1/simulator/sim-1/transcript.json",
        )

    def test_schema_version_default_1(self) -> None:
        result = self._make_result()
        assert result.schema_version == 1

    def test_frozen_immutable(self) -> None:
        result = self._make_result()
        with pytest.raises(ValidationError):
            result.total_turns = 99

    def test_termination_reason_strenum(self) -> None:
        result = self._make_result()
        assert result.termination_reason == TerminationReason.MAX_TURNS
        # accepts string value too (StrEnum coercion via model_validate)
        ts = datetime.now(tz=UTC)
        raw = {
            "simulation_id": str(uuid4()),
            "run_id": str(uuid4()),
            "tenant_id": str(uuid4()),
            "archetype_slug": "x",
            "actor_profile_id": "y",
            "trial_n": 0,
            "transcript": [],
            "termination_reason": "max_turns",
            "total_turns": 0,
            "cost_summary": CostSummary().model_dump(mode="json"),
            "started_at": ts.isoformat(),
            "completed_at": ts.isoformat(),
            "artifact_path": "_artifacts/x.json",
        }
        result2 = SimulationResult.model_validate(raw)
        assert result2.termination_reason == TerminationReason.MAX_TURNS

    def test_error_subtype_optional(self) -> None:
        result = self._make_result()
        assert result.error_subtype is None

    def test_round_trip_serialization(self) -> None:
        result = self._make_result()
        raw = result.model_dump(mode="json")
        rebuilt = SimulationResult.model_validate(raw)
        assert rebuilt.simulation_id == result.simulation_id
        assert rebuilt.termination_reason == result.termination_reason


# ════════════════════════════════════════════════════════════════════════
# SimulationState — Pydantic, schema_version, transcript reducer annotated
# ════════════════════════════════════════════════════════════════════════


class TestSimulationState:
    def _make_state(self) -> SimulationState:
        return SimulationState(
            simulation_id=uuid4(),
            run_id=uuid4(),
            tenant_id=uuid4(),
            archetype_slug="tenant_coach_lat",
            actor_profile=_make_actor(),
        )

    def test_schema_version_default_1(self) -> None:
        state = self._make_state()
        assert state.schema_version == 1

    def test_extra_forbid(self) -> None:
        with pytest.raises(ValidationError):
            SimulationState.model_validate(
                {
                    "simulation_id": uuid4(),
                    "run_id": uuid4(),
                    "tenant_id": uuid4(),
                    "archetype_slug": "x",
                    "actor_profile": _make_actor(),
                    "unknown_extra": "should fail",
                }
            )

    def test_transcript_reducer_annotation_operator_add(self) -> None:
        """Verify Annotated[list[ConversationTurn], operator.add] reducer hint present.

        LangGraph reads metadata from Annotated to apply add reducer.
        """
        # Inspect the model field annotation
        field = SimulationState.model_fields["transcript"]
        annotation = field.metadata
        # Pydantic stores Annotated metadata in field.metadata (list)
        assert any(meta is operator.add for meta in annotation), (
            f"transcript reducer not Annotated[..., operator.add]: metadata={annotation}"
        )

    def test_transcript_default_empty_list(self) -> None:
        state = self._make_state()
        assert state.transcript == []

    def test_iterations_max_iter_guard_field_present(self) -> None:
        state = self._make_state()
        assert state.iterations == 0
        assert state.max_turns == 10

    def test_max_turns_validation_bounds(self) -> None:
        with pytest.raises(ValidationError):
            SimulationState(
                simulation_id=uuid4(),
                run_id=uuid4(),
                tenant_id=uuid4(),
                archetype_slug="x",
                actor_profile=_make_actor(),
                max_turns=0,
            )
        with pytest.raises(ValidationError):
            SimulationState(
                simulation_id=uuid4(),
                run_id=uuid4(),
                tenant_id=uuid4(),
                archetype_slug="x",
                actor_profile=_make_actor(),
                max_turns=21,
            )

    def test_termination_reason_optional_strenum(self) -> None:
        state = self._make_state()
        assert state.termination_reason is None
        # Coercion check via re-validate
        raw = state.model_dump()
        raw["termination_reason"] = "max_turns"
        rebuilt = SimulationState.model_validate(raw)
        assert rebuilt.termination_reason == TerminationReason.MAX_TURNS

    def test_error_subtype_optional_strenum(self) -> None:
        state = self._make_state()
        assert state.error_subtype is None
        raw = state.model_dump()
        raw["error_subtype"] = "timeout"
        rebuilt = SimulationState.model_validate(raw)
        assert rebuilt.error_subtype == AgentErrorSubtype.TIMEOUT

    def test_tenant_id_required(self) -> None:
        with pytest.raises(ValidationError):
            SimulationState.model_validate(
                {
                    "simulation_id": uuid4(),
                    "run_id": uuid4(),
                    "archetype_slug": "x",
                    "actor_profile": _make_actor(),
                },
            )

    def test_uuid_fields_typed(self) -> None:
        state = self._make_state()
        assert isinstance(state.simulation_id, UUID)
        assert isinstance(state.run_id, UUID)
        assert isinstance(state.tenant_id, UUID)


# ════════════════════════════════════════════════════════════════════════
# Cross-class invariants — every Pydantic class has schema_version: int = 1
# ════════════════════════════════════════════════════════════════════════


SCHEMA_VERSIONED_CLASSES: list[type[BaseModel]] = [
    ActorProfile,
    ConversationTurn,
    CostSummary,
    SimulationResult,
    SimulationState,
]


@pytest.mark.parametrize("cls", SCHEMA_VERSIONED_CLASSES)
def test_every_class_has_schema_version_field(cls: type[BaseModel]) -> None:
    """H1 forward-compat — every Pydantic model has schema_version field.

    Default value MUST equal CURRENT_SCHEMA_VERSIONS[cls.__name__] (data-driven).
    This contract makes the registry the single source of truth for the active
    version of every Pydantic class. Story C bumps ActorProfile 1 → 2; future
    stories may bump others — but each model's default must always track its
    registry entry exactly (catches accidental drift between the two SSoTs).
    """
    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        CURRENT_SCHEMA_VERSIONS,
    )

    fields = cls.model_fields
    assert "schema_version" in fields, f"{cls.__name__} missing schema_version field"
    field = fields["schema_version"]
    expected_default = CURRENT_SCHEMA_VERSIONS[cls.__name__]
    assert field.default == expected_default, (
        f"{cls.__name__}.schema_version default ({field.default}) != "
        f"CURRENT_SCHEMA_VERSIONS[{cls.__name__!r}] ({expected_default}). "
        "Update the model default to match the registry entry, or vice versa."
    )
    assert field.annotation is int, f"{cls.__name__}.schema_version type != int (got {field.annotation})"


def test_transcript_typed_list_of_conversation_turn() -> None:
    """SimulationState.transcript must be list[ConversationTurn] for type safety."""
    field = SimulationState.model_fields["transcript"]
    annotation = field.annotation
    # annotation should be list[ConversationTurn] (origin=list, args=(ConversationTurn,))
    origin = get_origin(annotation)
    args = get_args(annotation)
    assert origin is list, f"transcript origin != list (got {origin})"
    assert args == (ConversationTurn,), f"transcript args != (ConversationTurn,) (got {args})"
