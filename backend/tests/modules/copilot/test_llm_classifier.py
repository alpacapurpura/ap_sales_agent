"""Tests for ``LLMClassifier`` — F8 fallback when rule classifier defers.

The LLM classifier is consulted *only* when the rule classifier returns
``None`` (no regex match). It calls ``ModelRole.NANO`` with a structured-output
prompt and returns a ``RoutingDecision`` only when confidence ≥ threshold —
otherwise returns ``None`` so the chain falls through to ``policy.default_role``.

# [COPILOT-LLM-CLASSIFIER-F8] -> docs/domains/copilot/redesign-2026-04/phases/F8-routing-cost-optim.md
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from langchain_core.messages import AIMessage

from luana_core_copilot.application.router.classifiers.llm_classifier import (
    LLMClassifier,
)
from luana_core_copilot.application.router.model_router import RoutingRequest
from luana_core_platform.core.enums import ModelRole
from luana_core_copilot.domain.routing_policy import (
    DEFAULT_ROUTING_POLICY,
    ClassifierType,
)


@dataclass
class _StubLLM:
    """Minimal stub matching ``langchain_core`` chat-model invoke contract."""

    response_content: str

    def invoke(self, _messages: list) -> AIMessage:
        return AIMessage(content=self.response_content)


def _request(msg: str = "diseñame una landing para ofertón abril") -> RoutingRequest:
    return RoutingRequest(user_msg=msg, route="/offer-studio", mode="chat")


class TestLLMClassifierReturnsDecision:
    def test_returns_reasoning_decision_when_high_confidence(self) -> None:
        llm = _StubLLM(
            response_content='{"role": "reasoning", "confidence": 0.92, "reason": "needs_step_by_step_reasoning"}',
        )
        classifier = LLMClassifier(DEFAULT_ROUTING_POLICY, llm=llm)

        decision = classifier.classify(_request())

        assert decision is not None
        assert decision.role == ModelRole.REASONING
        assert decision.classifier_used == ClassifierType.LLM
        assert decision.confidence == 0.92
        assert decision.reason == "needs_step_by_step_reasoning"
        assert decision.fallback_role == ModelRole.FAST

    def test_returns_heavy_decision(self) -> None:
        llm = _StubLLM(
            response_content='{"role": "agent", "confidence": 0.81, "reason": "complex_audit"}',
        )
        classifier = LLMClassifier(DEFAULT_ROUTING_POLICY, llm=llm)

        decision = classifier.classify(_request())

        assert decision is not None
        assert decision.role == ModelRole.AGENT

    def test_returns_nano_decision(self) -> None:
        llm = _StubLLM(
            response_content='{"role": "nano", "confidence": 0.78, "reason": "trivial_ack"}',
        )
        classifier = LLMClassifier(DEFAULT_ROUTING_POLICY, llm=llm)

        decision = classifier.classify(_request("ok gracias"))

        assert decision is not None
        assert decision.role == ModelRole.NANO

    def test_accepts_fenced_json_response(self) -> None:
        """LLM may wrap output in ```json fences — parser must tolerate."""
        llm = _StubLLM(
            response_content='```json\n{"role": "fast", "confidence": 0.85, "reason": "default_chat"}\n```',
        )
        classifier = LLMClassifier(DEFAULT_ROUTING_POLICY, llm=llm)

        decision = classifier.classify(_request())

        assert decision is not None
        assert decision.role == ModelRole.FAST


class TestLLMClassifierReturnsNone:
    def test_returns_none_when_confidence_below_threshold(self) -> None:
        llm = _StubLLM(
            response_content='{"role": "reasoning", "confidence": 0.40, "reason": "low_signal"}',
        )
        classifier = LLMClassifier(DEFAULT_ROUTING_POLICY, llm=llm, threshold=0.7)

        assert classifier.classify(_request()) is None

    def test_returns_none_when_threshold_higher(self) -> None:
        llm = _StubLLM(
            response_content='{"role": "reasoning", "confidence": 0.65, "reason": "ok"}',
        )
        classifier = LLMClassifier(DEFAULT_ROUTING_POLICY, llm=llm, threshold=0.7)

        assert classifier.classify(_request()) is None

    def test_returns_none_on_unknown_tier_value(self) -> None:
        llm = _StubLLM(
            response_content='{"tier": "ultra", "confidence": 0.95, "reason": "made_up_tier"}',
        )
        classifier = LLMClassifier(DEFAULT_ROUTING_POLICY, llm=llm)

        assert classifier.classify(_request()) is None

    def test_returns_none_on_malformed_json(self) -> None:
        llm = _StubLLM(response_content="not json at all, just prose")
        classifier = LLMClassifier(DEFAULT_ROUTING_POLICY, llm=llm)

        assert classifier.classify(_request()) is None

    def test_returns_none_on_llm_exception(self) -> None:
        class BoomLLM:
            def invoke(self, _messages: list) -> AIMessage:
                msg = "OpenAI 503"
                raise RuntimeError(msg)

        classifier = LLMClassifier(DEFAULT_ROUTING_POLICY, llm=BoomLLM())

        assert classifier.classify(_request()) is None

    def test_returns_none_on_missing_confidence_field(self) -> None:
        llm = _StubLLM(response_content='{"role": "reasoning", "reason": "no_conf"}')
        classifier = LLMClassifier(DEFAULT_ROUTING_POLICY, llm=llm)

        assert classifier.classify(_request()) is None


class TestLLMClassifierDefaultsAndContract:
    def test_default_threshold_is_seven_tenths(self) -> None:
        classifier = LLMClassifier(DEFAULT_ROUTING_POLICY, llm=_StubLLM('{"role":"fast","confidence":0.7,"reason":""}'))

        assert classifier.threshold == pytest.approx(0.7)

    def test_threshold_validated_range(self) -> None:
        with pytest.raises(ValueError, match="threshold"):
            LLMClassifier(DEFAULT_ROUTING_POLICY, threshold=1.5, llm=_StubLLM(""))

        with pytest.raises(ValueError, match="threshold"):
            LLMClassifier(DEFAULT_ROUTING_POLICY, threshold=-0.1, llm=_StubLLM(""))

    def test_classify_passes_user_msg_and_route_to_llm(self) -> None:
        captured: list[list] = []

        class CapturingLLM:
            def invoke(self, messages: list) -> AIMessage:
                captured.append(messages)
                return AIMessage(content='{"role":"fast","confidence":0.9,"reason":"ok"}')

        classifier = LLMClassifier(DEFAULT_ROUTING_POLICY, llm=CapturingLLM())
        classifier.classify(_request("revisá mi landing"))

        assert len(captured) == 1
        rendered = "\n".join(getattr(m, "content", "") for m in captured[0])
        assert "revisá mi landing" in rendered
        assert "/offer-studio" in rendered
