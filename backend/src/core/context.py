from contextvars import ContextVar
from typing import Optional
from uuid import UUID

_tenant_id_ctx: ContextVar[Optional[UUID]] = ContextVar("tenant_id", default=None)

def get_tenant_id() -> Optional[UUID]:
    """Retrieves the current Tenant ID from the context."""
    return _tenant_id_ctx.get()

def set_tenant_id(tenant_id: Optional[UUID]) -> None:
    """Sets the current Tenant ID in the context."""
    _tenant_id_ctx.set(tenant_id)
