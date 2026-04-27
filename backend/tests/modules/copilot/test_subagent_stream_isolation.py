"""Subagent stream isolation — orchestrator no debe leak-ear sub-agente events.

Regression contra la duplicación reportada en conversación
``795cdfbb-c5a5-45eb-9384-792560fe2f8d``: el ``audit_inspector`` corría dentro
del ``task`` tool, sus tokens entraban al ``text_block`` del user, y su
``AIMessage`` final se appendeaba a ``acc.messages`` además del ToolMessage
que ``deepagents`` ya emite. Resultado: 2 AIMessages persistidos + texto
duplicado en pantalla.

Estos tests bloquean que vuelva a pasar para CUALQUIER subagente registrado
(``audit_inspector``, ``url_analyzer``, ``data_query``, futuros).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from src.modules.copilot.application.orchestrator.chat import CopilotOrchestrator


def _make_orchestrator() -> CopilotOrchestrator:
    """Orchestrator mockado — copia mínima de test_streaming_integration."""
    mock_db = MagicMock()
    mock_conv = MagicMock()
    mock_conv.title = None
    mock_conv.messages = []

    with patch(
        "src.modules.copilot.application.orchestrator.chat.ConversationRepository",
    ) as mock_cls:
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_conv
        mock_repo.create.return_value = mock_conv
        mock_cls.return_value = mock_repo
        orch = CopilotOrchestrator(mock_db)

    orch.conv_repo = mock_repo
    return orch


# Namespaces representativos de un compiled subgraph (deepagents task tool
# spawn). Real-world ejemplo: ``tools:abc-123|task:audit_inspector|model:xyz-456``.
SUBAGENT_CHECKPOINT_NS = "tools:abc-123|task:audit_inspector|model:xyz-456"


@pytest.fixture()
def orch() -> CopilotOrchestrator:
    return _make_orchestrator()


class TestSubagentChatModelEnd:
    """``on_chat_model_end`` events de subagente NO se appendean a messages.

    Caso de uso: el sub-agente ``audit_inspector`` produce su reporte final
    y dispara ``on_chat_model_end``. Sin este filter, ese AIMessage entra a
    ``acc.messages`` y termina persistido al lado del AIMessage final del
    parent → user ve el reporte 2 veces, paga 2x output tokens.
    """

    def test_subagent_aimessage_not_appended(self, orch: CopilotOrchestrator) -> None:
        ai = AIMessage(content="reporte sub-agente: 3 hallazgos…")
        event = {
            "event": "on_chat_model_end",
            "data": {"output": ai},
            "metadata": {"langgraph_checkpoint_ns": SUBAGENT_CHECKPOINT_NS},
        }
        accumulated: list = []

        sse, text = orch._process_stream_event(event, accumulated, {})

        assert sse is None
        assert text is None
        assert accumulated == []

    def test_root_aimessage_still_appended(self, orch: CopilotOrchestrator) -> None:
        """Sanity check: root events siguen capturándose normalmente."""
        ai = AIMessage(content="respuesta final del parent agent")
        event = {
            "event": "on_chat_model_end",
            "data": {"output": ai},
            "metadata": {"langgraph_checkpoint_ns": ""},
        }
        accumulated: list = []

        orch._process_stream_event(event, accumulated, {})

        assert len(accumulated) == 1
        assert accumulated[0] is ai

    def test_subagent_event_via_langgraph_path_also_dropped(self, orch: CopilotOrchestrator) -> None:
        """Cuando ``langgraph_checkpoint_ns`` falta pero ``langgraph_path``
        revela el ``task`` en el camino, también drop. Defensa frente al
        issue #6330 de langgraph (metadata propagation incompleta)."""
        ai = AIMessage(content="reporte vía path detection")
        event = {
            "event": "on_chat_model_end",
            "data": {"output": ai},
            "metadata": {
                "langgraph_path": ("__pregel_pull", "task", "model"),
            },
        }
        accumulated: list = []

        orch._process_stream_event(event, accumulated, {})

        assert accumulated == []


