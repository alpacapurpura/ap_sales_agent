"""Tests confirming extract_structured accepts fields from any section.

The tool lives in ``tools/guided/`` since the interview engine was retired
on 2026-04-22. It no longer takes a ``session_id`` argument — state is
conversation-scoped via ``core.context``.
"""

from __future__ import annotations

import json

from src.modules.copilot.application.tools.guided.extract import extract_structured


class TestExtractStructuredGlobal:
    def test_extracts_fields_from_multiple_sections(self) -> None:
        result = extract_structured.invoke(
            {
                "domain": "brand",
                "extractions": [
                    {"field_path": "identity.brand_name", "value": "Mi Marca", "confidence": 0.9},
                    {
                        "field_path": "positioning.competitive_environment",
                        "value": "mercado competitivo",
                        "confidence": 0.85,
                    },
                    {"field_path": "story.origin_story", "value": "Empezamos en 2020", "confidence": 0.95},
                ],
            },
        )
        parsed = json.loads(result)
        delta = parsed["ui_action"]["delta"]
        assert "identity.brand_name" in delta
        assert "positioning.competitive_environment" in delta
        assert "story.origin_story" in delta

    def test_low_confidence_tracked(self) -> None:
        result = extract_structured.invoke(
            {
                "domain": "brand",
                "extractions": [
                    {"field_path": "identity.brand_name", "value": "Maybe", "confidence": 0.6},
                ],
            },
        )
        parsed = json.loads(result)
        confidence_map = parsed["ui_action"]["confidence_map"]
        assert "identity.brand_name" in confidence_map
        assert confidence_map["identity.brand_name"] == 0.6

    def test_empty_extractions(self) -> None:
        result = extract_structured.invoke(
            {
                "domain": "brand",
                "extractions": [],
            },
        )
        parsed = json.loads(result)
        assert parsed["ui_action"]["delta"] == {}

    def test_invalid_field_paths_are_skipped(self) -> None:
        result = extract_structured.invoke(
            {
                "domain": "brand",
                "extractions": [
                    {"field_path": "identity.brand_name", "value": "OK", "confidence": 1.0},
                    {"field_path": "completely.invalid.path", "value": "NOPE", "confidence": 1.0},
                ],
            },
        )
        parsed = json.loads(result)
        assert "identity.brand_name" in parsed["ui_action"]["delta"]
        assert "completely.invalid.path" in parsed["ui_action"]["skipped"]
