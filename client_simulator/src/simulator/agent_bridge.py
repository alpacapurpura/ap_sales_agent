import structlog
import httpx

from src.config import settings
from src.simulator.state import SimulationState

logger = structlog.get_logger()


async def agent_bridge(state: SimulationState) -> dict:
    """Send the latest customer message to the sales agent via webhook and collect response."""
    last_customer_turn = None
    for turn in reversed(state["turns"]):
        if turn["role"] == "customer":
            last_customer_turn = turn
            break

    if not last_customer_turn:
        return {
            "is_finished": True,
            "finish_reason": "agent_error",
        }

    url = f"{settings.backend_url}/api/v1/connections/webhook/chat"
    headers = {"X-Webhook-Secret": settings.webhook_secret}
    payload = {
        "user_id": state["simulated_user_id"],
        "message": last_customer_turn["content"],
        "metadata": {
            "source": "simulator",
            "simulation_id": state["simulation_id"],
            "turn": state["current_turn"],
        },
    }

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        agent_message = data.get("response", "")
        if not agent_message:
            logger.warning("empty_agent_response", simulation_id=state["simulation_id"])
            return {
                "is_finished": True,
                "finish_reason": "agent_error",
            }

        from datetime import datetime

        agent_turn = {
            "turn_number": state["current_turn"],
            "role": "agent",
            "content": agent_message,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": data.get("metadata"),
        }

        return {
            "turns": state["turns"] + [agent_turn],
            "last_agent_response": agent_message,
        }

    except httpx.TimeoutException:
        logger.error("agent_timeout", simulation_id=state["simulation_id"])
        return {
            "is_finished": True,
            "finish_reason": "agent_error",
        }
    except httpx.HTTPStatusError as e:
        logger.error(
            "agent_http_error",
            simulation_id=state["simulation_id"],
            status=e.response.status_code,
            body=e.response.text[:500],
        )
        return {
            "is_finished": True,
            "finish_reason": "agent_error",
        }
    except Exception as e:
        logger.error("agent_bridge_error", simulation_id=state["simulation_id"], error=str(e))
        return {
            "is_finished": True,
            "finish_reason": "agent_error",
        }
