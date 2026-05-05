"""Integration tests — sales_agent specialists per-role multi-provider routing (S4).

These tests verify that the SSoT mapping ``SPECIALIST_TO_ROLE`` plus
``settings.get_provider_for_role`` resolve to the correct provider when
``AI_PROVIDER_<ROLE>`` env vars override defaults. Post PI-12 S1
sales-agent-litellm-canonicalization T-7 + T-4: every runtime LLM call
goes through ``LiteLLMService``; per-provider adapter classes (KimiService,
DeepSeekService, …) are deleted. Mocks target the abstract ``LLMFactory``
seam — providers are identified by their ``AIProvider`` enum + ``ModelRole``
mapping, not by class identity.

The tests do NOT make real LLM calls. They:

1. Patch ``LLMFactory`` to capture the ``model_type`` kwarg passed by
   each specialist.
2. Verify that ``settings.get_provider_for_role`` honours per-role
   overrides + global fallback.
3. Verify reasoning-budget reserve still applies when a reasoning spec
   handles REASONING — the kwargs normalizer adds reserve transparently.
   (Per-provider clamps + thinking-disabled directives are covered
   end-to-end in ``tests/shared/infrastructure/llm/test_litellm_kimi_clamp.py``
   via the LiteLLMService canonical path.)
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


class TestReasoningBudgetReserveForReasoningSpec:
    """Reasoning-model spec MUST inflate max_output_tokens via normalizer.

    Sales_agent qualifier/product_expert route to REASONING. When the
    active spec is reasoning-capable (e.g. DeepSeek-V4 reasoning, OpenAI
    o-series), the kwargs normalizer adds the per-spec reserve so the
    visible answer never starves. The reserve mechanism is provider-
    agnostic — covered centrally in ``providers/_kwargs.py``.

    Pre-T-7: the reasoning-spec instance was imported from
    ``providers.deepseek.DEEPSEEK_NATIVE_SPEC``. T-4 deletes that adapter,
    so the test now constructs an equivalent ``ChatModelSpec`` inline
    (same shape as the deepseek spec: ``is_reasoning_model=True``,
    ``reasoning_token_reserve=4000``). The ``_kwargs.py`` contract is
    what we are protecting; the spec instance is just a fixture.
    """

    @staticmethod
    def _reasoning_spec():
        from langchain_openai import ChatOpenAI

        from src.shared.infrastructure.llm.providers._chat_model_resolver import (
            ChatModelSpec,
            build_chat_openai,
        )

        return ChatModelSpec(
            chat_class=ChatOpenAI,
            builder=build_chat_openai,
            is_reasoning_model=True,
            reasoning_token_reserve=4000,
        )

    def test_normalizer_inflates_max_tokens_for_reasoning_spec(self) -> None:
        from src.shared.infrastructure.llm.providers._kwargs import (
            normalize_openai_protocol_kwargs,
        )

        spec = self._reasoning_spec()
        kwargs = {"max_output_tokens": 700}
        out = normalize_openai_protocol_kwargs(kwargs, spec=spec)
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
