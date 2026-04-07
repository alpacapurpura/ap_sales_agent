"""Web crawler and HTML/CSS parsing utilities.

Stateless module — no database, no tenant context.
Extracts text, CSS variables, inline styles, and visual identity data from HTML.
"""

from __future__ import annotations

import asyncio
import re
from urllib.parse import urljoin, urlparse

import httpx
import structlog
from bs4 import BeautifulSoup

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# URL / link scoring constants
# ---------------------------------------------------------------------------

SKIP_PATTERNS: frozenset[str] = frozenset(
    {
        "blog",
        "post",
        "wp-admin",
        "login",
        "cart",
        "search",
        "feed",
        "tag",
        "category",
        "author",
        "page",
        "wp-content",
        "wp-includes",
        "admin",
        "checkout",
        "account",
        "signup",
        "register",
    }
)
SKIP_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".pdf",
        ".zip",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".mp4",
        ".mp3",
        ".doc",
        ".docx",
        ".xls",
    }
)
HIGH_KEYWORDS: frozenset[str] = frozenset(
    {
        "about",
        "nosotros",
        "nosotras",
        "quienes-somos",
        "equipo",
        "team",
        "servicios",
        "services",
        "contacto",
        "contact",
        "testimonios",
        "testimonials",
        "casos",
        "casos-de-exito",
        "reviews",
    }
)
MEDIUM_KEYWORDS: frozenset[str] = frozenset(
    {
        "legal",
        "terminos",
        "terms",
        "privacidad",
        "privacy",
        "historia",
        "story",
        "mision",
        "vision",
        "precios",
        "pricing",
        "partners",
        "socios",
        "clientes",
        "metodologia",
        "portafolio",
    }
)

# Backward-compat aliases
_SKIP_PATTERNS = SKIP_PATTERNS
_SKIP_EXTENSIONS = SKIP_EXTENSIONS
_HIGH_KEYWORDS = HIGH_KEYWORDS
_MEDIUM_KEYWORDS = MEDIUM_KEYWORDS

# ---------------------------------------------------------------------------
# Standalone functions
# ---------------------------------------------------------------------------


def score_link(url: str, anchor_text: str) -> int:
    """Score an internal link by relevance to extraction. Returns -1 to skip."""
    parsed = urlparse(url)
    path = parsed.path.lower().rstrip("/")

    # Skip anchors, mailto, tel
    if url.startswith(("#", "mailto:", "tel:")):
        return -1

    # Skip file downloads
    for ext in SKIP_EXTENSIONS:
        if path.endswith(ext):
            return -1

    # Collect terms from path segments and anchor text
    path_segments = set(path.strip("/").split("/")) if path.strip("/") else set()
    anchor_words = set(anchor_text.lower().split()) if anchor_text else set()
    all_terms = path_segments | anchor_words

    # Skip patterns
    if all_terms & SKIP_PATTERNS:
        return -1

    # High relevance
    if all_terms & HIGH_KEYWORDS:
        return 10

    # Medium relevance
    if all_terms & MEDIUM_KEYWORDS:
        return 5

    # Low: any other same-domain link
    return 1


def extract_text_from_html(html: str) -> str:
    """Parse HTML and extract clean text content, preserving structural sections."""
    soup = BeautifulSoup(html, "html.parser")
    # Remove only non-content elements
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()

    # Preserve header/nav/footer with section markers
    for tag_name, marker in [
        ("header", "HEADER"),
        ("nav", "NAV"),
        ("footer", "FOOTER"),
    ]:
        for tag in soup.find_all(tag_name):
            section_text = tag.get_text(separator="\n", strip=True)
            if section_text:
                tag.replace_with(f"\n[{marker}]\n{section_text}\n[/{marker}]\n")
            else:
                tag.decompose()

    return soup.get_text(separator="\n", strip=True)


