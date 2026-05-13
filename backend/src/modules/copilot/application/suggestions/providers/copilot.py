"""CopilotSuggestionProvider — transversal, low-priority fallback.

Active on ALL routes (``applies_to_routes == ()``).  Emits contextual chips
based on conversation state, route validity, and platform setup completion.

Heuristic rules (D-5, 5 reglas):
 1. conversation_id is None             -> "Empieza tu primer chat"    (0.65)
 2. conv set + recent_messages empty    -> "Retoma tu conversación"    (0.62)
 3. current_route is None               -> "Explora capacidades"       (0.60)
 4. route not in module registry        -> "Vuelve a un módulo"        (0.58)
 5. count_completed_modules <= 1        -> "Completa tu setup"         (0.56)

Relies only on:
 - ``shared/links/ports/brand.py``  (brand completion proxy)
 - ``shared/links/ports/offer.py``  (offer count proxy via lazy import)
 - ``copilot/domain/module_registry`` (route validity — INTRA-MODULE, OK)

[COPILOT-SUGGESTIONS-ENGINE] -> docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

import structlog
from luana_core_copilot.domain.module_registry import get_module_registry
from luana_core_copilot.domain.suggestion import (
    Suggestion,
    SuggestionCategory,
    SuggestionContext,
)
from luana_core_platform.core.database import SessionLocal
from luana_core_platform.links.ports.brand import create_brand_data_port
from luana_core_platform.links.ports.offer import get_offer_repository

logger = structlog.get_logger()


class CopilotSuggestionProvider:
    """Transversal fallback suggestions — always active, lowest priority."""

    @property
    def provider_id(self) -> str:
        """Stable id matching the module slug."""
        return "copilot"

    @property
    def provider_priority(self) -> int:
        """Lowest tie-break weight — fallback of last resort."""
        return 5

    @property
    def applies_to_routes(self) -> tuple[str, ...]:
        """Empty tuple = active on all routes."""
        return ()

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
                "copilot_suggestion_provider_failed",
                tenant_id=str(ctx.tenant_id),
                error=str(exc),
            )
            return []

    def _compute(
        self,
        ctx: SuggestionContext,
        *,
        max_per_provider: int,
    ) -> list[Suggestion]:
        module_registry = get_module_registry()

        db = SessionLocal()
        try:
            brand_port = create_brand_data_port(db)
            offer_repo = get_offer_repository(db)

            suggestions: list[Suggestion] = []

            # Rule 1 — no conversation yet (first-time user)
            if ctx.conversation_id is None:
                suggestions.append(
                    Suggestion(
                        label="Empieza tu primer chat con el copiloto",
                        prompt=("Hola, soy nuevo aquí. ¿Qué puedes hacer por mi negocio?"),
                        confidence=0.65,
                        category=SuggestionCategory.ACTION,
                        source_module="copilot",
                    )
                )

            # Rule 2 — conversation exists but has no messages
            elif not ctx.recent_message_ids:
                suggestions.append(
                    Suggestion(
                        label="Retoma tu conversación",
                        prompt=("Continuemos donde lo dejamos. ¿Cuál era el siguiente paso?"),
                        confidence=0.62,
                        category=SuggestionCategory.ACTION,
                        source_module="copilot",
                    )
                )

            # Rule 3 — no active route
            if ctx.current_route is None:
                suggestions.append(
                    Suggestion(
                        label="Explora las capacidades del copiloto",
                        prompt=("¿Cuáles módulos puedes ayudarme a gestionar hoy?"),
                        confidence=0.60,
                        category=SuggestionCategory.NAV,
                        source_module="copilot",
                    )
                )

            # Rule 4 — route exists but is not recognized in registry
            elif ctx.current_route and not any(ctx.current_route.startswith(key) for key in module_registry):
                suggestions.append(
                    Suggestion(
                        label="Vuelve a un módulo conocido",
                        prompt=(
                            "Parece que estoy en una sección no reconocida. Llévame a Brand Studio o Offer Studio."
                        ),
                        confidence=0.58,
                        category=SuggestionCategory.NAV,
                        source_module="copilot",
                    )
                )

            # Rule 5 — low platform setup (brand incomplete + no offers + no personality)
            completed = self._count_completed_modules(ctx, brand_port, offer_repo)
            if completed <= 1:
                suggestions.append(
                    Suggestion(
                        label="Completa tu setup inicial",
                        prompt=("Guíame paso a paso para configurar mi marca, mi primera oferta y mi sales agent."),
                        confidence=0.56,
                        category=SuggestionCategory.ACTION,
                        source_module="copilot",
                    )
                )

            suggestions.sort(key=lambda s: s.confidence, reverse=True)
            return suggestions[:max_per_provider]
        finally:
            db.close()

    def _count_completed_modules(
        self,
        ctx: SuggestionContext,
        brand_port: object,
        offer_repo: object,
    ) -> int:
        """Heuristic count of completed setup modules (0 to 3).

        Counts: brand identity present + offer exists + personality present.
        Returns int in [0, 3].
        """
        count = 0

        # Brand: brand_name present
        try:
            knowledge = brand_port.get_brand_knowledge(ctx.tenant_id)  # type: ignore[attr-defined]
            brand_data = (knowledge.brand_data if knowledge else {}) or {}
            if brand_data.get("identity", {}).get("brand_name"):
                count += 1
        except Exception:  # noqa: BLE001
            pass

        # Offer: at least one offer exists
        try:
            offers = offer_repo.get_all_by_tenant(ctx.tenant_id)  # type: ignore[attr-defined]
            if offers:
                count += 1
        except Exception:  # noqa: BLE001
            pass

        # Personality: active profile present
        try:
            if brand_port.get_active_personality_profile_present(ctx.tenant_id):  # type: ignore[attr-defined]
                count += 1
        except Exception:  # noqa: BLE001
            pass

        return count


__all__ = ["CopilotSuggestionProvider"]
