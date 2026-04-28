"""Integration tests — sales_agent specialists per-role multi-provider routing (S4).

These tests verify that the SSoT mapping ``SPECIALIST_TO_ROLE`` plus
the existing ``MultiRoleLLMRouter`` resolve to the correct provider
when ``AI_PROVIDER_<ROLE>`` env vars override defaults.

The tests do NOT make real LLM calls. They:

1. Patch ``LLMFactory`` to capture the ``model_type`` kwarg passed by
   each specialist. The router's ``settings.get_provider_for_role(role)``
   logic is exercised via parametrized env-var fixtures.
2. Verify that switching ``AI_PROVIDER_AGENT=kimi`` routes the closer
   call through the Kimi service (post-S4 closer maps to AGENT).
3. Verify reasoning-budget reserve still applies when DeepSeek serves
   REASONING — the kwargs normalizer adds reserve transparently.
"""

from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch

import pytest

from src.core.enums import AIProvider, ModelRole
from src.modules.sales_agent.domain.model_tier import SPECIALIST_TO_ROLE

_TRACE_PATCH = "src.modules.sales_agent.infrastructure.monitoring.tracing.trace_node"


def _noop_trace(name):
    def decorator(func):
        return func

    return decorator


def _base_state(**overrides) -> dict:
    state = {
        "messages": [{"role": "user", "content": "Hola"}],
        "next_node": None,
        "user_id": None,
        "tenant_id": None,
        "session_id": "test-session",
        "current_state": "rapport",
        "detected_intent": "unknown",
        "lead_score": 0,
        "lead_data": {},
        "tenant_config": {},
        "history": [],
        "user_profile": {},
        "session_active": True,
        "active_enrollment": None,
        "active_product": None,
        "last_intent": None,
        "launch_stage": None,
        "agent_identity": "",
        "buying_signals": [],
        "objection_history": [],
        "qualification_answers": {},
        "turn_count": 0,
        "customer_profile_id": None,
        "channel_type": None,
        "close_strategy": None,
        "internal_turn": 0,
        "error": None,
    }
    state.update(overrides)
    return state


class TestSpecialistsRouteViaSSoT:
    """Each specialist must invoke generate_response with the role from SSoT."""

    @patch(_TRACE_PATCH, _noop_trace)
    def test_supervisor_passes_nano_role(self) -> None:
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        with (
            patch.object(nodes_mod, "LLMFactory") as mock_factory,
            patch.object(nodes_mod, "prompt_loader") as mock_prompt,
        ):
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "qualifier"
            mock_factory.get_service.return_value = mock_service
            mock_prompt.render.return_value = "routing"

            nodes_mod.node_sales_supervisor(_base_state())

            kwargs = mock_service.generate_response.call_args.kwargs
            assert kwargs["model_type"] is SPECIALIST_TO_ROLE["supervisor"]
            assert kwargs["model_type"] is ModelRole.NANO

    @patch(_TRACE_PATCH, _noop_trace)
    def test_qualifier_passes_reasoning_role(self) -> None:
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        with patch.object(nodes_mod, "LLMFactory") as mock_factory:
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "Hola"
            mock_factory.get_service.return_value = mock_service

            nodes_mod.node_qualifier(_base_state())

            kwargs = mock_service.generate_response.call_args.kwargs
            assert kwargs["model_type"] is SPECIALIST_TO_ROLE["qualifier"]
            assert kwargs["model_type"] is ModelRole.REASONING

    @patch(_TRACE_PATCH, _noop_trace)
    def test_product_expert_passes_reasoning_role(self) -> None:
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        with patch.object(nodes_mod, "LLMFactory") as mock_factory:
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "info producto"
            mock_factory.get_service.return_value = mock_service

            nodes_mod.node_product_expert(_base_state())

            kwargs = mock_service.generate_response.call_args.kwargs
            assert kwargs["model_type"] is SPECIALIST_TO_ROLE["product_expert"]
            assert kwargs["model_type"] is ModelRole.REASONING

    @patch(_TRACE_PATCH, _noop_trace)
    def test_closer_passes_agent_role(self) -> None:
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        with patch.object(nodes_mod, "LLMFactory") as mock_factory:
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "link de pago"
            mock_factory.get_service.return_value = mock_service

            nodes_mod.node_closer(_base_state())

            kwargs = mock_service.generate_response.call_args.kwargs
            assert kwargs["model_type"] is SPECIALIST_TO_ROLE["closer"]
            assert kwargs["model_type"] is ModelRole.AGENT


