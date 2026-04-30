"""Brand repository implementation."""

from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from src.modules.brand.domain import BrandSettings
from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.shared.domain.events import BrandSectionUpdatedEvent
from src.shared.domain_events.outbox.application.event_bus_adapter import (
    adapter_bus as EventBus,  # noqa: N812
)

logger = structlog.get_logger()


class BrandRepository:
    """Repository for brand persistence."""

    def __init__(self, db: Session) -> None:
        """Initialize brand repository."""
        self.db = db

    def get_settings(self, tenant_id: UUID) -> BrandSettings:
        """Return settings."""
        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        result = self.db.execute(stmt)
        tenant = result.scalars().first()
        if not tenant:
            logger.info(
                "brand_repo_get",
                tenant_id=str(tenant_id),
                has_data=False,
                tenant_found=False,
            )
            return BrandSettings()

        config = tenant.config_json or {}
        brand_settings_data = config.get("brand_settings", {})

        logger.info(
            "brand_repo_get",
            tenant_id=str(tenant_id),
            has_data=bool(brand_settings_data),
            data_keys=list(brand_settings_data.keys()) if brand_settings_data else [],
        )

        # Ensure we return a Pydantic model
        if not brand_settings_data:
            return BrandSettings()

        return BrandSettings.model_validate(brand_settings_data)

    def save_settings(self, tenant_id: UUID, settings: BrandSettings) -> BrandSettings:
        """Save settings."""
        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        result = self.db.execute(stmt)
        tenant = result.scalars().first()
        if not tenant:
            msg = "Tenant not found"
            raise ValueError(msg)

        config = dict(tenant.config_json or {})
        settings_dict = settings.model_dump(mode="json")
        config["brand_settings"] = settings_dict

        logger.info(
            "brand_repo_saving",
            tenant_id=str(tenant_id),
            data_keys=list(settings_dict.keys()),
            has_identity=bool((settings_dict.get("identity") or {}).get("brand_name")),
            has_story=bool((settings_dict.get("story") or {}).get("origin_story")),
            has_strategy=bool(
                (settings_dict.get("strategy") or {}).get("methodology_name"),
            ),
        )

        tenant.config_json = config
        flag_modified(tenant, "config_json")

        self.db.add(tenant)
        # Register the after-commit listener BEFORE the commit so the
        # subscriber (F3 regen worker enqueue) only sees a successfully
        # persisted document.
        EventBus.publish(
            BrandSectionUpdatedEvent.create(tenant_id=tenant_id),
            session=self.db,
        )
        self.db.commit()
        self.db.refresh(tenant)

        # Verify after commit
        saved_config = (tenant.config_json or {}).get("brand_settings") or {}
        logger.info(
            "brand_repo_saved_verified",
            tenant_id=str(tenant_id),
            saved_keys=list(saved_config.keys()) if saved_config else [],
            has_identity=bool(
                (saved_config.get("identity") or {}).get("brand_name") if saved_config else False,
            ),
        )

        return settings
