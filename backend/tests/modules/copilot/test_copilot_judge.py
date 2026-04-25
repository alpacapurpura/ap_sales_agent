"""F9 — CopilotJudge contract.

# [COPILOT-LLM-JUDGE-F9]
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from langchain_core.messages import AIMessage

from src.modules.copilot.application.observability.judge import (
    CANONICAL_DIMENSIONS,
    DEFAULT_THRESHOLD,
    CopilotJudge,
)


class _StubLLM:
    """Captures the last invocation + returns a configurable response."""

    def __init__(self, payload: dict[str, Any] | str, *, response_id: str = "resp_test"):
        self.payload = payload
        self.response_id = response_id
        self.last_messages = None

    def invoke(self, messages):
        self.last_messages = messages
        content = self.payload if isinstance(self.payload, str) else json.dumps(self.payload)
        return AIMessage(content=content, response_metadata={"id": self.response_id})


def _good_payload(score: float = 4.0) -> dict[str, dict[str, Any]]:
    return {
        "accuracy": {"score": score, "reason": "respuesta factual"},
        "brand_coherence": {"score": score, "reason": "voz consistente"},
        "tone": {"score": score, "reason": "neutro LatAm"},
        "utility": {"score": score, "reason": "resuelve intención"},
    }


def test_canonical_dimensions_alphabetical():
    """Bias mitigation: dims must be alphabetised so position is deterministic."""
    assert tuple(sorted(CANONICAL_DIMENSIONS)) == CANONICAL_DIMENSIONS
    assert set(CANONICAL_DIMENSIONS) == {
        "accuracy",
        "brand_coherence",
        "tone",
        "utility",
    }


def test_default_threshold_is_3_5():
    """Threshold = 3.5/5 (70%) per F9 research decision."""
    assert DEFAULT_THRESHOLD == 3.5


def test_evaluate_returns_passing_result_above_threshold():
    llm = _StubLLM(_good_payload(score=4.5))
    judge = CopilotJudge(llm=llm)
    result = judge.evaluate(
        user_input="¿Cuántos leads esta semana?",
        assistant_output="Tienes 12 leads inbound esta semana.",
        brand_summary="Marca: Coraje. Voz cálida y directa.",
    )
    assert result.passes_threshold is True
    assert result.avg_score == pytest.approx(4.5, abs=0.01)
    assert len(result.dimensions) == 4
    assert {d.name for d in result.dimensions} == set(CANONICAL_DIMENSIONS)
    assert result.response_id == "resp_test"


def test_evaluate_returns_failing_result_below_threshold():
    llm = _StubLLM(_good_payload(score=2.0))
    judge = CopilotJudge(llm=llm)
    result = judge.evaluate(
        user_input="hola",
        assistant_output="hola",
        brand_summary=None,
    )
    assert result.passes_threshold is False
    assert result.avg_score == pytest.approx(2.0, abs=0.01)


def test_evaluate_handles_invalid_json_gracefully():
    llm = _StubLLM("no json here, just prose")
    judge = CopilotJudge(llm=llm)
    result = judge.evaluate(user_input="x", assistant_output="y")
    assert result.passes_threshold is False
    assert result.avg_score == 0.0
    assert result.metadata.get("error") in {"no_json_in_response", "invalid_json"}


def test_evaluate_handles_missing_dimension():
    bad = {"accuracy": {"score": 5, "reason": "ok"}}  # missing 3 dims
    llm = _StubLLM(bad)
    judge = CopilotJudge(llm=llm)
    result = judge.evaluate(user_input="x", assistant_output="y")
    assert result.passes_threshold is False
    assert "missing_dimension" in result.metadata.get("error", "")


def test_evaluate_handles_invalid_score_range():
    bad = _good_payload()
    bad["accuracy"]["score"] = 99  # out of range
    llm = _StubLLM(bad)
    judge = CopilotJudge(llm=llm)
    result = judge.evaluate(user_input="x", assistant_output="y")
    assert result.passes_threshold is False
    assert "invalid_score" in result.metadata.get("error", "")


def test_evaluate_handles_llm_exception():
    class _BoomLLM:
        def invoke(self, _messages):
            msg = "boom"
            raise RuntimeError(msg)

    judge = CopilotJudge(llm=_BoomLLM())
    result = judge.evaluate(user_input="x", assistant_output="y")
    assert result.passes_threshold is False
    assert result.metadata.get("error") == "llm_invoke_failed"


def test_evaluate_truncates_long_inputs():
    llm = _StubLLM(_good_payload())
    judge = CopilotJudge(llm=llm)
    huge = "x" * 50_000
    judge.evaluate(user_input=huge, assistant_output=huge)
    payload = llm.last_messages[1].content
    assert "[truncated]" in payload


def test_evaluate_handles_missing_brand_summary_with_neutral_directive():
    llm = _StubLLM(_good_payload())
    judge = CopilotJudge(llm=llm)
    judge.evaluate(user_input="x", assistant_output="y", brand_summary=None)
    payload = llm.last_messages[1].content
    assert "no disponible" in payload


def test_invalid_threshold_raises():
    with pytest.raises(ValueError, match="threshold"):
        CopilotJudge(threshold=10.0)


def test_system_prompt_lists_4_dimensions_in_alphabetical_order():
    """System prompt must list dims alphabetised — position bias mitigation."""
    from src.modules.copilot.application.observability.judge import (
        _SYSTEM_PROMPT_ES,
    )

    pos_accuracy = _SYSTEM_PROMPT_ES.index("accuracy")
    pos_brand = _SYSTEM_PROMPT_ES.index("brand_coherence")
    pos_tone = _SYSTEM_PROMPT_ES.index("tone")
    pos_utility = _SYSTEM_PROMPT_ES.index("utility")
    assert pos_accuracy < pos_brand < pos_tone < pos_utility


def test_system_prompt_in_spanish_neutro():
    """Per .claude/rules/spanish-text.md — judge prompt must NOT use voseo."""
    from src.modules.copilot.application.observability.judge import (
        _SYSTEM_PROMPT_ES,
    )

    voseo_tokens = [
        " vos ",
        " sos ",
        " tenés",
        " querés",
        " podés",
        " sabés",
        " mirá",
        " dejá",
        " seleccioná",
    ]
    for token in voseo_tokens:
        assert token not in _SYSTEM_PROMPT_ES, f"voseo found in judge prompt: {token!r}"
