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

from src.modules.sales_agent.application.services.offer_prompt_renderer import (
    filter_offer_for_prompt,
)
from src.modules.sales_agent.application.services.semantic_router import SemanticRouter
from src.modules.sales_agent.infrastructure.prompts.base import prompt_loader
from src.shared.links.ports.brand import BrandDataPort, create_brand_data_port
from src.shared.links.ports.offer import get_offer_repository, get_offer_type_preset
from src.shared.links.ports.social_proof import resolve_sales_agent_context

logger = logging.getLogger(__name__)


class TenantKnowledgeBuilder:
    """Constructs the agent_identity prompt for a given tenant by reading.

    Brand and Offer data from the database and rendering agent_identity.j2.
    """

    def __init__(self, db: Session, brand_port: BrandDataPort | None = None) -> None:
        """Initialize instance."""
        self.db = db
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
            # Strip top-level paths whose FieldContract status is not ACTIVE
            # (deprecated / removed). This is the lifecycle gate for the
            # sales-agent prompt: a field marked DEPRECATED in
            # ``offer/domain/field_contract.py`` disappears from every
            # tenant's identity prompt on the next build without any
            # template edit. ADR-013.
            offers_data = [filter_offer_for_prompt(o) for o in offers_data]
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
            contact = brand_data.get("contact", {}) or {}
            positioning = brand_data.get("positioning", {}) or {}

            # Social proof (testimonials, team, authority) now lives in the
            # social_proof bounded context. The port returns pre-serialized
            # dicts so the Jinja template keeps the same shape.
            social_proof_ctx = resolve_sales_agent_context(self.db, tenant_id)
            testimonials = social_proof_ctx["testimonials"]
            team = social_proof_ctx["team_members"]
            authority_items = social_proof_ctx["authority_items"]

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

            # 5. S7: voice lives in slot 5 (BRAND_VOICE) via build_brand_voice().
            # personality_profile_data is read here only to keep the DTO load
            # surface unchanged. The voice block itself is NOT injected into
            # slot 4 (agent_identity) anymore — see compose.py + brand_voice.
            _ = personality_profile_data  # kept for backwards compat with logging

            # 6. Derive legal / compliance flags from BrandIdentity.
            #    These surface three conditional blocks in ``agent_identity.j2``:
            #      - Guardrails         → disclaimer + out-of-scope + escalation
            #      - Credenciales       → regulated profession (license, authorization)
            #      - Documentos legales → terms / privacy / refund / cookies / use
            #
            #    Flags are derived here (not in the template) to keep Jinja
            #    readable and to match the existing convenience-flag pattern
            #    (``has_offers``, ``has_team`` …). The underlying values stay
            #    on ``identity.*`` so new fields flow through automatically.
            has_legal_guardrails = any(
                identity.get(key)
                for key in (
                    "sales_agent_disclaimer",
                    "sales_agent_out_of_scope",
                )
            )
            has_regulated_profession = any(
                identity.get(key)
                for key in (
                    "regulated_profession_body",
                    "professional_license_number",
                    "professional_license_holder",
                    "operating_authorization",
                    "liability_insurance_carrier",
                )
            )
            has_legal_documents = any(
                identity.get(key)
                for key in (
                    "terms_url",
                    "privacy_url",
                    "cookies_url",
                    "refund_policy_url",
                    "acceptable_use_url",
                )
            )

            # 7. Render the agent_identity template
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
                authority_items=authority_items,
                positioning=positioning,
                default_avatar=default_avatar,
                # Counts for conditional rendering
                has_brand=bool(identity.get("brand_name")),
                has_offers=len(offers_data) > 0,
                has_avatars=len(avatar_data) > 0,
                has_testimonials=len(testimonials) > 0,
                has_authority=len(authority_items) > 0,
                has_team=len(team) > 0,
                # Legal / compliance (new — brand.legal section)
                has_legal_guardrails=has_legal_guardrails,
                has_regulated_profession=has_regulated_profession,
                has_legal_documents=has_legal_documents,
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

    def build_brand_voice(self, tenant_id: UUID) -> str | None:
        """Build the BRAND_VOICE block (slot 5) for this tenant.

        Returns the active PersonalityProfile.system_instruction (compiled
        deterministically by PersonalityCompiler in Brand Studio) when a
        profile exists, falling back to legacy ``BrandIdentity.voice_tone``
        wrapped in a minimal "Tu Voz y Tono" header. Returns ``None`` when
        the tenant has neither configured.

        The returned string is cacheable per tenant — recompilation only
        happens when the tenant edits the profile (Brand Studio "Estilo
        Comunicacional"). See ``.claude/rules/sales-agent-brand-voice.md``.
        """
        try:
            knowledge = self.brand_port.get_brand_knowledge(tenant_id)
        except Exception:
            logger.exception(
                "Error loading brand knowledge for brand_voice (tenant=%s)",
                tenant_id,
            )
            return None

        profile = knowledge.personality_profile
        if profile and profile.get("system_instruction"):
            return str(profile["system_instruction"])

        identity = (knowledge.brand_data or {}).get("identity", {}) or {}
        legacy = identity.get("voice_tone")
        if legacy:
            return f"## Tu Voz y Tono\n{legacy}"

        return None
