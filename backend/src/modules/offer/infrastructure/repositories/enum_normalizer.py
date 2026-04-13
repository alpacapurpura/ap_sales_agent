"""Pure functions for normalizing legacy enum values from DB to domain enums.

All functions are pure (no side effects, no DB access) and can be tested in isolation.
"""

import contextlib

from src.modules.offer.domain.enums import (
    DeliverableFormat,
    GuaranteeType,
    OfferArchetype,
    OfferDeliveryModel,
    OfferStatus,
    OfferValueLevel,
    PaymentPlanType,
)
from src.shared.domain.enums import FinancialCapacity


def normalize_value_level(raw: str | None) -> OfferValueLevel | None:
    if not raw:
        return None
    try:
        return OfferValueLevel(raw)
    except ValueError:
        try:
            return OfferValueLevel(raw.lower())
        except ValueError:
            return None


def normalize_delivery_model(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        OfferDeliveryModel(raw)
        return raw
    except ValueError:
        try:
            lowered = raw.lower()
            OfferDeliveryModel(lowered)
            return lowered
        except ValueError:
            return None


def normalize_guarantee_type(raw: str | None) -> str:
    value = raw or "none"
    if value.upper() == "NO_REFUNDS":
        return "none"
    try:
        GuaranteeType(value)
        return value
    except ValueError:
        try:
            lowered = value.lower()
            GuaranteeType(lowered)
            return lowered
        except ValueError:
            return "none"


def normalize_archetype(raw: str, offer_id=None) -> OfferArchetype:
    try:
        return OfferArchetype(raw)
    except ValueError:
        try:
            return OfferArchetype(raw.lower())
        except (ValueError, AttributeError):
            import structlog

            structlog.get_logger().warning(
                "invalid_archetype",
                raw=raw,
                offer_id=str(offer_id),
            )
            msg = f"Invalid OfferArchetype in DB: {raw}"
            raise ValueError(msg) from None


def normalize_status(raw: str | None) -> OfferStatus:
    if not raw:
        return OfferStatus.DRAFT
    return OfferStatus(raw.lower())


def normalize_financial_capacity(raw: str | None) -> FinancialCapacity:
    value = raw or FinancialCapacity.LOW_INCOME
    if value == "LOW":
        return FinancialCapacity.LOW_INCOME
    return value


def normalize_pricing_options(pricing_raw: list) -> list[dict]:
    """Normalize legacy plan_type values in pricing JSONB."""
    result = []
    for p in pricing_raw:
        if not isinstance(p, dict):
            result.append(p)
            continue
        new_p = p.copy()
        plan_type = new_p.get("plan_type")
        if plan_type == "PAY_IN_FULL":
            new_p["plan_type"] = "one_time"
        elif plan_type in ("SPLIT_PAY", "split_pay"):
            new_p["plan_type"] = "payment_plan"
        if new_p.get("plan_type"):
            try:
                PaymentPlanType(new_p["plan_type"])
            except ValueError:
                with contextlib.suppress(ValueError, AttributeError):
                    new_p["plan_type"] = new_p["plan_type"].lower()
        result.append(new_p)
    return result


def normalize_deliverables(deliverables_raw: list) -> list[dict]:
    """Normalize legacy format values in deliverables JSONB."""
    result = []
    for d in deliverables_raw:
        if not isinstance(d, dict):
            result.append(d)
            continue
        new_d = d.copy()
        fmt = new_d.get("format")
        if fmt == "LIVE_GROUP_CALL":
            new_d["format"] = "live_session"
        elif fmt:
            try:
                DeliverableFormat(fmt)
            except ValueError:
                with contextlib.suppress(ValueError, AttributeError):
                    new_d["format"] = fmt.lower()
        result.append(new_d)
    return result


_DETAILS_REPLACEMENTS = {
    "format": {"RECORDED_CONTENT": "video_course"},
    "structure_type": {"FIXED_COHORT": "fixed_cohort"},
    "interaction_type": {"LIVE_PROGRAM_DELIVERY": "group_q_and_a"},
    "community_platform": {"ZOOM": "none"},
    "location_type": {
        "VIRTUAL": "virtual",
        "DESTINATION_RETREAT": "destination_retreat",
    },
}


def normalize_specific_details(details_json: dict) -> dict:
    """Normalize legacy uppercase values in specific_details JSONB."""
    if not details_json:
        return details_json
    result = details_json.copy()
    for field, replacements in _DETAILS_REPLACEMENTS.items():
        if field in result and result[field] in replacements:
            result[field] = replacements[result[field]]
    return result