def extract_css_relevant(css_text: str, max_chars: int = 8000) -> str:
    """Extract only brand-relevant CSS rules (colors, fonts, variables) from raw CSS.

    Uses a two-tier approach:
    1. HIGH priority: CSS variable definitions (--color-name: #hex) — always included first
    2. NORMAL priority: color/font declarations in custom classes — fill remaining space

    Filters out reset/normalize rules, layout-only rules, and framework boilerplate.
    """
    # Strip @font-face blocks (multi-line) — font names are captured from
    # font-family declarations and WebFont.load() instead
    css_text = re.sub(
        r"@font-face\s*\{[^}]*\}", "", css_text, flags=re.DOTALL | re.IGNORECASE
    )

    # Patterns that indicate framework boilerplate to skip
    skip_pattern = re.compile(
        r"(\.w-icon|\.w-widget|webflow-icons|"
        r"webkit-appearance|moz-osx-font|speak:\s*none|"
        r"text-size-adjust|box-sizing|display:\s*(block|inline|none|flex)|"
        r"vertical-align|line-height:\s*[01]|outline:\s*0|"
        r"border:\s*0(?:;|\s)|padding:\s*0(?:;|\s)|margin:\s*0(?:;|\s)|"
        r"overflow:\s*(hidden|auto|visible)|cursor:\s*|"
        r"src:\s*url\(|format\(|font-display|font-style)",
        re.IGNORECASE,
    )

    # Tier 1: CSS variable definitions with color values
    var_pattern = re.compile(r"--[\w-]+\s*:", re.IGNORECASE)
    # Tier 2: Color/font declarations in custom styles
    color_pattern = re.compile(
        r"(#[0-9a-fA-F]{3,8}|rgba?\s*\(|hsla?\s*\(|"
        r"(?:background-)?color\s*:|background-image|gradient|"
        r"font-family|border-radius)",
        re.IGNORECASE,
    )
    # Skip generic/unset values that add no information
    noise_pattern = re.compile(
        r"(:\s*(inherit|unset|initial|normal|none|auto|transparent)\s*;|"
        r"color:\s*#0000\s|background-color:\s*#0000\s|"
        r"font-weight:\s*(normal|bold)\s*;)",
        re.IGNORECASE,
    )

    high_priority: list[str] = []
    normal_priority: list[str] = []

    for line in css_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if skip_pattern.search(stripped):
            continue
        if noise_pattern.search(stripped):
            continue

        if var_pattern.search(stripped):
            high_priority.append(stripped)
        elif color_pattern.search(stripped):
            normal_priority.append(stripped)

    # Compose: variables first (most valuable), then color rules
    result_parts = high_priority
    remaining = max_chars - len("\n".join(result_parts))
    if remaining > 0:
        normal_text = "\n".join(normal_priority)
        if len(normal_text) > remaining:
            normal_text = normal_text[:remaining]
        result_parts_str = "\n".join(result_parts)
        if normal_text.strip():
            result_parts_str += "\n" + normal_text
        return result_parts_str

    result = "\n".join(result_parts)
    if len(result) > max_chars:
        result = result[:max_chars]
    return result