class TestSubagentChatModelStream:
    """Tokens streaming del subagente NO entran al ``text_block`` del user."""

    def test_subagent_tokens_dropped(self, orch: CopilotOrchestrator) -> None:
        chunk = MagicMock()
        chunk.content = "token interno del sub-agente "
        event = {
            "event": "on_chat_model_stream",
            "data": {"chunk": chunk},
            "metadata": {"langgraph_checkpoint_ns": SUBAGENT_CHECKPOINT_NS},
        }

        sse, text = orch._process_stream_event(event, [], {})

        assert sse is None
        assert text is None  # NO emit a block_delta

    def test_root_tokens_still_emitted(self, orch: CopilotOrchestrator) -> None:
        """Sanity check: tokens del parent agent se emiten normal."""
        chunk = MagicMock()
        chunk.content = "Hola, "
        event = {
            "event": "on_chat_model_stream",
            "data": {"chunk": chunk},
            "metadata": {"langgraph_checkpoint_ns": ""},
        }

        _sse, text = orch._process_stream_event(event, [], {})

        assert text == "Hola, "


class TestEndToEndSubagentTurn:
    """Replay simulado de un turn que invoca ``task`` — assert message shape final.

    Sequence (simplificada):
      1. Parent emite AIMessage con tool_calls=[task, get_module_datax8]
      2. ``get_module_data`` returns x8 → ToolMessages
      3. Sub-agente corre dentro del ``task`` tool:
         - on_chat_model_stream (tokens del sub-agente) — DEBE drop
         - on_chat_model_end (AIMessage del sub-agente) — DEBE drop
      4. ``task`` on_tool_end con ``Command(update={messages: [ToolMessage]})``
         — DEBE appendear ToolMessage al accumulator
      5. Parent corre 2do model call post-tool:
         - on_chat_model_end con AIMessage final — DEBE appendear

    Expected acc.messages: [
        AIMessage(parent, tool_calls),
        ToolMessagex8 (get_module_data),
        ToolMessage(task) ← NUEVO: pre-fix se perdía silencioso
        AIMessage(parent_final),
    ]
    Total: 11 mensajes. NO 12 (sin AIMessage del subagente colado).
    """

    def test_full_turn_no_duplicate_aimessages(self, orch: CopilotOrchestrator) -> None:
        from langgraph.types import Command

        accumulated: list = []
        last_tool_call_ids: dict[str, str] = {}

        # 1. Parent AIMessage con tool_calls
        parent_initial = AIMessage(
            content="Voy a revisar tu Brand Studio…",
            tool_calls=[
                {"id": "task:0", "name": "task", "args": {}},
                *[{"id": f"gmd:{i}", "name": "get_module_data", "args": {}} for i in range(8)],
            ],
        )
        orch._process_stream_event(
            {
                "event": "on_chat_model_end",
                "data": {"output": parent_initial},
                "metadata": {"langgraph_checkpoint_ns": ""},
            },
            accumulated,
            last_tool_call_ids,
        )

        # 2. 8x get_module_data ToolMessages via on_tool_end (str outputs)
        for i in range(8):
            orch._handle_tool_end(
                {
                    "event": "on_tool_end",
                    "name": "get_module_data",
                    "data": {"output": f"data_section_{i}"},
                },
                accumulated,
                last_tool_call_ids,
            )

        # 3. Sub-agente events — DEBEN ser dropped
        sub_chunk = MagicMock()
        sub_chunk.content = "razonamiento interno sub-agente "
        orch._process_stream_event(
            {
                "event": "on_chat_model_stream",
                "data": {"chunk": sub_chunk},
                "metadata": {"langgraph_checkpoint_ns": SUBAGENT_CHECKPOINT_NS},
            },
            accumulated,
            last_tool_call_ids,
        )
        sub_final = AIMessage(content="reporte sub-agente: 3 hallazgos…")
        orch._process_stream_event(
            {
                "event": "on_chat_model_end",
                "data": {"output": sub_final},
                "metadata": {"langgraph_checkpoint_ns": SUBAGENT_CHECKPOINT_NS},
            },
            accumulated,
            last_tool_call_ids,
        )

        # 4. task on_tool_end con Command — debe extraer ToolMessage
        cmd = Command(
            update={
                "messages": [
                    ToolMessage(
                        content="reporte sub-agente: 3 hallazgos…",
                        tool_call_id="task:0",
                        name="task",
                    ),
                ],
            },
        )
        orch._handle_tool_end(
            {"event": "on_tool_end", "name": "task", "data": {"output": cmd}},
            accumulated,
            last_tool_call_ids,
        )

        # 5. Parent post-tool AIMessage final
        parent_final = AIMessage(
            content="Aquí los puntos de mejora basados en el reporte.",
        )
        orch._process_stream_event(
            {
                "event": "on_chat_model_end",
                "data": {"output": parent_final},
                "metadata": {"langgraph_checkpoint_ns": ""},
            },
            accumulated,
            last_tool_call_ids,
        )

        # Assertions
        assert len(accumulated) == 11, (
            f"Expected 11 mensajes (parent_initial + 8 ToolMessage + ToolMessage(task) + parent_final), "
            f"got {len(accumulated)}: {[type(m).__name__ for m in accumulated]}"
        )

        ai_messages = [m for m in accumulated if isinstance(m, AIMessage)]
        tool_messages = [m for m in accumulated if isinstance(m, ToolMessage)]

        assert len(ai_messages) == 2, "Parent inicial + parent final. NUNCA AIMessage del sub-agente."
        assert ai_messages[0] is parent_initial
        assert ai_messages[1] is parent_final

        # Sub-agente content NO aparece como AIMessage standalone.
        for m in ai_messages:
            assert "reporte sub-agente" not in (m.content or ""), (
                "Reporte del sub-agente nunca debe ser AIMessage del parent — solo ToolMessage."
            )

        # Tool messages: 8 get_module_data + 1 task = 9
        task_tool_msgs = [m for m in tool_messages if m.name == "task"]
        assert len(task_tool_msgs) == 1, (
            "task tool debe persistirse como ToolMessage exactamente una vez (extraído del Command de deepagents)."
        )
        assert task_tool_msgs[0].tool_call_id == "task:0"
        assert "reporte sub-agente" in task_tool_msgs[0].content

        gmd_tool_msgs = [m for m in tool_messages if m.name == "get_module_data"]
        assert len(gmd_tool_msgs) == 8


