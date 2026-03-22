from uuid import UUID
from typing import Dict, Optional
from src.modules.copilot.application.orchestrator.graph import copilot_app
from src.modules.copilot.application.orchestrator.state import create_initial_copilot_state

class CopilotOrchestrator:
    """
    Orchestrates the interaction between the Internal User (Business Owner) and the Copilot.
    """
    
    async def process_user_request(self, user_id: UUID, tenant_id: UUID, message: str, context: Optional[Dict] = None) -> str:
        """
        Processes a user request through the Copilot graph.
        """
        # 1. Create State
        initial_state = create_initial_copilot_state(user_id, tenant_id)
        
        # 2. Add User Message
        initial_state["messages"].append({"role": "user", "content": message})
        if context:
            initial_state["short_term_memory"].update(context)
            
        # 3. Invoke Graph
        try:
            result = await copilot_app.ainvoke(initial_state)
            
            # 4. Extract Response
            last_msg = result["messages"][-1]
            return last_msg.get("content", "I processed your request.")
            
        except Exception as e:
            # Fallback error handling
            return f"I encountered an error: {str(e)}"
