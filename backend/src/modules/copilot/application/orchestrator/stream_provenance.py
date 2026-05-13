"""Stream event provenance + routing policy for the copilot orchestrator.

LangGraph ``astream_events(version="v2")`` bubble-uppea events de subgraphs
anidados. Cuando el deep agent invoca un sub-agente vía la ``task`` tool
(deepagents), ese sub-agente corre dentro de un compiled graph anidado
y sus events de chat model (stream + end) llegan al loop principal del
orquestador junto con los del parent.

Sin clasificación, ``_process_stream_event`` trataba ambos por igual:
- tokens del sub-agente entraban al ``text_block`` del user (leak visual)
- ``AIMessage`` final del sub-agente se appendeaba a ``acc.messages``
  duplicando lo que ``deepagents`` ya devuelve como ``ToolMessage``
  vía ``Command(update={"messages": [...]})``.

Este módulo provee la clasificación canónica y la matriz de política
que ``_process_stream_event`` consulta. Complementa
:mod:`stream_filters` (que ya filtra LLM internos de tools); juntos
cubren los 3 orígenes de events: parent, subagente, tool interno.

Detección defensiva: ver
https://github.com/langchain-ai/langgraph/issues/6330 — algunos campos
de metadata se pueden perder en upgrades, así que combinamos dos
señales (``langgraph_checkpoint_ns`` con ``|`` separador + ``langgraph_path``
conteniendo ``task``). Una sola señal positiva basta.
"""

from __future__ import annotations

from enum import StrEnum

from luana_core_copilot.application.orchestrator.stream_filters import (
    is_internal_llm_event,
)


class EventOrigin(StrEnum):
    """De dónde proviene un event de ``astream_events``."""

    ROOT = "root"
    SUBAGENT = "subagent"
    INTERNAL_TOOL = "internal_tool"


class StreamPolicy(StrEnum):
    """Qué hacer con un event clasificado."""

    EMIT_TO_USER = "emit"
    CAPTURE_HISTORY = "capture"
    DROP = "drop"


def classify_event(event: dict) -> EventOrigin:
    """Determinar el origen de un event de ``astream_events``.

    Orden de chequeo: tag interno (más específico) → subagente → root
    (default seguro: si no podemos detectar nesting, asumimos root para
    no romper functionality user-facing).
    """
    if is_internal_llm_event(event):
        return EventOrigin.INTERNAL_TOOL
    if _is_subagent_event(event):
        return EventOrigin.SUBAGENT
    return EventOrigin.ROOT


def _is_subagent_event(event: dict) -> bool:
    """``True`` si el event proviene de un compiled graph anidado.

    Señales (cualquiera positiva basta):
    1. ``metadata.langgraph_checkpoint_ns`` contiene ``|`` — LangGraph usa
       ese separador para anidar namespaces de subgraphs.
    2. ``metadata.langgraph_path`` contiene un componente ``task`` o
       ``task:<id>`` — indica que un deepagents ``task`` tool está en el
       camino del nodo actual.
    """
    metadata = event.get("metadata") or {}
    ns = str(metadata.get("langgraph_checkpoint_ns") or "")
    if "|" in ns:
        return True
    path = metadata.get("langgraph_path") or ()
    if isinstance(path, list | tuple):
        for component in path:
            if component == "task":
                return True
            if isinstance(component, str) and component.startswith("task:"):
                return True
    return False


_POLICY_MATRIX: dict[tuple[EventOrigin, str], StreamPolicy] = {
    # Root: tokens y AIMessage finales son user-facing y deben persistirse.
    (EventOrigin.ROOT, "on_chat_model_stream"): StreamPolicy.EMIT_TO_USER,
    (EventOrigin.ROOT, "on_chat_model_end"): StreamPolicy.CAPTURE_HISTORY,
    # Subagente: drop. Su resultado final llega al parent como ToolMessage
    # vía deepagents Command(update={"messages": [...]}). Capturarlo aquí
    # duplicaría el contenido y llenaría el text_block del user con su
    # razonamiento intermedio.
    (EventOrigin.SUBAGENT, "on_chat_model_stream"): StreamPolicy.DROP,
    (EventOrigin.SUBAGENT, "on_chat_model_end"): StreamPolicy.DROP,
    # Tool interno: ya cubierto por INTERNAL_LLM_TAG. Política explícita
    # para que la matriz sea exhaustiva.
    (EventOrigin.INTERNAL_TOOL, "on_chat_model_stream"): StreamPolicy.DROP,
    (EventOrigin.INTERNAL_TOOL, "on_chat_model_end"): StreamPolicy.DROP,
}


def policy_for(event: dict) -> StreamPolicy:
    """Resolver la política de surfacing para un event clasificado.

    Default seguro: ``DROP``. Si un event no encaja en la matriz (kind
    distinto a stream/end, o origen futuro), no lo surface ni se persiste —
    el caller hace fallback a su lógica de catch-all (tool_start, etc.).
    """
    origin = classify_event(event)
    kind = str(event.get("event") or "")
    return _POLICY_MATRIX.get((origin, kind), StreamPolicy.DROP)


__all__ = [
    "EventOrigin",
    "StreamPolicy",
    "classify_event",
    "policy_for",
]
