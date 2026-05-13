"""API-layer tests for the ``/clone`` endpoint (Phase 3).

These tests exercise request → DTO validation only; the full clone
service integration is covered in
``tests/modules/offer/application/test_edition_clone_service.py``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from luana_core_offer_studio.api.launch_editions import (
    CloneEditionRequestDTO,
    CloneEditionResponseDTO,
    EditionCloneInputDTO,
)
from luana_core_offer_studio.application.edition_clone_service import CloneStrategy


class TestCloneEditionRequestDTO:
    def test_defaults_to_literal_strategy(self) -> None:
        dto = CloneEditionRequestDTO(
            new_edition_input=EditionCloneInputDTO(
                start_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
            ),
        )
        assert dto.strategy == CloneStrategy.LITERAL
        assert dto.changes_brief is None
        assert dto.attachment_ids is None

    def test_accepts_all_strategies(self) -> None:
        for strategy in ("literal", "date_replace", "ai_regen"):
            dto = CloneEditionRequestDTO(
                strategy=strategy,  # type: ignore[arg-type]
                new_edition_input=EditionCloneInputDTO(
                    start_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
                ),
            )
            assert dto.strategy.value == strategy

    def test_location_override_roundtrip(self) -> None:
        dto = CloneEditionRequestDTO(
            strategy=CloneStrategy.DATE_REPLACE,
            new_edition_input=EditionCloneInputDTO(
                start_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
                location_override={"venue": "Pucallpa Hub"},
            ),
        )
        assert dto.new_edition_input.location_override == {"venue": "Pucallpa Hub"}


class TestCloneEditionResponseDTO:
    def test_empty_asset_ids_default(self) -> None:
        from uuid import uuid4

        from luana_core_offer_studio.api.launch_editions import LaunchEditionResponse

        edition_resp = LaunchEditionResponse(
            id=uuid4(),
            offer_id=uuid4(),
            edition_name="Edición #1",
            edition_number=1,
            timezone="UTC",
            effective_pricing=[],
            currency="USD",
            enrollment_count=0,
            status="draft",
            visibility="private",
            is_placeholder=False,
        )
        response = CloneEditionResponseDTO(edition=edition_resp)
        assert response.asset_ids == []
        assert response.landing_id is None
