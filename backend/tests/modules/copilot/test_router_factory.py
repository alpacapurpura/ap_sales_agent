"""Tests for ``build_default_router`` factory — F8 chain wiring."""

from __future__ import annotations

from langchain_core.messages import AIMessage

from src.modules.copilot.application.router import (
    LLMClassifier,
    ModelRouter,
    RoutingRequest,
    RuleClassifier,
    build_default_router,
)
from src.modules.copilot.domain.model_tier import ModelTier
from src.modules.copilot.domain.routing_policy import (
    DEFAULT_ROUTING_POLICY,
    ClassifierType,
)


class _StubLLM:
    def __init__(self, content: str) -> None:
        self.content = content

    def invoke(self, _messages: list) -> AIMessage:
        return AIMessage(content=self.content)


class TestBuildDefaultRouter:
    def test_chain_has_rule_then_llm_in_order(self) -> None:
        router = build_default_router(llm=_StubLLM('{"tier":"mini","confidence":0.9,"reason":""}'))

        assert isinstance(router, ModelRouter)
        # Access the private tuple — invariant test, intentional
        chain = router._classifiers
        assert len(chain) == 2
        assert isinstance(chain[0], RuleClassifier)
        assert isinstance(chain[1], LLMClassifier)

    def test_chain_skips_llm_when_disabled(self) -> None:
        router = build_default_router(enable_llm_fallback=False)

        chain = router._classifiers
        assert len(chain) == 1
        assert isinstance(chain[0], RuleClassifier)

    def test_rule_match_short_circuits_llm(self) -> None:
        # ``audita`` is in DEFAULT_ROUTING_POLICY at priority 10 → HEAVY.
        # If rule matches, LLM should NOT be invoked. Stub that would raise
        # confirms the chain stopped at rule.
        class ExplodingLLM:
            def invoke(self, _messages: list) -> AIMessage:
                msg = "should not be called when rule matches"
                raise AssertionError(msg)

        router = build_default_router(llm=ExplodingLLM())

        decision = router.select(
            RoutingRequest(user_msg="audita mi marca completa"),
        )

        assert decision.tier == ModelTier.HEAVY
        assert decision.classifier_used == ClassifierType.RULE

    def test_llm_consulted_when_rule_defers(self) -> None:
        router = build_default_router(
            llm=_StubLLM('{"tier":"reasoning","confidence":0.85,"reason":"compare_clean"}'),
        )

        # Message that does NOT match any DEFAULT_ROUTING_POLICY rule.
        decision = router.select(
            RoutingRequest(user_msg="che pongamos esto bien claro mejor pensarlo dos veces"),
        )

        assert decision.classifier_used == ClassifierType.LLM
        assert decision.tier == ModelTier.REASONING

    def test_default_fallback_when_both_defer(self) -> None:
        # LLM returns confidence below threshold → defers → ModelRouter default.
        router = build_default_router(
            llm=_StubLLM('{"tier":"reasoning","confidence":0.20,"reason":"low"}'),
        )

        decision = router.select(
            RoutingRequest(user_msg="che pongamos esto claro mejor pensarlo dos veces"),
        )

        assert decision.classifier_used == ClassifierType.DEFAULT
        assert decision.tier == DEFAULT_ROUTING_POLICY.default_tier

    def test_short_msg_routes_nano_with_tools_available(self) -> None:
        """Short greeting matches NANO rule even when chat overlay exposes registry tools.

        Regression: F8 ``max_tools=0`` guard incorrectly excluded every chat turn
        because chat overlay always wires the full tool registry
        (``available_tool_count`` ~26). Result was the rule never fired and every
        short turn cascaded to LLMClassifier — wasted NANO calls + classifier=llm
        in ``copilot_routing_log`` for trivial greetings (TP1 anomaly A2).
        """

        class ExplodingLLM:
            def invoke(self, _messages: list) -> AIMessage:
                msg = "rule should match before LLM is consulted"
                raise AssertionError(msg)

        router = build_default_router(llm=ExplodingLLM())

        decision = router.select(
            RoutingRequest(user_msg="hola", available_tool_count=26),
        )

        assert decision.classifier_used == ClassifierType.RULE
        assert decision.tier == ModelTier.NANO
        assert decision.reason == "short_msg_no_tools"
