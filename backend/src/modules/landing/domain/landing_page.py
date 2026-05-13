"""Landing Page domain definitions."""

from datetime import datetime
from uuid import UUID

from luana_core_landing.domain.content import LandingPageConfig
from luana_core_platform.domain.base_entity import BaseEntity


class LandingPage(BaseEntity):
    """Represent landing page.

    A landing may be either offer-level (``edition_id is None`` —
    legacy fallback template shared across all editions) or
    edition-scoped (``edition_id`` set — owned by one ``LaunchEdition``).
    The repository uses ``edition_id`` to serve the right landing at
    public URL resolution time; see Phase 3 of the editions refactor.
    """

    id: UUID
    tenant_id: UUID | None = None
    offer_id: UUID | None = None
    edition_id: UUID | None = None

    slug: str
    config: LandingPageConfig

    is_published: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
