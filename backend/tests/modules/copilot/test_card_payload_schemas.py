"""Arch test: every ``CardBlock.card_kind`` literal has a typed payload schema.

Previously ``CardBlock.payload`` was ``dict`` with no per-kind validation.
A malformed clarify/alternatives/proposal payload would slip through to the
frontend and crash the renderer. The registry gives us a single place where
each card_kind names its expected payload shape, plus a warn-only runtime
validator that logs mismatches without rejecting the card (LLM-produced
payloads are best-effort — we degrade gracefully).
"""

from __future__ import annotations

import pytest

from luana_core_copilot.domain.card_payloads import (
    CARD_PAYLOAD_MODELS,
    ClarifyCardPayload,
    validate_card_payload,
)
from luana_core_copilot.domain.message_blocks import CardBlock


def _card_kinds() -> set[str]:
    # Pydantic Literal — pull the allowed values directly.
    field = CardBlock.model_fields["card_kind"]
    return set(field.annotation.__args__)


class TestCardPayloadRegistry:
    def test_every_card_kind_is_registered(self) -> None:
        """The CardBlock discriminator must match the registry exactly —
        no card_kind without a schema, no schema without a card_kind."""
        registered = set(CARD_PAYLOAD_MODELS.keys())
        declared = _card_kinds()
        missing = declared - registered
        extra = registered - declared
        assert not missing, f"card_kinds without schema entry: {missing}"
        assert not extra, f"schema entries for unknown card_kind: {extra}"


class TestClarifyPayload:
    def test_valid_payload_passes(self) -> None:
        payload = {
            "type": "clarify_card",
            "clarify_items": [
                {
                    "field_path": "extraction.scope",
                    "issue": "¿Extraer todo o solo sección?",
                    "options": ["Todo", "Solo sección"],
                },
            ],
        }
        model = ClarifyCardPayload.model_validate(payload)
        assert len(model.clarify_items) == 1
        assert model.clarify_items[0].options == ["Todo", "Solo sección"]

    def test_missing_items_rejected(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ClarifyCardPayload.model_validate({"type": "clarify_card"})


class TestPlanCardPayload:
    """B18-TP9 — plan_card schema introduced for deep-agent ``write_todos``."""

    def test_valid_payload_passes(self) -> None:
        from luana_core_copilot.domain.card_payloads import PlanCardPayload

        payload = {
            "type": "plan_card",
            "todos": [
                {"content": "Auditar identidad", "status": "in_progress", "active_form": ""},
                {"content": "Revisar storytelling", "status": "pending", "active_form": ""},
                {"content": "Sintetizar hallazgos", "status": "completed", "active_form": ""},
            ],
        }
        model = PlanCardPayload.model_validate(payload)
        assert len(model.todos) == 3
        assert model.todos[0].status == "in_progress"
        assert model.todos[2].status == "completed"

    def test_missing_todos_rejected(self) -> None:
        from pydantic import ValidationError

        from luana_core_copilot.domain.card_payloads import PlanCardPayload

        with pytest.raises(ValidationError):
            PlanCardPayload.model_validate({"type": "plan_card"})

    def test_registry_validates_via_validate_card_payload(self) -> None:
        ok, err = validate_card_payload(
            "plan_card",
            {"type": "plan_card", "todos": [{"content": "x", "status": "pending"}]},
        )
        assert ok is True
        assert err is None


class TestValidateCardPayloadWarnOnly:
    def test_valid_payload_returns_true(self) -> None:
        ok, err = validate_card_payload(
            "clarify",
            {
                "type": "clarify_card",
                "clarify_items": [
                    {"field_path": "x", "issue": "y", "options": ["a", "b"]},
                ],
            },
        )
        assert ok is True
        assert err is None

    def test_invalid_payload_returns_false_with_message(self) -> None:
        ok, err = validate_card_payload("clarify", {"type": "clarify_card"})
        assert ok is False
        assert err is not None
        assert "clarify_items" in err

    def test_unknown_card_kind_returns_false(self) -> None:
        ok, err = validate_card_payload("unknown_kind", {})
        assert ok is False
        assert err is not None
