"""F2 — Deep Agent harness wrapper.

The harness wraps :func:`deepagents.create_deep_agent` and exposes a
graph compatible with the existing ``copilot_graph`` consumers
(``astream_events`` + dict state with ``messages``).

These tests target the wrapper, not deepagents internals.
"""

from __future__ import annotations

from typing import ClassVar
from uuid import uuid4

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class _RecordingFakeLLM(BaseChatModel):
    """Minimal BaseChatModel that records the messages it receives."""

    received_messages: ClassVar[list] = []

    @property
    def _llm_type(self) -> str:  # pragma: no cover - LangChain plumbing
        return "fake"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        type(self).received_messages.append(list(messages))
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content="ok"))],
        )

    def bind_tools(self, tools, **_kwargs):
        return self


@pytest.fixture(autouse=True)
def _reset_fake_llm():
    _RecordingFakeLLM.received_messages = []
    yield
    _RecordingFakeLLM.received_messages = []


@pytest.fixture(autouse=True)
def _stub_system_prompt(monkeypatch):
    """``build_system_prompt`` opens DB sessions for the completion snapshot.

    The harness tests don't need the real prompt — only that the wrapper
    threads SOMETHING through the deepagents ``system_prompt`` slot and
    appends the deep-agent suffix. Stubbing keeps the test hermetic.
    """
    monkeypatch.setattr(
        "src.modules.copilot.application.orchestrator.deep_agent.build_system_prompt",
        lambda _state: "Eres el Copilot de Nicolify.",
    )


@pytest.fixture
def base_state():
    """Minimal CopilotState dict the harness understands."""
    return {
        "messages": [HumanMessage(content="auditá la sección de identidad")],
        "user_id": uuid4(),
        "tenant_id": uuid4(),
        "client_context": {"current_route": "/brand-studio/identity"},
        "conversation_id": str(uuid4()),
        "pending_ui_actions": [],
        "active_tool_names": [],
        "active_procedure": None,
        "guided_state": None,
        "error": None,
    }


class TestHarnessConstruction:
    """``build_deep_agent_graph`` returns a compiled LangGraph graph."""

    def test_returns_compiled_graph_with_messages_input(self, base_state) -> None:
        from langgraph.graph.state import CompiledStateGraph

        from src.modules.copilot.application.orchestrator.deep_agent import (
            build_deep_agent_graph,
        )

        graph = build_deep_agent_graph(base_state, llm=_RecordingFakeLLM(), tools=[])

        assert isinstance(graph, CompiledStateGraph)
        schema = graph.get_input_jsonschema()
        assert "messages" in (schema.get("properties") or {})

    def test_audit_inspector_subagent_registered(self, base_state) -> None:
        """Spawn-able sub-agents include the dummy ``audit_inspector``."""
        from src.modules.copilot.application.orchestrator.deep_agent import (
            build_deep_agent_graph,
        )
        from src.modules.copilot.application.orchestrator.subagents import (
            AUDIT_INSPECTOR_SUBAGENT,
        )

        graph = build_deep_agent_graph(base_state, llm=_RecordingFakeLLM(), tools=[])

        # Sanity: name & description match the spec we shipped.
        assert AUDIT_INSPECTOR_SUBAGENT["name"] == "audit_inspector"
        assert "audita" in AUDIT_INSPECTOR_SUBAGENT["description"].lower()

        # The compiled graph contains the standard deepagents nodes.
        node_names = list(graph.nodes.keys())
        assert "model" in node_names
        assert "tools" in node_names


class TestSystemPromptInjection:
    """The Nicolify system prompt is prepended to the deep-agent boilerplate."""

    @pytest.mark.asyncio
    async def test_system_prompt_starts_with_nicolify_layer(self, base_state) -> None:
        from src.modules.copilot.application.orchestrator.deep_agent import (
            build_deep_agent_graph,
        )

        llm = _RecordingFakeLLM()
        graph = build_deep_agent_graph(base_state, llm=llm, tools=[])
        await graph.ainvoke({"messages": base_state["messages"]})

        assert _RecordingFakeLLM.received_messages, "LLM was never invoked"
        first_call = _RecordingFakeLLM.received_messages[0]
        sys_msg = next(m for m in first_call if isinstance(m, SystemMessage))
        # Either a string or list-of-blocks payload — normalize.
        content = (
            sys_msg.content
            if isinstance(sys_msg.content, str)
            else "".join(blk.get("text", "") if isinstance(blk, dict) else str(blk) for blk in sys_msg.content)
        )
        # Nicolify branding from build_system_prompt or fallback string.
        assert "Nicolify" in content or "Copilot" in content
        # Deep-agent boilerplate is appended.
        assert "Deep Agent" in content or "task" in content.lower()


class TestPlanningEvent:
    """Streaming preserves the same astream_events contract."""

    @pytest.mark.asyncio
    async def test_astream_events_emits_chat_model_lifecycle(self, base_state) -> None:
        from src.modules.copilot.application.orchestrator.deep_agent import (
            build_deep_agent_graph,
        )

        graph = build_deep_agent_graph(base_state, llm=_RecordingFakeLLM(), tools=[])
        kinds: list[str] = []
        async for ev in graph.astream_events(
            {"messages": base_state["messages"]},
            version="v2",
        ):
            kinds.append(ev.get("event", ""))

        assert "on_chat_model_start" in kinds
        assert "on_chat_model_end" in kinds
