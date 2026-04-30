"""Tests for SegmentFilterEvaluator — runtime check + SQL predicate.

TDD RED-first per layer A (application).
Tests cover:
- In-memory evaluate_one() for each field type
- to_sql_predicate() produces valid SQLA expressions (inspect via str())
- ALL vs ANY combinator semantics
- Edge cases: empty filter → false(), single field, multiple fields
"""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest

from src.modules.campaigns.application.segment_filter_evaluator import SegmentFilterEvaluator
from src.modules.campaigns.domain.enums import SegmentFilterCombinator
from src.modules.campaigns.domain.segment_filter import (
    DateRange,
    PredefinedSegmentFilter,
    ScoreRange,
    TagsFilter,
)

TENANT_ID = uuid4()
NOW = dt.datetime.now(dt.timezone.utc)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

evaluator = SegmentFilterEvaluator()


def make_filter(**kwargs) -> PredefinedSegmentFilter:
    """Thin factory for PredefinedSegmentFilter with overrides."""
    return PredefinedSegmentFilter(**kwargs)


def make_lead(**kwargs) -> dict:
    """Thin factory for a lead dict snapshot."""
    base = {
        "lifecycle_stage": "SUBSCRIBER",
        "temperature": "WARM",
        "fit_score": 50,
        "intent_score": 60,
        "lead_source": "facebook",
        "country": "pe",
        "created_at": NOW - dt.timedelta(days=10),
        "last_interaction_date": NOW - dt.timedelta(days=2),
        "profile_data": {"tags": ["interesado", "vip"]},
        "is_blacklisted": False,
        "telegram_id": None,
        "whatsapp_id": "+51999000001",
        "instagram_id": None,
        "tiktok_id": None,
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# In-memory evaluate_one() tests
# ---------------------------------------------------------------------------


class TestEvaluateOneEmptyFilter:
    """Empty filter returns False (safer default)."""

    def test_empty_filter_returns_false(self):
        f = make_filter()
        assert evaluator.evaluate_one(f, make_lead()) is False


class TestEvaluateOneLifecycleStage:
    def test_match_lifecycle_stage(self):
        f = make_filter(lifecycle_stage=["SUBSCRIBER", "MQL"])
        assert evaluator.evaluate_one(f, make_lead(lifecycle_stage="SUBSCRIBER")) is True

    def test_no_match_lifecycle_stage(self):
        f = make_filter(lifecycle_stage=["CUSTOMER"])
        assert evaluator.evaluate_one(f, make_lead(lifecycle_stage="SUBSCRIBER")) is False


class TestEvaluateOneTemperature:
    def test_match_temperature(self):
        f = make_filter(temperature=["WARM", "HOT"])
        assert evaluator.evaluate_one(f, make_lead(temperature="WARM")) is True

    def test_no_match_temperature(self):
        f = make_filter(temperature=["HOT"])
        assert evaluator.evaluate_one(f, make_lead(temperature="COLD")) is False


class TestEvaluateOneScoreRange:
    def test_match_fit_score_range(self):
        f = make_filter(score_range=ScoreRange(fit_score_min=40, fit_score_max=80))
        assert evaluator.evaluate_one(f, make_lead(fit_score=60)) is True

    def test_no_match_fit_score_below(self):
        f = make_filter(score_range=ScoreRange(fit_score_min=70))
        assert evaluator.evaluate_one(f, make_lead(fit_score=50)) is False

    def test_match_intent_score_range(self):
        f = make_filter(score_range=ScoreRange(intent_score_min=50))
        assert evaluator.evaluate_one(f, make_lead(intent_score=60)) is True

    def test_no_match_intent_score_above(self):
        f = make_filter(score_range=ScoreRange(intent_score_max=30))
        assert evaluator.evaluate_one(f, make_lead(intent_score=60)) is False


class TestEvaluateOneSource:
    def test_match_source(self):
        f = make_filter(source=["facebook", "instagram"])
        assert evaluator.evaluate_one(f, make_lead(lead_source="facebook")) is True

    def test_no_match_source(self):
        f = make_filter(source=["google"])
        assert evaluator.evaluate_one(f, make_lead(lead_source="facebook")) is False


class TestEvaluateOneCountry:
    def test_match_country_lowercase(self):
        f = make_filter(country=["pe", "mx"])
        assert evaluator.evaluate_one(f, make_lead(country="pe")) is True

    def test_match_country_case_insensitive(self):
        f = make_filter(country=["PE"])
        assert evaluator.evaluate_one(f, make_lead(country="pe")) is True

    def test_no_match_country(self):
        f = make_filter(country=["ar"])
        assert evaluator.evaluate_one(f, make_lead(country="pe")) is False


class TestEvaluateOneDateRange:
    def test_match_created_at_range(self):
        f = make_filter(
            created_at_range=DateRange(
                gte=NOW - dt.timedelta(days=20),
                lte=NOW,
            )
        )
        lead = make_lead(created_at=NOW - dt.timedelta(days=10))
        assert evaluator.evaluate_one(f, lead) is True

    def test_no_match_created_at_range(self):
        f = make_filter(
            created_at_range=DateRange(
                gte=NOW - dt.timedelta(days=5),
            )
        )
        lead = make_lead(created_at=NOW - dt.timedelta(days=10))
        assert evaluator.evaluate_one(f, lead) is False

    def test_match_last_interaction_at_range(self):
        f = make_filter(
            last_interaction_at_range=DateRange(
                gte=NOW - dt.timedelta(days=7),
            )
        )
        lead = make_lead(last_interaction_date=NOW - dt.timedelta(days=2))
        assert evaluator.evaluate_one(f, lead) is True


class TestEvaluateOneTags:
    def test_match_tags_any(self):
        f = make_filter(tags=TagsFilter(mode="any", tags=["vip", "hot"]))
        lead = make_lead(profile_data={"tags": ["vip", "interesado"]})
        assert evaluator.evaluate_one(f, lead) is True

    def test_no_match_tags_any(self):
        f = make_filter(tags=TagsFilter(mode="any", tags=["hot"]))
        lead = make_lead(profile_data={"tags": ["cold"]})
        assert evaluator.evaluate_one(f, lead) is False

    def test_match_tags_all(self):
        f = make_filter(tags=TagsFilter(mode="all", tags=["vip", "interesado"]))
        lead = make_lead(profile_data={"tags": ["vip", "interesado", "extra"]})
        assert evaluator.evaluate_one(f, lead) is True

    def test_no_match_tags_all_partial(self):
        f = make_filter(tags=TagsFilter(mode="all", tags=["vip", "hot"]))
        lead = make_lead(profile_data={"tags": ["vip"]})
        assert evaluator.evaluate_one(f, lead) is False


class TestEvaluateOneIsBlacklisted:
    def test_match_blacklisted_true(self):
        f = make_filter(is_blacklisted=True)
        assert evaluator.evaluate_one(f, make_lead(is_blacklisted=True)) is True

    def test_no_match_blacklisted_true(self):
        f = make_filter(is_blacklisted=True)
        assert evaluator.evaluate_one(f, make_lead(is_blacklisted=False)) is False

    def test_match_blacklisted_false(self):
        f = make_filter(is_blacklisted=False)
        assert evaluator.evaluate_one(f, make_lead(is_blacklisted=False)) is True


class TestEvaluateOneChannelId:
    def test_match_has_whatsapp(self):
        f = make_filter(has_channel_id=["whatsapp_id"])
        assert evaluator.evaluate_one(f, make_lead(whatsapp_id="+51999")) is True

    def test_no_match_has_telegram(self):
        f = make_filter(has_channel_id=["telegram_id"])
        assert evaluator.evaluate_one(f, make_lead(telegram_id=None)) is False

    def test_match_any_of_channels(self):
        f = make_filter(has_channel_id=["telegram_id", "whatsapp_id"])
        assert evaluator.evaluate_one(f, make_lead(telegram_id=None, whatsapp_id="+51")) is True


class TestEvaluateCombinator:
    """ALL vs ANY combinator semantics."""

    def test_all_combinator_both_match(self):
        f = make_filter(
            combinator=SegmentFilterCombinator.ALL,
            temperature=["WARM"],
            country=["pe"],
        )
        lead = make_lead(temperature="WARM", country="pe")
        assert evaluator.evaluate_one(f, lead) is True

    def test_all_combinator_one_misses(self):
        f = make_filter(
            combinator=SegmentFilterCombinator.ALL,
            temperature=["HOT"],
            country=["pe"],
        )
        lead = make_lead(temperature="WARM", country="pe")
        assert evaluator.evaluate_one(f, lead) is False

    def test_any_combinator_one_match(self):
        f = make_filter(
            combinator=SegmentFilterCombinator.ANY,
            temperature=["HOT"],
            country=["pe"],
        )
        lead = make_lead(temperature="WARM", country="pe")
        assert evaluator.evaluate_one(f, lead) is True

    def test_any_combinator_none_match(self):
        f = make_filter(
            combinator=SegmentFilterCombinator.ANY,
            temperature=["HOT"],
            country=["ar"],
        )
        lead = make_lead(temperature="COLD", country="pe")
        assert evaluator.evaluate_one(f, lead) is False


# ---------------------------------------------------------------------------
# to_sql_predicate() — structural tests (no DB required)
# ---------------------------------------------------------------------------


class TestToSqlPredicateStructure:
    """Test that to_sql_predicate returns valid SQLA expressions without DB."""

    def _compile_predicate(self, predicate) -> str:
        """Compile predicate to SQL string for inspection (dialect-agnostic)."""
        from sqlalchemy.dialects import sqlite

        return str(predicate.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True}))

    def test_empty_filter_returns_false(self):
        f = make_filter()
        pred = evaluator.to_sql_predicate(f, tenant_id=TENANT_ID)
        sql = self._compile_predicate(pred)
        assert "false" in sql.lower() or "0" in sql  # SQLite false() = 0

    def test_temperature_filter_produces_in_clause(self):
        f = make_filter(temperature=["WARM", "HOT"])
        pred = evaluator.to_sql_predicate(f, tenant_id=TENANT_ID)
        sql = self._compile_predicate(pred)
        assert "leads.temperature" in sql
        assert "WARM" in sql

    def test_country_filter_lowercased(self):
        f = make_filter(country=["PE", "MX"])
        pred = evaluator.to_sql_predicate(f, tenant_id=TENANT_ID)
        sql = self._compile_predicate(pred)
        assert "leads.country" in sql
        assert "pe" in sql.lower()
        assert "mx" in sql.lower()

    def test_score_range_produces_comparison(self):
        f = make_filter(score_range=ScoreRange(fit_score_min=50, intent_score_max=80))
        pred = evaluator.to_sql_predicate(f, tenant_id=TENANT_ID)
        sql = self._compile_predicate(pred)
        assert "fit_score" in sql
        assert "intent_score" in sql

    def test_is_blacklisted_filter(self):
        f = make_filter(is_blacklisted=False)
        pred = evaluator.to_sql_predicate(f, tenant_id=TENANT_ID)
        sql = self._compile_predicate(pred)
        assert "is_blacklisted" in sql

    def test_channel_id_filter_not_null(self):
        f = make_filter(has_channel_id=["telegram_id"])
        pred = evaluator.to_sql_predicate(f, tenant_id=TENANT_ID)
        sql = self._compile_predicate(pred)
        assert "telegram_id" in sql

    def test_all_combinator_produces_and(self):
        f = make_filter(
            combinator=SegmentFilterCombinator.ALL,
            temperature=["WARM"],
            is_blacklisted=False,
        )
        pred = evaluator.to_sql_predicate(f, tenant_id=TENANT_ID)
        sql = self._compile_predicate(pred)
        assert "AND" in sql.upper()

    def test_any_combinator_produces_or(self):
        f = make_filter(
            combinator=SegmentFilterCombinator.ANY,
            temperature=["WARM"],
            is_blacklisted=False,
        )
        pred = evaluator.to_sql_predicate(f, tenant_id=TENANT_ID)
        sql = self._compile_predicate(pred)
        assert "OR" in sql.upper()

    def test_lifecycle_stage_uses_exists_subquery(self):
        """lifecycle_stage requires JOIN customer_profiles → EXISTS subquery."""
        f = make_filter(lifecycle_stage=["SUBSCRIBER", "MQL"])
        pred = evaluator.to_sql_predicate(f, tenant_id=TENANT_ID)
        sql = self._compile_predicate(pred)
        assert "customer_profiles" in sql or "EXISTS" in sql.upper()

    def test_source_uses_exists_subquery(self):
        """source requires JOIN customer_profiles → EXISTS subquery."""
        f = make_filter(source=["facebook"])
        pred = evaluator.to_sql_predicate(f, tenant_id=TENANT_ID)
        sql = self._compile_predicate(pred)
        assert "customer_profiles" in sql or "EXISTS" in sql.upper()

    def test_date_range_filter_structure(self):
        f = make_filter(
            created_at_range=DateRange(
                gte=NOW - dt.timedelta(days=30),
                lte=NOW,
            )
        )
        pred = evaluator.to_sql_predicate(f, tenant_id=TENANT_ID)
        sql = self._compile_predicate(pred)
        assert "leads.created_at" in sql

    def test_last_interaction_range_filter_structure(self):
        f = make_filter(last_interaction_at_range=DateRange(gte=NOW - dt.timedelta(days=7)))
        pred = evaluator.to_sql_predicate(f, tenant_id=TENANT_ID)
        sql = self._compile_predicate(pred)
        assert "last_interaction_date" in sql

    def test_email_channel_filter_raises_value_error(self):
        """email channel_id has no direct column on LeadModel → ValueError from evaluator."""
        # email is a valid ChannelIdentifier enum value but does NOT exist as a column
        # on LeadModel (it lives on CustomerIdentityModel). The evaluator raises ValueError.
        f = make_filter(has_channel_id=["email"])
        with pytest.raises(ValueError, match="no existe en LeadModel"):
            evaluator.to_sql_predicate(f, tenant_id=TENANT_ID)
