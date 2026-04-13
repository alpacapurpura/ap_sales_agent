"""Domain-layer declaration of which Offer fields the copilot may write.

Keeping this constant in the domain layer lets schema_introspection.py
(also domain) reference it without crossing into infrastructure. The
OfferPersister (infrastructure) imports from here too, so there is a
single source of truth.
"""

from __future__ import annotations

# All Offer entity fields that the interview can write to.
# Excludes system fields (id, tenant_id, status, deleted_at, etc.)
PERSISTABLE_FIELDS: set[str] = {
    "public_name",
    "archetype",
    "format_hint",
    "value_level",
    "delivery_model",
    "headline_promise",
    "primary_outcome",
    "time_to_value",
    "target_avatar_match",
    "marketing_pain_points",
    "marketing_desires",
    "objections",
    "pricing_options",
    "price_pay_in_full",
    "guarantee_type",
    "guarantee_terms",
    "deliverables",
    "includes_offers",
    "access_duration_text",
    "support_duration_days",
    "onboarding_action",
    "prerequisites",
    "requires_application",
    "anti_avatar_keywords",
    "currency",
}
