from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.iam.domain.tenant import Tenant
from src.modules.iam.infrastructure.models.tenant_model import TenantModel


class TenantRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, tenant_id: UUID) -> Tenant | None:
        model = self.db.execute(select(TenantModel).where(TenantModel.id == tenant_id)).scalars().first()
        if model:
            return Tenant.model_validate(model)
        return None

    def get_by_slug(self, slug: str) -> Tenant | None:
        model = self.db.execute(select(TenantModel).where(TenantModel.slug == slug)).scalars().first()
        if model:
            return Tenant.model_validate(model)
        return None

    def get_all(self) -> list[Tenant]:
        models = self.db.execute(select(TenantModel).order_by(TenantModel.created_at.desc())).scalars().all()
        return [Tenant.model_validate(m) for m in models]

    def create(self, tenant: Tenant) -> Tenant:
        db_tenant = TenantModel(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            config_json=tenant.config_json,
            openai_api_key=tenant.openai_api_key,
            gemini_api_key=tenant.gemini_api_key,
            webhook_secret=tenant.webhook_secret,
            can_use_platform_keys=tenant.can_use_platform_keys,
            is_active=tenant.is_active,
        )
        self.db.add(db_tenant)
        self.db.commit()
        self.db.refresh(db_tenant)
        return Tenant.model_validate(db_tenant)

    def update(self, tenant: Tenant) -> Tenant:
        db_tenant = self.db.execute(select(TenantModel).where(TenantModel.id == tenant.id)).scalars().first()
        if db_tenant:
            db_tenant.name = tenant.name
            db_tenant.slug = tenant.slug
            db_tenant.config_json = tenant.config_json
            db_tenant.openai_api_key = tenant.openai_api_key
            db_tenant.gemini_api_key = tenant.gemini_api_key
            db_tenant.webhook_secret = tenant.webhook_secret
            db_tenant.can_use_platform_keys = tenant.can_use_platform_keys
            db_tenant.is_active = tenant.is_active

            self.db.commit()
            self.db.refresh(db_tenant)
            return Tenant.model_validate(db_tenant)
        return tenant
