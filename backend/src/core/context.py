"""Request-scoped context variables for tenant and user isolation."""

from contextvars import ContextVar
from uuid import UUID

_tenant_id_ctx: ContextVar[UUID | None] = ContextVar("tenant_id", default=None)
_user_id_ctx: ContextVar[UUID | None] = ContextVar("user_id", default=None)


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
