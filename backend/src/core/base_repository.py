"""Base repository with tenant isolation support."""

from sqlalchemy.orm import Query, Session

from src.core.context import get_tenant_id
from src.core.database import SessionLocal


class BaseRepository:
    """Synchronous base repository with tenant isolation helpers."""

    def __init__(self, db: Session = None) -> None:
        """Initialize with an optional database session."""
        self.db = db or SessionLocal()

    def close(self) -> None:
        """Close the database session."""
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
