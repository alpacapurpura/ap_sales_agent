"""TDD — offer_section_tools refactor: _no_data_response + _ok_response D-7.

Tests written RED first per ``tdd-mandatory.md``.
Verifies the pure expansion: next_step_hint field + empty suggestions in _no_data_response.

PR-2-pure-expansion-providers / PI-2 S2.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestNoDataResponseRefactor:
    def test_no_data_response_returns_empty_suggestions_and_next_step_hint(self) -> None:
        """_no_data_response produces: suggestions=[], next_step_hint=hint."""
        from luana_core_copilot.application.tools.offer_section_tools import (
            _no_data_response,
        )

        result = json.loads(_no_data_response("identity", "Completa primero la marca"))
        assert result["suggestions"] == [], f"Expected empty suggestions list, got: {result['suggestions']!r}"
        assert result["next_step_hint"] == "Completa primero la marca", (
            f"Expected next_step_hint to carry the hint, got: {result.get('next_step_hint')!r}"
        )
        assert result["section_slug"] == "identity"
        assert result["confidence"] == 0.0
        assert result["draft_fields"] == {}

    def test_no_data_response_no_hardcoded_hint_literal(self) -> None:
        """_no_data_response must not produce 'suggestions': [<hint>] literal.

        Regression guard: ensures PR-2 deuda was resolved.
        """
        from luana_core_copilot.application.tools.offer_section_tools import (
            _no_data_response,
        )

        hint = "Test hint value"
        result = json.loads(_no_data_response("promise", hint))
        # suggestions must be an empty list, never [hint]
        assert result["suggestions"] != [hint], (
            "REGRESSION: 'suggestions' field is still carrying the hint as a list item. "
            "This is the D-7 deuda that PR-2 must resolve."
        )
        assert result["suggestions"] == []


class TestOkResponseRefactor:
    def test_ok_response_includes_optional_next_step_hint(self) -> None:
        """_ok_response accepts next_step_hint keyword and includes it in output."""
        from luana_core_copilot.application.tools.offer_section_tools import _ok_response

        result = json.loads(
            _ok_response(
                "promise",
                {"headline": "Test headline"},
                ["Suggestion A"],
                0.8,
                next_step_hint="Siguiente paso aquí",
            )
        )
        assert result["suggestions"] == ["Suggestion A"]
        assert result["next_step_hint"] == "Siguiente paso aquí"
        assert result["confidence"] == 0.8

    def test_ok_response_next_step_hint_defaults_to_none(self) -> None:
        """_ok_response without next_step_hint still works (backwards compat)."""
        from luana_core_copilot.application.tools.offer_section_tools import _ok_response

        result = json.loads(_ok_response("identity", {"brand_name": "ACME"}, ["chip"], 0.9))
        # next_step_hint is either absent or None — not required
        hint_val = result.get("next_step_hint")
        assert hint_val is None or hint_val == "", f"Expected next_step_hint to be None or absent, got {hint_val!r}"


class TestGrepNoStaticSuggestionsHintLiteral:
    def test_grep_no_static_suggestions_hint_literal(self) -> None:
        """Source file must not contain '\"suggestions\": [hint]' literal (regression guard).

        This is the acceptance criterion from PR.md:
        grep -n '"suggestions": [hint]' offer_section_tools.py → 0 hits
        """
        src_file = Path(__file__).resolve().parents[5] / (
            "src/modules/copilot/application/tools/offer_section_tools.py"
        )
        assert src_file.exists(), f"Source file not found: {src_file}"
        content = src_file.read_text(encoding="utf-8")
        assert '"suggestions": [hint]' not in content, (
            "REGRESSION: '\"suggestions\": [hint]' literal found in offer_section_tools.py. "
            "PR-2 must remove this hardcoded static residual (D-7)."
        )

    def test_existing_tools_still_export_correctly(self) -> None:
        """OFFER_SECTION_TOOLS still exports all expected tools after refactor."""
        from luana_core_copilot.application.tools.offer_section_tools import (
            OFFER_SECTION_TOOLS,
        )

        assert len(OFFER_SECTION_TOOLS) >= 1, "OFFER_SECTION_TOOLS is empty post-refactor"
        for tool in OFFER_SECTION_TOOLS:
            assert hasattr(tool, "name"), f"Tool {tool!r} missing .name (not a LangChain tool)"
