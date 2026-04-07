"""Tests for BrandExtractionService -- crawling, parsing, merging with mocked LLM."""

import pytest

from src.modules.brand.application.extraction_service import (
    _HIGH_KEYWORDS,
    _SKIP_PATTERNS,
    PROFILE_FAST,
    PROFILE_SAFE,
    BrandAuthorityExtraction,
    BrandExtractionService,
    BrandPeopleContactExtraction,
    BrandTestimonialsExtraction,
    _summarize_settings,
)
from src.modules.brand.domain import (
    BrandIdentity,
    BrandPositioning,
    BrandSettings,
)


class TestExtractionProfiles:
    def test_safe_profile_values(self):
        assert PROFILE_SAFE.name == "safe"
        assert PROFILE_SAFE.concurrency_waves == 3
        assert PROFILE_SAFE.retries == 3

    def test_fast_profile_values(self):
        assert PROFILE_FAST.name == "fast"
        assert PROFILE_FAST.concurrency_waves == 1
        assert PROFILE_FAST.retries == 2

    def test_profile_is_frozen(self):
        with pytest.raises(AttributeError):
            PROFILE_SAFE.name = "modified"


class TestLinkScoring:
    def test_skip_mailto(self):
        assert BrandExtractionService._score_link("mailto:test@example.com", "") == -1

    def test_skip_tel(self):
        assert BrandExtractionService._score_link("tel:+1234567890", "") == -1

    def test_skip_pdf(self):
        assert (
            BrandExtractionService._score_link("https://example.com/file.pdf", "") == -1
        )

    def test_skip_blog(self):
        assert (
            BrandExtractionService._score_link("https://example.com/blog/post-1", "")
            == -1
        )

    def test_high_score_about(self):
        assert BrandExtractionService._score_link("https://example.com/about", "") == 10

    def test_high_score_nosotros(self):
        assert (
            BrandExtractionService._score_link("https://example.com/nosotros", "") == 10
        )

    def test_high_score_anchor_text(self):
        assert (
            BrandExtractionService._score_link("https://example.com/info", "About Us")
            == 10
        )

    def test_medium_score_pricing(self):
        assert (
            BrandExtractionService._score_link("https://example.com/pricing", "") == 5
        )

    def test_low_score_generic(self):
        assert (
            BrandExtractionService._score_link("https://example.com/random-page", "")
            == 1
        )


class TestHtmlExtraction:
    def test_extract_text_removes_scripts(self):
        html = "<html><body><script>alert('x')</script><p>Hello</p></body></html>"
        result = BrandExtractionService._extract_text_from_html(html)
        assert "alert" not in result
        assert "Hello" in result

    def test_extract_text_preserves_header_marker(self):
        html = "<html><body><header>Brand Name</header><p>Content</p></body></html>"
        result = BrandExtractionService._extract_text_from_html(html)
        assert "[HEADER]" in result
        assert "Brand Name" in result

    def test_extract_text_preserves_footer_marker(self):
        html = "<html><body><footer>Copyright 2024</footer></body></html>"
        result = BrandExtractionService._extract_text_from_html(html)
        assert "[FOOTER]" in result


class TestCssExtraction:
    def test_extracts_css_variables(self):
        css = ":root { --color-primary: #3b82f6; --color-accent: #ef4444; }"
        result = BrandExtractionService._extract_css_relevant(css)
        assert "--color-primary" in result
        assert "#3b82f6" in result

    def test_skips_framework_boilerplate(self):
        css = ".w-widget { display: block; }\n.brand { color: #ff0000; }"
        result = BrandExtractionService._extract_css_relevant(css)
        assert "w-widget" not in result
        assert "#ff0000" in result

    def test_respects_max_chars(self):
        css = "\n".join([f"--var-{i}: #{i:06x};" for i in range(1000)])
        result = BrandExtractionService._extract_css_relevant(css, max_chars=500)
        assert len(result) <= 500


class TestSummarizeSettings:
    def test_empty_settings(self):
        s = BrandSettings()
        summary = _summarize_settings(s)
        assert summary["identity"] is False
        assert summary["team_count"] == 0

    def test_populated_settings(self, sample_settings):
        summary = _summarize_settings(sample_settings)
        assert summary["identity"] is True
        assert summary["story"] is True
        assert summary["visuals"] is True


class TestIsEmpty:
    def test_empty_identity(self):
        assert BrandExtractionService._is_empty(BrandIdentity()) is True

    def test_non_empty_identity(self):
        assert BrandExtractionService._is_empty(BrandIdentity(brand_name="X")) is False

    def test_empty_positioning(self):
        assert BrandExtractionService._is_empty(BrandPositioning()) is True

    def test_non_empty_positioning(self):
        assert (
            BrandExtractionService._is_empty(BrandPositioning(brand_essence="Core"))
            is False
        )


class TestTruncateAtPageBoundary:
    def test_no_truncation_needed(self):
        content = "Short content"
        assert BrandExtractionService._truncate_at_page_boundary(content) == content

    def test_truncates_at_marker(self):
        content = (
            "Page1\n=== FIN PAGINA ===\nPage2\n=== FIN PAGINA ===\nPage3 very long..."
            + "x" * 100000
        )
        result = BrandExtractionService._truncate_at_page_boundary(
            content, max_chars=60
        )
        assert result.endswith("=== FIN PAGINA ===")
        assert len(result) <= 60


class TestExtractionModels:
    """Test the intermediate extraction Pydantic models."""

    def test_people_contact_extraction_defaults(self):
        m = BrandPeopleContactExtraction()
        assert m.key_leadership == []
        assert m.contact is None

    def test_testimonials_extraction_defaults(self):
        m = BrandTestimonialsExtraction()
        assert m.testimonials == []

    def test_authority_extraction_defaults(self):
        m = BrandAuthorityExtraction()
        assert m.authority_vault == []


class TestSkipAndHighKeywords:
    """Verify the keyword sets are populated and contain expected entries."""

    def test_skip_patterns_contains_blog(self):
        assert "blog" in _SKIP_PATTERNS
        assert "cart" in _SKIP_PATTERNS
        assert "login" in _SKIP_PATTERNS

    def test_high_keywords_contains_about(self):
        assert "about" in _HIGH_KEYWORDS
        assert "nosotros" in _HIGH_KEYWORDS
        assert "testimonials" in _HIGH_KEYWORDS