class TestSettingsResolvesProviderPerRole:
    """``settings.get_provider_for_role`` must honor AI_PROVIDER_<ROLE> env."""

    @pytest.mark.parametrize(
        ("role", "env_var", "provider"),
        [
            (ModelRole.NANO, "AI_PROVIDER_NANO", AIProvider.OPENAI),
            (ModelRole.REASONING, "AI_PROVIDER_REASONING", AIProvider.DEEPSEEK),
            (ModelRole.AGENT, "AI_PROVIDER_AGENT", AIProvider.KIMI),
            (ModelRole.FAST, "AI_PROVIDER_FAST", AIProvider.OPENAI),
        ],
    )
    def test_role_to_provider_mapping(
        self,
        monkeypatch: pytest.MonkeyPatch,
        role: ModelRole,
        env_var: str,
        provider: AIProvider,
    ) -> None:
        # Patch the typed Settings attribute (env var only triggers re-load
        # at process boot — for runtime tests we override the field
        # directly which is the supported in-process pattern).
        from src.core.config import settings

        monkeypatch.setattr(settings, env_var, provider)
        resolved = settings.get_provider_for_role(role)
        assert resolved is provider

    def test_role_falls_back_to_global_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.core.config import settings

        # Force per-role overrides to None and global to a sentinel.
        monkeypatch.setattr(settings, "AI_PROVIDER_AGENT", None)
        monkeypatch.setattr(settings, "AI_PROVIDER", AIProvider.OPENAI)
        assert settings.get_provider_for_role(ModelRole.AGENT) is AIProvider.OPENAI


class TestKimiKwargsForceThinkingDisabled:
    """Regression — Kimi K2.6 client MUST set extra_body.thinking=disabled.

    Required by Moonshot server: thinking-enabled needs reasoning_content
    round-trip across turns (LangChain doesn't preserve yet → 400).
    Implemented in ``KimiService._get_chat_model`` via model_kwargs.
    Test reproduces the path called when sales_agent closer routes to Kimi.
    """

    def test_kimi_k2_client_has_thinking_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.core.config import settings
        from src.shared.infrastructure.llm.providers.kimi import KimiService

        # Stub get_model so settings.get_model returns a K2-flavoured name.
        monkeypatch.setattr(settings, "AI_MODEL_AGENT", "kimi-k2.6")
        # KIMI_API_KEY may be unset in CI — provide a stub via ctor arg.
        svc = KimiService(api_key="test-stub-kimi-key")
        client = svc._get_chat_model(ModelRole.AGENT)

        extra = client.model_kwargs.get("extra_body") or {}
        thinking = extra.get("thinking")
        assert thinking == {"type": "disabled"}, (
            f"Kimi K2.6 client missing thinking-disabled directive: model_kwargs={client.model_kwargs!r}"
        )

    def test_kimi_k2_client_temperature_clamped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.core.config import settings
        from src.shared.infrastructure.llm.providers.kimi import (
            _K2_REQUIRED_TEMPERATURE,
            KimiService,
        )

        monkeypatch.setattr(settings, "AI_MODEL_AGENT", "kimi-k2.6")
        svc = KimiService(api_key="test-stub-kimi-key")
        # Caller requests 0.4 (closer's pre-S4 temp) — must clamp to 0.6.
        client = svc._get_chat_model(ModelRole.AGENT, temperature=0.4)
        assert client.temperature == _K2_REQUIRED_TEMPERATURE


class TestReasoningBudgetReserveAppliesToDeepSeek:
    """Reasoning-model spec MUST inflate max_output_tokens via normalizer.

    Sales_agent qualifier/product_expert route to REASONING. When env var
    ``AI_PROVIDER_REASONING=deepseek`` activates DeepSeek-V4, the kwargs
    normalizer adds the 4000-token reserve so the visible answer never
    starves. Trap reproduced across DeepSeek-V4 / OpenAI o-series /
    Anthropic extended thinking — covered centrally in ``_kwargs.py``.
    """

    def test_normalizer_inflates_max_tokens_for_reasoning_spec(self) -> None:
        from src.shared.infrastructure.llm.providers._kwargs import (
            normalize_openai_protocol_kwargs,
        )
        from src.shared.infrastructure.llm.providers.deepseek import (
            DEEPSEEK_NATIVE_SPEC,
        )

        kwargs = {"max_output_tokens": 700}
        out = normalize_openai_protocol_kwargs(kwargs, spec=DEEPSEEK_NATIVE_SPEC)
        # 700 visible + 4000 reserve = 4700 wire budget.
        assert out["max_tokens"] == 4700
        assert "max_output_tokens" not in out

    def test_normalizer_passthrough_for_non_reasoning_spec(self) -> None:
        from src.shared.infrastructure.llm.providers._chat_model_resolver import (
            DEFAULT_OPENAI_SPEC,
        )
        from src.shared.infrastructure.llm.providers._kwargs import (
            normalize_openai_protocol_kwargs,
        )

        kwargs = {"max_output_tokens": 700}
        out = normalize_openai_protocol_kwargs(kwargs, spec=DEFAULT_OPENAI_SPEC)
        # No reserve — raw 700 → max_tokens.
        assert out["max_tokens"] == 700
