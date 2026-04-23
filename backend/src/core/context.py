"""Request-scoped context variables for tenant, user, and conversation isolation."""

from contextvars import ContextVar
from uuid import UUID

_tenant_id_ctx: ContextVar[UUID | None] = ContextVar("tenant_id", default=None)
_user_id_ctx: ContextVar[UUID | None] = ContextVar("user_id", default=None)
_conversation_id_ctx: ContextVar[str | None] = ContextVar("conversation_id", default=None)


def get_tenant_id() -> UUID | None:
    """Retrieve the current tenant ID from the context."""
    return _tenant_id_ctx.get()


def set_tenant_id(tenant_id: UUID | None) -> None:
    """Set the current tenant ID in the context."""
    _tenant_id_ctx.set(tenant_id)


def get_user_id() -> UUID | None:
    """Retrieve the current user ID from the context."""
    return _user_id_ctx.get()


def set_user_id(user_id: UUID | None) -> None:
    """Set the current user ID in the context."""
    _user_id_ctx.set(user_id)


def get_conversation_id() -> str | None:
    """Retrieve the current copilot conversation ID from the context.

    Populated by the copilot chat orchestrator before the LangGraph invocation
    so tools can persist conversation-scoped state (e.g. guided setup progress)
    without threading the id through tool arguments.
    """
    return _conversation_id_ctx.get()


def set_conversation_id(conversation_id: str | None) -> None:
    """Set the current copilot conversation ID in the context."""
    _conversation_id_ctx.set(conversation_id)
