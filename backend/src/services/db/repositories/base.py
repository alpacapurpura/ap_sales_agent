from sqlalchemy.orm import Session, Query
from src.services.database import SessionLocal
from src.core.context import get_tenant_id
from typing import Type

class BaseRepository:
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()

    def close(self):
        self.db.close()
        
    def _apply_tenant_filter(self, query: Query, model: Type) -> Query:
        """
        Applies tenant isolation filter if a tenant context exists.
        """
        tenant_id = get_tenant_id()
        if tenant_id and hasattr(model, 'tenant_id'):
             return query.filter(model.tenant_id == tenant_id)
        return query
        
    def _set_tenant(self, instance: object):
        """
        Sets the tenant_id on an instance before saving.
        """
        tenant_id = get_tenant_id()
        if tenant_id and hasattr(instance, 'tenant_id') and not instance.tenant_id:
            instance.tenant_id = tenant_id