def extract_html_with_styles(html: str, external_css: str = "") -> str:  # noqa: C901
    """Parse HTML preserving CSS data for visual identity analysis.

    Unlike extract_text_from_html which strips <style> tags, this method
    extracts and preserves CSS variables, inline styles, class names,
    Google Font links and theme-color meta — everything needed for
    accurate color/font extraction by the LLM.

    Args:
        html: Raw HTML of the page.
        external_css: Pre-fetched content from external <link rel="stylesheet"> files,
                      already filtered for brand-relevant rules.
    """
    soup = BeautifulSoup(html, "html.parser")

    # --- Extract WebFont.load() fonts from scripts BEFORE decomposing ---
    webfont_fonts: list[str] = []
    for script_tag in soup.find_all("script"):
        script_text = script_tag.string or ""
        if "WebFont.load" in script_text or "webfont" in script_text.lower():
            families_match = re.findall(
                r"families\s*:\s*\[(.*?)\]", script_text, re.DOTALL
            )
            for families_str in families_match:
                for fam in re.findall(r'"([^"]+)"|\'([^\']+)\'', families_str):
                    font_raw = fam[0] or fam[1]
                    font_name = font_raw.split(":")[0].strip()
                    if font_name:
                        webfont_fonts.append(f"WebFont: {font_name}")

    # Remove only scripts (keep styles!)
    for tag in soup.find_all("script"):
        tag.decompose()

    # --- [CSS_STYLES] section ---
    css_parts: list[str] = []

    # External CSS (fetched from <link rel="stylesheet"> files)
    if external_css.strip():
        css_parts.append(f"/* === EXTERNAL STYLESHEETS === */\n{external_css}")

    # <style> tag contents
    for style_tag in soup.find_all("style"):
        text = style_tag.get_text(strip=True)
        if text:
            css_parts.append(text)

    # <meta name="theme-color">
    for meta in soup.find_all("meta", attrs={"name": "theme-color"}):
        color = meta.get("content", "")
        if color:
            css_parts.append(f"theme-color: {color}")

    # Google Fonts links — extract font family names
    for link in soup.find_all("link", href=True):
        href = link["href"]
        if "fonts.googleapis.com" in href:
            match = re.findall(r"family=([^&]+)", href)
            for fam in match:
                font_name = fam.split(":")[0].replace("+", " ")
                css_parts.append(f"Google Font: {font_name}")

    # WebFont.load() fonts (extracted before script decomposition)
    css_parts.extend(webfont_fonts)

    # Favicon links
    for link in soup.find_all("link", href=True):
        rel = " ".join(link.get("rel", []))
        if any(k in rel for k in ("icon", "shortcut", "apple-touch-icon")):
            css_parts.append(f"Favicon: {link['href']}")

    css_section = "\n".join(css_parts) if css_parts else "(no CSS data found)"

    # --- [INLINE_STYLES] section ---
    inline_parts: list[str] = []
    for i, el in enumerate(soup.find_all(attrs={"style": True})):
        if i >= 50:
            break
        tag_name = el.name
        classes = " ".join(el.get("class", []))
        style_val = el.get("style", "")
        label = f"{tag_name}.{classes}" if classes else tag_name
        inline_parts.append(f"{label}: {style_val}")

    inline_section = (
        "\n".join(inline_parts) if inline_parts else "(no inline styles found)"
    )

    # --- [KEY_ELEMENTS] section ---
    key_tags = [
        "body",
        "header",
        "nav",
        "footer",
        "main",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "button",
        "a",
    ]
    element_parts: list[str] = []
    for tag_name in key_tags:
        for j, el in enumerate(soup.find_all(tag_name)):
            if j >= 5:
                break
            classes = el.get("class")
            if classes:
                element_parts.append(f'<{tag_name} class="{" ".join(classes)}">')

    elements_section = (
        "\n".join(element_parts) if element_parts else "(no class attributes found)"
    )

    # --- [TEXT_CONTENT] section (lightweight body text for context) ---
    body = soup.find("body")
    text_content = ""
    if body:
        body_copy = BeautifulSoup(str(body), "html.parser")
        for s in body_copy.find_all("style"):
            s.decompose()
        text_content = body_copy.get_text(separator="\n", strip=True)
    else:
        text_content = soup.get_text(separator="\n", strip=True)

    # Combine sections
    return (
        f"[CSS_STYLES]\n{css_section}\n[/CSS_STYLES]\n\n"
        f"[INLINE_STYLES]\n{inline_section}\n[/INLINE_STYLES]\n\n"
        f"[KEY_ELEMENTS]\n{elements_section}\n[/KEY_ELEMENTS]\n\n"
        f"[TEXT_CONTENT]\n{text_content}\n[/TEXT_CONTENT]"
    )


def truncate_at_page_boundary(content: str, max_chars: int = 50000) -> str:
    """Truncate content at the nearest === FIN PAGINA === boundary within max_chars."""
    if len(content) <= max_chars:
        return content
    marker = "=== FIN PAGINA ==="
    last_marker = content.rfind(marker, 0, max_chars)
    if last_marker > 0:
        return content[: last_marker + len(marker)]
    return content[:max_chars]


# ---------------------------------------------------------------------------
# WebCrawler — stateless HTTP crawler
# ---------------------------------------------------------------------------


