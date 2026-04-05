from datetime import datetime
from uuid import UUID

from src.modules.landing.domain.content import LandingPageConfig
from src.shared.domain.base_entity import BaseEntity


class LandingPage(BaseEntity):
    id: UUID
    tenant_id: UUID | None = None
    offer_id: UUID | None = None

    slug: str
    config: LandingPageConfig

    is_published: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
