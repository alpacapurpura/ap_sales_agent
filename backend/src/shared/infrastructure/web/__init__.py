"""Shared web infrastructure — crawlers and HTML parsing utilities."""

from luana_core_platform.infrastructure.web.crawler import (
    WebCrawler,
    extract_css_relevant,
    extract_html_with_styles,
    extract_text_from_html,
    score_link,
    truncate_at_page_boundary,
)

__all__ = [
    "WebCrawler",
    "extract_css_relevant",
    "extract_html_with_styles",
    "extract_text_from_html",
    "score_link",
    "truncate_at_page_boundary",
]
