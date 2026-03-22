from typing import List, Tuple, Optional, Union
import uuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.modules.iam.domain.tenant import Tenant
from src.modules.iam.infrastructure.repositories.tenant_repository import TenantRepository

class TenantService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TenantRepository(db)

    def get_all_tenants(self) -> List[Tenant]:
        """Obtiene todos los tenants ordenados por fecha de creación descendente."""
        return self.repository.get_all()


    def create_tenant(
        self,
        name: str,
        slug: str,
        can_use_keys: bool,
        company_name: str,
        agent_persona: str,
    ) -> Tuple[Optional[Tenant], Optional[str]]:
        """
        Crea un nuevo tenant.
        Retorna (Tenant, None) si es exitoso, o (None, error_msg) si falla.
        """
        try:
            config = {
                "company_name": company_name,
                "agent_persona": agent_persona
            }
            # Domain Entity Creation
            new_tenant = Tenant(
                id=uuid.uuid4(),
                name=name,
                slug=slug,
                can_use_platform_keys=can_use_keys,
                config_json=config,
                is_active=True
            )
            
            created_tenant = self.repository.create(new_tenant)
            return created_tenant, None
            
        except IntegrityError:
            self.db.rollback()
            return None, "Error: El Slug ya existe."
        except Exception as e:
            self.db.rollback()
            return None, str(e)

    def update_tenant(
        self,
        tenant_id: Union[str, uuid.UUID],
        name: str,
        slug: str,
        can_use_keys: bool,
        is_active: bool
    ) -> Tuple[Optional[Tenant], Optional[str]]:
        """
        Actualiza un tenant existente.
        Retorna (Tenant, None) si es exitoso, o (None, error_msg) si falla.
        """
        try:
            if isinstance(tenant_id, str):
                tenant_id = uuid.UUID(tenant_id)

            tenant = self.repository.get_by_id(tenant_id)
            if not tenant:
                return None, "Error: Tenant no encontrado."
            
            # Update Domain Entity
            tenant.name = name
            tenant.slug = slug
            tenant.can_use_platform_keys = can_use_keys
            tenant.is_active = is_active
            
            updated_tenant = self.repository.update(tenant)
            return updated_tenant, None
            
        except IntegrityError:
            self.db.rollback()
            return None, "Error: El Slug ya existe."
        except Exception as e:
            self.db.rollback()
            return None, str(e)
