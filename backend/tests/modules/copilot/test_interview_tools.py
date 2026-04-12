"""Tests for Interview Engine tools."""

import json
from uuid import uuid4

from src.modules.copilot.application.tools.interview.advance_block import advance_block
from src.modules.copilot.application.tools.interview.checkpoint import checkpoint
from src.modules.copilot.application.tools.interview.clarify import clarify
from src.modules.copilot.application.tools.interview.complete_interview import (
    complete_interview,
)
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


class TestClarify:
    def test_returns_clarify_card(self):
        result = clarify.invoke(
            {
                "items": [
                    {
                        "field_path": "positioning.competitors",
                        "issue": "Contradiction detected",
                        "options": ["Option A", "Option B"],
                    },
                ],
            }
        )
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["type"] == "clarify_card"
        assert len(parsed["ui_action"]["items"]) == 1
        assert parsed["text"] != ""

    def test_max_2_items(self):
        result = clarify.invoke(
            {
                "items": [
                    {"field_path": "f1", "issue": "Issue 1", "options": ["A"]},
                    {"field_path": "f2", "issue": "Issue 2", "options": ["B"]},
                    {"field_path": "f3", "issue": "Issue 3", "options": ["C"]},
                ],
            }
        )
        parsed = json.loads(result) if isinstance(result, str) else result
        assert len(parsed["ui_action"]["items"]) <= 2


class TestCheckpoint:
    def test_returns_checkpoint_card(self):
        result = checkpoint.invoke(
            {
                "block_id": "identidad",
                "block_label": "Tu Identidad",
                "summary": {
                    "story.origin_story": "Founded in 2019...",
                    "story.mission": "Democratize sales...",
                },
                "health_score": 85,
                "blocks_completed": 1,
                "blocks_total": 5,
            }
        )
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["type"] == "checkpoint_card"
        assert parsed["ui_action"]["block_id"] == "identidad"
        assert parsed["ui_action"]["health_score"] == 85
        assert parsed["text"] != ""

    def test_includes_blocks_progress(self):
        result = checkpoint.invoke(
            {
                "block_id": "narrativa",
                "block_label": "Narrativa",
                "summary": {},
                "health_score": 60,
                "blocks_completed": 3,
                "blocks_total": 5,
            }
        )
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["blocks_progress"]["completed"] == 3
        assert parsed["ui_action"]["blocks_progress"]["total"] == 5


class TestAdvanceBlock:
    def test_returns_preview_update_persisted(self):
        result = advance_block.invoke(
            {
                "block_id": "identidad",
                "persisted_fields": ["story.origin_story", "story.mission"],
                "next_block_id": "posicionamiento",
                "next_block_label": "Tu Posicionamiento",
            }
        )
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["type"] == "preview_update"
        assert parsed["ui_action"]["persisted"] is True
        assert parsed["metadata"]["next_block"] == "posicionamiento"
        assert parsed["text"] != ""

    def test_last_block_no_next(self):
        result = advance_block.invoke(
            {
                "block_id": "identidad_creativa",
                "persisted_fields": ["identity.archetype"],
                "next_block_id": None,
                "next_block_label": None,
            }
        )
        parsed = json.loads(result) if isinstance(result, str) else result
        assert "completados" in parsed["text"]
        assert parsed["metadata"]["next_block"] is None


class TestCompleteInterview:
    def test_returns_interview_complete(self):
        sid = str(uuid4())
        result = complete_interview.invoke(
            {
                "session_id": sid,
                "health_score": 92,
                "redirect_path": "/brand-studio",
            }
        )
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["type"] == "interview_complete"
        assert parsed["ui_action"]["health_score"] == 92
        assert parsed["ui_action"]["redirect"] == "/brand-studio"
        assert "92%" in parsed["text"]
