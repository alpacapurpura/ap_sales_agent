"""LLM extraction wave output schemas — application layer.

These Pydantic schemas define the structured output contracts for each
extraction wave. They re-expose the domain Update models as named wave
outputs so the orchestrator and tests can reference them by their wave role,
not just their update role.

Architecture note: schemas live in the *application* layer (NOT domain)
because they represent a concern of the extraction use-case, not of the
core domain. Domain layer owns ``OfferPromiseUpdate`` etc. as update
value-objects; here we name them per-wave for caller clarity.

All ``Field(description=...)`` annotations come from the domain classes
already — no duplication needed here.

Wave assignment:
  - W1: promise, strategy
  - W2: psychology, value_stack, closing
  - W3: details
"""

from __future__ import annotations

from src.modules.offer.domain.offer import (
    ObjectionItem,
    OfferClosingUpdate,
    OfferDetailsUpdate,
    OfferPromiseUpdate,
    OfferPsychologyUpdate,
    OfferStrategyUpdate,
    OfferValueStackUpdate,
)

# ---------------------------------------------------------------------------
# Wave output type aliases (named by wave role for clarity in orchestrator /
# tests / future structured-output wiring).
# ---------------------------------------------------------------------------

#: W1 — promise wave output.
#: Fields: headline_promise, primary_outcome, time_to_value,
#:         before_state, after_state, why_now, measurable_outcomes.
PromiseWaveOutput = OfferPromiseUpdate

#: W1 — strategy wave output.
#: Fields: value_level (serialized as offer_value_level), delivery_model.
StrategyWaveOutput = OfferStrategyUpdate

#: W2 — psychology wave output.
#: Fields: target_avatar_match, anti_avatar_keywords, marketing_pain_points,
#:         marketing_desires, objections (structured ObjectionItem[]),
#:         cultural_trust_barriers, emotional_triggers, status_drivers,
#:         regret_scenarios.
PsychologyWaveOutput = OfferPsychologyUpdate

#: W2 — value stack wave output.
#: Fields: deliverables (DeliverableItem[]), includes_offers (UUID[]).
ValueStackWaveOutput = OfferValueStackUpdate

#: W2 — closing wave output.
#: Fields: guarantee_type, guarantee_terms, checkout_page_url,
#:         calendar_type_id, onboarding_action, onboarding_url,
#:         downsell_offer_id, upsell_offer_id,
#:         refund_process_description, urgency_drivers, scarcity_reason_honest,
#:         bonus_if_act_now, final_push_copy, support_duration_days.
ClosingWaveOutput = OfferClosingUpdate

#: W3 — details wave output (polymorphic: delegates to archetype-specific models).
DetailsWaveOutput = OfferDetailsUpdate

# Re-export ObjectionItem for use in tests without cross-layer imports.
__all__ = [
    "ClosingWaveOutput",
    "DetailsWaveOutput",
    "ObjectionItem",
    "PromiseWaveOutput",
    "PsychologyWaveOutput",
    "StrategyWaveOutput",
    "ValueStackWaveOutput",
]
