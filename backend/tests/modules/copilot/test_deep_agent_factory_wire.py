"""Regression: ``build_deep_agent_graph(llm=None)`` must not crash with deepagents 0.5+.

Bug detectado durante TP1 (testing-2026-04 plan), 2026-04-25:

- Síntoma producción: cada turn `/api/v1/copilot/chat` devolvía
  ``event: error / "Ocurrio un error procesando tu mensaje"`` mid-stream.
  HTTP 200 (auth pass), pero el LLM nunca se invocaba.
- Stack trace en docker logs::

    File "deep_agent.py", line 144, in build_deep_agent_graph
      return create_deep_agent(model=llm, ...)
    File "deepagents/_models.py", line 34, in resolve_model
      profile = _get_harness_profile(model)
    File "deepagents/profiles/_harness_profiles.py", line 160
      exact = _HARNESS_PROFILES.get(spec)
    TypeError: unhashable type: 'RunnableBinding'

- Root cause: ``deep_agent.py:136`` hacía ``llm = llm.bind(temperature=0.6)``
  para overridear la temperature default (0.7) del factory. ``.bind()`` devuelve
  ``RunnableBinding`` (Runnable, NO BaseChatModel). ``deepagents 0.5.3``
  endureció ``resolve_model()``: si el arg no pasa
  ``isinstance(BaseChatModel)`` lo trata como string spec y lo busca como
  key de un dict — RunnableBinding es unhashable → TypeError.

- Por qué los tests previos no lo capturaron:
  ``test_deep_agent_harness.py`` siempre llama
  ``build_deep_agent_graph(state, llm=_RecordingFakeLLM(), tools=[])`` —
  el ``llm`` override salta el path de producción
  (``LLMFactory.get_service().get_client(...).bind(...)``) que era el
  que crasheaba.

- Fix arquitectónico: ``BaseLLMService.get_client()`` ahora acepta
  ``temperature: float | None`` kwarg. ``OpenAIService`` lo cachea por
  ``(model_name, temperature)``. ``deep_agent.py`` usa el factory en
  lugar de ``.bind()`` — el resultado es un ``BaseChatModel`` limpio
  (hashable, deepagents-compat).

Estos tests aseguran que el path ``llm=None`` nunca vuelva a romperse.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from src.core.enums import ModelRole
from src.shared.infrastructure.llm.factory import LLMFactory


@pytest.fixture
def base_state():
    """Minimal CopilotState dict para forzar el path llm=None del harness."""
    return {
        "messages": [HumanMessage(content="hola")],
        "user_id": uuid4(),
        "tenant_id": uuid4(),
        "client_context": {"current_route": None},
        "conversation_id": str(uuid4()),
        "pending_ui_actions": [],
        "active_tool_names": [],
        "active_procedure": None,
        "guided_state": None,
        "error": None,
    }


@pytest.fixture(autouse=True)
def _stub_system_prompt(monkeypatch):
    """``build_system_prompt`` toca DB; los tests de factory wire son hermeticos."""
    monkeypatch.setattr(
        "src.modules.copilot.application.orchestrator.deep_agent.build_system_prompt",
        lambda _state: "Eres el Copilot de Nicolify.",
    )


@pytest.fixture(autouse=True)
def _stub_tools(monkeypatch):
    """Skip route-based tool resolution — el bug es del wire LLM, no de tools.

    PI-5 PR-2 added ``channel`` kwarg to ``get_tools_for_context`` for runtime
    Telegram filter (D-PI5-023). Stub accepts **kwargs to stay compatible.
    """
    monkeypatch.setattr(
        "src.modules.copilot.application.orchestrator.deep_agent.get_tools_for_context",
        lambda _ctx, **_kwargs: [],
    )


class TestFactoryTemperatureOverride:
    """``LLMFactory.get_client(temperature=...)`` devuelve BaseChatModel hashable."""

    def test_default_temperature_returns_basechatmodel(self) -> None:
        client = LLMFactory.get_service().get_client(ModelRole.AGENT)
        assert isinstance(client, BaseChatModel), (
            f"get_client() default debe devolver BaseChatModel, got {type(client).__name__}"
        )

    def test_temperature_override_returns_basechatmodel(self) -> None:
        """El override NO debe envolver en RunnableBinding (deepagents 0.5+ rechaza)."""
        client = LLMFactory.get_service().get_client(ModelRole.AGENT, temperature=0.6)
        assert isinstance(client, BaseChatModel), (
            f"get_client(temperature=0.6) debe devolver BaseChatModel, got {type(client).__name__}. "
            "Si ves RunnableBinding aquí, el factory regresó al patrón viejo de .bind()."
        )

    def test_temperature_override_is_applied(self) -> None:
        """La instancia devuelta refleja el temperature pedido.

        Usamos ``ModelRole.REASONING`` (DeepSeek deepseek-reasoner) porque
        ``ModelRole.AGENT`` resuelve a Kimi K2.6 y el adapter clampea
        ``temperature`` al valor exigido por el server (TP4-B4 + TP5-B8) —
        comportamiento correcto pero oculta el wire que este test cuida.
        """
        client = LLMFactory.get_service().get_client(ModelRole.REASONING, temperature=0.6)
        # ChatOpenAI expone temperature como atributo serializable.
        config = client.model_dump()
        assert config.get("temperature") == 0.6, f"Expected temperature=0.6, got {config.get('temperature')}"

    def test_temperature_cache_segregates_instances(self) -> None:
        """Cache key incluye temperature — distintos overrides → distintas instancias.

        Como en ``test_temperature_override_is_applied`` usamos REASONING para
        evitar el clamp Kimi K2.6 — el cache vive en
        ``OpenAICompatibleService._models`` para los tres providers chinos.
        """
        service = LLMFactory.get_service()
        client_a = service.get_client(ModelRole.REASONING, temperature=0.6)
        client_b = service.get_client(ModelRole.REASONING, temperature=0.2)
        client_a2 = service.get_client(ModelRole.REASONING, temperature=0.6)
        assert client_a is not client_b, "Distinta temperature debe dar instancia distinta"
        assert client_a is client_a2, "Misma temperature debe re-usar instancia cacheada"

    def test_kimi_k2_temperature_clamped_for_agent_role(self) -> None:
        """``ModelRole.AGENT`` resuelve Kimi K2.6 y debe clampear cualquier
        temperature ≠ 0.6 al valor exigido por el server (TP4-B4 + TP5-B8).
        Con thinking deshabilitado (B8), K2.6 sólo acepta ``temperature=0.6``;
        sin coerción, el deep-agent factory explota con HTTP 400 ``only 0.6
        is allowed for this model``.
        """
        service = LLMFactory.get_service()
        client = service.get_client(ModelRole.AGENT, temperature=1.0)
        config = client.model_dump()
        assert config.get("temperature") == 0.6, (
            f"Kimi K2.6 (thinking disabled) debe clampear temperature a 0.6; got {config.get('temperature')}"
        )


class TestDeepAgentGraphWithFactoryLLM:
    """``build_deep_agent_graph(llm=None)`` ejerce el factory wire de producción."""

    def test_compiles_without_typeerror(self, base_state) -> None:
        """Repro directo del bug TP1-pre: llm=None → crash en deepagents.resolve_model."""
        from langgraph.graph.state import CompiledStateGraph

        from src.modules.copilot.application.orchestrator.deep_agent import (
            build_deep_agent_graph,
        )

        # Si este call crashea con TypeError: unhashable type: 'RunnableBinding'
        # → la regresión volvió. Fix está en LLMFactory.get_client(temperature=...).
        graph = build_deep_agent_graph(base_state, llm=None, tools=None)
        assert isinstance(graph, CompiledStateGraph)
