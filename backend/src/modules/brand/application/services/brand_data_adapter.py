"""BrandDataPort adapter — provides brand knowledge for the sales agent."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

from src.modules.brand.infrastructure.repositories.avatar_repository import (
    AvatarRepository,
)
from src.modules.brand.infrastructure.repositories.brand_repository import (
    BrandRepository,
)
from src.modules.brand.infrastructure.repositories.buyer_persona_repository import (
    BuyerPersonaRepository,
)
from src.modules.brand.infrastructure.repositories.personality_repository import (
    PersonalityProfileRepository,
)
from src.shared.links.ports.brand import BrandDataPort, BrandKnowledgeDTO


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

        return BrandKnowledgeDTO(
            brand_data=brand.model_dump(mode="json") if brand else {},
            avatars=[a.model_dump(mode="json") for a in avatars] if avatars else [],
            personality_profile=personality_profile.model_dump(mode="json") if personality_profile else None,
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
