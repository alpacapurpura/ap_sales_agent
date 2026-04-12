"""Tests for Interview Engine tools."""

import json
from uuid import uuid4

from src.modules.copilot.application.tools.interview.extract_structured import (
    extract_structured,
)
from src.modules.copilot.application.tools.interview.offer_alternatives import (
    offer_alternatives,
)


class TestExtractStructured:
    def test_returns_preview_update_action(self):
        result = extract_structured.invoke(
            {
                "session_id": str(uuid4()),
                "extractions": [
                    {
                        "field_path": "story.origin_story",
                        "value": "Test origin",
                        "confidence": 0.9,
                        "source": "user_explicit",
                    },
                ],
            }
        )
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["type"] == "preview_update"
        assert "story.origin_story" in parsed["ui_action"]["delta"]

    def test_empty_extractions_returns_empty_delta(self):
        result = extract_structured.invoke(
            {
                "session_id": str(uuid4()),
                "extractions": [],
            }
        )
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["delta"] == {}

    def test_low_confidence_in_confidence_map(self):
        result = extract_structured.invoke(
            {
                "session_id": str(uuid4()),
                "extractions": [
                    {
                        "field_path": "positioning.competitors",
                        "value": ["A", "B"],
                        "confidence": 0.6,
                        "source": "inferred",
                    },
                ],
            }
        )
        parsed = json.loads(result) if isinstance(result, str) else result
        assert "positioning.competitors" in parsed["ui_action"]["confidence_map"]
        assert parsed["ui_action"]["confidence_map"]["positioning.competitors"] == 0.6

    def test_text_is_empty_silent(self):
        result = extract_structured.invoke(
            {
                "session_id": str(uuid4()),
                "extractions": [
                    {
                        "field_path": "story.mission",
                        "value": "Test",
                        "confidence": 1.0,
                        "source": "user_explicit",
                    },
                ],
            }
        )
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["text"] == ""

    def test_skips_items_without_field_path(self):
        result = extract_structured.invoke(
            {
                "session_id": str(uuid4()),
                "extractions": [
                    {
                        "field_path": "",
                        "value": "ignored",
                        "confidence": 1.0,
                        "source": "user_explicit",
                    },
                    {"value": "also ignored", "confidence": 1.0, "source": "inferred"},
                ],
            }
        )
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["delta"] == {}


class TestOfferAlternatives:
    def test_returns_alternatives_card(self):
        result = offer_alternatives.invoke(
            {
                "field_path": "identity.archetype",
                "question": "Which archetype fits?",
                "alternatives": [
                    {
                        "id": "a",
                        "title": "The Magician",
                        "description": "Transforms complex into simple",
                        "recommended": True,
                        "recommendation_reason": "Matches your pitch",
                    },
                    {
                        "id": "b",
                        "title": "The Hero",
                        "description": "Empowers users",
                        "recommended": False,
                    },
                ],
                "allow_custom": True,
            }
        )
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["type"] == "alternatives_card"
        assert len(parsed["ui_action"]["alternatives"]) == 2
        assert parsed["ui_action"]["allow_custom"] is True

    def test_text_is_empty(self):
        result = offer_alternatives.invoke(
            {
                "field_path": "identity.tone",
                "question": "Tone?",
                "alternatives": [
                    {
                        "id": "a",
                        "title": "A",
                        "description": "Desc",
                        "recommended": False,
                    },
                    {
                        "id": "b",
                        "title": "B",
                        "description": "Desc",
                        "recommended": True,
                        "recommendation_reason": "Fits better",
                    },
                ],
                "allow_custom": False,
            }
        )
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["text"] == ""

    def test_field_path_included(self):
        result = offer_alternatives.invoke(
            {
                "field_path": "positioning.uvp",
                "question": "UVP?",
                "alternatives": [
                    {
                        "id": "a",
                        "title": "A",
                        "description": "D",
                        "recommended": True,
                        "recommendation_reason": "R",
                    },
                ],
                "allow_custom": True,
            }
        )
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["field_path"] == "positioning.uvp"
