from langgraph.graph import StateGraph, END
from src.modules.copilot.application.orchestrator.state import CopilotState

def copilot_router(state: CopilotState):
    """
    Decides whether to route to a specific agent (e.g. Web Extractor) or handle as general chat.
    """
    # Placeholder logic
    intent = state.get("detected_intent")
    if intent == "extract_web":
        return {"current_task": "web_extraction"}
    return {"current_task": "general_chat"}

def general_chat_node(state: CopilotState):
    """
    General assistant logic.
    """
    return {"messages": [{"role": "assistant", "content": "I am your Copilot. How can I help you manage your business today?"}]}

workflow = StateGraph(CopilotState)
workflow.add_node("router", copilot_router)
workflow.add_node("general_chat", general_chat_node)

workflow.set_entry_point("router")

workflow.add_conditional_edges(
    "router",
    lambda x: x["current_task"],
    {
        "general_chat": "general_chat",
        "web_extraction": "general_chat" # Fallback for now as web extractor is separate graph
    }
)

workflow.add_edge("general_chat", END)

copilot_app = workflow.compile()
