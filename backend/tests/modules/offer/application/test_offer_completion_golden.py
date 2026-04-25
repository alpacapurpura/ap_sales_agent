"""Golden snapshot for ``OfferCompletionService.compute()``.

Locks ``percentage`` / ``completed_sections`` / ``total_sections`` /
``next_milestone`` / ``section_depth`` for synthetic offers covering
each archetype + an empty offer per archetype. Future refactors must
keep this file green to prove that completion semantics didn't drift.

Refresh: ``REFRESH_GOLDEN=1 .venv/bin/pytest tests/modules/offer/application/test_offer_completion_golden.py``.

Workspace: ``docs/refactors/field-contract-platform/`` Fase 05.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from src.modules.offer.application.services.offer_completion_service import (
    _compute_section_depth,
    _sections_for,
    _validate_section,
)
from src.modules.offer.domain.enums import OfferArchetype

GOLDEN_PATH = Path(__file__).parent / "fixtures" / "offer_completion_golden.json"


class _StubOffer:
    """Lightweight stand-in for ``Offer`` used by completion validators."""

    def __init__(self, **fields: Any) -> None:
        self.__dict__.update(fields)


def _full_offer(archetype: OfferArchetype) -> _StubOffer:
    return _StubOffer(
        public_name="Programa Alquimia LATAM",
        archetype=archetype.value,
        value_level="transformacion",
        target_avatar_match=[uuid4()],
        marketing_pain_points=["dolor 1", "dolor 2"],
        marketing_desires=["deseo 1", "deseo 2"],
        headline_promise="Promesa principal",
        before_state="estado previo",
        after_state="estado posterior",
        why_now="razón temporal",
        measurable_outcomes=["+250%"],
        objections=[{"type": "precio"}],
        cultural_trust_barriers=["barrera"],
        emotional_triggers=["miedo"],
        status_drivers=["estatus"],
        regret_scenarios=["arrepentimiento"],
        urgency_drivers=["urgencia"],
        scarcity_reason_honest="escasez",
        bonus_if_act_now="bonus",
        final_push_copy="cierre",
        refund_process_description="reembolso",
        guarantee_type="money_back",
        guarantee_terms="14 días",
        pricing_options=[{"label": "único", "total_amount": 1497}],
        deliverables=[{"name": "sesión 1"}],
        instructors=[{"name": "Coach"}],
        specific_details={"duration_weeks": 12, "schedule": [{"day": "lunes"}]},
    )


def _empty_offer(archetype: OfferArchetype) -> _StubOffer:
    return _StubOffer(
        public_name=None,
        archetype=archetype.value,
        value_level=None,
        target_avatar_match=None,
        marketing_pain_points=[],
        marketing_desires=[],
        headline_promise=None,
        pricing_options=[],
        deliverables=[],
        guarantee_type=None,
        instructors=[],
        specific_details=None,
    )


def _compute_for(offer: _StubOffer) -> dict[str, Any]:
    sections = _sections_for(getattr(offer, "archetype", None))
    completed = 0
    total = 0
    next_milestone: str | None = None
    section_status: dict[str, str] = {}

    for section_id in sections:
        status = _validate_section(section_id, offer)
        section_status[section_id] = status
        if status == "optional":
            continue
        total += 1
        if status == "complete":
            completed += 1
        elif next_milestone is None:
            next_milestone = section_id

    if total == 0:
        percentage = 100.0
    else:
        percentage = round((completed / total) * 100.0, 2)
        if percentage.is_integer():
            percentage = float(int(percentage))

    return {
        "percentage": percentage,
        "completed_sections": completed,
        "total_sections": total,
        "next_milestone": next_milestone,
        "section_status": section_status,
        "section_depth": _compute_section_depth(offer),
    }


def _produce_golden() -> dict[str, Any]:
    return {
        archetype.value: {
            "full": _compute_for(_full_offer(archetype)),
            "empty": _compute_for(_empty_offer(archetype)),
        }
        for archetype in OfferArchetype
    }


def test_completion_byte_identical_to_golden() -> None:
    actual = _produce_golden()

    if os.environ.get("REFRESH_GOLDEN") == "1":
        GOLDEN_PATH.write_text(
            json.dumps(actual, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        pytest.skip("Refreshed golden — re-run without REFRESH_GOLDEN=1 to validate.")

    assert GOLDEN_PATH.exists(), (
        f"Missing golden at {GOLDEN_PATH}. Generate via "
        "REFRESH_GOLDEN=1 .venv/bin/pytest tests/modules/offer/application/test_offer_completion_golden.py"
    )

    expected = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert actual == expected, (
        "Completion service output drift detected vs golden snapshot. "
        "If intentional, refresh with REFRESH_GOLDEN=1 and audit the diff."
    )
