"""Tests for shared.application.field_diff — the pre/post extraction diff."""

from __future__ import annotations

from src.shared.application.field_diff import (
    diff_filled_by_section,
    filled_fields_by_section,
)


class TestFilledFieldsBySection:
    def test_empty_dump_returns_empty(self) -> None:
        assert filled_fields_by_section({}) == {}

    def test_only_empties_returns_empty(self) -> None:
        dump = {
            "identity": {"brand_name": "", "tagline": None},
            "story": {},
            "visuals": [],
        }
        assert filled_fields_by_section(dump) == {}

    def test_flat_filled_identity(self) -> None:
        dump = {"identity": {"brand_name": "Visionarias", "tagline": ""}}
        assert filled_fields_by_section(dump) == {"identity": ["identity.brand_name"]}

    def test_nested_dict_enumerates_leaves(self) -> None:
        dump = {
            "strategy": {
                "mission": {"statement": "Empoderar a expertos", "since": ""},
                "vision": {"statement": "", "horizon": None},
            },
        }
        assert filled_fields_by_section(dump) == {
            "strategy": ["strategy.mission.statement"],
        }

    def test_list_as_top_level_section_counts_once(self) -> None:
        dump = {"testimonials": [{"author": "Ana"}, {"author": "Luis"}]}
        # list aggregate is collapsed to a single path — exact author count
        # is not needed for the summary card granularity.
        assert filled_fields_by_section(dump) == {"testimonials": ["testimonials"]}

    def test_primitives_counted_as_filled(self) -> None:
        dump = {"story": {"founding_year": 2021, "is_remote": True, "staff": 0}}
        # 0 is a legitimate value — _is_filled treats primitives as present
        paths = filled_fields_by_section(dump)["story"]
        assert "story.founding_year" in paths
        assert "story.is_remote" in paths
        assert "story.staff" in paths

    def test_ignores_whitespace_only_strings(self) -> None:
        dump = {"identity": {"brand_name": "   ", "tagline": "Real"}}
        assert filled_fields_by_section(dump) == {"identity": ["identity.tagline"]}


class TestDiffFilledBySection:
    def test_no_change_returns_empty(self) -> None:
        before = {"identity": {"brand_name": "Visionarias"}}
        after = {"identity": {"brand_name": "Visionarias"}}
        assert diff_filled_by_section(before, after) == {}

    def test_new_field_in_existing_section(self) -> None:
        before = {"identity": {"brand_name": "Visionarias", "tagline": ""}}
        after = {"identity": {"brand_name": "Visionarias", "tagline": "Marca con alma"}}
        assert diff_filled_by_section(before, after) == {
            "identity": ["identity.tagline"],
        }

    def test_entire_new_section(self) -> None:
        before = {"identity": {"brand_name": "Visionarias"}}
        after = {
            "identity": {"brand_name": "Visionarias"},
            "strategy": {"mission": {"statement": "X"}},
        }
        assert diff_filled_by_section(before, after) == {
            "strategy": ["strategy.mission.statement"],
        }

    def test_multiple_sections_diffed_independently(self) -> None:
        before = {
            "identity": {"brand_name": "Visionarias"},
            "strategy": {"mission": {"statement": ""}},
        }
        after = {
            "identity": {"brand_name": "Visionarias", "tagline": "nueva"},
            "strategy": {"mission": {"statement": "llenada"}},
            "positioning": {"uvp": "nueva"},
        }
        delta = diff_filled_by_section(before, after)
        assert delta == {
            "identity": ["identity.tagline"],
            "strategy": ["strategy.mission.statement"],
            "positioning": ["positioning.uvp"],
        }

    def test_removed_field_is_not_reported(self) -> None:
        # "initial" mode can blank fields — diff only reports NEW fills
        before = {"identity": {"brand_name": "Viejo", "tagline": "Vieja"}}
        after = {"identity": {"brand_name": "Viejo", "tagline": ""}}
        assert diff_filled_by_section(before, after) == {}

    def test_noop_on_empty_inputs(self) -> None:
        assert diff_filled_by_section({}, {}) == {}
