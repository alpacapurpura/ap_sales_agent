"""Offer-type-preset API — exposes the 7th SSoT axis catalog.

Public, tenant-agnostic, highly cacheable. Clients pass
``?business_types=<csv>`` to narrow the preset list to what the tenant
actually sells. Mirrors the versioning/caching patterns of
``/offer/archetypes/catalog`` and ``/offer/value-levels/catalog``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict

from src.modules.offer.domain.offer_type_preset_catalog import (
    OFFER_TYPE_PRESET_CATALOG,
    QUESTION_REGISTRY,
    ConditionalQuestion,
    OfferTypePreset,
    get_presets_for_business_types,
)

# ExpertBusinessType MUST be imported at runtime — FastAPI resolves the
# ``Annotated[list[ExpertBusinessType] | None, Query(...)]`` forward
# reference when it builds the dependency graph. Hiding this behind
# ``TYPE_CHECKING`` triggers ``PydanticUserError: TypeAdapter ... is not
# fully defined`` on the first request. The ``# noqa: TC001`` silences
# the legitimate ruff hint because the import genuinely is not
# typing-only for this consumer.
from src.shared.domain.expert_business_type import ExpertBusinessType  # noqa: TC001

router = APIRouter()


class ConditionalQuestionDTO(BaseModel):
    """DTO mirror of :class:`ConditionalQuestion`."""

    model_config = ConfigDict(frozen=True)

    question_id: str
    question_es: str
    help_es: str
    on_yes_sections: list[str]
    on_yes_flags: list[str]

    @classmethod
    def from_domain(cls, question: ConditionalQuestion) -> ConditionalQuestionDTO:
        """Build a DTO from the frozen domain record."""
        return cls(
            question_id=question.question_id,
            question_es=question.question_es,
            help_es=question.help_es,
            on_yes_sections=[s.value for s in question.on_yes_sections],
            on_yes_flags=[f.value for f in question.on_yes_flags],
        )


class OfferTypePresetDTO(BaseModel):
    """DTO mirror of :class:`OfferTypePreset`."""

    model_config = ConfigDict(frozen=True)

    preset_id: str
    business_type: str
    archetype: str
    label_es: str
    description_es: str
    icon_name: str
    base_sections: list[str]
    conditional_question_ids: list[str]
    default_flags: list[str]
    suitability_note_es: str
    examples_es: list[str]

    @classmethod
    def from_domain(cls, preset: OfferTypePreset) -> OfferTypePresetDTO:
        """Build a DTO from the frozen domain record."""
        return cls(
            preset_id=preset.preset_id,
            business_type=preset.business_type.value,
            archetype=preset.archetype.value,
            label_es=preset.label_es,
            description_es=preset.description_es,
            icon_name=preset.icon_name,
            base_sections=[s.value for s in preset.base_sections],
            conditional_question_ids=list(preset.conditional_question_ids),
            default_flags=[f.value for f in preset.default_flags],
            suitability_note_es=preset.suitability_note_es,
            examples_es=list(preset.examples_es),
        )


class OfferTypePresetCatalogResponse(BaseModel):
    """Versioned wrapper returning presets + the conditional question registry."""

    model_config = ConfigDict(frozen=True)

    version: str
    presets: list[OfferTypePresetDTO]
    questions: list[ConditionalQuestionDTO]


# Bump this when ``offer_type_preset_catalog.py`` changes materially (adding,
# removing or renaming a preset, question or flag). Clients key their cache
# off this string.
_CATALOG_VERSION = "2026-04-19.1"


@router.get(
    "/catalog",
    response_model=OfferTypePresetCatalogResponse,
    summary="Offer-type-preset catalog (public, cacheable)",
)
async def get_offer_type_presets_catalog(
    business_types: Annotated[
        list[ExpertBusinessType] | None,
        Query(
            description=(
                "Optional filter. Pass one or more ExpertBusinessType values to "
                "get only the presets relevant to the tenant's declared profile. "
                "Omit to receive the full catalog."
            )
        ),
    ] = None,
) -> OfferTypePresetCatalogResponse:
    """Return offer-type presets filtered by business types.

    When ``business_types`` is omitted, returns every preset. Ordering is
    stable per-insertion in the catalog dict and is preserved end-to-end so
    clients can render the grid deterministically.
    """
    presets_tuple = get_presets_for_business_types(tuple(business_types) if business_types else None)
    return OfferTypePresetCatalogResponse(
        version=_CATALOG_VERSION,
        presets=[OfferTypePresetDTO.from_domain(p) for p in presets_tuple],
        questions=[ConditionalQuestionDTO.from_domain(q) for q in QUESTION_REGISTRY.values()],
    )


@router.get(
    "/catalog/all",
    response_model=OfferTypePresetCatalogResponse,
    summary="Offer-type-preset full catalog (admin / discovery)",
)
async def get_offer_type_presets_full_catalog() -> OfferTypePresetCatalogResponse:
    """Return the unfiltered catalog.

    Used by admin surfaces and first-time discovery flows before the tenant
    has declared ``business_types``.
    """
    return OfferTypePresetCatalogResponse(
        version=_CATALOG_VERSION,
        presets=[OfferTypePresetDTO.from_domain(p) for p in OFFER_TYPE_PRESET_CATALOG.values()],
        questions=[ConditionalQuestionDTO.from_domain(q) for q in QUESTION_REGISTRY.values()],
    )
