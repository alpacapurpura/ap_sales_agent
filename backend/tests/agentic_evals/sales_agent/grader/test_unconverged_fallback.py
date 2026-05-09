"""Unconverged fallback semantics tests (Story E T-9).

Validates D4 / DQ8 cement — when Round 2 variance ≥ 0.10:
  - ``unconverged=True`` flag set
  - ``final_score = round_1_weighted_avg`` (R1 fallback)
  - ``structlog.warning`` emitted (NOT auto-block per DQ8 graceful degradation)

Reuses scenario fixtures from ``scenarios/test_scenario_2_edge_round_2_debate.py``
plus a dedicated structlog-spy test.

Cement decisions verified:
  - D4 unconverged fallback
  - DQ8 NO auto-block on unconverged

# voseo-allowed: docstring quotes D4 / DQ8 cement
"""

# NO ``from __future__ import annotations`` — story-wide cement parity.

from typing import Any
from unittest.mock import patch

import pytest

from tests.agentic_evals.sales_agent.grader._internal import maj_eval as me
from tests.agentic_evals.sales_agent.grader._internal.judge_registry import JUDGE_WEIGHTS
from tests.agentic_evals.sales_agent.grader.scenarios.test_scenario_2_edge_round_2_debate import (
    _async_return,
    _build_request_minimal_2_turns,
    _factory_round1_diverged_round2_unconverged,
    test_round_2_convergence_or_unconverged_flag,
)
from tests.agentic_evals.sales_agent.grader.conftest import _build_obs_context_stub

pytestmark = pytest.mark.no_eval


# ════════════════════════════════════════════════════════════════════════
# Tests
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_unconverged_r2_falls_back_to_r1_weighted_avg(
    monkeypatch: pytest.MonkeyPatch,
    mock_judge_factory: Any,
    grader_session: Any,
) -> None:
    """R2 variance >= 0.10 → final_score = round_1_weighted_avg (D4 cement)."""
    monkeypatch.setattr(
        me,
        "get_judge",
        _factory_round1_diverged_round2_unconverged(mock_judge_factory),
    )
    monkeypatch.setattr(me, "_read_rubric_md", lambda rubric_id: "")
    monkeypatch.setattr(me, "_get_rubric_version", lambda rubric_id: 1)

    with (
        patch.object(me, "cache_lookup", new=_async_return(None)),
        patch.object(me, "cache_persist", new=_async_return(None)),
        patch.object(me, "_persist_grade", new=_async_return(None)),
    ):
        request = _build_request_minimal_2_turns()
        obs = _build_obs_context_stub(simulation_id=request.simulation_id)
        scores = await me.grade_transcript_maj_eval(
            request,
            session=grader_session,
            obs_context=obs,
        )

    for score in scores:
        assert score.unconverged is True, "R2 variance >= 0.10 must mark unconverged=True"
        assert score.debate_triggered is True
        # Critical D4 assertion: final_score = R1 weighted avg
        assert score.final_score == pytest.approx(score.round_1_score, abs=0.001)


@pytest.mark.asyncio
async def test_unconverged_logs_structlog_warning(
    monkeypatch: pytest.MonkeyPatch,
    mock_judge_factory: Any,
    grader_session: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Unconverged path emits ``structlog.warning`` event ``maj_eval_unconverged``."""
    monkeypatch.setattr(
        me,
        "get_judge",
        _factory_round1_diverged_round2_unconverged(mock_judge_factory),
    )
    monkeypatch.setattr(me, "_read_rubric_md", lambda rubric_id: "")
    monkeypatch.setattr(me, "_get_rubric_version", lambda rubric_id: 1)

    # Spy on the maj_eval logger.
    warning_calls: list[dict[str, Any]] = []
    original_warning = me.logger.warning

    def _spy_warning(event: str, **kwargs: Any) -> None:
        warning_calls.append({"event": event, **kwargs})
        original_warning(event, **kwargs)

    monkeypatch.setattr(me.logger, "warning", _spy_warning)

    with (
        patch.object(me, "cache_lookup", new=_async_return(None)),
        patch.object(me, "cache_persist", new=_async_return(None)),
        patch.object(me, "_persist_grade", new=_async_return(None)),
    ):
        request = _build_request_minimal_2_turns()
        obs = _build_obs_context_stub(simulation_id=request.simulation_id)
        await me.grade_transcript_maj_eval(
            request,
            session=grader_session,
            obs_context=obs,
        )

    # Find the unconverged warning event
    unconverged_warnings = [w for w in warning_calls if w.get("event") == "maj_eval_unconverged"]
    assert len(unconverged_warnings) >= 1, (
        f"Expected at least 1 'maj_eval_unconverged' warning; got events: {[w.get('event') for w in warning_calls]}"
    )
    # Each warning should include the simulation_id + variance_r2 + fallback fields
    sample = unconverged_warnings[0]
    assert "simulation_id" in sample
    assert "variance_r2" in sample
    assert sample.get("fallback") == "round_1_weighted_avg"


@pytest.mark.asyncio
async def test_unconverged_does_not_raise_or_block(
    monkeypatch: pytest.MonkeyPatch,
    mock_judge_factory: Any,
    grader_session: Any,
) -> None:
    """DQ8 cement — unconverged path NEVER raises; returns valid MajEvalScore."""
    monkeypatch.setattr(
        me,
        "get_judge",
        _factory_round1_diverged_round2_unconverged(mock_judge_factory),
    )
    monkeypatch.setattr(me, "_read_rubric_md", lambda rubric_id: "")
    monkeypatch.setattr(me, "_get_rubric_version", lambda rubric_id: 1)

    with (
        patch.object(me, "cache_lookup", new=_async_return(None)),
        patch.object(me, "cache_persist", new=_async_return(None)),
        patch.object(me, "_persist_grade", new=_async_return(None)),
    ):
        request = _build_request_minimal_2_turns()
        obs = _build_obs_context_stub(simulation_id=request.simulation_id)

        # Should NOT raise — graceful degradation Rule 2
        try:
            scores = await me.grade_transcript_maj_eval(
                request,
                session=grader_session,
                obs_context=obs,
            )
        except Exception as exc:  # noqa: BLE001 — DQ8 verification
            pytest.fail(f"Unconverged path raised {type(exc).__name__}: {exc} — DQ8 violated")

    assert len(scores) == 2
    for score in scores:
        assert score.unconverged is True
        # final_score must be a valid float in [0, 1] even on unconverged.
        assert 0.0 <= score.final_score <= 1.0
