"""BrandSuggestionProvider — heuristic, route-scoped, tenant-isolated.

Reads brand state via ``shared/links/ports/brand.py::BrandDataPort``
(no direct cross-module import — preserves the F1 ratchet at 22 entries).

Heuristic rules (D-3, 7 reglas):
 1. brand.identity.brand_name vacío            -> "Empieza por tu marca"        (0.90)
 2. brand.positioning.UVP vacío                -> "Define tu propuesta única"   (0.85)
 3. brand.narrative.one_liner vacío            -> "Construye tu narrativa"      (0.82)
 4. brand.brand_personality.archetype vacío    -> "Elige tu arquetipo"          (0.78)
 5. PersonalityProfile activo ausente          -> "Configura la voz del agente" (0.76)
 6. buyer_persona_count == 0                   -> "Crea tu buyer persona"       (0.75)
 7. brand_completion_ratio < 0.30              -> "Activa el modo guiado"       (0.70)

[COPILOT-SUGGESTIONS-ENGINE] -> docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from collections.abc import Callable

from luana_core_copilot.domain.suggestion import (
    Suggestion,
    SuggestionCategory,
    SuggestionContext,
)
from luana_core_platform.core.database import SessionLocal
from luana_core_platform.links.ports.brand import create_brand_data_port

logger = structlog.get_logger()


class BrandSuggestionProvider:
    """Heuristic suggestions for the Brand Studio route."""

    @property
    def provider_id(self) -> str:
        """Stable id matching the module slug."""
        return "brand"

    @property
    def provider_priority(self) -> int:
        """Tie-break weight. 10 = same level as sales_agent (route-scoped)."""
        return 10

    @property
    def applies_to_routes(self) -> tuple[str, ...]:
        """Activate only on Brand Studio routes."""
        return ("brand-studio",)

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
                "brand_suggestion_provider_failed",
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

        db = SessionLocal()
        try:
            port = create_brand_data_port(db)

            # Tenant-scoped reads
            knowledge = self._safe_read(
                lambda: port.get_brand_knowledge(ctx.tenant_id),
                default=None,
            )
            persona_count = self._safe_read(
                lambda: port.get_buyer_persona_count(ctx.tenant_id),
                default=0,
            )
            personality_present = self._safe_read(
                lambda: port.get_active_personality_profile_present(ctx.tenant_id),
                default=False,
            )

            brand_data = (knowledge.brand_data if knowledge else {}) or {}  # type: ignore[attr-defined]
            identity = brand_data.get("identity") or {}
            positioning = brand_data.get("positioning") or {}
            narrative = brand_data.get("narrative") or {}
            brand_personality = brand_data.get("brand_personality") or {}

            suggestions: list[Suggestion] = []

            # Completion ratio (used by rule 7)
            populated = sum(
                [
                    bool(identity.get("brand_name")),
                    bool(positioning.get("unique_value_proposition")),
                    bool(narrative.get("one_liner")),
                    bool(brand_personality.get("archetype")),
                    bool(personality_present),
                    persona_count >= 1,  # type: ignore[operator]
                ]
            )
            completion_ratio = populated / 6.0

            # Rule 1 — identity missing
            if not identity.get("brand_name"):
                suggestions.append(
                    Suggestion(
                        label="Empieza por tu marca",
                        prompt=("Ayúdame a configurar la identidad de mi marca: nombre, tagline e industria."),
                        confidence=0.90,
                        category=SuggestionCategory.ACTION,
                        source_module="brand",
                    )
                )

            # Rule 2 — UVP missing (only if identity exists)
            if identity.get("brand_name") and not positioning.get("unique_value_proposition"):
                suggestions.append(
                    Suggestion(
                        label="Define tu propuesta única",
                        prompt=("Ayúdame a redactar mi propuesta única de valor usando el framework Brand Love Key."),
                        confidence=0.85,
                        category=SuggestionCategory.ACTION,
                        source_module="brand",
                    )
                )

            # Rule 3 — narrative missing (only if UVP exists)
            if positioning.get("unique_value_proposition") and not narrative.get("one_liner"):
                suggestions.append(
                    Suggestion(
                        label="Construye tu narrativa StoryBrand",
                        prompt=("Guíame para armar mi narrativa StoryBrand (hero, problem, guide, plan, CTA)."),
                        confidence=0.82,
                        category=SuggestionCategory.ACTION,
                        source_module="brand",
                    )
                )

            # Rule 4 — archetype missing
            if not brand_personality.get("archetype"):
                suggestions.append(
                    Suggestion(
                        label="Elige tu arquetipo de marca",
                        prompt=("Ayúdame a elegir el arquetipo Jung que mejor refleja mi marca y por qué."),
                        confidence=0.78,
                        category=SuggestionCategory.CLARIFY,
                        source_module="brand",
                    )
                )

            # Rule 5 — no active personality profile
            if not personality_present:
                suggestions.append(
                    Suggestion(
                        label="Configura la voz del agente",
                        prompt=(
                            "Quiero configurar el perfil de personalidad para que el sales agent suene como mi marca."
                        ),
                        confidence=0.76,
                        category=SuggestionCategory.ACTION,
                        source_module="brand",
                    )
                )

            # Rule 6 — no buyer personas
            if persona_count == 0:
                suggestions.append(
                    Suggestion(
                        label="Crea tu buyer persona principal",
                        prompt=("Ayúdame a definir mi buyer persona principal (demographics, pain points, deseos)."),
                        confidence=0.75,
                        category=SuggestionCategory.ACTION,
                        source_module="brand",
                    )
                )

            # Rule 7 — brand completion ratio below threshold
            if completion_ratio < 0.30:
                suggestions.append(
                    Suggestion(
                        label="Activa el modo guiado de marca",
                        prompt=("Quiero un recorrido guiado para completar mi marca paso a paso."),
                        confidence=0.70,
                        category=SuggestionCategory.NAV,
                        source_module="brand",
                    )
                )

            suggestions.sort(key=lambda s: s.confidence, reverse=True)
            return suggestions[:max_per_provider]
        finally:
            db.close()

    @staticmethod
    def _safe_read(fn: Callable[[], object], default: object) -> object:
        """Execute fn(); return default on any exception."""
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            logger.warning("brand_provider_safe_read_failed", error=str(exc))
            return default


__all__ = ["BrandSuggestionProvider"]
