"""WebSocket endpoint for Closer Studio real-time updates."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import structlog

from src.modules.sales_agent.infrastructure.ws_manager import ws_manager

logger = structlog.get_logger()
router = APIRouter()


@router.websocket("/ws/closer-studio")
async def closer_studio_ws(
    websocket: WebSocket,
    tenant_id: str = Query(...),
):
    """
    WebSocket endpoint for Closer Studio.

    Connect with: ws://<host>/ws/closer-studio?tenant_id=<uuid>

    Events emitted:
      - new_message: { type, lead_id, role, content, handler_mode }
      - conversation_updated: { type, lead_id, field, value }
      - handler_changed: { type, lead_id, handler_mode }
    """
    if not tenant_id:
        await websocket.close(code=4001, reason="Missing tenant_id")
        return

    await ws_manager.connect(tenant_id, websocket)
    try:
        while True:
            # Keep connection alive; client can send pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(tenant_id, websocket)
    except Exception as e:
        logger.warning("ws_error", tenant_id=tenant_id, error=str(e))
        ws_manager.disconnect(tenant_id, websocket)
