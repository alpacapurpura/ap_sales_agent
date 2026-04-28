"""S10 — SalesAgentJudge contract tests.

# [SALES-AGENT-QUALITY-S10] -> docs/domains/sales-agent/redesign-2026-04/phases/S10-quality-eval-loop.md

Mirror del test_copilot_judge contract con extensions específicas:

* PII sanitization en el prompt del judge (las 3 entradas free-text pasan
  por sanitize_payload antes de inyectarse al LLM).
* Stub default + RUN_LLM_JUDGE=1 opt-in (cost guard).
* Scale 1-5 + threshold 3.5 (alineado con copilot F9).
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from langchain_core.messages import AIMessage

from src.modules.sales_agent.application.quality.judge import (
    CANONICAL_DIMENSIONS,
    DEFAULT_THRESHOLD,
    SalesAgentJudge,
)


class _StubLLM:
    """Captures the last invocation + returns a configurable response."""

    def __init__(self, payload: dict[str, Any] | str, *, response_id: str = "resp_sales"):
        self.payload = payload
        self.response_id = response_id
        self.last_messages = None

    def invoke(self, messages):
        self.last_messages = messages
        content = self.payload if isinstance(self.payload, str) else json.dumps(self.payload)
        return AIMessage(content=content, response_metadata={"id": self.response_id})


def _good_payload(score: float = 4.0) -> dict[str, dict[str, Any]]:
    return {
        "brand_voice_fidelity": {"score": score, "reason": "voz consistente"},
        "channel_format_correctness": {"score": score, "reason": "formato OK"},
        "commercial_effectiveness": {"score": score, "reason": "avanza funnel"},
        "pii_safety": {"score": score, "reason": "limpio"},
        "tone_locale_fitness": {"score": score, "reason": "neutro LATAM"},
    }


# ── Schema invariants ────────────────────────────────────────────────────


def test_canonical_dimensions_alphabetical_and_complete():
    """Bias mitigation: dims alfabéticas + cobertura de las 5 esperadas."""
    assert tuple(sorted(CANONICAL_DIMENSIONS)) == CANONICAL_DIMENSIONS
    assert set(CANONICAL_DIMENSIONS) == {
        "brand_voice_fidelity",
        "channel_format_correctness",
        "commercial_effectiveness",
        "pii_safety",
        "tone_locale_fitness",
    }


def test_default_threshold_is_3_5_to_align_with_copilot_f9():
    """Threshold 3.5/5 (70%) — mismo que CopilotJudge para dashboard cross-agent."""
    assert DEFAULT_THRESHOLD == 3.5


# ── Happy path ───────────────────────────────────────────────────────────


def test_evaluate_returns_passing_result_above_threshold():
    llm = _StubLLM(_good_payload(score=4.5))
    judge = SalesAgentJudge(llm=llm)
    result = judge.evaluate(
        user_input="me interesa el programa",
        assistant_output="¡Genial! Te paso el link para reservar 15 min.",
        brand_voice="Marca: Visionarias. Voz cálida y profesional.",
        channel="whatsapp",
        stage="discovery",
    )
    assert result.passes_threshold is True
    assert result.avg_score == pytest.approx(4.5, abs=0.01)
    assert len(result.dimensions) == 5
    assert {d.name for d in result.dimensions} == set(CANONICAL_DIMENSIONS)
    assert result.response_id == "resp_sales"


def test_evaluate_returns_failing_result_below_threshold():
    llm = _StubLLM(_good_payload(score=2.0))
    judge = SalesAgentJudge(llm=llm)
    result = judge.evaluate(user_input="hola", assistant_output="hola")
    assert result.passes_threshold is False
    assert result.avg_score == pytest.approx(2.0, abs=0.01)


# ── Error handling — fail-soft ───────────────────────────────────────────


def test_evaluate_handles_invalid_json_gracefully():
    llm = _StubLLM("no json — solo texto")
    judge = SalesAgentJudge(llm=llm)
    result = judge.evaluate(user_input="x", assistant_output="y")
    assert result.passes_threshold is False
    assert result.avg_score == 0.0
    assert result.metadata.get("error") in {"no_json_in_response", "invalid_json"}


def test_evaluate_handles_missing_dimension():
    bad = {"brand_voice_fidelity": {"score": 5, "reason": "ok"}}  # falta 4
    llm = _StubLLM(bad)
    judge = SalesAgentJudge(llm=llm)
    result = judge.evaluate(user_input="x", assistant_output="y")
    assert result.passes_threshold is False
    assert "missing_dimension" in result.metadata.get("error", "")


def test_evaluate_handles_invalid_score_range():
    bad = _good_payload()
    bad["pii_safety"]["score"] = 99
    llm = _StubLLM(bad)
    judge = SalesAgentJudge(llm=llm)
    result = judge.evaluate(user_input="x", assistant_output="y")
    assert result.passes_threshold is False
    assert "invalid_score" in result.metadata.get("error", "")


def test_evaluate_handles_llm_exception():
    class _BoomLLM:
        def invoke(self, _messages):
            msg = "boom"
            raise RuntimeError(msg)

    judge = SalesAgentJudge(llm=_BoomLLM())
    result = judge.evaluate(user_input="x", assistant_output="y")
    assert result.passes_threshold is False
    assert result.metadata.get("error") == "llm_invoke_failed"


# ── Truncation + brand voice / channel context ───────────────────────────


def test_evaluate_truncates_long_inputs():
    llm = _StubLLM(_good_payload())
    judge = SalesAgentJudge(llm=llm)
    huge = "x" * 50_000
    judge.evaluate(user_input=huge, assistant_output=huge)
    payload = llm.last_messages[1].content
    assert "[truncated]" in payload


def test_evaluate_handles_missing_brand_voice_with_neutral_directive():
    llm = _StubLLM(_good_payload())
    judge = SalesAgentJudge(llm=llm)
    judge.evaluate(user_input="x", assistant_output="y", brand_voice=None)
    payload = llm.last_messages[1].content
    assert "no disponible" in payload


def test_evaluate_passes_channel_and_stage_to_judge_prompt():
    llm = _StubLLM(_good_payload())
    judge = SalesAgentJudge(llm=llm)
    judge.evaluate(
        user_input="hola",
        assistant_output="hola",
        channel="telegram",
        stage="closing",
    )
    payload = llm.last_messages[1].content
    assert "CHANNEL: telegram" in payload
    assert "STAGE: closing" in payload


# ── Ctor validation ──────────────────────────────────────────────────────


def test_invalid_threshold_raises():
    with pytest.raises(ValueError, match="threshold"):
        SalesAgentJudge(threshold=10.0)


# ── Prompt invariants ────────────────────────────────────────────────────


def test_system_prompt_lists_5_dimensions_in_alphabetical_order():
    """System prompt — dims alfabéticas para mitigar position bias."""
    from src.modules.sales_agent.application.quality.judge import (
        build_system_prompt,
    )

    prompt = build_system_prompt(CANONICAL_DIMENSIONS)
    pos_brand = prompt.index("brand_voice_fidelity")
    pos_chan = prompt.index("channel_format_correctness")
    pos_comm = prompt.index("commercial_effectiveness")
    pos_pii = prompt.index("pii_safety")
    pos_tone = prompt.index("tone_locale_fitness")
    assert pos_brand < pos_chan < pos_comm < pos_pii < pos_tone


def test_system_prompt_does_not_voseo_tutela_aliasing():
    """El propio prompt del juez instruye español neutro en su razón."""
    from src.modules.sales_agent.application.quality.judge import (
        build_system_prompt,
    )

    prompt = build_system_prompt(CANONICAL_DIMENSIONS)
    # El prompt instruye "español neutro LatAm" en su salida.
    assert "neutro" in prompt.lower()


# ── PII sanitization en el judge prompt (NEW S10) ─────────────────────────


def test_evaluate_sanitizes_pii_email_before_sending_to_judge():
    """user_input / assistant_output con PII NO llegan crudos al judge LLM.

    Compliance LATAM: el judge recibe textos sanitizados — un email
    ``juan@example.com`` debe aparecer enmascarado, NO en claro.
    """
    llm = _StubLLM(_good_payload())
    judge = SalesAgentJudge(llm=llm)
    judge.evaluate(
        user_input="mi email es juan.perez@example.com",
        assistant_output="Te escribo a juan.perez@example.com en un rato",
    )
    payload = llm.last_messages[1].content
    assert "juan.perez@example.com" not in payload, "El email del lead llegó crudo al judge prompt — viola PII safety."


def test_evaluate_sanitizes_pii_phone_before_sending_to_judge():
    llm = _StubLLM(_good_payload())
    judge = SalesAgentJudge(llm=llm)
    judge.evaluate(
        user_input="mi telefono es +51 999 888 777",
        assistant_output="Te llamo al +51 999 888 777",
    )
    payload = llm.last_messages[1].content
    assert "999 888 777" not in payload, "El phone del lead llegó crudo al judge prompt — viola PII safety."


def test_evaluate_sanitizes_pii_in_brand_voice_block():
    """brand_voice puede contener ejemplos con PII de instructor — sanitizar."""
    llm = _StubLLM(_good_payload())
    judge = SalesAgentJudge(llm=llm)
    judge.evaluate(
        user_input="hola",
        assistant_output="hola",
        brand_voice="Voz cálida. Contacto: maria@empresa.test",
    )
    payload = llm.last_messages[1].content
    assert "maria@empresa.test" not in payload
