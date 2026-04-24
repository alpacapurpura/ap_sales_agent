"""SSoT: mapping of Offer entity fields to FE section slugs.

Aligned with frontend/src/features/offer-studio/lib/section-catalog.ts (21 slugs).
Used by the extraction worker to group filled field paths by FE-aligned
section slug — replacing the broken flat-key grouping in field_diff.

Polymorphic details: the FE shows program_details / service_details /
event_details / product_details / subscription_details depending on the
offer's archetype. resolve_details_section() maps an OfferArchetype value
to the correct FE slug.

FE section slugs reference (21 total):
  identity, strategy, psychology, promise,
  program_details, service_details, event_details, product_details,
  subscription_details, platform_details, location, instructors,
  value_stack, pricing, testimonials, portfolio, faq, gallery,
  resources, closing, knowledge
"""

from __future__ import annotations

from src.modules.offer.domain.enums import OfferArchetype

# All 21 FE section slugs from section-catalog.ts — used in arch test.
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

# Maps FE section slug → top-level Offer field names that belong to it.
# Keys are FE slugs (NOT backend wave slugs).
#
# Notes:
# - "identity" captures fields that the extraction wave named "promise" also
#   populates (headline_promise, primary_outcome, time_to_value, public_name,
#   internal_sku) because FE "identity" section covers the offer's public
#   identity fields alongside the core promise. The worker must assign these
#   to "identity" in the FE slug space.
# - "promise" (FE) captures the *pitch* fields not in identity:
#   access_duration + support_duration_days sit closest to the promise scope
#   but are actually surfaced in the polymorphic details sections in FE.
#   We leave them unmapped here to avoid double-grouping; they land in the
#   post-diff residual bucket.
# - "platform_details", "location", "gallery", "testimonials", "portfolio",
#   "faq", "resources", "knowledge": these sections are managed by dedicated
#   FE editors with their own data — they do NOT map to top-level Offer
#   entity fields today. Leaving them empty (not in the map) prevents false
#   "completed" badges on sections the extraction pipeline did not touch.
# - "specific_details.*" paths (from the polymorphic JSON column) are
#   handled by resolve_details_section() — NOT by this flat map.
OFFER_FIELDS_BY_FE_SECTION: dict[str, tuple[str, ...]] = {
    # Offer identity: who the offer is and what it's called
    "identity": (
        "public_name",
        "internal_sku",
        "headline_promise",
        "primary_outcome",
        "time_to_value",
    ),
    # Promise: the core pitch fields visible in the FE "Promesa" section
    # (access_duration/access_duration_text/support_duration_days are closer
    # to the polymorphic details and are intentionally excluded here)
    "promise": (
        "requires_application",
        "min_financial_capacity",
        "prerequisites",
        # NEW narrative:
        "before_state",
        "after_state",
        "why_now",
        "measurable_outcomes",
    ),
    # Strategy: audience targeting and delivery approach
    "strategy": (
        "value_level",
        "delivery_model",
        "target_avatar_match",
        "anti_avatar_keywords",
    ),
    # Psychology of purchase
    "psychology": (
        "marketing_pain_points",
        "marketing_desires",
        "objections",
        # NEW narrative:
        "cultural_trust_barriers",
        "emotional_triggers",
        "status_drivers",
        "regret_scenarios",
    ),
    # Value stack: deliverables + bundled offers
    "value_stack": (
        "deliverables",
        "includes_offers",
    ),
    # Pricing
    "pricing": (
        "pricing_options",
        "price_pay_in_full",
        "currency",
    ),
    # Instructors list
    "instructors": ("instructors",),
    # Closing: conversion mechanics
    "closing": (
        "guarantee_type",
        "guarantee_terms",
        "checkout_page_url",
        "calendar_type_id",
        "onboarding_action",
        "onboarding_url",
        "downsell_offer_id",
        "upsell_offer_id",
        "vsl_link",
        # NEW narrative:
        "refund_process_description",
        "urgency_drivers",
        "scarcity_reason_honest",
        "bonus_if_act_now",
        "final_push_copy",
        "support_duration_days",
    ),
    # Polymorphic details: field paths under "specific_details.*" are mapped
    # via resolve_details_section(archetype) at grouping time.
    # DO NOT add specific_details.* keys here — handled separately.
    #
    # Sections below have no top-level Offer field mapping today:
    # platform_details, location, gallery, testimonials, portfolio,
    # faq, resources, knowledge
}

# Backend wave slug → FE slugs it contributes to.
# A single backend wave can populate fields that land in multiple FE sections.
# Used by on_progress to decide which FE slugs to announce as "completed"
# when the extraction service signals section_completed=<backend_slug>.
BACKEND_WAVE_TO_FE_SLUGS: dict[str, tuple[str, ...]] = {
    "promise": ("identity", "promise"),  # promise wave fills both identity + promise FE sections
    "strategy": ("strategy",),
    "psychology": ("psychology",),
    "value_stack": ("value_stack", "pricing"),
    "closing": ("closing",),
    # "details" backend slug → resolved by resolve_details_section() at runtime
    "details": (),  # caller must use resolve_details_section() for the archetype-specific slug
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
        Fields not covered by the map are silently ignored (e.g. status, deleted_at).

    Example:
        >>> fields_to_fe_sections(
        ...     archetype=OfferArchetype.PROGRAMA,
        ...     filled_paths=["headline_promise", "value_level", "specific_details.duration"],
        ... )
        {
            "identity": ["headline_promise"],
            "strategy": ["value_level"],
            "program_details": ["specific_details.duration"],
        }
    """
    # Build a reverse lookup: field_name → fe_slug
    _field_to_slug: dict[str, str] = {}
    for slug, fields in OFFER_FIELDS_BY_FE_SECTION.items():
        for field_name in fields:
            _field_to_slug[field_name] = slug

    details_slug = resolve_details_section(archetype)

    result: dict[str, list[str]] = {}
    for path in filled_paths:
        # Handle polymorphic details: any path starting with "specific_details"
        if path == "specific_details" or path.startswith("specific_details."):
            if details_slug:
                result.setdefault(details_slug, [])
                if path not in result[details_slug]:
                    result[details_slug].append(path)
            continue

        # Top-level field lookup
        top_level = path.split(".")[0]
        slug = _field_to_slug.get(top_level)
        if slug:
            result.setdefault(slug, [])
            if path not in result[slug]:
                result[slug].append(path)
        # Fields not in the map (e.g. status, archived_at, deleted_at, metadata_info)
        # are intentionally ignored — they don't correspond to any FE editor section.

    return result
