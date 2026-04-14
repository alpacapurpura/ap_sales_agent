"""Tests for field_path validation in extract_structured."""

import pytest

from src.modules.copilot.domain.schema_introspection import validate_field_path


class TestValidateFieldPath:
    """Tests for validate_field_path — checks dot-notation paths against real schemas."""

    def test_valid_brand_field(self) -> None:
        """identity.brand_name is a real section.field in BrandSettings."""
        assert validate_field_path("brand", "identity.brand_name") is True

    def test_valid_brand_section(self) -> None:
        """identity is a top-level section name in BrandSettings."""
        assert validate_field_path("brand", "identity") is True

    def test_valid_brand_story_section(self) -> None:
        """story is a real section in BrandSettings."""
        assert validate_field_path("brand", "story") is True

    def test_valid_brand_positioning_field(self) -> None:
        """positioning is a real section in BrandSettings."""
        assert validate_field_path("brand", "positioning") is True

    def test_invalid_brand_section(self) -> None:
        """nonexistent_section is not a real section in BrandSettings."""
        assert validate_field_path("brand", "nonexistent_section.fake_field") is False

    def test_invalid_completely(self) -> None:
        """zzz_totally_fake is not any known path in BrandSettings."""
        assert validate_field_path("brand", "zzz_totally_fake") is False

    def test_unknown_domain(self) -> None:
        """Unknown domains always return False."""
        assert validate_field_path("unknown_domain", "any.field") is False

    def test_valid_offer_field(self) -> None:
        """public_name is a real persistable field for offer domain."""
        assert validate_field_path("offer", "public_name") is True

    def test_valid_offer_another_field(self) -> None:
        """headline_promise is a real persistable field for offer domain."""
        assert validate_field_path("offer", "headline_promise") is True

    def test_invalid_offer_field(self) -> None:
        """id is a system field excluded from PERSISTABLE_FIELDS."""
        assert validate_field_path("offer", "id") is False

    def test_invalid_offer_fake(self) -> None:
        """fake_field is not in offer PERSISTABLE_FIELDS."""
        assert validate_field_path("offer", "totally_fake_field") is False

    def test_cache_is_populated_on_second_call(self) -> None:
        """Calling validate_field_path twice for the same domain uses the cache.

        This is a behavioral test: no exception should be raised on second call.
        """
        result1 = validate_field_path("brand", "identity.brand_name")
        result2 = validate_field_path("brand", "identity.brand_name")
        assert result1 == result2 is True

    def test_empty_field_path(self) -> None:
        """Empty string is always invalid."""
        assert validate_field_path("brand", "") is False

    def test_brand_narrative_section(self) -> None:
        """narrative is a real section in BrandSettings."""
        assert validate_field_path("brand", "narrative") is True

    def test_brand_visuals_section(self) -> None:
        """visuals is a real section in BrandSettings."""
        assert validate_field_path("brand", "visuals") is True

    # ── buyer_persona domain ─────────────────────────────────────────────────

    def test_buyer_persona_all_campos_objetivo(self) -> None:
        """Every campos_objetivo path in buyer_persona_config must be valid."""
        from src.modules.copilot.domain.interview_configs.buyer_persona_config import (
            BUYER_PERSONA_BLOCKS,
        )

        for block in BUYER_PERSONA_BLOCKS:
            for path in block.campos_objetivo:
                assert validate_field_path("buyer_persona", path) is True, (
                    f"Block '{block.id}' path '{path}' rejected by validate_field_path"
                )

    def test_buyer_persona_demographics_known(self) -> None:
        assert validate_field_path("buyer_persona", "demographics.age_range") is True
        assert validate_field_path("buyer_persona", "demographics.location") is True
        assert validate_field_path("buyer_persona", "demographics.occupation") is True

    def test_buyer_persona_dict_prefix_fallback(self) -> None:
        """Any demographics.* path is accepted even if not pre-registered."""
        assert validate_field_path("buyer_persona", "demographics.marital_status") is True
        assert validate_field_path("buyer_persona", "psychographics.hobbies") is True
        assert validate_field_path("buyer_persona", "buyer_journey.post_purchase") is True

    def test_buyer_persona_list_fields(self) -> None:
        assert validate_field_path("buyer_persona", "pain_points") is True
        assert validate_field_path("buyer_persona", "desires") is True
        assert validate_field_path("buyer_persona", "objections") is True
        assert validate_field_path("buyer_persona", "preferred_channels") is True
        assert validate_field_path("buyer_persona", "purchase_triggers") is True
        assert validate_field_path("buyer_persona", "anti_patterns") is True

    def test_buyer_persona_scalar_fields(self) -> None:
        assert validate_field_path("buyer_persona", "name") is True
        assert validate_field_path("buyer_persona", "tagline") is True

    def test_buyer_persona_rejects_garbage(self) -> None:
        assert validate_field_path("buyer_persona", "nonexistent_section.fake_field") is False
        assert validate_field_path("buyer_persona", "totally_fake") is False
        assert validate_field_path("buyer_persona", "") is False
        assert validate_field_path("buyer_persona", "id") is False
        assert validate_field_path("buyer_persona", "tenant_id") is False

    def test_buyer_persona_dict_parents_invalid_as_top_level(self) -> None:
        """Dict parent names must NOT be valid as standalone paths.

        If accepted, the AI stores the whole dict as a string (e.g.
        demographics = "Mujeres de 30 a 45 años..."), which breaks
        BuyerPersona Pydantic validation when the record is reloaded.
        The AI must use dot-notation: demographics.age_range, etc.
        """
        assert validate_field_path("buyer_persona", "demographics") is False
        assert validate_field_path("buyer_persona", "psychographics") is False
        assert validate_field_path("buyer_persona", "buyer_journey") is False

    def test_buyer_persona_cache_hit(self) -> None:
        """Second call for buyer_persona uses cached paths."""
        r1 = validate_field_path("buyer_persona", "demographics.age_range")
        r2 = validate_field_path("buyer_persona", "demographics.age_range")
        assert r1 == r2 is True
