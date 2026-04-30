"""OfferSuggestionProvider — heuristic, route-scoped, tenant-isolated.

Reads offer state via ``shared/links/ports/offer.py`` (cross-module read goes
through the existing port — does NOT introduce a new entry in
``test_no_new_copilot_module_imports.py::KNOWN_COPILOT_TO_MODULE_IMPORTS`` since
``copilot -> offer`` already exists for ``offer_section_tools.py`` / ``offer_fields.py``).

Heuristic rules (initial set; expand in future PRs):
 1. Route ``offer-studio`` (no offer_id) → "Crea una oferta"
 2. Route ``offer-studio/{id}`` → preset-flag-driven:
    - ``HIGH_TICKET`` → "Sugiere 3-tier pricing"
    - ``RECURRING_BILLING`` → "Configura facturación recurrente"
    - ``IS_LEAD_MAGNET`` → "Vincula con oferta core"
 3. ``incomplete_fields`` includes ``promise.headline`` → "Genera variantes de promesa"

Confidence scoring (deterministic, in [0,1]):
    base_priority (0.5-0.9) * route_match_boost (1.0 if exact, 0.7 if prefix)
    * freshness_decay (1.0 always - heuristic provider, no time decay yet)

[COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

import structlog

from src.core.database import SessionLocal
from src.modules.copilot.application.services.offer_suggestion_reader import (
    OfferSuggestionReader,
)
from src.modules.copilot.domain.suggestion import Suggestion, SuggestionCategory, SuggestionContext

logger = structlog.get_logger()


class OfferSuggestionProvider:
    """Heuristic suggestions for the Offer Studio route.

    All reads are tenant-scoped via ``SuggestionContext.tenant_id``.
    """

    @property
    def provider_id(self) -> str:
        """Stable id matching the module slug."""
        return "offer"

    @property
    def provider_priority(self) -> int:
        """Explicit tie-break weight (Q3 decision). 0 = baseline."""
        return 0

    @property
    def applies_to_routes(self) -> tuple[str, ...]:
        """Activate only on Offer Studio routes."""
        return ("offer-studio",)

    def get_suggestions(
        self,
        ctx: SuggestionContext,
        *,
        max_per_provider: int = 5,
    ) -> list[Suggestion]:
        """Compute heuristic suggestions. MUST NOT raise — returns [] on any error."""
        try:
            return self._compute(ctx, max_per_provider=max_per_provider)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "offer_suggestion_provider_failed",
                tenant_id=str(ctx.tenant_id),
                error=str(exc),
            )
            return []

    # ------------------------------------------------------------------
    # Private implementation
    # ------------------------------------------------------------------

    def _compute(
        self,
        ctx: SuggestionContext,
        *,
        max_per_provider: int,
    ) -> list[Suggestion]:
        db = SessionLocal()
        try:
            reader = OfferSuggestionReader(db, tenant_id=ctx.tenant_id)
            suggestions: list[Suggestion] = []

            offers = reader.list_offers()

            # Rule 1: no offers at all → create chip
            if not offers:
                suggestions.append(
                    Suggestion(
                        label="Crea tu primera oferta",
                        prompt="Ayudame a crear mi primera oferta. ¿Por dónde empiezo?",
                        confidence=0.85,
                        category=SuggestionCategory.ACTION,
                        source_module="offer",
                    )
                )

            # Rule 2: route has offer_id → flag-driven chips
            route = ctx.current_route or ""
            parts = route.split("/")
            offer_id_str = parts[1] if len(parts) > 1 else None

            from uuid import UUID  # local import to keep module-level imports clean

            offer_id: UUID | None = None
            if offer_id_str:
                try:
                    offer_id = UUID(offer_id_str)
                except ValueError:
                    offer_id = None

            if offer_id:
                flags = reader.get_preset_flags(offer_id)

                if "high_ticket" in flags:
                    suggestions.append(
                        Suggestion(
                            label="Sugiere estructura de 3 niveles de pricing",
                            prompt=(
                                "Este es un programa de alto valor. "
                                "Sugiereme una estructura de 3 niveles de pricing con anclas psicológicas."
                            ),
                            confidence=0.82,
                            category=SuggestionCategory.ACTION,
                            source_module="offer",
                        )
                    )

                if "recurring_billing" in flags:
                    suggestions.append(
                        Suggestion(
                            label="Configura la facturación recurrente",
                            prompt=(
                                "Ayudame a configurar la facturación recurrente de esta oferta: "
                                "ciclo, período de prueba y política de cancelación."
                            ),
                            confidence=0.80,
                            category=SuggestionCategory.ACTION,
                            source_module="offer",
                        )
                    )

                if "is_lead_magnet" in flags:
                    suggestions.append(
                        Suggestion(
                            label="Vincula con oferta core",
                            prompt=(
                                "Este lead magnet necesita una oferta core para monetizar. "
                                "Ayudame a planificar el upsell natural."
                            ),
                            confidence=0.78,
                            category=SuggestionCategory.ACTION,
                            source_module="offer",
                        )
                    )

            # Rule 3: incomplete promise.headline → generate variants chip
            if "promise.headline" in ctx.incomplete_fields:
                suggestions.append(
                    Suggestion(
                        label="Genera variantes de promesa principal",
                        prompt=(
                            "Genera 3 variantes de promesa principal para esta oferta "
                            "basadas en la narrativa StoryBrand de mi marca."
                        ),
                        confidence=0.75,
                        category=SuggestionCategory.ACTION,
                        source_module="offer",
                    )
                )

            # Rule 4: lead magnet exists but no core offer
            if reader.detect_lead_magnet_without_core():
                suggestions.append(
                    Suggestion(
                        label="Vincula tu lead magnet con una oferta core",
                        prompt=(
                            "Tienes un lead magnet pero no una oferta core que lo monetice. "
                            "Ayudame a diseñar la oferta core ideal."
                        ),
                        confidence=0.76,
                        category=SuggestionCategory.ACTION,
                        source_module="offer",
                    )
                )

            # Sort by confidence descending, cap at max
            suggestions.sort(key=lambda s: s.confidence, reverse=True)
            return suggestions[:max_per_provider]
        finally:
            db.close()


__all__ = ["OfferSuggestionProvider"]
