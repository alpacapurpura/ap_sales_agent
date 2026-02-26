from typing import Dict, Any, Optional
from uuid import UUID
from src.modules.marketing.infrastructure.repositories.customer_repository import CustomerRepository
from src.modules.marketing.infrastructure.models.customer import CustomerProfile, IdentityType

class IdentityService:
    def __init__(self, customer_repository: CustomerRepository):
        self.customer_repository = customer_repository

    def get_or_create_customer(
        self, 
        tenant_id: UUID, 
        identity_type: IdentityType, 
        identity_value: str, 
        profile_data: Dict[str, Any]
    ) -> CustomerProfile:
        """
        Busca un cliente por su identidad. Si no existe, lo crea.
        """
        # Intentar buscar cliente existente pasando tenant_id explícitamente
        existing_customer = self.customer_repository.find_by_identity(
            identity_value=identity_value, 
            identity_type=identity_type, 
            tenant_id=tenant_id
        )
        
        if existing_customer:
            return existing_customer
            
        # Si no existe, crear uno nuevo
        return self.customer_repository.create_with_identity(
            tenant_id=tenant_id,
            identity_type=identity_type,
            identity_value=identity_value,
            profile_data=profile_data
        )
