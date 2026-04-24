"""SSoT: mapping of Offer entity fields to FE section slugs.

Aligned with frontend/src/features/offer-studio/lib/section-catalog.ts (21 slugs).
Used by the extraction worker to group filled field paths by FE-aligned
section slug — replacing the broken flat-key grouping in field_diff.

Post field-contract-platform refactor (Fase 04), :func:`fields_to_fe_sections`
derives the path→section mapping from the platform :data:`OFFER_FIELD_CONTRACTS`
in ``src.shared.domain.field_contract``. The legacy manual dict
``OFFER_FIELDS_BY_FE_SECTION`` was removed in sub-step 04.G — drift between
parallel registries can no longer happen by construction.
"""

from __future__ import annotations

# Triggers offer FieldContract registration on first import.
import src.modules.offer.domain.field_contract  # noqa: F401
from src.modules.offer.domain.enums import OfferArchetype
from src.shared.domain.field_contract import (
    FieldContract,
    get_module_contracts,
)

# All 21 FE section slugs from section-catalog.ts — used in arch tests.
FE_SECTION_SLUGS: frozenset[str] = frozenset(
    {
        "identity",
        "strategy",
        "psychology",
        "promise",
        "program_details",
        "service_details",
        "event_details",
        "product_details",
        "subscription_details",
        "platform_details",
        "location",
        "instructors",
        "value_stack",
        "pricing",
        "testimonials",
        "portfolio",
        "faq",
        "gallery",
        "resources",
        "closing",
        "knowledge",
    }
)

# Backend wave slug → FE slugs it contributes to.
# A single backend wave can populate fields that land in multiple FE sections.
# Used by on_progress to decide which FE slugs to announce as "completed"
# when the extraction service signals section_completed=<backend_slug>.
BACKEND_WAVE_TO_FE_SLUGS: dict[str, tuple[str, ...]] = {
    "promise": ("identity", "promise"),
    "strategy": ("strategy",),
    "psychology": ("psychology",),
    "value_stack": ("value_stack", "pricing"),
    "closing": ("closing",),
    # "details" backend slug → resolved by resolve_details_section() at runtime
    "details": (),
}

# Archetype → FE section slug for the polymorphic details editor.
_DETAILS_BY_ARCHETYPE: dict[OfferArchetype, str] = {
    OfferArchetype.PROGRAMA: "program_details",
    OfferArchetype.SERVICIO: "service_details",
    OfferArchetype.EXPERIENCIA: "event_details",
    OfferArchetype.PRODUCTO: "product_details",
    OfferArchetype.MEMBRESIA: "subscription_details",
}


def resolve_details_section(archetype: OfferArchetype | None) -> str | None:
    """Return the FE section slug for the polymorphic details editor.

    Returns None when archetype is None or unknown.
    """
    if archetype is None:
        return None
    return _DETAILS_BY_ARCHETYPE.get(archetype)


def _select_section_for_path(
    contracts_for_path: list[FieldContract],
    archetype_value: str | None,
) -> str | None:
    """Pick the section that applies to a contract candidate set.

    A path can have multiple contracts when polymorphic variants share
    field names (e.g. ``specific_details.start_date`` in Program + Event
    with different sections). The archetype filter narrows down the
    correct section.
    """
    # Universal contracts (no archetype_filter) win when present.
    universal = [c for c in contracts_for_path if c.archetype_filter is None]
    if universal:
        return universal[0].section
    # Archetype-filtered: find one matching the offer's archetype.
    if archetype_value is not None:
        for c in contracts_for_path:
            if c.archetype_filter and archetype_value in c.archetype_filter:
                return c.section
    return None


def fields_to_fe_sections(
    *,
    archetype: OfferArchetype | None,
    filled_paths: list[str],
) -> dict[str, list[str]]:
    """Map top-level Offer field paths to FE section slugs.

    Args:
        archetype: The offer's archetype (needed for polymorphic details routing).
        filled_paths: Top-level field name paths from Offer.model_dump() — e.g.
            ["headline_promise", "value_level", "specific_details.duration_weeks"].

    Returns:
        A dict mapping FE slug → list of field paths that landed in it.
        Deterministic and idempotent: same inputs always produce the same output.
        Fields not covered by the registry are silently ignored.

    Example:
        >>> fields_to_fe_sections(
        ...     archetype=OfferArchetype.PROGRAMA,
        ...     filled_paths=["headline_promise", "value_level", "specific_details.duration_weeks"],
        ... )
        {
            "promise": ["headline_promise"],
            "strategy": ["value_level"],
            "program_details": ["specific_details.duration_weeks"],
        }
    """
    archetype_value = archetype.value if archetype else None

    by_path: dict[str, list[FieldContract]] = {}
    for c in get_module_contracts("offer"):
        by_path.setdefault(c.path, []).append(c)

    result: dict[str, list[str]] = {}

    for path in filled_paths:
        # specific_details.* (and bare "specific_details") routes to
        # the archetype details slug — even when the exact sub-field has
        # no contract entry yet (forward-compat for fields not yet
        # formalized). Mirrors legacy resolve_details_section() behavior.
        if path == "specific_details" or path.startswith("specific_details."):
            details_slug = resolve_details_section(archetype)
            if details_slug:
                result.setdefault(details_slug, [])
                if path not in result[details_slug]:
                    result[details_slug].append(path)
            continue

        candidates = by_path.get(path)
        if not candidates:
            # Fallback: top-level lookup if path is a sub-path like
            # "pricing_options.0.label".
            top_level = path.split(".", 1)[0]
            candidates = by_path.get(top_level)
            if not candidates:
                continue

        section = _select_section_for_path(candidates, archetype_value)
        if section is None:
            continue
        result.setdefault(section, [])
        if path not in result[section]:
            result[section].append(path)

    return result
