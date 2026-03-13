"""
TenantKnowledgeBuilder: Builds the Agent Knowledge System (AKS) for each tenant.

Mirrors the CLAUDE.md pattern: a single, always-loaded identity document that gives
the Sales Agent complete context about the business it represents. Built dynamically
from Brand Studio + Offer Studio data — the business owner never touches anything technical.

Schema-Resilient: Uses model_dump() to pass entire Pydantic models to templates,
so new fields are automatically available without changing this builder.
"""

import logging
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from src.modules.brand.infrastructure.repositories.brand_repository import BrandRepository
from src.modules.brand.infrastructure.repositories.avatar_repository import AvatarRepository
from src.modules.offer.infrastructure.repositories.offer_repository import OfferRepository
from src.modules.sales_agent.infrastructure.prompts.base import prompt_loader
from src.modules.sales_agent.application.services.semantic_router import SemanticRouter

logger = logging.getLogger(__name__)


class TenantKnowledgeBuilder:
    """
    Constructs the agent_identity prompt for a given tenant by reading
    Brand and Offer data from the database and rendering agent_identity.j2.
    """

    def __init__(self, db: Session):
        self.brand_repo = BrandRepository(db)
        self.avatar_repo = AvatarRepository(db)
        self.offer_repo = OfferRepository(db)

    def build_identity(self, tenant_id: UUID) -> str:
        """
        Build the complete agent identity document for this tenant.
        Returns a rendered string ready to be prepended to any specialist prompt.
        """
        try:
            # 1. Fetch all data sources (schema-resilient via model_dump)
            brand = self.brand_repo.get_settings(tenant_id)
            avatars = self.avatar_repo.get_by_tenant(tenant_id)
            offers = self.offer_repo.get_all_by_tenant(tenant_id)

            # 2. Prepare template context using full model dumps
            # New fields added to these models will automatically flow into templates
            brand_data = brand.model_dump(mode="json") if brand else {}
            avatar_data = [a.model_dump(mode="json") for a in avatars] if avatars else []

            # Filter active offers only for the agent's knowledge
            active_offers = [o for o in offers if o.status.value in ("active", "draft")]
            offers_data = [o.model_dump(mode="json") for o in active_offers] if active_offers else []

            # 3. Extract convenience variables for the template
            identity = brand_data.get("identity", {}) or {}
            strategy = brand_data.get("strategy", {}) or {}
            story = brand_data.get("story", {}) or {}
            team = brand_data.get("team", []) or []
            contact = brand_data.get("contact", {}) or {}
            testimonials = brand_data.get("testimonials", []) or []

            # Default avatar (the primary ICP)
            default_avatar = next(
                (a for a in avatar_data if a.get("is_default")),
                avatar_data[0] if avatar_data else {}
            )

            # 4. Register tenant-specific semantic routes (objection trigger_phrases)
            try:
                SemanticRouter.register_tenant_routes(tenant_id, offers_data)
            except Exception as e:
                logger.warning(f"Could not register tenant semantic routes: {e}")

            # 5. Render the agent_identity template
            rendered = prompt_loader.render(
                "agent_identity",
                # Full dumps (schema-resilient)
                brand=brand_data,
                avatars=avatar_data,
                offers=offers_data,
                # Convenience accessors (for cleaner template syntax)
                identity=identity,
                strategy=strategy,
                story=story,
                team=team,
                contact=contact,
                testimonials=testimonials,
                default_avatar=default_avatar,
                # Counts for conditional rendering
                has_brand=bool(identity.get("brand_name")),
                has_offers=len(offers_data) > 0,
                has_avatars=len(avatar_data) > 0,
                has_testimonials=len(testimonials) > 0,
                has_team=len(team) > 0,
            )

            return rendered

        except Exception as e:
            logger.error(f"Error building agent identity for tenant {tenant_id}: {e}", exc_info=True)
            # Return a minimal fallback so the agent can still function
            return self._fallback_identity()

    @staticmethod
    def _fallback_identity() -> str:
        return (
            "Eres un asistente de ventas profesional. "
            "No se pudo cargar la configuración del negocio. "
            "Sé amable, haz preguntas sobre las necesidades del cliente "
            "y ofrece ayudar en lo que puedas."
        )
