"""Tests for the field-paths hint generator (LLM extraction guard rail)."""

from __future__ import annotations

from src.modules.copilot.domain.field_paths_hint import build_field_paths_hint


class TestBuildFieldPathsHint:
    def test_brand_hint_includes_known_paths(self) -> None:
        hint = build_field_paths_hint("brand")
        assert hint, "brand catalog must produce a non-empty hint"
        assert "`identity.brand_name`" in hint
        assert "`positioning.unique_value_proposition`" in hint
        assert "## Campos válidos para `brand`" in hint

    def test_offer_hint_marks_list_fields(self) -> None:
        hint = build_field_paths_hint("offer")
        # Scalar
        assert "`public_name` (string)" in hint
        # Lists
        assert "`pricing_options` (list)" in hint
        assert "`marketing_pain_points` (list)" in hint

    def test_buyer_persona_hint_includes_dynamic_block(self) -> None:
        hint = build_field_paths_hint("buyer_persona")
        # Catalog scalars rendered
        assert "`name` (string)" in hint
        assert "`demographics.age_range` (string)" in hint
        # Dynamic dict-parents block
        assert "### dynamic" in hint
        assert "`demographics.*`" in hint
        assert "`psychographics.*`" in hint
        assert "`buyer_journey.*`" in hint

    def test_buyer_persona_does_not_emit_excluded_lists(self) -> None:
        """pain_points/desires/objections/preferred_channels are intentionally
        absent from the buyer_persona editable catalog (edited via form-runtime).
        The hint must reflect that — telling the LLM otherwise would invite the
        exact hallucination we are trying to prevent."""
        hint = build_field_paths_hint("buyer_persona")
        for path in ("pain_points", "desires", "objections", "preferred_channels"):
            assert f"`{path}`" not in hint

    def test_unknown_domain_returns_empty(self) -> None:
        assert build_field_paths_hint("nonexistent") == ""
