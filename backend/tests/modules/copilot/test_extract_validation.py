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
