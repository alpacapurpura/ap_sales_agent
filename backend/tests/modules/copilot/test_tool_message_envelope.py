"""Tests for the ToolMessage content envelope logic in graph.py.

When a tool returns a JSON with ``llm_content`` key, the orchestrator must
feed the condensed summary — not the full payload — back to the LLM.
This prevents the model from regurgitating ``proposal`` deltas (or any
other large ui_action payload) into the assistant chat message.
"""

from __future__ import annotations

import json

from luana_core_copilot.application.orchestrator.graph import _tool_message_content


class TestToolMessageContent:
    def test_plain_string_is_returned_untouched(self) -> None:
        assert _tool_message_content("Tool returned plain text") == "Tool returned plain text"

    def test_json_without_llm_content_returns_raw_string(self) -> None:
        payload = json.dumps({"text": "ok", "ui_action": {"type": "noop"}})
        assert _tool_message_content(payload) == payload

    def test_llm_content_replaces_payload(self) -> None:
        payload = json.dumps(
            {
                "text": "Extraje 12 campos",
                "llm_content": "Extracción exitosa. El usuario ya ve la card, no repitas.",
                "ui_action": {
                    "type": "proposal",
                    "updates": [
                        {"field_id": "f", "new_value": "value" * 200, "reason": "x"},
                    ],
                },
            },
        )
        content = _tool_message_content(payload)
        assert "El usuario ya ve la card" in content
        # Raw delta must NOT leak into the LLM context.
        assert "value" * 200 not in content

    def test_empty_llm_content_falls_back_to_raw(self) -> None:
        payload = json.dumps({"llm_content": "   ", "text": "fallback"})
        assert _tool_message_content(payload) == payload

    def test_non_json_string_returned_untouched(self) -> None:
        # Some tools return free-form text; must pass through unchanged.
        raw = "Tool XYZ: done in 42ms"
        assert _tool_message_content(raw) == raw

    def test_truncation_still_applies_to_llm_content(self) -> None:
        huge = "A" * 10_000
        payload = json.dumps({"llm_content": huge})
        content = _tool_message_content(payload)
        assert len(content) < 4200  # cap ~ 4000 plus truncation marker
        assert content.endswith("(salida truncada)")
