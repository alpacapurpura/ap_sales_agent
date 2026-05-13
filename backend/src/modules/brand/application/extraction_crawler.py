"""Backward compat — crawler moved to shared/infrastructure/web/crawler.py."""

from luana_core_platform.infrastructure.web.crawler import (
    _HIGH_KEYWORDS,
    _MEDIUM_KEYWORDS,
    _SKIP_EXTENSIONS,
    _SKIP_PATTERNS,
    HIGH_KEYWORDS,
    MEDIUM_KEYWORDS,
    SKIP_EXTENSIONS,
    SKIP_PATTERNS,
    WebCrawler,
    extract_css_relevant,
    extract_html_with_styles,
    extract_text_from_html,
    score_link,
    truncate_at_page_boundary,
)

# Backward-compat: BrandCrawler is now WebCrawler
BrandCrawler = WebCrawler

__all__ = [
    "HIGH_KEYWORDS",
    "MEDIUM_KEYWORDS",
    "SKIP_EXTENSIONS",
    "SKIP_PATTERNS",
    "_HIGH_KEYWORDS",
    "_MEDIUM_KEYWORDS",
    "_SKIP_EXTENSIONS",
    "_SKIP_PATTERNS",
    "BrandCrawler",
    "WebCrawler",
    "extract_css_relevant",
    "extract_html_with_styles",
    "extract_text_from_html",
    "score_link",
    "truncate_at_page_boundary",
]
