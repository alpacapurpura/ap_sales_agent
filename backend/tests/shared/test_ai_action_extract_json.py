"""Regression tests for AIActionService._extract_json after the hardening.

Failure modes observed in production:

* The model wraps the response in ``\\`\\`\\`json ... \\`\\`\\``` AND emits trailing
  text after the closing brace. The previous regex captured the inner block
  but kept extra characters that produced ``Extra data: line N column M``.
* The model emits two consecutive code blocks (a "first attempt" + "let me
  fix that" pattern). The previous ``rfind`` spanned both, producing
  garbage that broke ``json.loads``.
* The JSON itself contains string values with braces or escaped quotes —
  a naïve depth counter reports false-negative balance.
"""

from __future__ import annotations

import json

from src.shared.application.ai_action_service import AIActionService


class TestExtractJson:
    def _loads(self, raw: str) -> object:
        """Run the same path AIActionService takes: extract → loads."""
        return json.loads(AIActionService._extract_json(raw))

    def test_plain_object(self) -> None:
        assert self._loads('{"a": 1}') == {"a": 1}

    def test_object_with_trailing_text(self) -> None:
        raw = '{"a": 1}\nMás explicación que el LLM agregó al final.'
        assert self._loads(raw) == {"a": 1}

    def test_markdown_block(self) -> None:
        raw = '```json\n{"a": 1}\n```'
        assert self._loads(raw) == {"a": 1}

    def test_markdown_block_with_text_before_and_after(self) -> None:
        raw = 'Aquí va el resultado:\n```json\n{"a": 1}\n```\nFin.'
        assert self._loads(raw) == {"a": 1}

    def test_two_consecutive_markdown_blocks_uses_first(self) -> None:
        raw = '```json\n{"a": 1}\n```\nDéjame mejorarlo:\n```json\n{"a": 2}\n```'
        assert self._loads(raw) == {"a": 1}

    def test_two_consecutive_objects_no_markdown_uses_first(self) -> None:
        """Mimics the production failure: model emitted two top-level objects."""
        raw = '{"a": 1}\n{"a": 2}'
        assert self._loads(raw) == {"a": 1}

    def test_braces_inside_string_value_do_not_confuse_balance(self) -> None:
        raw = '{"snippet": "if (x) { return 1; }", "ok": true}'
        assert self._loads(raw) == {"snippet": "if (x) { return 1; }", "ok": True}

    def test_escaped_quote_inside_string(self) -> None:
        raw = '{"quote": "she said \\"hi\\""}'
        assert self._loads(raw) == {"quote": 'she said "hi"'}

    def test_array_at_top_level(self) -> None:
        raw = '[{"a":1},{"a":2}]'
        assert self._loads(raw) == [{"a": 1}, {"a": 2}]

    def test_first_balanced_handles_nested_lists(self) -> None:
        raw = '{"groups": [[1,2],[3,4]], "name": "x"}'
        assert self._loads(raw) == {"groups": [[1, 2], [3, 4]], "name": "x"}

    def test_returns_raw_when_no_balanced_container(self) -> None:
        # Exercise the fallback path so a noisy response still surfaces a
        # clean JSONDecodeError to the retry loop instead of silently passing.
        assert AIActionService._extract_json("just text") == "just text"

    def test_empty_markdown_block_skipped(self) -> None:
        raw = '```json\n```\n```json\n{"a": 1}\n```'
        assert self._loads(raw) == {"a": 1}
