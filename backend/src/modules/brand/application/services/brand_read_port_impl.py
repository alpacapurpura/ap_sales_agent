"""BrandReadPort implementation -- provides brand identity data to analytics module."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from sqlalchemy import select

from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.shared.domain.ports import BrandReadPort

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


class BrandReadPortImpl(BrandReadPort):
    """Reads brand identity from tenant config_json."""

    def __init__(self, db: Session) -> None:
        self.db = db

    async def get_industry(self, tenant_id: UUID) -> str | None:
        """Get the industry string from brand settings."""
        stmt = select(TenantModel.config_json).where(TenantModel.id == tenant_id)
        result = await asyncio.to_thread(self.db.execute, stmt)
        config_json = result.scalar_one_or_none()

        if not config_json:
            return None

        brand_settings = config_json.get("brand_settings", {})
        identity = brand_settings.get("identity", {})
        return identity.get("industry")
