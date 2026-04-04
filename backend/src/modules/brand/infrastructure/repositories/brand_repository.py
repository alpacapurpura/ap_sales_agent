from sqlalchemy.orm import Session
from uuid import UUID
from sqlalchemy.orm.attributes import flag_modified
from src.modules.brand.domain import BrandSettings
from src.modules.iam.infrastructure.models.tenant_model import TenantModel
import structlog

logger = structlog.get_logger()

class BrandRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_settings(self, tenant_id: UUID) -> BrandSettings:
        tenant = self.db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
        if not tenant:
            logger.info("brand_repo_get", tenant_id=str(tenant_id), has_data=False, tenant_found=False)
            return BrandSettings()

        config = tenant.config_json or {}
        brand_settings_data = config.get("brand_settings", {})

        logger.info("brand_repo_get", tenant_id=str(tenant_id),
                     has_data=bool(brand_settings_data),
                     data_keys=list(brand_settings_data.keys()) if brand_settings_data else [])

        # Ensure we return a Pydantic model
        if not brand_settings_data:
            return BrandSettings()

        return BrandSettings.model_validate(brand_settings_data)

    def save_settings(self, tenant_id: UUID, settings: BrandSettings) -> BrandSettings:
        tenant = self.db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
        if not tenant:
            raise ValueError("Tenant not found")

        config = dict(tenant.config_json or {})
        settings_dict = settings.model_dump(mode='json')
        config["brand_settings"] = settings_dict

        logger.info("brand_repo_saving", tenant_id=str(tenant_id),
                     data_keys=list(settings_dict.keys()),
                     has_identity=bool((settings_dict.get("identity") or {}).get("brand_name")),
                     has_story=bool((settings_dict.get("story") or {}).get("origin_story")),
                     has_strategy=bool((settings_dict.get("strategy") or {}).get("methodology_name")))

        tenant.config_json = config
        flag_modified(tenant, "config_json")

        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)

        # Verify after commit
        saved_config = (tenant.config_json or {}).get("brand_settings") or {}
        logger.info("brand_repo_saved_verified", tenant_id=str(tenant_id),
                     saved_keys=list(saved_config.keys()) if saved_config else [],
                     has_identity=bool((saved_config.get("identity") or {}).get("brand_name") if saved_config else False))

        return settings
