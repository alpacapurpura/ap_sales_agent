from langgraph.graph import StateGraph, END
from src.modules.sales_agent.application.orchestrator.state import AgentState
from src.modules.sales_agent.application.agents.sales.nodes import (
    node_sales_supervisor,
    node_qualifier,
    node_product_expert,
    node_closer
)

def create_sales_subgraph():
    workflow = StateGraph(AgentState)
    
    # Nodes
    workflow.add_node("supervisor", node_sales_supervisor)
    workflow.add_node("qualifier", node_qualifier)
    workflow.add_node("product_expert", node_product_expert)
    workflow.add_node("closer", node_closer)
    # workflow.add_node("scheduler", node_scheduler) # TODO: Implement
    
    # Entry Point
    workflow.set_entry_point("supervisor")
    
    # Supervisor Routing
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next_node"],
        {
            "qualifier": "qualifier",
            "product_expert": "product_expert",
            "closer": "closer",
            "scheduler": "closer" # Fallback for now
        }
    )
    
    # Workers return to END (which means back to Main Graph if used as compiled node)
    # OR we can loop back to supervisor? usually workers finish a turn.
    workflow.add_edge("qualifier", END)
    workflow.add_edge("product_expert", END)
    workflow.add_edge("closer", END)
    
    return workflow.compile()

sales_app = create_sales_subgraph()
