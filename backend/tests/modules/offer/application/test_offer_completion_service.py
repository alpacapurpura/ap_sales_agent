"""Unit tests for OfferCompletionService.

Ports the frontend `getOfferHealth()` logic to backend. Verifies percentages
for empty/partial/complete offers across archetypes.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.modules.offer.application.services.offer_completion_service import (
    OfferCompletionService,
)
from src.modules.offer.domain.enums import (
    GuaranteeType,
    OfferArchetype,
    OfferValueLevel,
)


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def offer_id():
    return uuid4()


def _make_offer(
    *,
    archetype: OfferArchetype = OfferArchetype.PRODUCTO,
    name: str = "Test",
    value_level: OfferValueLevel | None = OfferValueLevel.ACTIVACION,
    headline_promise: str = "",
    target_avatar_match: list | None = None,
    marketing_pain_points: list | None = None,
    marketing_desires: list | None = None,
    pricing_options: list | None = None,
    guarantee_type: GuaranteeType | None = None,
    specific_details: dict | None = None,
    instructors: list | None = None,
):
    offer = MagicMock()
    offer.archetype = archetype
    offer.public_name = name
    offer.value_level = value_level
    offer.headline_promise = headline_promise
    offer.target_avatar_match = target_avatar_match or []
    offer.marketing_pain_points = marketing_pain_points or []
    offer.marketing_desires = marketing_desires or []
    offer.pricing_options = pricing_options or []
    offer.guarantee_type = guarantee_type
    offer.specific_details = specific_details
    offer.instructors = instructors or []
    return offer


@pytest.fixture
def offer_service():
    return MagicMock()


@pytest.fixture
def service(offer_service):
    return OfferCompletionService(offer_service=offer_service)


def test_empty_producto_is_low_completion(service, offer_service, tenant_id, offer_id):
    empty = _make_offer(
        name="",
        value_level=None,
        headline_promise="",
        guarantee_type=None,
    )
    offer_service.get_offer.return_value = empty

    result = service.compute(offer_id=offer_id, tenant_id=tenant_id)
    assert result["percentage"] == 0.0
    assert result["completed_sections"] == 0
    assert result["total_sections"] > 0
    assert result["next_milestone"] is not None


def test_fully_complete_producto_is_100(service, offer_service, tenant_id, offer_id):
    complete = _make_offer(
        name="Complete Offer",
        value_level=OfferValueLevel.ACTIVACION,
        headline_promise="Gran promesa",
        target_avatar_match=["avatar-1"],
        marketing_pain_points=["pain-1"],
        marketing_desires=["desire-1"],
        pricing_options=[{"plan_type": "one_time"}],
        guarantee_type=GuaranteeType.UNCONDITIONAL_30_DAY,
        specific_details={"category": "ebook"},
    )
    offer_service.get_offer.return_value = complete

    result = service.compute(offer_id=offer_id, tenant_id=tenant_id)
    assert result["percentage"] == 100.0
    assert result["completed_sections"] == result["total_sections"]
    assert result["next_milestone"] is None


def test_partial_producto_is_between(service, offer_service, tenant_id, offer_id):
    partial = _make_offer(
        name="Partial",
        value_level=OfferValueLevel.ACTIVACION,
        headline_promise="Promesa",
        target_avatar_match=["avatar"],
        marketing_pain_points=["pain"],
        marketing_desires=["desire"],
        pricing_options=[],  # missing
        guarantee_type=None,  # missing
        specific_details=None,  # missing
    )
    offer_service.get_offer.return_value = partial

    result = service.compute(offer_id=offer_id, tenant_id=tenant_id)
    assert 0 < result["percentage"] < 100


def test_programa_archetype_uses_program_details(
    service,
    offer_service,
    tenant_id,
    offer_id,
):
    offer = _make_offer(
        archetype=OfferArchetype.PROGRAMA,
        name="Prog",
        value_level=OfferValueLevel.TRANSFORMACION,
        headline_promise="Promise",
        target_avatar_match=["a"],
        marketing_pain_points=["p"],
        marketing_desires=["d"],
        pricing_options=[{"plan_type": "payment_plan"}],
        guarantee_type=GuaranteeType.UNCONDITIONAL_30_DAY,
        specific_details={"duration_weeks": 12},
    )
    offer_service.get_offer.return_value = offer

    result = service.compute(offer_id=offer_id, tenant_id=tenant_id)
    assert result["percentage"] == 100.0


def test_compute_not_found_raises(service, offer_service, tenant_id):
    offer_service.get_offer.return_value = None
    with pytest.raises(ValueError, match="not found"):
        service.compute(offer_id=uuid4(), tenant_id=tenant_id)


# ---------------------------------------------------------------------------
# FU-2: section_depth additive narrative coverage metric
# ---------------------------------------------------------------------------


def _make_offer_with_narratives(
    *,
    # promise narratives
    before_state: str | None = None,
    after_state: str | None = None,
    why_now: str | None = None,
    measurable_outcomes: list | None = None,
    # psychology narratives
    objections: list | None = None,
    cultural_trust_barriers: list | None = None,
    emotional_triggers: list | None = None,
    status_drivers: list | None = None,
    regret_scenarios: list | None = None,
    # closing narratives
    refund_process_description: str | None = None,
    urgency_drivers: list | None = None,
    scarcity_reason_honest: str | None = None,
    bonus_if_act_now: str | None = None,
    final_push_copy: str | None = None,
    # baseline required fields (filled by default so % is not affected)
    name: str = "Complete Offer",
    value_level=None,
    headline_promise: str = "Gran promesa",
    target_avatar_match: list | None = None,
    marketing_pain_points: list | None = None,
    marketing_desires: list | None = None,
    pricing_options: list | None = None,
    guarantee_type=None,
    specific_details: dict | None = None,
):
    """Build a MagicMock offer with both narrative and baseline fields."""
    from src.modules.offer.domain.enums import GuaranteeType, OfferValueLevel

    offer = MagicMock()
    offer.archetype = OfferArchetype.PRODUCTO
    offer.public_name = name
    offer.value_level = value_level if value_level is not None else OfferValueLevel.ACTIVACION
    offer.headline_promise = headline_promise
    offer.target_avatar_match = target_avatar_match if target_avatar_match is not None else ["avatar-1"]
    offer.marketing_pain_points = marketing_pain_points if marketing_pain_points is not None else ["pain-1"]
    offer.marketing_desires = marketing_desires if marketing_desires is not None else ["desire-1"]
    offer.pricing_options = pricing_options if pricing_options is not None else [{"plan_type": "one_time"}]
    offer.guarantee_type = guarantee_type if guarantee_type is not None else GuaranteeType.UNCONDITIONAL_30_DAY
    offer.specific_details = specific_details if specific_details is not None else {"category": "ebook"}
    offer.instructors = []
    # narrative fields
    offer.before_state = before_state
    offer.after_state = after_state
    offer.why_now = why_now
    offer.measurable_outcomes = measurable_outcomes or []
    offer.objections = objections or []
    offer.cultural_trust_barriers = cultural_trust_barriers or []
    offer.emotional_triggers = emotional_triggers or []
    offer.status_drivers = status_drivers or []
    offer.regret_scenarios = regret_scenarios or []
    offer.refund_process_description = refund_process_description
    offer.urgency_drivers = urgency_drivers or []
    offer.scarcity_reason_honest = scarcity_reason_honest
    offer.bonus_if_act_now = bonus_if_act_now
    offer.final_push_copy = final_push_copy
    return offer


class TestSectionDepth:
    """FU-2 — section_depth additive metric (zero baseline regression)."""

    def test_section_depth_empty_offer_reports_zero_filled(self, service, offer_service, tenant_id, offer_id):
        """Offer with no narrative fields → filled=0 for all narrative sections."""
        offer = _make_offer_with_narratives()
        offer_service.get_offer.return_value = offer

        result = service.compute(offer_id=offer_id, tenant_id=tenant_id)

        depth = result["section_depth"]
        assert "promise" in depth
        assert "psychology" in depth
        assert "closing" in depth
        assert depth["promise"]["filled"] == 0
        assert depth["psychology"]["filled"] == 0
        assert depth["closing"]["filled"] == 0

    def test_section_depth_full_narratives(self, service, offer_service, tenant_id, offer_id):
        """Offer with all 13 narrative fields filled → filled=total for each section."""
        offer = _make_offer_with_narratives(
            before_state="antes",
            after_state="después",
            why_now="razón",
            measurable_outcomes=["resultado 1"],
            objections=[{"type": "price"}],
            cultural_trust_barriers=["barrera 1"],
            emotional_triggers=["trigger 1"],
            status_drivers=["driver 1"],
            regret_scenarios=["escenario 1"],
            refund_process_description="proceso",
            urgency_drivers=["urgencia 1"],
            scarcity_reason_honest="razón escasez",
            bonus_if_act_now="bonus",
            final_push_copy="cierre",
        )
        offer_service.get_offer.return_value = offer

        result = service.compute(offer_id=offer_id, tenant_id=tenant_id)
        depth = result["section_depth"]

        assert depth["promise"]["filled"] == depth["promise"]["total"]
        assert depth["psychology"]["filled"] == depth["psychology"]["total"]
        assert depth["closing"]["filled"] == depth["closing"]["total"]

    def test_percentage_unchanged_when_narratives_filled(self, service, offer_service, tenant_id, offer_id):
        """REGRESSION LOCK: filling narrative fields MUST NOT change the % completion.

        This is the contract invariant: narrative fields are additive signals,
        not baseline requirements. A fully-complete offer stays at 100% whether
        narratives are present or absent.
        """
        # Baseline: complete offer without narratives
        baseline = _make_offer_with_narratives()
        offer_service.get_offer.return_value = baseline
        baseline_result = service.compute(offer_id=offer_id, tenant_id=tenant_id)

        # Same offer but with all narratives filled
        enriched = _make_offer_with_narratives(
            before_state="antes",
            after_state="después",
            why_now="razón",
            measurable_outcomes=["resultado 1"],
            cultural_trust_barriers=["barrera"],
            emotional_triggers=["trigger"],
            status_drivers=["driver"],
            regret_scenarios=["escenario"],
            refund_process_description="proceso",
            urgency_drivers=["urgencia"],
            scarcity_reason_honest="escasez",
            bonus_if_act_now="bonus",
            final_push_copy="cierre",
        )
        offer_service.get_offer.return_value = enriched
        enriched_result = service.compute(offer_id=offer_id, tenant_id=tenant_id)

        assert baseline_result["percentage"] == 100.0
        assert enriched_result["percentage"] == 100.0
        assert baseline_result["percentage"] == enriched_result["percentage"]

    def test_percentage_unchanged_when_narratives_empty(self, service, offer_service, tenant_id, offer_id):
        """REGRESSION LOCK: empty narratives do NOT reduce % below baseline.

        An offer meeting all required field criteria must stay at 100% even
        when every narrative field is absent.
        """
        offer = _make_offer_with_narratives()  # all narratives default to empty
        offer_service.get_offer.return_value = offer

        result = service.compute(offer_id=offer_id, tenant_id=tenant_id)
        assert result["percentage"] == 100.0

    def test_section_depth_partial_psychology(self, service, offer_service, tenant_id, offer_id):
        """Exactly 2 of 5 psychology narratives filled → depth_pct = 40.0."""
        offer = _make_offer_with_narratives(
            cultural_trust_barriers=["barrera"],
            emotional_triggers=["trigger"],
            # objections, status_drivers, regret_scenarios left empty
        )
        offer_service.get_offer.return_value = offer

        result = service.compute(offer_id=offer_id, tenant_id=tenant_id)
        depth = result["section_depth"]["psychology"]

        assert depth["filled"] == 2
        assert depth["total"] == 5
        assert depth["depth_pct"] == 40.0

    def test_compute_result_contains_section_depth_key(self, service, offer_service, tenant_id, offer_id):
        """compute() result always contains 'section_depth' key (backward-compat)."""
        offer = _make_offer_with_narratives()
        offer_service.get_offer.return_value = offer

        result = service.compute(offer_id=offer_id, tenant_id=tenant_id)
        assert "section_depth" in result
        assert isinstance(result["section_depth"], dict)
