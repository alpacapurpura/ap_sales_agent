"""Per-archetype landing content builders (FU-1).

Pure module-level functions — no Session, no ORM, no FastAPI.
They receive a Mapping[str, Any] representing a SQL row and return
a typed content object (or None when required fields are missing).

Used exclusively by ``landing_service.generate_landing_for_offer``.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

from luana_core_landing.domain.content import (
    BaseEntity,
    BrochureContent,
    EventContent,
    FeatureBullet,
    FlashOfferContent,
    SqueezeContent,
    TransformerContent,
    VelvetRopeContent,
)
from luana_core_landing.domain.enums import LandingPageArchetype

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_list(raw: object) -> list:
    """Safely parse a JSONB list column to a Python list.

    Handles:
    - ``None`` → ``[]``
    - Already a ``list`` / ``tuple`` → return as list
    - JSON string → parse and return list (or ``[]`` on error)
    """
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return list(raw)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def _parse_dict(raw: object) -> dict:
    """Safely parse a JSONB dict column to a Python dict."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def _deliverables_to_bullets(raw: object) -> list[FeatureBullet]:
    """Convert raw JSONB deliverables to a list of FeatureBullet."""
    items = _parse_list(raw)
    bullets: list[FeatureBullet] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or ""
        if not name:
            continue
        description = item.get("fulfillment_note") or item.get("description") or None
        bullets.append(FeatureBullet(title=name, description=description))
    return bullets


# ---------------------------------------------------------------------------
# Archetype content builders
# ---------------------------------------------------------------------------


def _build_squeeze_content(data: Mapping[str, Any]) -> SqueezeContent:
    """Build enhanced SQUEEZE content; prefers narrative fields when available.

    Never returns None — SQUEEZE is the universal fallback.
    """
    name: str = data.get("name") or "Mi oferta"
    headline: str = data.get("headline_promise") or f"Descubre {name}"
    # subheadline: prefer after_state > primary_outcome > generic
    subheadline: str = data.get("after_state") or data.get("primary_outcome") or "Transforma tu vida hoy"

    # bullets: prefer measurable_outcomes[:3] > pain_points[:3] > fallback
    measurable = _parse_list(data.get("measurable_outcomes"))
    pains = _parse_list(data.get("marketing_pain_points"))

    if measurable:
        bullets: list[str] = [str(m) for m in measurable[:3]]
    elif pains:
        bullets = [str(p) for p in pains[:3]]
    else:
        bullets = [
            "Resuelve tu problema",
            "Ahorra tiempo",
            "Logra resultados",
        ]

    return SqueezeContent(
        headline=headline,
        subheadline=subheadline,
        bullets=bullets,
        cta_text="Quiero esto ahora",
        privacy_text="Cuidamos tus datos.",
    )


def _build_transformer_content(data: Mapping[str, Any]) -> TransformerContent | None:
    """Build high-ticket TRANSFORMER content.

    Returns None when required fields are missing — caller falls back to SQUEEZE.

    Required: headline_promise, deliverables (at least 1 item), pricing.
    """
    headline: str | None = data.get("headline_promise")
    if not headline:
        return None

    raw_deliverables = data.get("deliverables")
    modules = _deliverables_to_bullets(raw_deliverables)
    if not modules:
        return None

    pricing_raw = data.get("pricing")
    pricing = _parse_dict(pricing_raw)
    if not pricing:
        return None

    # Derive price strings from pricing dict
    pay_full = pricing.get("pay_in_full")
    price_str = f"${pay_full:,.0f}" if pay_full else "Consultar"

    # Narrative fields (optional, with fallbacks)
    subheadline: str = data.get("after_state") or data.get("primary_outcome") or ""
    _pains = _parse_list(data.get("marketing_pain_points"))
    problem_text: str = data.get("before_state") or (_pains[0] if _pains else "")
    regret = _parse_list(data.get("regret_scenarios"))
    agitation_text: str = regret[0] if regret else (data.get("why_now") or "")
    solution_text: str = data.get("after_state") or data.get("primary_outcome") or ""
    method_name: str = data.get("name") or ""
    method_description: str = data.get("final_push_copy") or data.get("primary_outcome") or ""
    urgency_drivers = _parse_list(data.get("urgency_drivers"))
    scarcity_text: str = data.get("scarcity_reason_honest") or (
        urgency_drivers[0] if urgency_drivers else "Cupos limitados"
    )

    return TransformerContent(
        headline=headline,
        subheadline=subheadline,
        problem_text=problem_text,
        agitation_text=agitation_text,
        solution_text=solution_text,
        method_name=method_name,
        method_description=method_description,
        authority_name="",
        authority_bio="",
        modules=modules,
        bonuses=[],
        price_anchor=price_str,
        price_offer=price_str,
        scarcity_text=scarcity_text,
    )


