"""TenantKnowledgeBuilder: Builds the Agent Knowledge System (AKS) for each tenant.

Mirrors the CLAUDE.md pattern: a single, always-loaded identity document that gives
the Sales Agent complete context about the business it represents. Built dynamically
from Brand Studio + Offer Studio data — the business owner never touches anything technical.

Schema-Resilient: Uses model_dump() to pass entire Pydantic models to templates,
so new fields are automatically available without changing this builder.
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.sales_agent.application.services.semantic_router import SemanticRouter
from src.modules.sales_agent.infrastructure.prompts.base import prompt_loader
from src.shared.links.ports.brand import BrandDataPort, create_brand_data_port
from src.shared.links.ports.offer import get_offer_repository, get_offer_type_preset

logger = logging.getLogger(__name__)


class TenantKnowledgeBuilder:
    """Constructs the agent_identity prompt for a given tenant by reading.

    Brand and Offer data from the database and rendering agent_identity.j2.
    """

    def __init__(self, db: Session, brand_port: BrandDataPort | None = None) -> None:
        """Initialize instance."""
        self.brand_port = brand_port or create_brand_data_port(db)
        self.offer_repo = get_offer_repository(db)

    @staticmethod
    def _enrich_with_preset_metadata(offers_data: list[dict[str, Any]]) -> None:
        """Inject preset-derived context onto each offer dict in-place.

        Adds three keys per offer when ``preset_id`` matches the catalog:

        - ``preset_label``: user-facing label (``OfferTypePreset.label_es``)
        - ``preset_description``: 1-3 sentence card subtitle
        - ``preset_flags``: list[str] of the preset's default flags
          (``IS_LEAD_MAGNET``, ``HIGH_TICKET``, ``RECURRING_BILLING``, ...)

        When ``preset_id`` is missing or unknown the keys stay absent so
        the Jinja template can render defensively via ``if offer.preset_label``.
        """
        for offer in offers_data:
            preset_id = offer.get("preset_id")
            preset = get_offer_type_preset(preset_id)
            if preset is None:
                continue
            offer["preset_label"] = preset.label_es  # type: ignore[attr-defined]
            offer["preset_description"] = preset.description_es  # type: ignore[attr-defined]
            offer["preset_flags"] = [flag.value for flag in preset.default_flags]  # type: ignore[attr-defined]

    def build_identity(self, tenant_id: UUID) -> str:
        """Build the complete agent identity document for this tenant.

        Returns a rendered string ready to be prepended to any specialist prompt.
        """
        try:
            # 1. Fetch all data sources via ports
            brand_knowledge = self.brand_port.get_brand_knowledge(tenant_id)
            offers = self.offer_repo.get_all_by_tenant(tenant_id)

            brand_data = brand_knowledge.brand_data
            avatar_data = brand_knowledge.avatars
            personality_profile_data = brand_knowledge.personality_profile

            # Filter active offers only for the agent's knowledge
            active_offers = [o for o in offers if o.status.value in ("active", "draft")]
            offers_data = [o.model_dump(mode="json") for o in active_offers] if active_offers else []
            # Enrich each offer dict with OfferTypePreset metadata so the
            # agent grounding template can refer to the offer by the
            # tenant's vocabulary ("Consulta única") instead of the raw
            # archetype tag. Flags (IS_LEAD_MAGNET, HIGH_TICKET,
            # RECURRING_BILLING) are also surfaced so the specialist
            # prompts can branch on them.
            self._enrich_with_preset_metadata(offers_data)

            # 3. Extract convenience variables for the template
            identity = brand_data.get("identity", {}) or {}
            strategy = brand_data.get("strategy", {}) or {}
            story = brand_data.get("story", {}) or {}
            team = brand_data.get("team", []) or []
            contact = brand_data.get("contact", {}) or {}
            testimonials = brand_data.get("testimonials", []) or []
            positioning = brand_data.get("positioning", {}) or {}

            # Default avatar (the primary ICP)
            default_avatar = next(
                (a for a in avatar_data if a.get("is_default")),
                avatar_data[0] if avatar_data else {},
            )

            # 4. Register tenant-specific semantic routes (objection trigger_phrases)
            try:
                SemanticRouter.register_tenant_routes(tenant_id, offers_data)
            except Exception as e:  # noqa: BLE001 — agent resilience
                logger.warning("Could not register tenant semantic routes: %s", e)

            # 5. Resolve personality instruction (new system takes priority over voice_tone)
            if personality_profile_data and personality_profile_data.get("system_instruction"):
                personality_instruction = personality_profile_data["system_instruction"]
            else:
                personality_instruction = None

            # 6. Render the agent_identity template
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
                positioning=positioning,
                default_avatar=default_avatar,
                # Counts for conditional rendering
                has_brand=bool(identity.get("brand_name")),
                has_offers=len(offers_data) > 0,
                has_avatars=len(avatar_data) > 0,
                has_testimonials=len(testimonials) > 0,
                has_team=len(team) > 0,
                # Personality voice configuration (new)
                personality_instruction=personality_instruction,
            )

        except Exception:
            logger.exception(
                "Error building agent identity for tenant %s",
                tenant_id,
            )
            # Return a minimal fallback so the agent can still function
            return self._fallback_identity()

        else:
            return rendered

    @staticmethod
    def _fallback_identity() -> str:
        return (
            "Eres un asistente de ventas profesional. "
            "No se pudo cargar la configuración del negocio. "
            "Sé amable, haz preguntas sobre las necesidades del cliente "
            "y ofrece ayudar en lo que puedas."
        )