class TestSubagentCoverageInvariant:
    """Lista de subagentes registrados — fuerza que cualquier subagente nuevo
    aparezca aquí. Si agrego ``foo_inspector`` a ``subagents/__init__.py`` y
    no lo agrego acá, este test pasa pero el architecture fitness en
    ``tests/architecture/test_subagent_isolation_invariants.py`` falla.

    El propósito de este test es documentar la lista expected — el otro
    test es el ratchet real.
    """

    REGISTERED = ("audit_inspector", "url_analyzer", "data_query")

    def test_registered_list_matches_subagents_module(self) -> None:
        from src.modules.copilot.application.orchestrator.subagents import (
            AUDIT_INSPECTOR_SUBAGENT,
            DATA_QUERY_SUBAGENT,
            URL_ANALYZER_SUBAGENT,
        )

        actual_names = {
            AUDIT_INSPECTOR_SUBAGENT["name"],
            URL_ANALYZER_SUBAGENT["name"],
            DATA_QUERY_SUBAGENT["name"],
        }
        assert actual_names == set(self.REGISTERED), (
            "Subagent registrado en subagents/__init__.py no está en la lista de "
            "REGISTERED de este test. Agregar (o eliminar si fue removido) y "
            "asegurar que tiene cobertura de aislamiento."
        )
