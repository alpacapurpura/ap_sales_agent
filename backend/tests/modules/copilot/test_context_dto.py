"""Tests for extended ClientContextDTO with focus and interview fields."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.modules.copilot.api.dto import ClientContextDTO, FocusContextDTO


class TestFocusContextDTO:
    def test_valid_focus_context(self) -> None:
        dto = FocusContextDTO(domain="offer", entity_id=str(uuid4()))
        assert dto.domain == "offer"
        assert dto.entity_id is not None

    def test_focus_context_without_entity_id(self) -> None:
        dto = FocusContextDTO(domain="brand")
        assert dto.domain == "brand"
        assert dto.entity_id is None

    def test_focus_context_requires_domain(self) -> None:
        with pytest.raises(ValidationError):
            FocusContextDTO()


class TestClientContextDTOExtended:
    def test_client_context_with_focus(self) -> None:
        dto = ClientContextDTO(
            current_route="/offer-studio/offer/123",
            focus=FocusContextDTO(domain="offer", entity_id="123"),
        )
        assert dto.focus is not None
        assert dto.focus.domain == "offer"

    def test_client_context_with_interview_session_id(self) -> None:
        sid = str(uuid4())
        dto = ClientContextDTO(
            current_route="/brand-studio/interview",
            interview_session_id=sid,
        )
        assert dto.interview_session_id == sid

    def test_client_context_backward_compatible(self) -> None:
        dto = ClientContextDTO(current_route="/brand-studio")
        assert dto.focus is None
        assert dto.interview_session_id is None

    def test_client_context_with_both_focus_and_interview(self) -> None:
        sid = str(uuid4())
        dto = ClientContextDTO(
            current_route="/offer-studio/offer/123",
            focus=FocusContextDTO(domain="offer", entity_id="123"),
            interview_session_id=sid,
        )
        assert dto.focus.domain == "offer"
        assert dto.interview_session_id == sid
