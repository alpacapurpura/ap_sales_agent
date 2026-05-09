"""Unit tests for MAJ-EVAL Pydantic v2 types (T-2 TDD).

Pure unit tests — no LLM calls, no DB. Marked @pytest.mark.no_eval so they
run on default CI without requiring ``--run-evals`` flag.

Tests:
- test_majeval_score_frozen_extra_forbid
- test_judge_opinion_score_optional_for_failed_judge
- test_judge_opinion_weight_range_validates
- test_rubric_request_default_cache_policy_use
- test_orm_round_trip_minimal
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from tests.agentic_evals.sales_agent.grader.result import (
    JudgeOpinion,
    MajEvalScore,
    RubricGradeRequest,
)

pytestmark = pytest.mark.no_eval  # Pure Pydantic unit tests — no LLM, no DB, run default CI


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _make_judge_opinion(**overrides: object) -> JudgeOpinion:
    """Factory for a minimal valid JudgeOpinion."""
    defaults: dict[str, object] = {
        "judge_id": "sonnet",
        "model_used": "claude-sonnet-4-6",
        "weight": 0.4,
        "score": 0.85,
        "reasoning": "Voice fidelity is high; agent maintained warmth throughout.",
        "confidence": 0.9,
        "latency_ms": 1200,
        "tokens_input": 500,
        "tokens_output": 120,
        "cost_usd": Decimal("0.003"),
        "round_n": 1,
        "cache_hit": False,
        "injection_attempt_detected": False,
    }
    defaults.update(overrides)
    return JudgeOpinion(**defaults)


def _make_majeval_score(**overrides: object) -> MajEvalScore:
    """Factory for a minimal valid MajEvalScore."""
    judges = [
        _make_judge_opinion(judge_id="sonnet", weight=0.4, score=0.85),
        _make_judge_opinion(judge_id="gpt4o", weight=0.4, score=0.80),
        _make_judge_opinion(judge_id="kimi", weight=0.2, score=0.78),
    ]
    defaults: dict[str, object] = {
        "simulation_id": "sim-001",
        "turn_n": 1,
        "rubric_id": "voice-fidelity",
        "rubric_version": 1,
        "tenant_slug": "tenant_coach_lat",
        "persona_kind": "happy",
        "actor_profile_id": "coach_lat_happy_v1",
        "judges": judges,
        "round_1_score": 0.82,
        "final_score": 0.82,
        "round_1_variance": 0.07,
        "latency_ms_total": 3600,
        "cache_hit_count": 0,
        "created_at": datetime(2026, 5, 9, 0, 0, 0, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return MajEvalScore(**defaults)


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestMajEvalScoreFrozenExtraForbid:
    """Verify MajEvalScore immutability + extra field rejection."""

    def test_frozen_prevents_attribute_mutation(self) -> None:
        """MajEvalScore instances must be immutable post-creation (D-BE-5)."""
        score = _make_majeval_score()
        with pytest.raises((ValidationError, TypeError)):
            score.final_score = 0.99  # type: ignore[misc]

    def test_extra_fields_raise_validation_error(self) -> None:
        """Extra fields must be rejected (extra='forbid')."""
        with pytest.raises(ValidationError) as exc_info:
            MajEvalScore(  # type: ignore[call-arg]
                simulation_id="sim-001",
                turn_n=1,
                rubric_id="voice-fidelity",
                rubric_version=1,
                tenant_slug="tenant_coach_lat",
                persona_kind="happy",
                actor_profile_id="coach_lat_happy_v1",
                judges=[],
                round_1_score=0.82,
                final_score=0.82,
                round_1_variance=0.07,
                latency_ms_total=3600,
                created_at=datetime(2026, 5, 9, tzinfo=timezone.utc),
                unexpected_field="should_fail",  # extra
            )
        assert "unexpected_field" in str(exc_info.value)

    def test_schema_version_default_is_1(self) -> None:
        """schema_version must default to Literal[1] (D-BE-4 cement)."""
        score = _make_majeval_score()
        assert score.schema_version == 1

    def test_schema_version_only_accepts_1(self) -> None:
        """schema_version must only accept Literal[1] (v1 cement — future bumps via SCHEMA_MIGRATIONS)."""
        with pytest.raises(ValidationError):
            _make_majeval_score(schema_version=2)


class TestJudgeOpinionScoreOptionalForFailedJudge:
    """Verify score=None is valid when a judge fails."""

    def test_score_none_allowed(self) -> None:
        """score=None must be accepted (judge failure — excluded from variance calc)."""
        opinion = _make_judge_opinion(score=None)
        assert opinion.score is None

    def test_score_float_accepted(self) -> None:
        """score=0.0 through 1.0 must be accepted."""
        for score in [0.0, 0.5, 1.0]:
            opinion = _make_judge_opinion(score=score)
            assert opinion.score == score

    def test_score_out_of_range_rejected(self) -> None:
        """score > 1.0 or < 0.0 must raise ValidationError."""
        with pytest.raises(ValidationError):
            _make_judge_opinion(score=1.1)
        with pytest.raises(ValidationError):
            _make_judge_opinion(score=-0.1)

    def test_judge_opinion_is_frozen(self) -> None:
        """JudgeOpinion must be frozen (immutable post-creation)."""
        opinion = _make_judge_opinion()
        with pytest.raises((ValidationError, TypeError)):
            opinion.score = 0.5  # type: ignore[misc]


class TestJudgeOpinionWeightRangeValidates:
    """Verify weight field 0.0 <= weight <= 1.0 constraint."""

    def test_weight_0_4_accepted(self) -> None:
        """Canonical Sonnet/GPT-4o weight 0.4 must be accepted."""
        opinion = _make_judge_opinion(weight=0.4)
        assert opinion.weight == 0.4

    def test_weight_0_2_accepted(self) -> None:
        """Canonical Kimi weight 0.2 must be accepted."""
        opinion = _make_judge_opinion(weight=0.2)
        assert opinion.weight == 0.2

    def test_weight_boundaries_accepted(self) -> None:
        """Boundary values 0.0 and 1.0 must be accepted."""
        assert _make_judge_opinion(weight=0.0).weight == 0.0
        assert _make_judge_opinion(weight=1.0).weight == 1.0

    def test_weight_above_1_rejected(self) -> None:
        """weight > 1.0 must raise ValidationError."""
        with pytest.raises(ValidationError):
            _make_judge_opinion(weight=1.1)

    def test_weight_below_0_rejected(self) -> None:
        """weight < 0.0 must raise ValidationError."""
        with pytest.raises(ValidationError):
            _make_judge_opinion(weight=-0.1)

    def test_judge_id_literal_validated(self) -> None:
        """judge_id must be one of {'sonnet', 'gpt4o', 'kimi'} (D15 pinned models)."""
        for valid_id in ["sonnet", "gpt4o", "kimi"]:
            opinion = _make_judge_opinion(judge_id=valid_id)
            assert opinion.judge_id == valid_id
        with pytest.raises(ValidationError):
            _make_judge_opinion(judge_id="unknown_judge")


class TestRubricRequestDefaultCachePolicyUse:
    """Verify RubricGradeRequest defaults and literal constraints."""

    def _make_request(self, **overrides: object) -> RubricGradeRequest:
        """Factory for a minimal valid RubricGradeRequest."""
        defaults: dict[str, object] = {
            "transcript": [],
            "tenant_voice_profile": None,  # forward-ref; None acceptable for type unit tests
            "rubrics": ["voice-fidelity"],
            "simulation_id": "sim-001",
            "tenant_slug": "tenant_coach_lat",
            "persona_kind": "happy",
            "actor_profile_id": "coach_lat_happy_v1",
        }
        defaults.update(overrides)
        return RubricGradeRequest(**defaults)

    def test_cache_policy_default_is_use(self) -> None:
        """cache_policy must default to 'use' (D8 deterministic cache on by default)."""
        req = self._make_request()
        assert req.cache_policy == "use"

    def test_cache_policy_bypass_accepted(self) -> None:
        """cache_policy='bypass' must be accepted for cold-run scenarios."""
        req = self._make_request(cache_policy="bypass")
        assert req.cache_policy == "bypass"

    def test_cache_policy_invalid_rejected(self) -> None:
        """cache_policy must only accept Literal['use', 'bypass']."""
        with pytest.raises(ValidationError):
            self._make_request(cache_policy="skip")

    def test_judge_set_default_is_full_3(self) -> None:
        """judge_set must default to 'full_3' (D-AG-2 3-judge ensemble)."""
        req = self._make_request()
        assert req.judge_set == "full_3"

    def test_persona_kind_literal_validated(self) -> None:
        """persona_kind must be one of {'happy', 'nurture', 'unqualified', 'adversarial'}."""
        valid_kinds = ["happy", "nurture", "unqualified", "adversarial"]
        for kind in valid_kinds:
            req = self._make_request(persona_kind=kind)
            assert req.persona_kind == kind
        with pytest.raises(ValidationError):
            self._make_request(persona_kind="unknown_kind")

    def test_rubric_id_literal_validated_in_rubrics_list(self) -> None:
        """rubrics list must only contain valid rubric IDs (D5 — 4 rubrics in scope)."""
        valid_rubrics = [
            "voice-fidelity",
            "qualification-accuracy",
            "no-overpromise",
            "no-hallucination",
        ]
        req = self._make_request(rubrics=valid_rubrics)
        assert len(req.rubrics) == 4
        with pytest.raises(ValidationError):
            self._make_request(rubrics=["unknown-rubric"])

    def test_request_is_frozen(self) -> None:
        """RubricGradeRequest must be frozen (immutable input contract)."""
        req = self._make_request()
        with pytest.raises((ValidationError, TypeError)):
            req.cache_policy = "bypass"  # type: ignore[misc]


class TestOrmRoundTripMinimal:
    """Verify SQLAlchemy model imports work and columns match migration 127."""

    def test_eval_simulator_grade_model_importable(self) -> None:
        """EvalSimulatorGradeModel must be importable from models package."""
        from src.modules.sales_agent.observability.eval_simulator.persistence.models import (
            EvalSimulatorGradeModel,
        )

        assert EvalSimulatorGradeModel.__tablename__ == "eval_simulator_grade"

    def test_eval_simulator_grade_cache_model_importable(self) -> None:
        """EvalSimulatorGradeCacheModel must be importable from models package."""
        from src.modules.sales_agent.observability.eval_simulator.persistence.models import (
            EvalSimulatorGradeCacheModel,
        )

        assert EvalSimulatorGradeCacheModel.__tablename__ == "eval_simulator_grade_cache"

    def test_grade_model_has_composite_pk_columns(self) -> None:
        """EvalSimulatorGradeModel must expose simulation_id, turn_n, rubric_id columns."""
        from src.modules.sales_agent.observability.eval_simulator.persistence.models import (
            EvalSimulatorGradeModel,
        )

        table = EvalSimulatorGradeModel.__table__
        col_names = {c.name for c in table.columns}
        assert "simulation_id" in col_names
        assert "turn_n" in col_names
        assert "rubric_id" in col_names
        assert "judges" in col_names
        assert "metadata" in col_names  # SQL column name (Python attr = metadata_)
        assert "final_score" in col_names
        assert "debate_triggered" in col_names
        assert "unconverged" in col_names

    def test_grade_cache_model_has_expected_columns(self) -> None:
        """EvalSimulatorGradeCacheModel must expose cache_key, payload, hashes."""
        from src.modules.sales_agent.observability.eval_simulator.persistence.models import (
            EvalSimulatorGradeCacheModel,
        )

        table = EvalSimulatorGradeCacheModel.__table__
        col_names = {c.name for c in table.columns}
        assert "cache_key" in col_names
        assert "payload" in col_names
        assert "transcript_hash" in col_names
        assert "tenant_voice_hash" in col_names
        assert "judge_set_hash" in col_names
        assert "rubric_version" in col_names

    def test_models_package_exports_both_new_models(self) -> None:
        """__init__.py must export EvalSimulatorGradeModel + EvalSimulatorGradeCacheModel."""
        from src.modules.sales_agent.observability.eval_simulator.persistence import models as m

        assert hasattr(m, "EvalSimulatorGradeModel")
        assert hasattr(m, "EvalSimulatorGradeCacheModel")
        assert "EvalSimulatorGradeModel" in m.__all__
        assert "EvalSimulatorGradeCacheModel" in m.__all__

    def test_grade_model_has_pk_constraint_named(self) -> None:
        """eval_simulator_grade must have named PK constraint (migration 127 mirror)."""
        from src.modules.sales_agent.observability.eval_simulator.persistence.models import (
            EvalSimulatorGradeModel,
        )

        table = EvalSimulatorGradeModel.__table__
        # PrimaryKeyConstraint must include the 3 composite columns
        pk_cols = {c.name for c in table.primary_key.columns}
        assert pk_cols == {"simulation_id", "turn_n", "rubric_id"}
