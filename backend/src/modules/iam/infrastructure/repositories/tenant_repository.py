"""Tenant Repository implementation.

T-6a (PI-12 S1 — sales-agent-litellm-canonicalization, Phase 1
expand-contract): ``create`` and ``update`` no longer assign to the
deprecated provider API key columns (``openai_api_key``,
``deepseek_api_key``, ``kimi_api_key``, ``dashscope_api_key``). The
columns still exist in the DB and the SQLAlchemy ORM still loads them
on read (so ``Tenant.model_validate`` works), but the Python write path
is severed. T-6c will physically ``DROP COLUMN`` and remove the fields
from the SQLAlchemy model.

``gemini_api_key`` writes are preserved (out of scope per architect §2.4
— still active for landing extractors).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.iam.domain.tenant import Tenant
from src.modules.iam.infrastructure.models.tenant_model import TenantModel


class TenantRepository:
    """Concrete repository implementation for tenant."""

    def __init__(self, db: Session) -> None:
        """Initialize TenantRepository."""
        self.db = db

    def get_by_id(self, tenant_id: UUID) -> Tenant | None:
        """Retrieve by id."""
        model = self.db.execute(select(TenantModel).where(TenantModel.id == tenant_id)).scalars().first()
        if model:
            return Tenant.model_validate(model)
        return None

    def get_by_slug(self, slug: str) -> Tenant | None:
        """Retrieve by slug."""
        model = self.db.execute(select(TenantModel).where(TenantModel.slug == slug)).scalars().first()
        if model:
            return Tenant.model_validate(model)
        return None

    def get_all(self) -> list[Tenant]:
        """Retrieve all."""
        models = self.db.execute(select(TenantModel).order_by(TenantModel.created_at.desc())).scalars().all()
        return [Tenant.model_validate(m) for m in models]

    def create(self, tenant: Tenant) -> Tenant:
        """Handle create operation.

        Writes only currently-active fields. The 4 deprecated provider
        API key columns (``openai_api_key``, ``deepseek_api_key``,
        ``kimi_api_key``, ``dashscope_api_key``) are intentionally NOT
        assigned — they default to NULL at the DB level (T-6a).
        """
        db_tenant = TenantModel(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            config_json=tenant.config_json,
            gemini_api_key=tenant.gemini_api_key,  # still active per arch §2.4
            webhook_secret=tenant.webhook_secret,
            can_use_platform_keys=tenant.can_use_platform_keys,
            is_active=tenant.is_active,
        )
        self.db.add(db_tenant)
        self.db.commit()
        self.db.refresh(db_tenant)
        return Tenant.model_validate(db_tenant)

    def update(self, tenant: Tenant) -> Tenant:
        """Handle update operation.

        Writes only currently-active fields. Deprecated provider key
        columns are deliberately not touched — they were NULLed by the
        T-6a migration and stay NULL until T-6c drops them.
        """
        db_tenant = self.db.execute(select(TenantModel).where(TenantModel.id == tenant.id)).scalars().first()
        if db_tenant:
            db_tenant.name = tenant.name
            db_tenant.slug = tenant.slug
            db_tenant.config_json = tenant.config_json
            db_tenant.gemini_api_key = tenant.gemini_api_key  # still active per arch §2.4
            db_tenant.webhook_secret = tenant.webhook_secret
            db_tenant.can_use_platform_keys = tenant.can_use_platform_keys
            db_tenant.is_active = tenant.is_active

            self.db.commit()
            self.db.refresh(db_tenant)
            return Tenant.model_validate(db_tenant)
        return tenant
