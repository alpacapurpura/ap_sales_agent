"""
Copilot ReAct Agent — LangGraph StateGraph with tool-calling loop.

The agent follows a simple cycle:
  1. LLM generates a response (possibly with tool calls)
  2. If tool calls → execute them → feed results back to LLM → repeat
  3. If no tool calls → respond to user → END
"""

from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

from src.core.config import settings
from src.modules.copilot.application.orchestrator.state import CopilotState
from src.modules.copilot.application.tools.awareness import AWARENESS_TOOLS
from src.modules.copilot.application.tools.brand_tools import BRAND_TOOLS
from src.modules.copilot.application.tools.mutations import MUTATION_TOOLS
from src.modules.copilot.application.tools.navigation import NAVIGATION_TOOLS
from src.modules.copilot.application.tools.offer_tools import OFFER_TOOLS
from src.modules.copilot.infrastructure.prompts.base import prompt_loader

import structlog

logger = structlog.get_logger()

# ── Tools ────────────────────────────────────────────────────────────
# Navigation tools are always available.
# Awareness tools require DB access and are injected per-request via
# the orchestrator's _build_tools() (see chat.py).
# This list is the static/default set used for schema binding.

COPILOT_TOOLS: list = [*NAVIGATION_TOOLS, *AWARENESS_TOOLS, *MUTATION_TOOLS, *BRAND_TOOLS, *OFFER_TOOLS]


# ── Nodes ────────────────────────────────────────────────────────────

def build_system_prompt(state: CopilotState) -> str:
    """Render the system prompt with current context."""
    ctx = state.get("client_context", {})
    try:
        return prompt_loader.render(
            "copilot_system",
            current_route=ctx.get("current_route"),
            selected_fields=ctx.get("selected_fields", []),
        )
    except Exception as e:
        logger.warning("copilot_system_prompt_fallback", error=str(e))
        return (
            "Eres el Copilot de Nicolify, un asistente experto en marketing y ventas. "
            "Habla siempre en español, de forma profesional pero cercana."
        )


def agent_node(state: CopilotState) -> dict:
    """
    Core agent node: calls LLM with conversation history + system prompt.
    The LLM may return text, tool calls, or both.
    """
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.6,
        streaming=True,
    )

    if COPILOT_TOOLS:
        llm = llm.bind_tools(COPILOT_TOOLS)

    system_prompt = build_system_prompt(state)

    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])

    response = llm.invoke(messages)

    return {"messages": [response]}


def tool_executor_node(state: CopilotState) -> dict:
    """
    Execute tool calls from the last AIMessage and return ToolMessages.
    """
    from langchain_core.messages import ToolMessage

    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}

    tool_map = {t.name: t for t in COPILOT_TOOLS}
    tool_messages = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if tool_name in tool_map:
            try:
                result = tool_map[tool_name].invoke(tool_args)
                tool_messages.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"],
                        name=tool_name,
                    )
                )
            except Exception as e:
                logger.error("copilot_tool_error", tool=tool_name, error=str(e))
                tool_messages.append(
                    ToolMessage(
                        content=f"Error ejecutando {tool_name}: {str(e)}",
                        tool_call_id=tool_call["id"],
                        name=tool_name,
                    )
                )
        else:
            tool_messages.append(
                ToolMessage(
                    content=f"Tool '{tool_name}' no encontrada.",
                    tool_call_id=tool_call["id"],
                    name=tool_name,
                )
            )

    return {"messages": tool_messages}


def should_continue(state: CopilotState) -> Literal["tools", "end"]:
    """Route: if the LLM made tool calls, go to tool_executor; otherwise end."""
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "end"


# ── Build Graph ──────────────────────────────────────────────────────

workflow = StateGraph(CopilotState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_executor_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
workflow.add_edge("tools", "agent")

copilot_graph = workflow.compile()
