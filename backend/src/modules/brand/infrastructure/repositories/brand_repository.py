from sqlalchemy.orm import Session
from uuid import UUID
from sqlalchemy.orm.attributes import flag_modified
from src.modules.brand.domain import BrandSettings
from src.modules.iam.infrastructure.models.tenant_model import TenantModel

class BrandRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_settings(self, tenant_id: UUID) -> BrandSettings:
        tenant = self.db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
        if not tenant:
            return BrandSettings()
        
        config = tenant.config_json or {}
        brand_settings_data = config.get("brand_settings", {})
        
        # Ensure we return a Pydantic model
        if not brand_settings_data:
            return BrandSettings()
            
        return BrandSettings.model_validate(brand_settings_data)

    def save_settings(self, tenant_id: UUID, settings: BrandSettings) -> BrandSettings:
        tenant = self.db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
        if not tenant:
            raise ValueError("Tenant not found")
            
        config = dict(tenant.config_json or {})
        config["brand_settings"] = settings.model_dump(mode='json')
        
        tenant.config_json = config
        flag_modified(tenant, "config_json")
        
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        
        return settings