class WebCrawler:
    """Stateless web crawler for content extraction.

    Does not hold database references or tenant context —
    only needs httpx for HTTP calls.
    """

    _USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    async def crawl_content(self, url: str) -> str:
        """Crawl the URL and up to 8 scored internal subpages, returning labeled text content."""
        try:
            base_domain = urlparse(url).netloc
            headers = {"User-Agent": self._USER_AGENT}

            async with httpx.AsyncClient(
                timeout=15.0, follow_redirects=True, headers=headers
            ) as client:
                # Fetch main page
                response = await client.get(url)
                response.raise_for_status()
                main_text = extract_text_from_html(response.text)

                # Score and rank internal links
                soup = BeautifulSoup(response.text, "html.parser")
                normalized_main = url.rstrip("/")
                seen_urls: set[str] = {normalized_main}
                scored_links: list[tuple[int, str]] = []

                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"]
                    full_url = urljoin(url, href)
                    parsed = urlparse(full_url)
                    clean_url = parsed._replace(fragment="").geturl().rstrip("/")

                    if (
                        parsed.netloc == base_domain
                        and clean_url not in seen_urls
                        and parsed.scheme in ("http", "https")
                    ):
                        link_score = score_link(clean_url, a_tag.get_text(strip=True))
                        if link_score >= 0:
                            seen_urls.add(clean_url)
                            scored_links.append((link_score, clean_url))

                # Sort by score descending, take top 8
                scored_links.sort(key=lambda x: x[0], reverse=True)
                top_links = [link_url for _, link_url in scored_links[:8]]

                logger.info(
                    "crawl_links_scored",
                    url=url,
                    total_found=len(scored_links),
                    selected=len(top_links),
                    top_urls=top_links[:4],
                )

                # Fetch subpages concurrently
                async def _fetch_subpage(sub_url: str) -> tuple[str, str]:
                    try:
                        sub_response = await client.get(sub_url)
                        sub_response.raise_for_status()
                        return sub_url, extract_text_from_html(sub_response.text)
                    except Exception:
                        return sub_url, ""

                subpage_results = await asyncio.gather(
                    *[_fetch_subpage(link) for link in top_links]
                )

            # Build labeled content
            parts: list[str] = [
                f"=== PAGINA PRINCIPAL: {url} ===\n{main_text}\n=== FIN PAGINA ==="
            ]
            for sub_url, sub_text in subpage_results:
                if sub_text.strip():
                    parts.append(
                        f"=== PAGINA: {sub_url} ===\n{sub_text}\n=== FIN PAGINA ==="
                    )

            result = "\n\n".join(parts)[:100_000]
            pages_crawled = len(parts)
            logger.info(
                "crawl_completed",
                url=url,
                pages_crawled=pages_crawled,
                total_chars=len(result),
            )
            return result

        except Exception as e:
            logger.error("crawl_exception", url=url, error=str(e))
            return ""

    async def crawl_content_with_styles(self, url: str) -> str:
        """Crawl the main page preserving CSS data for visual identity extraction."""
        try:
            headers = {"User-Agent": self._USER_AGENT}
            async with httpx.AsyncClient(
                timeout=15.0, follow_redirects=True, headers=headers
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text

                # Discover external CSS files from <link rel="stylesheet">
                soup = BeautifulSoup(html, "html.parser")
                css_links: list[str] = []
                for link_tag in soup.find_all("link", rel=True, href=True):
                    rel = link_tag.get("rel", [])
                    if "stylesheet" in rel:
                        href = link_tag["href"]
                        if "fonts.googleapis.com" in href:
                            continue
                        full_url = urljoin(url, href)
                        css_links.append(full_url)

                # Fetch external CSS files in parallel (limit to 5 to avoid abuse)
                external_css = ""
                if css_links:
                    css_links = css_links[:5]
                    logger.info("fetching_external_css", url=url, css_files=css_links)

                    async def _fetch_css(css_url: str) -> str:
                        try:
                            css_resp = await client.get(css_url, timeout=10.0)
                            css_resp.raise_for_status()
                            raw_css = css_resp.text
                            return extract_css_relevant(raw_css)
                        except Exception as e:
                            logger.warning(
                                "external_css_fetch_failed",
                                css_url=css_url,
                                error=str(e),
                            )
                            return ""

                    css_results = await asyncio.gather(
                        *[_fetch_css(u) for u in css_links]
                    )
                    external_css = "\n".join(r for r in css_results if r.strip())
                    logger.info(
                        "external_css_fetched",
                        url=url,
                        files_found=len(css_links),
                        total_relevant_chars=len(external_css),
                    )

                enriched = extract_html_with_styles(html, external_css=external_css)
                result = enriched[:40_000]
                logger.info(
                    "crawl_with_styles_completed",
                    url=url,
                    total_chars=len(result),
                    had_external_css=bool(external_css),
                )
                return result
        except Exception as e:
            logger.error("crawl_with_styles_exception", url=url, error=str(e))
            return ""


# Backward-compat alias
BrandCrawler = WebCrawler
