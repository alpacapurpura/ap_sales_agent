from contextvars import ContextVar
from typing import Optional
from uuid import UUID

_tenant_id_ctx: ContextVar[Optional[UUID]] = ContextVar("tenant_id", default=None)
_user_id_ctx: ContextVar[Optional[UUID]] = ContextVar("user_id", default=None)

def get_tenant_id() -> Optional[UUID]:
    """Retrieves the current Tenant ID from the context."""
    return _tenant_id_ctx.get()

def set_tenant_id(tenant_id: Optional[UUID]) -> None:
    """Sets the current Tenant ID in the context."""
    _tenant_id_ctx.set(tenant_id)

def get_user_id() -> Optional[UUID]:
    """Retrieves the current User ID from the context."""
    return _user_id_ctx.get()

def set_user_id(user_id: Optional[UUID]) -> None:
    """Sets the current User ID in the context."""
    _user_id_ctx.set(user_id)
