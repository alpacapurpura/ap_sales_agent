"""Connections API dependencies — cross-module DI wiring.

Centralizes imports of concrete adapters from other modules so that
individual endpoint files depend only on shared port ABCs.
"""

# DDD exception (intentional): this file IS the composition root for connections.
# Its sole job is to wire ChatOrchestrator as the concrete MessageHandlerPort
# implementation. The import of sales_agent here is correct DI wiring.
from src.modules.sales_agent.application.orchestrator.chat import ChatOrchestrator
from src.shared.links.ports.message_handler import MessageHandlerPort

# Singleton — ChatOrchestrator is stateless (no DB session in __init__).
_message_handler: MessageHandlerPort = ChatOrchestrator()


def get_message_handler() -> MessageHandlerPort:
    """Return the message handler (ChatOrchestrator) singleton."""
    return _message_handler
