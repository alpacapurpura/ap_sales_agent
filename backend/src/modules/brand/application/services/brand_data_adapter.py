"""BrandDataPort adapter — provides brand knowledge for the sales agent."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

from luana_core_brand_studio.api.personality import PersonalityProfileDTO
from luana_core_brand_studio.infrastructure.repositories.avatar_repository import (
    AvatarRepository,
)
from luana_core_brand_studio.infrastructure.repositories.brand_repository import (
    BrandRepository,
)
from luana_core_brand_studio.infrastructure.repositories.buyer_persona_repository import (
    BuyerPersonaRepository,
)
from luana_core_brand_studio.infrastructure.repositories.personality_repository import (
    PersonalityProfileRepository,
)
from luana_core_platform.links.ports.brand import BrandDataPort, BrandKnowledgeDTO


class BrandDataAdapter(BrandDataPort):
    """Concrete adapter that fetches brand data from brand repositories."""

    def __init__(self, db: Session) -> None:
        """Initialize with DB session."""
        self._db = db
        self.brand_repo = BrandRepository(db)
        self.avatar_repo = AvatarRepository(db)
        self.personality_repo = PersonalityProfileRepository(db)

    def get_brand_knowledge(self, tenant_id: UUID) -> BrandKnowledgeDTO:
        """Return pre-serialized brand data for the agent identity builder."""
        brand = self.brand_repo.get_settings(tenant_id)
        avatars = self.avatar_repo.get_by_tenant(tenant_id)
        personality_profile = self.personality_repo.get_active(tenant_id=tenant_id)

        # PersonalityProfileRepository.get_active returns SQLA ORM
        # (PersonalityProfileModel) — convert via existing Pydantic DTO
        # (brand/api/personality.py::PersonalityProfileDTO,
        # ConfigDict(from_attributes=True)) before serialising.
        # Bug #7 fix — PR-1 PI-7 S1 (2026-05-01).
        personality_dict: dict[str, object] | None = None
        if personality_profile is not None:
            personality_dict = PersonalityProfileDTO.model_validate(
                personality_profile,
            ).model_dump(mode="json")

        return BrandKnowledgeDTO(
            brand_data=brand.model_dump(mode="json") if brand else {},
            avatars=[a.model_dump(mode="json") for a in avatars] if avatars else [],
            personality_profile=personality_dict,
        )

    # ── NEW (PR-2-pure-expansion-providers) ───────────────────────────────────

    def get_buyer_persona_count(self, tenant_id: UUID) -> int:
        """Active buyer personas count (soft-delete excluded)."""
        repo = BuyerPersonaRepository(self._db)
        return len(repo.list_by_tenant(tenant_id))

    def get_active_personality_profile_present(self, tenant_id: UUID) -> bool:
        """True iff there is an active global PersonalityProfile for the tenant."""
        profile = self.personality_repo.get_active(tenant_id=tenant_id)
        return profile is not None
