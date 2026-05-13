"""Tests for SegmentFilter DSL — v1 predefined fields.

Verifies extra='forbid', combinator values, score_range bounds,
country lowercase ISO, tags mode, and property-based fuzzing.
"""

from __future__ import annotations

import datetime as dt

import pytest
from hypothesis import given, settings, strategies as st
from pydantic import ValidationError

from luana_core_campaigns.domain.enums import SegmentFilterCombinator
from luana_core_campaigns.domain.segment_filter import (
    DateRange,
    PredefinedSegmentFilter,
    ScoreRange,
    TagsFilter,
)


NOW = dt.datetime.now(dt.timezone.utc)


class TestPredefinedSegmentFilterStrict:
    """Test extra='forbid' on all filter classes."""

    def test_empty_filter_valid(self):
        """Empty filter (all None fields) is valid."""
        f = PredefinedSegmentFilter()
        assert f.combinator == SegmentFilterCombinator.ALL

    def test_extra_field_rejected(self):
        """Extra field should be rejected by extra='forbid'."""
        with pytest.raises(ValidationError):
            PredefinedSegmentFilter(unknown_field="value")

    def test_combinator_all(self):
        """combinator='all' should be accepted."""
        f = PredefinedSegmentFilter(combinator="all")
        assert f.combinator == SegmentFilterCombinator.ALL

    def test_combinator_any(self):
        """combinator='any' should be accepted."""
        f = PredefinedSegmentFilter(combinator="any")
        assert f.combinator == SegmentFilterCombinator.ANY

    def test_invalid_combinator(self):
        """Invalid combinator value should be rejected."""
        with pytest.raises(ValidationError):
            PredefinedSegmentFilter(combinator="or")


class TestScoreRange:
    """Test ScoreRange bounds validation."""

    def test_valid_score_range(self):
        """A valid score range should be accepted."""
        sr = ScoreRange(fit_score_min=20, fit_score_max=80)
        assert sr.fit_score_min == 20
        assert sr.fit_score_max == 80

    def test_score_below_zero(self):
        """Scores below 0 should be rejected."""
        with pytest.raises(ValidationError):
            ScoreRange(fit_score_min=-1)

    def test_score_above_100(self):
        """Scores above 100 should be rejected."""
        with pytest.raises(ValidationError):
            ScoreRange(fit_score_max=101)

    def test_all_none_ok(self):
        """All None scores is valid."""
        sr = ScoreRange()
        assert sr.fit_score_min is None
        assert sr.fit_score_max is None

    def test_score_range_extra_field_rejected(self):
        """Extra fields in ScoreRange should be rejected."""
        with pytest.raises(ValidationError):
            ScoreRange(unknown_score=50)


class TestDateRange:
    """Test DateRange validation."""

    def test_valid_date_range(self):
        """Valid gte/lte date range should be accepted."""
        dr = DateRange(gte=NOW)
        assert dr.gte == NOW

    def test_both_none_ok(self):
        """All None is valid."""
        dr = DateRange()
        assert dr.gte is None
        assert dr.lte is None

    def test_date_range_extra_field_rejected(self):
        """Extra fields in DateRange should be rejected."""
        with pytest.raises(ValidationError):
            DateRange(unknown_date=NOW)


class TestTagsFilter:
    """Test TagsFilter validation."""

    def test_valid_any_mode(self):
        """mode='any' with tags list should be valid."""
        tf = TagsFilter(mode="any", tags=["hot-lead", "interested"])
        assert tf.mode == "any"

    def test_valid_all_mode(self):
        """mode='all' should be accepted."""
        tf = TagsFilter(mode="all", tags=["premium"])
        assert tf.mode == "all"

    def test_invalid_mode(self):
        """Invalid mode should be rejected."""
        with pytest.raises(ValidationError):
            TagsFilter(mode="none")

    def test_empty_tags_ok(self):
        """Empty tags list is valid."""
        tf = TagsFilter(tags=[])
        assert tf.tags == []

    def test_tags_extra_field_rejected(self):
        """Extra fields in TagsFilter should be rejected."""
        with pytest.raises(ValidationError):
            TagsFilter(unknown_field="value")


class TestPredefinedFilterFields:
    """Test individual field acceptance in PredefinedSegmentFilter."""

    def test_lifecycle_stage_filter(self):
        """lifecycle_stage field accepts valid values."""
        f = PredefinedSegmentFilter(lifecycle_stage=["MQL", "SQL"])
        assert f.lifecycle_stage == ["MQL", "SQL"]

    def test_invalid_lifecycle_stage(self):
        """Invalid lifecycle stage should be rejected."""
        with pytest.raises(ValidationError):
            PredefinedSegmentFilter(lifecycle_stage=["UNKNOWN_STAGE"])

    def test_temperature_filter(self):
        """temperature field accepts valid values."""
        f = PredefinedSegmentFilter(temperature=["HOT", "WARM"])
        assert f.temperature == ["HOT", "WARM"]

    def test_invalid_temperature(self):
        """Invalid temperature should be rejected."""
        with pytest.raises(ValidationError):
            PredefinedSegmentFilter(temperature=["LUKEWARM"])

    def test_has_channel_id_filter(self):
        """has_channel_id accepts valid ChannelIdentifier values."""
        f = PredefinedSegmentFilter(has_channel_id=["telegram_id", "email"])
        assert "telegram_id" in f.has_channel_id

    def test_invalid_channel_id(self):
        """Invalid channel identifier should be rejected."""
        with pytest.raises(ValidationError):
            PredefinedSegmentFilter(has_channel_id=["sms"])

    def test_is_blacklisted_bool(self):
        """is_blacklisted accepts bool values."""
        f = PredefinedSegmentFilter(is_blacklisted=True)
        assert f.is_blacklisted is True

    def test_score_range_nested(self):
        """score_range accepts ScoreRange nested model."""
        f = PredefinedSegmentFilter(score_range=ScoreRange(fit_score_min=50))
        assert f.score_range is not None
        assert f.score_range.fit_score_min == 50

    def test_country_list(self):
        """country field accepts list of ISO country codes."""
        f = PredefinedSegmentFilter(country=["pe", "mx", "co"])
        assert "pe" in f.country

    def test_source_list(self):
        """source field accepts list of strings."""
        f = PredefinedSegmentFilter(source=["facebook", "instagram"])
        assert "facebook" in f.source


class TestPropertyBasedFuzzing:
    """Property-based fuzz tests for PredefinedSegmentFilter."""

    @settings(max_examples=50)
    @given(extra_key=st.text(min_size=1, max_size=30).filter(lambda x: x.isidentifier()))
    def test_no_extra_fields_accepted(self, extra_key):
        """No extra field should ever be accepted."""
        # Skip known valid fields
        valid_fields = {
            "combinator",
            "lifecycle_stage",
            "temperature",
            "score_range",
            "source",
            "country",
            "created_at_range",
            "last_interaction_at_range",
            "tags",
            "is_blacklisted",
            "has_channel_id",
        }
        if extra_key in valid_fields:
            return
        with pytest.raises(ValidationError):
            PredefinedSegmentFilter(**{extra_key: "some_value"})

    @settings(max_examples=50)
    @given(score=st.integers(min_value=0, max_value=100))
    def test_valid_scores_accepted(self, score):
        """All scores in [0, 100] should be accepted."""
        sr = ScoreRange(fit_score_min=score, fit_score_max=score)
        assert sr.fit_score_min == score
        assert sr.fit_score_max == score
