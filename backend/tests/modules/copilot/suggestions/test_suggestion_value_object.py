"""TDD — domain value objects for suggestion engine.

Tests written RED first per ``tdd-mandatory.md``.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest


class TestSuggestionCategory:
    def test_values_match_fe_locked_contract(self) -> None:
        """FE TS union: 'followup' | 'action' | 'clarify' | 'nav'."""
        from src.modules.copilot.domain.suggestion import SuggestionCategory

        assert SuggestionCategory.FOLLOWUP == "followup"
        assert SuggestionCategory.ACTION == "action"
        assert SuggestionCategory.CLARIFY == "clarify"
        assert SuggestionCategory.NAV == "nav"


class TestSuggestionContext:
    def test_tenant_id_is_required_uuid(self) -> None:
        from src.modules.copilot.domain.suggestion import SuggestionContext

        tenant = uuid4()
        ctx = SuggestionContext(
            tenant_id=tenant,
            user_id=None,
            conversation_id=None,
            current_route=None,
        )
        assert ctx.tenant_id == tenant

    def test_defaults_are_empty_tuples(self) -> None:
        from src.modules.copilot.domain.suggestion import SuggestionContext

        ctx = SuggestionContext(
            tenant_id=uuid4(),
            user_id=None,
            conversation_id=None,
            current_route="offer-studio",
        )
        assert ctx.recent_message_ids == ()
        assert ctx.incomplete_fields == ()
        assert ctx.locale == "es"

    def test_context_is_frozen(self) -> None:
        from src.modules.copilot.domain.suggestion import SuggestionContext

        ctx = SuggestionContext(
            tenant_id=uuid4(),
            user_id=None,
            conversation_id=None,
            current_route=None,
        )
        with pytest.raises((AttributeError, TypeError)):
            ctx.current_route = "brand-studio"  # type: ignore[misc]


class TestSuggestionInvariants:
    def test_confidence_below_zero_raises(self) -> None:
        from src.modules.copilot.domain.suggestion import Suggestion

        with pytest.raises(ValueError, match="confidence"):
            Suggestion(label="Hola", prompt="Hola", confidence=-0.1)

    def test_confidence_above_one_raises(self) -> None:
        from src.modules.copilot.domain.suggestion import Suggestion

        with pytest.raises(ValueError, match="confidence"):
            Suggestion(label="Hola", prompt="Hola", confidence=1.1)

    def test_confidence_boundary_zero_ok(self) -> None:
        from src.modules.copilot.domain.suggestion import Suggestion

        s = Suggestion(label="Hola", prompt="Hola", confidence=0.0)
        assert s.confidence == 0.0

    def test_confidence_boundary_one_ok(self) -> None:
        from src.modules.copilot.domain.suggestion import Suggestion

        s = Suggestion(label="Hola", prompt="Hola", confidence=1.0)
        assert s.confidence == 1.0

    def test_label_exceeds_60_chars_raises(self) -> None:
        from src.modules.copilot.domain.suggestion import Suggestion

        long_label = "A" * 61
        with pytest.raises(ValueError, match="label"):
            Suggestion(label=long_label, prompt="ok", confidence=0.5)

    def test_label_exactly_60_chars_ok(self) -> None:
        from src.modules.copilot.domain.suggestion import Suggestion

        label = "A" * 60
        s = Suggestion(label=label, prompt="ok", confidence=0.5)
        assert len(s.label) == 60

    def test_empty_label_raises(self) -> None:
        from src.modules.copilot.domain.suggestion import Suggestion

        with pytest.raises(ValueError, match="required"):
            Suggestion(label="", prompt="ok", confidence=0.5)

    def test_whitespace_label_raises(self) -> None:
        from src.modules.copilot.domain.suggestion import Suggestion

        with pytest.raises(ValueError, match="required"):
            Suggestion(label="   ", prompt="ok", confidence=0.5)

    def test_empty_prompt_raises(self) -> None:
        from src.modules.copilot.domain.suggestion import Suggestion

        with pytest.raises(ValueError, match="required"):
            Suggestion(label="ok", prompt="", confidence=0.5)

    def test_suggestion_has_uuid_id(self) -> None:
        from src.modules.copilot.domain.suggestion import Suggestion

        s = Suggestion(label="ok", prompt="ok", confidence=0.5)
        assert isinstance(s.id, UUID)

    def test_suggestion_is_frozen(self) -> None:
        from src.modules.copilot.domain.suggestion import Suggestion

        s = Suggestion(label="ok", prompt="ok", confidence=0.5)
        with pytest.raises((AttributeError, TypeError)):
            s.label = "changed"  # type: ignore[misc]

    def test_default_category_is_action(self) -> None:
        from src.modules.copilot.domain.suggestion import Suggestion, SuggestionCategory

        s = Suggestion(label="ok", prompt="ok", confidence=0.5)
        assert s.category == SuggestionCategory.ACTION


class TestSuggestionEvents:
    def test_suggestion_shown_create_builds_payload(self) -> None:
        from src.modules.copilot.domain.events import SuggestionShown

        tenant = uuid4()
        sid1, sid2 = uuid4(), uuid4()
        event = SuggestionShown.create(
            tenant_id=tenant,
            user_id=None,
            conversation_id=None,
            current_route="offer-studio",
            suggestion_ids=[sid1, sid2],
            provider_breakdown={"offer": 2},
            latency_ms=5,
        )
        assert event.event_name == "copilot_suggestion_shown"
        assert event.tenant_id == tenant
        payload = event.payload
        assert payload["current_route"] == "offer-studio"
        assert len(payload["suggestion_ids"]) == 2
        assert payload["provider_breakdown"] == {"offer": 2}
        assert payload["latency_ms"] == 5

    def test_suggestion_accepted_create_builds_payload(self) -> None:
        from src.modules.copilot.domain.events import SuggestionAccepted

        tenant = uuid4()
        sid = uuid4()
        event = SuggestionAccepted.create(
            tenant_id=tenant,
            user_id=None,
            conversation_id=None,
            suggestion_id=sid,
            source_module="offer",
            category="action",
        )
        assert event.event_name == "copilot_suggestion_accepted"
        assert event.payload["suggestion_id"] == str(sid)
        assert event.payload["source_module"] == "offer"
        assert event.payload["category"] == "action"
