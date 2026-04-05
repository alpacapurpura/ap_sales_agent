"""In-process WebSocket connection manager for Closer Studio real-time events."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from fastapi import WebSocket

logger = structlog.get_logger()


class ConnectionManager:
    """
    Manages WebSocket connections per tenant.

    Uses an in-process dict for dev. For horizontal scaling, swap the
    _emit_to_connections call with Redis pub/sub.
    """

    def __init__(self) -> None:
        # tenant_id -> set of active WebSocket connections
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, tenant_id: str, ws: WebSocket) -> None:
        await ws.accept()
        if tenant_id not in self._connections:
            self._connections[tenant_id] = set()
        self._connections[tenant_id].add(ws)
        logger.info(
            "ws_connected", tenant_id=tenant_id, total=len(self._connections[tenant_id])
        )

    def disconnect(self, tenant_id: str, ws: WebSocket) -> None:
        if tenant_id in self._connections:
            self._connections[tenant_id].discard(ws)
            if not self._connections[tenant_id]:
                del self._connections[tenant_id]
        logger.info("ws_disconnected", tenant_id=tenant_id)

    async def emit(self, tenant_id: str, data: dict) -> None:
        """Broadcast an event to all connections for a tenant."""
        connections = self._connections.get(tenant_id, set())
        if not connections:
            return

        payload = json.dumps(data, default=str)
        dead: list[WebSocket] = []

        for ws in connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(tenant_id, ws)

    @property
    def active_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


# Singleton instance
ws_manager = ConnectionManager()
