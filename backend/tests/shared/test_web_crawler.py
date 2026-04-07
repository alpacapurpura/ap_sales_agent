"""Tests for shared WebCrawler — validates the module moved from brand correctly."""

from src.shared.infrastructure.web.crawler import (
    HIGH_KEYWORDS,
    MEDIUM_KEYWORDS,
    SKIP_EXTENSIONS,
    SKIP_PATTERNS,
    WebCrawler,
    extract_text_from_html,
    score_link,
    truncate_at_page_boundary,
)


class TestScoreLink:
    """Test link scoring for web crawling."""

    def test_skip_anchors(self):
        assert score_link("#section", "") == -1

    def test_skip_mailto(self):
        assert score_link("mailto:a@b.com", "") == -1

    def test_skip_tel(self):
        assert score_link("tel:+1234567890", "") == -1

    def test_skip_pdf(self):
        assert score_link("https://example.com/file.pdf", "") == -1

    def test_skip_blog(self):
        assert score_link("https://example.com/blog/post-1", "") == -1

    def test_high_score_about(self):
        assert score_link("https://example.com/about", "") == 10

    def test_high_score_nosotros(self):
        assert score_link("https://example.com/nosotros", "") == 10

    def test_high_score_from_anchor(self):
        assert score_link("https://example.com/page1", "Sobre Nosotros") == 10

    def test_medium_score_pricing(self):
        assert score_link("https://example.com/precios", "") == 5

    def test_low_score_generic(self):
        assert score_link("https://example.com/something", "") == 1


class TestExtractTextFromHtml:
    """Test HTML text extraction."""

    def test_removes_scripts(self):
        html = "<html><script>alert('x')</script><p>Hello</p></html>"
        result = extract_text_from_html(html)
        assert "alert" not in result
        assert "Hello" in result

    def test_removes_styles(self):
        html = "<html><style>.a{color:red}</style><p>World</p></html>"
        result = extract_text_from_html(html)
        assert "color" not in result
        assert "World" in result

    def test_preserves_header_marker(self):
        html = "<html><header>My Brand</header><p>Content</p></html>"
        result = extract_text_from_html(html)
        assert "[HEADER]" in result
        assert "My Brand" in result


class TestTruncateAtPageBoundary:
    """Test content truncation at page boundaries."""

    def test_no_truncation_needed(self):
        content = "short text"
        assert truncate_at_page_boundary(content, 100) == content

    def test_truncates_at_boundary(self):
        content = "Page 1\n=== FIN PAGINA ===\nPage 2\n=== FIN PAGINA ===\nPage 3"
        result = truncate_at_page_boundary(content, 40)
        assert result.endswith("=== FIN PAGINA ===")
        assert "Page 3" not in result

    def test_hard_truncate_without_boundary(self):
        content = "A" * 200
        result = truncate_at_page_boundary(content, 100)
        assert len(result) == 100


class TestWebCrawlerClass:
    """Test WebCrawler instantiation and structure."""

    def test_webcrawler_exists(self):
        crawler = WebCrawler()
        assert hasattr(crawler, "crawl_content")
        assert hasattr(crawler, "crawl_content_with_styles")

    def test_backward_compat_brandcrawler(self):
        """BrandCrawler alias still works."""
        from src.shared.infrastructure.web.crawler import BrandCrawler

        assert BrandCrawler is WebCrawler

    def test_brand_module_reexport(self):
        """Brand module re-export still works."""
        from src.modules.brand.application.extraction_crawler import BrandCrawler

        assert BrandCrawler is WebCrawler


class TestConstants:
    """Verify constants are properly defined."""

    def test_skip_patterns_is_frozenset(self):
        assert isinstance(SKIP_PATTERNS, frozenset)
        assert "blog" in SKIP_PATTERNS

    def test_skip_extensions_is_frozenset(self):
        assert isinstance(SKIP_EXTENSIONS, frozenset)
        assert ".pdf" in SKIP_EXTENSIONS

    def test_high_keywords_is_frozenset(self):
        assert isinstance(HIGH_KEYWORDS, frozenset)
        assert "about" in HIGH_KEYWORDS

    def test_medium_keywords_is_frozenset(self):
        assert isinstance(MEDIUM_KEYWORDS, frozenset)
        assert "pricing" in MEDIUM_KEYWORDS
