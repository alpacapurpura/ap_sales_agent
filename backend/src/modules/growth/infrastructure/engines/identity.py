from typing import Dict, Any
from sqlalchemy.orm import Session
from src.modules.marketing.infrastructure.repositories.customer_repository import CustomerRepository
from src.modules.marketing.infrastructure.models.customer_model import CustomerProfileModel as CustomerProfile
from src.modules.marketing.domain.enums import IdentityType

class IdentityResolutionEngine:
    def __init__(self, db: Session):
        self.repository = CustomerRepository(db)

    def resolve(self, identity_type: IdentityType, value: str, traits: Dict[str, Any] = None) -> CustomerProfile:
        """
        Resuelve una identidad a un perfil de cliente unificado.
        Si la identidad existe, devuelve el perfil asociado.
        Si no, crea un nuevo perfil y asocia la identidad.
        
        Args:
            identity_type: Tipo de identidad (email, phone, etc.)
            value: Valor de la identidad (ej. usuario@email.com)
            traits: Atributos adicionales para el perfil (opcional)
        """
        if traits is None:
            traits = {}

        # 1. Buscar perfil existente por identidad
        profile = self.repository.find_by_identity(value, identity_type)
        
        if profile:
            # TODO: Actualizar traits si es necesario (merge)
            return profile

        # 2. Si no existe, crear nuevo perfil
        # Asumimos que tenant_id viene en los traits o se infiere del contexto.
        # Por seguridad, debería ser obligatorio.
        tenant_id = traits.get("tenant_id")
        if not tenant_id:
            raise ValueError("tenant_id is required for creating a new profile")

        profile_data = {
            "tenant_id": tenant_id,
            "properties": traits,
            "computed_traits": {}
        }
        
        new_profile = self.repository.create(profile_data)

        # 3. Asociar la identidad al nuevo perfil
        identity_data = {
            "tenant_id": tenant_id,
            "type": identity_type,
            "value": value,
            "is_primary": True, # Primera identidad es primaria por defecto
            "is_verified": False,
            "source": traits.get("source", "unknown")
        }
        
        self.repository.add_identity(new_profile.id, identity_data)
        
        return new_profile
