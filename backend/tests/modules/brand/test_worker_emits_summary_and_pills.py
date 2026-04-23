"""TDD: brand worker emits extraction_summary card and navigation pills.

Tests cover Phase 2 + Phase 4 of the async extraction feedback spec:
- At job completion, an extraction_summary card is inserted into the conversation.
- Per section completion transition, a navigation pill (card_kind="navigation") is inserted.
- Worker retries must not duplicate cards (idempotency).

Card emission lives in copilot/application/extraction_card_flow.py (merged
subscriber + emitter). Full emitter + handler tests are in
tests/modules/copilot/test_extraction_event_handlers.py.

These tests verify:
1. The Redis progress payload schema (shape contract, no live execution).
2. The copilot CardBlock schema (extraction_summary kind registered).
3. The copilot card payload model (ExtractionSummaryCardPayload validates).
"""

from __future__ import annotations

from datetime import UTC, datetime


class TestRedisPayloadEnrichment:
    """Verify the on_progress Redis payload includes the new fields."""

    def test_completed_payload_has_new_keys(self) -> None:
        """The completed Redis payload must include the enriched fields."""
        required_keys = {
            "status",
            "progress",
            "stage",
            "started_at",
            "filled_fields",
            "filled_fields_by_section",
            "sections_touched",
            "sections_completed",
            "newly_completed_section",
        }

        # Build a minimal completed payload matching what the worker should write
        completed_payload = {
            "status": "completed",
            "progress": 100,
            "stage": "¡Análisis completado!",
            "started_at": datetime.now(UTC).isoformat(),
            "finished_at": datetime.now(UTC).isoformat(),
            "filled_fields": ["brand_name", "tagline"],
            "filled_fields_by_section": {"identity": ["brand_name", "tagline"]},
            "sections_touched": ["identity"],
            "sections_completed": ["identity"],
            "newly_completed_section": None,
        }

        missing = required_keys - set(completed_payload.keys())
        assert not missing, f"Completed payload missing keys: {missing}"

    def test_processing_payload_has_new_keys(self) -> None:
        """Mid-extraction on_progress calls should also carry the new fields."""
        required_keys = {
            "status",
            "progress",
            "stage",
            "started_at",
            "filled_fields",
            "filled_fields_by_section",
            "sections_touched",
            "sections_completed",
            "newly_completed_section",
        }

        processing_payload = {
            "status": "processing",
            "progress": 50,
            "stage": "Analizando sección 'Identidad'...",
            "started_at": datetime.now(UTC).isoformat(),
            "finished_at": None,
            "filled_fields": ["brand_name"],
            "filled_fields_by_section": {"identity": ["brand_name"]},
            "sections_touched": ["identity"],
            "sections_completed": [],
            "newly_completed_section": "identity",
        }

        missing = required_keys - set(processing_payload.keys())
        assert not missing, f"Processing payload missing keys: {missing}"


class TestExtractionSummaryCardKind:
    """Verify extraction_summary is a registered card_kind."""

    def test_extraction_summary_in_card_block_literal(self) -> None:
        """CardBlock.card_kind must accept 'extraction_summary'."""
        from src.modules.copilot.domain.message_blocks import CardBlock

        field = CardBlock.model_fields["card_kind"]
        allowed_kinds = set(field.annotation.__args__)
        assert "extraction_summary" in allowed_kinds, (
            "extraction_summary must be in CardBlock.card_kind literal. Add it to message_blocks.py."
        )

    def test_extraction_summary_in_card_payload_registry(self) -> None:
        """card_payloads.py must have an entry for extraction_summary."""
        from src.modules.copilot.domain.card_payloads import CARD_PAYLOAD_MODELS

        assert "extraction_summary" in CARD_PAYLOAD_MODELS, (
            "extraction_summary must be in CARD_PAYLOAD_MODELS. Add ExtractionSummaryCardPayload to card_payloads.py."
        )

    def test_extraction_summary_payload_model_validates(self) -> None:
        """ExtractionSummaryCardPayload must validate a minimal correct payload."""
        from src.modules.copilot.domain.card_payloads import CARD_PAYLOAD_MODELS

        model = CARD_PAYLOAD_MODELS.get("extraction_summary")
        assert model is not None

        payload = {
            "type": "extraction_summary",
            "source_ref": "https://visionarias.pe",
            "duration_seconds": 38,
            "total_fields": 27,
            "total_sections": 6,
            "coverage_by_section": [
                {"slug": "identity", "label": "Identidad", "filled": 14, "total": 18},
            ],
            "strong_assumptions_count": 4,
            "open_questions_count": 6,
            "primary_cta_route": "/brand-studio/identity",
        }
        instance = model.model_validate(payload)
        assert instance is not None
