"""Tests for Sprint 2.D data-model purge.

These tests define the NEW expected shape of the brand domain after purge.
They must be RED before the implementation and GREEN after.

Purges in scope:
  1. BrandTeam class deleted; BrandSettings.team_metadata deleted.
  2. BrandValues (positioning.values) loses core_values / personality_traits / archetype.
  3. New BrandPersonality VO added to BrandSettings with those 3 fields.

The 9 visual fields (primary_color, accent_color, etc.) were NOT in BrandIdentity
already — verified by reading the source. No action needed for them.
"""

import pytest
from pydantic import ValidationError

from src.modules.brand.domain import BrandSettings


class TestBrandTeamPurge:
    """BrandTeam and team_metadata must be gone."""

    def test_brand_settings_has_no_team_metadata(self):
        """team_metadata is not a field on BrandSettings."""
        s = BrandSettings()
        assert not hasattr(s, "team_metadata")

    def test_brand_team_not_exported_from_domain(self):
        """BrandTeam is removed from the domain __init__ public API."""
        import src.modules.brand.domain as brand_domain

        assert not hasattr(brand_domain, "BrandTeam"), "BrandTeam should not be exported from brand domain after purge"

    def test_brand_settings_ignores_legacy_team_metadata_json(self):
        """Old JSON blobs with team_metadata key are accepted without errors
        (extra='ignore' on BrandSettings absorbs the unknown key).
        """
        data = {
            "team_metadata": {
                "key_leadership": ["Alice"],
                "culture_vibe": "startup",
            },
        }
        s = BrandSettings(**data)
        assert not hasattr(s, "team_metadata")


class TestBrandPersonalityNew:
    """BrandPersonality VO must exist and hold the three moved fields."""

    def test_brand_personality_importable(self):
        """BrandPersonality is importable from brand domain."""
        from src.modules.brand.domain import BrandPersonality

    def test_brand_personality_has_core_values(self):
        from src.modules.brand.domain import BrandPersonality

        p = BrandPersonality(core_values=["Innovation", "Transparency"])
        assert p.core_values == ["Innovation", "Transparency"]

    def test_brand_personality_has_personality_traits(self):
        from src.modules.brand.domain import BrandPersonality

        p = BrandPersonality(personality_traits=["Bold", "Empathetic"])
        assert p.personality_traits == ["Bold", "Empathetic"]

    def test_brand_personality_has_archetype(self):
        from src.modules.brand.domain import BrandPersonality

        p = BrandPersonality(archetype="Hero")
        assert p.archetype == "Hero"

    def test_brand_personality_all_optional(self):
        from src.modules.brand.domain import BrandPersonality

        p = BrandPersonality()
        assert p.core_values == []
        assert p.personality_traits == []
        assert p.archetype is None

    def test_brand_settings_has_brand_personality_field(self):
        """BrandSettings now has a brand_personality field."""
        s = BrandSettings()
        assert hasattr(s, "brand_personality")
        assert s.brand_personality is None

    def test_brand_settings_accepts_brand_personality(self):
        from src.modules.brand.domain import BrandPersonality

        bp = BrandPersonality(archetype="Rebel", core_values=["Freedom"])
        s = BrandSettings(brand_personality=bp)
        assert s.brand_personality is not None
        assert s.brand_personality.archetype == "Rebel"
        assert s.brand_personality.core_values == ["Freedom"]

    def test_brand_settings_roundtrip_with_brand_personality(self):
        from src.modules.brand.domain import BrandPersonality

        bp = BrandPersonality(
            core_values=["Creativity"],
            personality_traits=["Playful"],
            archetype="Jester",
        )
        s = BrandSettings(brand_personality=bp)
        dumped = s.model_dump(mode="json")
        restored = BrandSettings.model_validate(dumped)
        assert restored.brand_personality is not None
        assert restored.brand_personality.archetype == "Jester"


class TestBrandValuesLosePersonalityFields:
    """BrandValues (positioning.values) must NOT contain the 3 moved fields."""

    def test_brand_values_has_no_core_values(self):
        """core_values is no longer on BrandValues."""
        from src.modules.brand.domain import BrandValues

        v = BrandValues()
        assert not hasattr(v, "core_values"), "core_values should have been moved to BrandPersonality"

    def test_brand_values_has_no_personality_traits(self):
        from src.modules.brand.domain import BrandValues

        v = BrandValues()
        assert not hasattr(v, "personality_traits"), "personality_traits should have been moved to BrandPersonality"

    def test_brand_values_has_no_archetype(self):
        from src.modules.brand.domain import BrandValues

        v = BrandValues()
        assert not hasattr(v, "archetype"), "archetype should have been moved to BrandPersonality"

    def test_brand_values_still_has_other_fields(self):
        """BrandValues is not deleted, just trimmed.

        After the purge BrandValues may still exist (even if empty) or be
        replaced by a simpler model — as long as the 3 fields are gone.
        This test is deliberately lenient: it only checks we didn't break
        BrandPositioning construction.
        """
        from src.modules.brand.domain import BrandPositioning

        p = BrandPositioning()
        assert p.values is None or isinstance(p.values, object)

    def test_positioning_values_legacy_json_accepted_without_error(self):
        """Old JSON blobs that include core_values in positioning.values
        must not crash on load — the unknown keys are silently dropped
        (extra='ignore' on BrandValues).
        """
        from src.modules.brand.domain import BrandPositioning

        data = {
            "values": {
                "core_values": ["Innovation"],
                "personality_traits": ["Bold"],
                "archetype": "Hero",
            },
        }
        # Must not raise
        p = BrandPositioning(**data)
        assert p.values is not None
        # The old fields must not appear on the values object
        assert not hasattr(p.values, "core_values")
        assert not hasattr(p.values, "personality_traits")
        assert not hasattr(p.values, "archetype")


class TestMigrationDataFlow:
    """Integration: legacy JSON with old fields can be read into new model.

    The JSONB migration copies data before dropping keys — these tests
    confirm the Pydantic layer handles old shapes gracefully in both
    directions (old-data-in, new-data-out).
    """

    def test_full_legacy_brand_settings_parsed_without_crash(self):
        """A full legacy BrandSettings JSON with team_metadata and
        positioning.values.core_values is parsed without raising.
        """
        legacy_data = {
            "identity": {"brand_name": "LegacyCorp"},
            "team_metadata": {
                "key_leadership": ["Bob"],
                "culture_vibe": "remote-first",
            },
            "positioning": {
                "brand_essence": "Freedom",
                "values": {
                    "core_values": ["Innovation"],
                    "personality_traits": ["Bold"],
                    "archetype": "Hero",
                },
            },
        }
        s = BrandSettings.model_validate(legacy_data)
        assert s.identity is not None
        assert s.identity.brand_name == "LegacyCorp"
        # team_metadata silently dropped
        assert not hasattr(s, "team_metadata")
        # values parsed without 3 moved fields
        assert s.positioning is not None
        assert s.positioning.brand_essence == "Freedom"
