"""F2 — ``write_todos`` tool args → ``plan_card`` block synthesis.

The deep-agent harness can call the built-in ``write_todos`` tool which
returns a ``Command`` mutation, not a ``ui_action``. We synthesize a
``plan_card`` block directly from the tool *input* args so the FE can
render the planning UI without touching cards UI semantics.
"""

from __future__ import annotations

from src.modules.copilot.application.orchestrator.chat import (
    _write_todos_to_plan_card,
)


class TestWriteTodosToPlanCard:
    """Args → plan_card block payload."""

    def test_minimal_three_step_plan(self) -> None:
        block = _write_todos_to_plan_card(
            {
                "todos": [
                    {"content": "Auditar identidad", "status": "in_progress"},
                    {"content": "Revisar storytelling", "status": "pending"},
                    {"content": "Sintetizar hallazgos", "status": "pending"},
                ],
            },
        )
        assert block is not None
        assert block["type"] == "card"
        assert block["card_kind"] == "plan_card"
        assert block["status"] == "pending"
        todos = block["payload"]["todos"]
        assert len(todos) == 3
        assert todos[0]["content"] == "Auditar identidad"
        assert todos[0]["status"] == "in_progress"
        assert todos[1]["status"] == "pending"

    def test_unknown_status_defaults_to_pending(self) -> None:
        block = _write_todos_to_plan_card(
            {"todos": [{"content": "x", "status": "weird"}]},
        )
        assert block is not None
        assert block["payload"]["todos"][0]["status"] == "pending"

    def test_supports_active_form_camel_case(self) -> None:
        block = _write_todos_to_plan_card(
            {"todos": [{"content": "Compilar", "status": "in_progress", "activeForm": "Compilando"}]},
        )
        assert block is not None
        assert block["payload"]["todos"][0]["active_form"] == "Compilando"

    def test_empty_or_invalid_returns_none(self) -> None:
        assert _write_todos_to_plan_card({}) is None
        assert _write_todos_to_plan_card({"todos": []}) is None
        assert _write_todos_to_plan_card({"todos": [{"content": ""}]}) is None
        assert _write_todos_to_plan_card("not a dict") is None
        assert _write_todos_to_plan_card({"todos": "wrong"}) is None
