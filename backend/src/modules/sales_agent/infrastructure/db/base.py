"""Base infrastructure module."""

from luana_core_platform.core.context import get_tenant_id
from luana_core_platform.core.database import SessionLocal
from sqlalchemy.orm import Query, Session


class BaseRepository:
    """Repository for base persistence."""

    def __init__(self, db: Session = None) -> None:
        """Initialize repository with database session."""
        self.db = db or SessionLocal()

    def close(self) -> None:
        """Close."""
        self.db.close()

    def _apply_tenant_filter(self, query: Query, model: type) -> Query:
        """Apply tenant isolation filter if a tenant context exists."""
        tenant_id = get_tenant_id()
        if tenant_id and hasattr(model, "tenant_id"):
            return query.filter(model.tenant_id == tenant_id)
        return query

    def _set_tenant(self, instance: object) -> None:
        """Set the tenant_id on an instance before saving."""
        tenant_id = get_tenant_id()
        if tenant_id and hasattr(instance, "tenant_id") and not instance.tenant_id:
            instance.tenant_id = tenant_id
