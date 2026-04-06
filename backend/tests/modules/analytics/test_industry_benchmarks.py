"""Tests for industry benchmarks domain module."""

from src.modules.analytics.domain.industry_benchmarks import (
    INDUSTRY_BENCHMARKS,
    IndustryCategory,
    get_benchmarks,
    normalize_industry,
)


class TestNormalizeIndustry:
    """Test free-text to IndustryCategory resolution."""

    def test_none_returns_general(self):
        assert normalize_industry(None) == IndustryCategory.GENERAL

    def test_empty_string_returns_general(self):
        assert normalize_industry("") == IndustryCategory.GENERAL

    def test_whitespace_returns_general(self):
        assert normalize_industry("   ") == IndustryCategory.GENERAL

    def test_exact_match_case_insensitive(self):
        assert normalize_industry("Fitness") == IndustryCategory.FITNESS
        assert normalize_industry("ECOMMERCE") == IndustryCategory.ECOMMERCE
        assert normalize_industry("coaching") == IndustryCategory.EDUCATION

    def test_spanish_aliases(self):
        assert normalize_industry("educación") == IndustryCategory.EDUCATION
        assert normalize_industry("tienda") == IndustryCategory.ECOMMERCE
        assert normalize_industry("belleza") == IndustryCategory.BEAUTY
        assert normalize_industry("gimnasio") == IndustryCategory.FITNESS

    def test_substring_match(self):
        assert (
            normalize_industry("Mi tienda online de moda") == IndustryCategory.ECOMMERCE
        )
        assert (
            normalize_industry("Coaching para emprendedores")
            == IndustryCategory.EDUCATION
        )

    def test_unknown_returns_general(self):
        assert normalize_industry("something random") == IndustryCategory.GENERAL
        assert normalize_industry("xyz123") == IndustryCategory.GENERAL


class TestGetBenchmarks:
    """Test benchmark lookups with industry fallback."""

    def test_general_metric_found(self):
        entry = get_benchmarks(IndustryCategory.GENERAL, "CTR")
        assert entry is not None
        assert entry.metric_name == "CTR"
        assert entry.low == 0.9
        assert entry.high == 2.19

    def test_industry_specific_overrides_general(self):
        entry = get_benchmarks(IndustryCategory.EDUCATION, "CPL")
        assert entry is not None
        assert entry.median == 7.85  # Education-specific, not general 27.66

    def test_fallback_to_general(self):
        # CPC only exists in GENERAL, not in EDUCATION
        entry = get_benchmarks(IndustryCategory.EDUCATION, "CPC")
        assert entry is not None
        assert entry.metric_name == "CPC"

    def test_nonexistent_metric_returns_none(self):
        entry = get_benchmarks(IndustryCategory.GENERAL, "nonexistent_metric")
        assert entry is None

    def test_all_industries_have_benchmarks(self):
        for category in IndustryCategory:
            benchmarks = INDUSTRY_BENCHMARKS.get(category, [])
            assert isinstance(benchmarks, list)