def _build_brochure_content(data: Mapping[str, Any]) -> BrochureContent | None:
    """Build B2B BROCHURE content from deliverables.

    Returns None when headline_promise or deliverables are missing.
    """
    headline: str | None = data.get("headline_promise")
    if not headline:
        return None

    modules = _deliverables_to_bullets(data.get("deliverables"))
    if not modules:
        return None

    process_steps = modules[:6]
    deliverables_list = [b.title for b in modules]

    return BrochureContent(
        headline=headline,
        process_steps=process_steps,
        deliverables=deliverables_list,
        case_studies=[],
    )


def _build_velvet_rope_content(data: Mapping[str, Any]) -> VelvetRopeContent | None:
    """Build high-ticket VELVET ROPE content.

    Returns None when headline_promise or marketing_desires are missing.
    """
    headline: str | None = data.get("headline_promise")
    if not headline:
        return None

    desires = _parse_list(data.get("marketing_desires"))
    if not desires:
        return None

    manifesto: str = data.get("why_now") or data.get("after_state") or data.get("primary_outcome") or ""

    anti_avatar = _parse_list(data.get("anti_avatar_keywords"))

    urgency_drivers = _parse_list(data.get("urgency_drivers"))
    scarcity_text: str = data.get("scarcity_reason_honest") or (
        urgency_drivers[0] if urgency_drivers else "Cupos limitados"
    )

    return VelvetRopeContent(
        headline=headline,
        manifesto_text=manifesto,
        who_is_this_for=[str(d) for d in desires[:5]],
        who_is_NOT_for=[str(k) for k in anti_avatar],
        scarcity_text=scarcity_text,
    )


def _build_event_content(data: Mapping[str, Any]) -> EventContent | None:
    """Build EVENT content.

    NOTE: The Offer aggregate does not carry ``event_date`` today (Sprint 14).
    This builder always returns None until a future sprint exposes event_date
    on the Offer entity. Callers fall back to SQUEEZE automatically.
    """
    # Future sprint: extract event_date from specific_details.start_date when
    # EventDetails is propagated to this SQL query.
    return None


def _build_flash_offer_content(data: Mapping[str, Any]) -> FlashOfferContent | None:
    """Build FLASH OFFER (tripwire) content.

    Requires ``original_price`` and ``discounted_price`` in the ``pricing``
    JSONB column. Returns None when those keys are absent.
    """
    headline: str | None = data.get("headline_promise")
    if not headline:
        return None

    pricing = _parse_dict(data.get("pricing"))
    original_price = pricing.get("original_price")
    discounted_price = pricing.get("discounted_price")

    if original_price is None or discounted_price is None:
        return None

    name: str = data.get("name") or "Oferta especial"

    return FlashOfferContent(
        headline=headline,
        offer_name=name,
        problem_agitation=data.get("before_state") or "",
        solution_description=data.get("after_state") or data.get("primary_outcome") or "",
        original_price=float(original_price),
        discounted_price=float(discounted_price),
    )


# ---------------------------------------------------------------------------
# Strategy mapping and resolver
# ---------------------------------------------------------------------------

_CONTENT_BUILDERS: dict[
    LandingPageArchetype,
    Callable[[Mapping[str, Any]], BaseEntity | None],
] = {
    LandingPageArchetype.THE_SQUEEZE: _build_squeeze_content,  # type: ignore[dict-item]
    LandingPageArchetype.THE_TRANSFORMER: _build_transformer_content,
    LandingPageArchetype.THE_BROCHURE: _build_brochure_content,
    LandingPageArchetype.THE_VELVET_ROPE: _build_velvet_rope_content,
    LandingPageArchetype.THE_EVENT: _build_event_content,
    LandingPageArchetype.THE_FLASH_OFFER: _build_flash_offer_content,
}


def _resolve_content(
    archetype: LandingPageArchetype,
    data: Mapping[str, Any],
) -> tuple[LandingPageArchetype, BaseEntity]:
    """Build content for ``archetype``; fall back to SQUEEZE if builder returns None.

    Returns:
        (actual_archetype_used, content). The archetype may downgrade to
        ``THE_SQUEEZE`` when the specific builder cannot produce a result due
        to missing required fields.
    """
    builder = _CONTENT_BUILDERS.get(archetype)
    if builder is not None:
        content = builder(data)
        if content is not None:
            return archetype, content

    logger.debug(
        "landing_content_builder_fallback",
        requested_archetype=archetype,
        fallback=LandingPageArchetype.THE_SQUEEZE,
    )
    squeeze = _build_squeeze_content(data)
    return LandingPageArchetype.THE_SQUEEZE, squeeze


__all__ = [
    "_CONTENT_BUILDERS",
    "_build_brochure_content",
    "_build_event_content",
    "_build_flash_offer_content",
    "_build_squeeze_content",
    "_build_transformer_content",
    "_build_velvet_rope_content",
    "_parse_list",
    "_resolve_content",
]
