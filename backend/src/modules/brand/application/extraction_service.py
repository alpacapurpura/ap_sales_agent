from typing import Optional, Literal, List
from uuid import UUID
from dataclasses import dataclass
from sqlalchemy.orm import Session
import structlog
import json
import asyncio
import time
from pydantic import BaseModel, Field

from src.modules.brand.domain import (
    BrandSettings, BrandIdentity, BrandStory, BrandStrategy, BrandVisuals,
    BrandContact, BrandTestimonial, BrandAuthorityItem, KeyFigure, BrandTeam,
    BrandPositioning, BrandNarrative, CommunicationAssets,
)
from src.modules.brand.infrastructure.repositories.brand_repository import BrandRepository
from src.modules.copilot.infrastructure.prompts.base import prompt_loader
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from src.shared.application.ai_action_service import AIActionService, AIActionPolicy, AIModelPolicy
import traceback
import re

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Extraction Profiles — both always exist, switch via BRAND_EXTRACTION_PROFILE
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExtractionProfile:
    """Immutable configuration for how brand extraction behaves."""
    name: str
    model_type: str           # "smart" or "fast" — maps to LLM factory
    max_output_tokens: int    # max completion tokens (model-dependent limit)
    retries: int              # how many attempts per section
    retry_delay_seconds: float  # base delay between retries
    concurrency_waves: int    # 1 = all-6-concurrent, 2 = two-waves-of-3
    wave_delay_seconds: float # pause between waves (only when waves > 1)


# "safe" — conservative with 2 waves. Now uses gpt-4o-mini (200K+ TPM)
# so waves are less critical but kept as safety margin.
PROFILE_SAFE = ExtractionProfile(
    name="safe",
    model_type="smart",
    max_output_tokens=4000,
    retries=2,
    retry_delay_seconds=2.0,
    concurrency_waves=2,
    wave_delay_seconds=2.0,
)

# "fast" — all 6 concurrent, minimal delays. Safe with gpt-4o-mini (200K+ TPM).
PROFILE_FAST = ExtractionProfile(
    name="fast",
    model_type="smart",
    max_output_tokens=4000,
    retries=2,
    retry_delay_seconds=1.0,
    concurrency_waves=1,
    wave_delay_seconds=0,
)

_PROFILES = {
    "safe": PROFILE_SAFE,
    "fast": PROFILE_FAST,
}


def _get_active_profile() -> ExtractionProfile:
    """Resolve active profile from settings.BRAND_EXTRACTION_PROFILE (default: safe)."""
    from src.core.config import settings as app_settings
    name = app_settings.BRAND_EXTRACTION_PROFILE.lower()
    profile = _PROFILES.get(name)
    if not profile:
        logger.warning("unknown_extraction_profile", requested=name, fallback="safe")
        profile = PROFILE_SAFE
    return profile


def _summarize_settings(settings: BrandSettings) -> dict:
    """Produce a compact summary of which sections have data."""
    return {
        "identity": bool(settings.identity and settings.identity.brand_name),
        "story": bool(settings.story and settings.story.origin_story),
        "strategy": bool(settings.strategy and settings.strategy.methodology_name),
        "team_count": len(settings.team or []),
        "contact": bool(settings.contact and (settings.contact.support_email or settings.contact.phone)),
        "testimonials_count": len(settings.testimonials or []),
        "authority_count": len(settings.authority_vault or []),
        "visuals": bool(settings.visuals and settings.visuals.primary_color),
        "positioning": bool(settings.positioning and settings.positioning.brand_essence),
        "narrative": bool(settings.narrative and settings.narrative.hero),
        "communication_assets_count": len((settings.communication_assets or CommunicationAssets()).assets),
    }


class BrandPeopleContactExtraction(BaseModel):
    """Wrapper model for the combined people + contact extraction."""
    key_leadership: List[KeyFigure] = Field(default_factory=list)
    culture_vibe: Optional[str] = None
    locations: Optional[str] = None
    contact: Optional[BrandContact] = None


class BrandTestimonialsExtraction(BaseModel):
    """Wrapper model for testimonials extraction."""
    testimonials: List[BrandTestimonial] = Field(default_factory=list)


class BrandAuthorityExtraction(BaseModel):
    """Wrapper model for authority vault extraction."""
    authority_vault: List[BrandAuthorityItem] = Field(default_factory=list)


# URL path segments / anchor text keywords for link scoring
_SKIP_PATTERNS = {
    "blog", "post", "wp-admin", "login", "cart", "search", "feed",
    "tag", "category", "author", "page", "wp-content", "wp-includes",
    "admin", "checkout", "account", "signup", "register",
}
_SKIP_EXTENSIONS = {".pdf", ".zip", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".mp4", ".mp3", ".doc", ".docx", ".xls"}
_HIGH_KEYWORDS = {
    "about", "nosotros", "nosotras", "quienes-somos", "equipo", "team",
    "servicios", "services", "contacto", "contact", "testimonios",
    "testimonials", "casos", "casos-de-exito", "reviews",
}
_MEDIUM_KEYWORDS = {
    "legal", "terminos", "terms", "privacidad", "privacy", "historia",
    "story", "mision", "vision", "precios", "pricing", "partners",
    "socios", "clientes", "metodologia", "portafolio",
}


class BrandExtractionService:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repository = BrandRepository(db)
        self.ai_action_service = AIActionService()

        # Resolve extraction profile from env
        self.profile = _get_active_profile()
        self.default_policy = AIActionPolicy(
            retries=self.profile.retries,
            retry_delay_seconds=self.profile.retry_delay_seconds,
            model=AIModelPolicy(
                model_type=self.profile.model_type,
                temperature=0,
                max_output_tokens=self.profile.max_output_tokens,
            ),
        )

        logger.info("extraction_profile_loaded",
                     profile=self.profile.name,
                     model_type=self.profile.model_type,
                     max_output_tokens=self.profile.max_output_tokens,
                     concurrency_waves=self.profile.concurrency_waves,
                     retries=self.profile.retries)

    def _visuals_policy(self) -> AIActionPolicy:
        """Policy override for visuals extraction — needs more output tokens
        because the expanded BrandVisuals schema has ~20 additional fields
        with dicts/lists that produce larger JSON responses."""
        return AIActionPolicy(
            retries=self.profile.retries,
            retry_delay_seconds=self.profile.retry_delay_seconds,
            model=AIModelPolicy(
                model_type=self.profile.model_type,
                temperature=0,
                max_output_tokens=6000,
            ),
        )

    @staticmethod
    def _score_link(url: str, anchor_text: str) -> int:
        """Score an internal link by relevance to brand extraction. Returns -1 to skip."""
        parsed = urlparse(url)
        path = parsed.path.lower().rstrip("/")

        # Skip anchors, mailto, tel
        if url.startswith("#") or url.startswith("mailto:") or url.startswith("tel:"):
            return -1

        # Skip file downloads
        for ext in _SKIP_EXTENSIONS:
            if path.endswith(ext):
                return -1

        # Collect terms from path segments and anchor text
        path_segments = set(path.strip("/").split("/")) if path.strip("/") else set()
        anchor_words = set(anchor_text.lower().split()) if anchor_text else set()
        all_terms = path_segments | anchor_words

        # Skip patterns
        if all_terms & _SKIP_PATTERNS:
            return -1

        # High relevance
        if all_terms & _HIGH_KEYWORDS:
            return 10

        # Medium relevance
        if all_terms & _MEDIUM_KEYWORDS:
            return 5

        # Low: any other same-domain link
        return 1

    async def crawl_content(self, url: str) -> str:
        """
        Crawls the URL and up to 8 scored internal subpages, returning labeled text content.
        """
        try:
            base_domain = urlparse(url).netloc
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
                # Fetch main page
                response = await client.get(url)
                response.raise_for_status()
                main_text = self._extract_text_from_html(response.text)

                # Score and rank internal links
                soup = BeautifulSoup(response.text, "html.parser")
                normalized_main = url.rstrip("/")
                seen_urls: set[str] = {normalized_main}
                scored_links: list[tuple[int, str]] = []

                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"]
                    full_url = urljoin(url, href)
                    # Strip fragment and trailing slash for dedup
                    parsed = urlparse(full_url)
                    clean_url = parsed._replace(fragment="").geturl().rstrip("/")

                    if (
                        parsed.netloc == base_domain
                        and clean_url not in seen_urls
                        and parsed.scheme in ("http", "https")
                    ):
                        score = self._score_link(clean_url, a_tag.get_text(strip=True))
                        if score >= 0:
                            seen_urls.add(clean_url)
                            scored_links.append((score, clean_url))

                # Sort by score descending, take top 8
                scored_links.sort(key=lambda x: x[0], reverse=True)
                top_links = [link_url for _, link_url in scored_links[:8]]

                logger.info("crawl_links_scored",
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
                        return sub_url, self._extract_text_from_html(sub_response.text)
                    except Exception:
                        return sub_url, ""

                subpage_results = await asyncio.gather(*[_fetch_subpage(link) for link in top_links])

            # Build labeled content
            parts: list[str] = [
                f"=== PAGINA PRINCIPAL: {url} ===\n{main_text}\n=== FIN PAGINA ==="
            ]
            for sub_url, sub_text in subpage_results:
                if sub_text.strip():
                    parts.append(f"=== PAGINA: {sub_url} ===\n{sub_text}\n=== FIN PAGINA ===")

            result = "\n\n".join(parts)[:100_000]
            pages_crawled = len(parts)
            logger.info("crawl_completed", url=url, pages_crawled=pages_crawled, total_chars=len(result))
            return result

        except Exception as e:
            logger.error("crawl_exception", url=url, error=str(e))
            return ""

    @staticmethod
    def _extract_text_from_html(html: str) -> str:
        """Parse HTML and extract clean text content, preserving structural sections."""
        soup = BeautifulSoup(html, "html.parser")
        # Remove only non-content elements
        for tag in soup.find_all(["script", "style"]):
            tag.decompose()

        # Preserve header/nav/footer with section markers
        for tag_name, marker in [("header", "HEADER"), ("nav", "NAV"), ("footer", "FOOTER")]:
            for tag in soup.find_all(tag_name):
                section_text = tag.get_text(separator="\n", strip=True)
                if section_text:
                    tag.replace_with(f"\n[{marker}]\n{section_text}\n[/{marker}]\n")
                else:
                    tag.decompose()

        return soup.get_text(separator="\n", strip=True)

    @staticmethod
    def _extract_css_relevant(css_text: str, max_chars: int = 8000) -> str:
        """Extract only brand-relevant CSS rules (colors, fonts, variables) from raw CSS.

        Uses a two-tier approach:
        1. HIGH priority: CSS variable definitions (--color-name: #hex) — always included first
        2. NORMAL priority: color/font declarations in custom classes — fill remaining space

        Filters out reset/normalize rules, layout-only rules, and framework boilerplate.
        """
        # Strip @font-face blocks (multi-line) — font names are captured from
        # font-family declarations and WebFont.load() instead
        css_text = re.sub(r'@font-face\s*\{[^}]*\}', '', css_text, flags=re.DOTALL | re.IGNORECASE)

        # Patterns that indicate framework boilerplate to skip
        skip_pattern = re.compile(
            r'(\.w-icon|\.w-widget|webflow-icons|'
            r'webkit-appearance|moz-osx-font|speak:\s*none|'
            r'text-size-adjust|box-sizing|display:\s*(block|inline|none|flex)|'
            r'vertical-align|line-height:\s*[01]|outline:\s*0|'
            r'border:\s*0(?:;|\s)|padding:\s*0(?:;|\s)|margin:\s*0(?:;|\s)|'
            r'overflow:\s*(hidden|auto|visible)|cursor:\s*|'
            r'src:\s*url\(|format\(|font-display|font-style)',
            re.IGNORECASE
        )

        # Tier 1: CSS variable definitions with color values
        var_pattern = re.compile(r'--[\w-]+\s*:', re.IGNORECASE)
        # Tier 2: Color/font declarations in custom styles
        color_pattern = re.compile(
            r'(#[0-9a-fA-F]{3,8}|rgba?\s*\(|hsla?\s*\(|'
            r'(?:background-)?color\s*:|background-image|gradient|'
            r'font-family|border-radius)',
            re.IGNORECASE
        )
        # Skip generic/unset values that add no information
        noise_pattern = re.compile(
            r'(:\s*(inherit|unset|initial|normal|none|auto|transparent)\s*;|'
            r'color:\s*#0000\s|background-color:\s*#0000\s|'
            r'font-weight:\s*(normal|bold)\s*;)',
            re.IGNORECASE
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

    @staticmethod
    def _extract_html_with_styles(html: str, external_css: str = "") -> str:
        """Parse HTML preserving CSS data for visual identity analysis.

        Unlike _extract_text_from_html which strips <style> tags, this method
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
                # Extract font families from WebFont.load({ google: { families: [...] } })
                families_match = re.findall(r'families\s*:\s*\[(.*?)\]', script_text, re.DOTALL)
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
                # Extract family param: family=Montserrat:wght@400;700&family=Open+Sans
                match = re.findall(r"family=([^&]+)", href)
                for fam in match:
                    # Clean: "Montserrat:wght@400;700" -> "Montserrat"
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

        inline_section = "\n".join(inline_parts) if inline_parts else "(no inline styles found)"

        # --- [KEY_ELEMENTS] section ---
        key_tags = ["body", "header", "nav", "footer", "main",
                     "h1", "h2", "h3", "h4", "h5", "h6", "button", "a"]
        element_parts: list[str] = []
        for tag_name in key_tags:
            for j, el in enumerate(soup.find_all(tag_name)):
                if j >= 5:
                    break
                classes = el.get("class")
                if classes:
                    element_parts.append(f'<{tag_name} class="{" ".join(classes)}">')

        elements_section = "\n".join(element_parts) if element_parts else "(no class attributes found)"

        # --- [TEXT_CONTENT] section (lightweight body text for context) ---
        body = soup.find("body")
        text_content = ""
        if body:
            # Remove style tags from a copy to get clean text
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

    async def crawl_content_with_styles(self, url: str) -> str:
        """Crawl the main page preserving CSS data for visual identity extraction.

        Fetches the homepage HTML, discovers external <link rel="stylesheet"> files,
        downloads them in parallel, filters for brand-relevant CSS rules, and passes
        everything to _extract_html_with_styles() for structured extraction.

        This ensures sites that use external CSS files (Webflow, WordPress themes,
        plain HTML, etc.) are analyzed as accurately as sites with inline <style> blocks.
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
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
                        # Skip font-only CSS (Google Fonts CSS doesn't contain brand colors)
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
                            # Filter to keep only brand-relevant rules (colors, fonts, variables)
                            return self._extract_css_relevant(raw_css)
                        except Exception as e:
                            logger.warning("external_css_fetch_failed", css_url=css_url, error=str(e))
                            return ""

                    css_results = await asyncio.gather(*[_fetch_css(u) for u in css_links])
                    external_css = "\n".join(r for r in css_results if r.strip())
                    logger.info("external_css_fetched",
                                url=url,
                                files_found=len(css_links),
                                total_relevant_chars=len(external_css))

                enriched = self._extract_html_with_styles(html, external_css=external_css)
                result = enriched[:40_000]
                logger.info("crawl_with_styles_completed", url=url, total_chars=len(result),
                            had_external_css=bool(external_css))
                return result
        except Exception as e:
            logger.error("crawl_with_styles_exception", url=url, error=str(e))
            return ""

    @staticmethod
    def _truncate_at_page_boundary(content: str, max_chars: int = 50000) -> str:
        """Truncate content at the nearest === FIN PAGINA === boundary within max_chars."""
        if len(content) <= max_chars:
            return content
        marker = "=== FIN PAGINA ==="
        last_marker = content.rfind(marker, 0, max_chars)
        if last_marker > 0:
            return content[:last_marker + len(marker)]
        return content[:max_chars]

    def _render_prompt(self, template_name: str, content: str, current_data: str, instructions: str, max_chars: int = 50000) -> str:
        """Render a brand extraction prompt using the PromptLoader (Jinja2 + DB fallback)."""
        try:
            rendered = prompt_loader.render(
                template_name,
                content=self._truncate_at_page_boundary(content, max_chars=max_chars),
                current_data=current_data or "None",
                instructions=instructions or "None",
            )
            logger.info("prompt_rendered", template=template_name, prompt_length=len(rendered),
                         content_input_length=len(content), current_data_length=len(current_data or ""))
            return rendered
        except Exception as e:
            logger.error("prompt_render_failed", template=template_name, error=str(e),
                         error_type=type(e).__name__, traceback=traceback.format_exc())
            raise

    async def extract_all(
        self,
        url: Optional[str] = None,
        text: Optional[str] = None,
        mode: Literal["initial", "update"] = "initial",
        update_instructions: Optional[str] = None,
        dry_run: bool = False,
        include_visuals: bool = False
    ) -> BrandSettings:
        """
        Orchestrates the full brand extraction process.
        When a URL is provided, visual identity extraction is included as the
        7th section using CSS-enriched HTML (not stripped text).
        """
        # 1. Get Content
        content = text or ""
        enriched_visual_content = ""
        has_url = bool(url)

        if url:
            logger.info("starting_crawl", url=url)

            t0 = time.time()

            async def safe_crawl():
                try:
                    return await self.crawl_content(url)
                except Exception as e:
                    logger.error("crawl_failed", error=str(e))
                    return ""

            async def safe_crawl_styles():
                try:
                    return await self.crawl_content_with_styles(url)
                except Exception as e:
                    logger.error("crawl_styles_failed", error=str(e))
                    return ""

            # Parallel: regular crawl (for text sections) + CSS-enriched crawl (for visuals)
            crawled_content, enriched_visual_content = await asyncio.gather(
                safe_crawl(), safe_crawl_styles()
            )

            t1 = time.time()
            logger.info("parallel_crawl_completed",
                        duration=t1-t0,
                        crawl_length=len(crawled_content),
                        enriched_length=len(enriched_visual_content),
            )

            if crawled_content:
                content = f"{content}\n\n{crawled_content}"

        if not content.strip() and not update_instructions:
            logger.warning("no_content_to_extract", tenant_id=self.tenant_id)
            return self.repository.get_settings(self.tenant_id)

        logger.info("extraction_context_prepared", total_content_length=len(content))

        # 2. Prepare Context (Current Data)
        current_settings = self.repository.get_settings(self.tenant_id)
        current_data_str = ""
        if mode == "update":
            current_data_str = json.dumps(current_settings.model_dump(mode='json'), indent=2)

        logger.info("extraction_content_ready",
                    content_length=len(content),
                    current_data_length=len(current_data_str)
        )

        # 3. Run LLM extractions (wave strategy from profile)
        waves = self.profile.concurrency_waves
        base_sections = 8  # identity, story, strategy, people_contact, testimonials, authority, positioning, narrative
        total_sections = base_sections + (1 if has_url and enriched_visual_content.strip() else 0) + 1  # +1 for communication_assets (wave 3)
        logger.info("starting_llm_extractions", sections=total_sections, waves=waves, profile=self.profile.name)

        extracted_visuals = None
        positioning = BrandPositioning()
        narrative = BrandNarrative()
        communication_assets = CommunicationAssets()

        if waves >= 2:
            # Wave 1: identity, story, testimonials + visuals (lighter extractions)
            wave1_sections = ["identity", "story", "testimonials"]
            wave1_coros = [
                self._extract_identity(content, current_data_str, update_instructions),
                self._extract_story(content, current_data_str, update_instructions),
                self._extract_testimonials(content, current_data_str, update_instructions),
            ]
            if has_url and enriched_visual_content.strip():
                wave1_sections.append("visuals")
                wave1_coros.append(
                    self._extract_visuals(enriched_visual_content, current_data_str, update_instructions)
                )

            logger.info("extraction_wave_starting", wave=1, sections=wave1_sections)
            wave1_results = await asyncio.gather(*wave1_coros)
            identity, story, testimonials_data = wave1_results[0], wave1_results[1], wave1_results[2]
            if len(wave1_results) > 3:
                extracted_visuals = wave1_results[3]

            # Pause between waves to let TPM budget recover
            logger.info("extraction_wave_pause", delay=self.profile.wave_delay_seconds)
            await asyncio.sleep(self.profile.wave_delay_seconds)

            # Wave 2: strategy, people_contact, authority, positioning, narrative
            wave2_sections = ["strategy", "people_contact", "authority", "positioning", "narrative"]
            logger.info("extraction_wave_starting", wave=2, sections=wave2_sections)
            strategy, people_contact, authority_data, positioning, narrative = await asyncio.gather(
                self._extract_strategy(content, current_data_str, update_instructions),
                self._extract_people_contact(content, current_data_str, update_instructions),
                self._extract_authority(content, current_data_str, update_instructions),
                self._extract_positioning(content, current_data_str, update_instructions),
                self._extract_narrative(content, current_data_str, update_instructions),
            )

            # Wave 3: communication_assets (depends on positioning + narrative)
            logger.info("extraction_wave_pause", delay=self.profile.wave_delay_seconds)
            await asyncio.sleep(self.profile.wave_delay_seconds)

            positioning_ctx = json.dumps(positioning.model_dump(exclude_none=True), indent=2) if not self._is_empty(positioning) else ""
            narrative_ctx = json.dumps(narrative.model_dump(exclude_none=True), indent=2) if not self._is_empty(narrative) else ""

            logger.info("extraction_wave_starting", wave=3, sections=["communication_assets"])
            communication_assets = await self._extract_communication_assets(
                content, current_data_str, update_instructions,
                positioning_ctx, narrative_ctx,
            )
        else:
            # All concurrent (for high-tier rate limits) — except communication_assets which needs positioning/narrative
            coros = [
                self._extract_identity(content, current_data_str, update_instructions),
                self._extract_story(content, current_data_str, update_instructions),
                self._extract_strategy(content, current_data_str, update_instructions),
                self._extract_people_contact(content, current_data_str, update_instructions),
                self._extract_testimonials(content, current_data_str, update_instructions),
                self._extract_authority(content, current_data_str, update_instructions),
                self._extract_positioning(content, current_data_str, update_instructions),
                self._extract_narrative(content, current_data_str, update_instructions),
            ]
            if has_url and enriched_visual_content.strip():
                coros.append(
                    self._extract_visuals(enriched_visual_content, current_data_str, update_instructions)
                )
            all_results = await asyncio.gather(*coros)
            identity, story, strategy, people_contact, testimonials_data, authority_data = all_results[:6]
            positioning, narrative = all_results[6], all_results[7]
            if len(all_results) > 8:
                extracted_visuals = all_results[8]

            # Communication assets depend on positioning + narrative
            positioning_ctx = json.dumps(positioning.model_dump(exclude_none=True), indent=2) if not self._is_empty(positioning) else ""
            narrative_ctx = json.dumps(narrative.model_dump(exclude_none=True), indent=2) if not self._is_empty(narrative) else ""
            communication_assets = await self._extract_communication_assets(
                content, current_data_str, update_instructions,
                positioning_ctx, narrative_ctx,
            )

        # Log extraction results summary
        results = {
            "identity": not self._is_empty(identity),
            "story": not self._is_empty(story),
            "strategy": not self._is_empty(strategy),
            "people_contact": not self._is_empty(people_contact),
            "testimonials": not self._is_empty(testimonials_data),
            "authority": not self._is_empty(authority_data),
            "positioning": not self._is_empty(positioning),
            "narrative": not self._is_empty(narrative),
            "communication_assets": not self._is_empty(communication_assets),
        }
        if extracted_visuals is not None:
            results["visuals"] = not self._is_empty(extracted_visuals)
        succeeded = sum(1 for v in results.values() if v)
        logger.info("extraction_results_summary",
                     results=results,
                     succeeded=succeeded,
                     total=total_sections,
        )

        # 4. Merge & Save
        return self._merge_and_save(
            identity, story, strategy, people_contact,
            testimonials_data, authority_data,
            extracted_visuals,
            new_positioning=positioning,
            new_narrative=narrative,
            new_communication_assets=communication_assets,
            dry_run=dry_run,
        )

    async def _run_section(self, section_name: str, action_name: str, prompt: str,
                           response_model, default_result, user_prompt: str,
                           per_call_timeout: float = 120.0,
                           policy: Optional[AIActionPolicy] = None):
        """Generic wrapper for running a single extraction section with timing and timeout."""
        effective_policy = policy or self.default_policy
        t0 = time.time()
        try:
            logger.info(f"extract_{section_name}_starting", prompt_length=len(prompt))
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self.ai_action_service.run_structured_action,
                    action_name=action_name,
                    tenant_id=self.tenant_id,
                    system_prompt=self._append_schema_instruction(prompt, response_model),
                    user_prompt=user_prompt,
                    response_model=response_model,
                    policy=effective_policy,
                    metadata={"prompt_template": action_name},
                ),
                timeout=per_call_timeout,
            )
            elapsed = time.time() - t0
            extracted = result.model_dump(exclude_unset=True, exclude_none=True)
            logger.info(f"extract_{section_name}_success",
                        fields_extracted=list(extracted.keys()),
                        field_count=len(extracted),
                        duration_s=round(elapsed, 2))
            return result
        except asyncio.TimeoutError:
            elapsed = time.time() - t0
            logger.error(f"extract_{section_name}_timeout",
                         timeout=per_call_timeout, duration_s=round(elapsed, 2))
            return default_result
        except Exception as e:
            elapsed = time.time() - t0
            logger.error(f"extract_{section_name}_failed",
                         error=str(e), error_type=type(e).__name__,
                         duration_s=round(elapsed, 2),
                         traceback=traceback.format_exc())
            return default_result

    async def _extract_identity(self, content: str, current_data: str, instructions: str) -> BrandIdentity:
        prompt = self._render_prompt("brand_extract_identity", content, current_data, instructions)
        return await self._run_section("identity", "brand_extract_identity", prompt,
                                       BrandIdentity, BrandIdentity(), "Extract the Brand Identity.")

    async def _extract_story(self, content: str, current_data: str, instructions: str) -> BrandStory:
        prompt = self._render_prompt("brand_extract_story", content, current_data, instructions)
        return await self._run_section("story", "brand_extract_story", prompt,
                                       BrandStory, BrandStory(), "Extract the Brand Story.")

    async def _extract_strategy(self, content: str, current_data: str, instructions: str) -> BrandStrategy:
        prompt = self._render_prompt("brand_extract_strategy", content, current_data, instructions, max_chars=65000)
        return await self._run_section("strategy", "brand_extract_strategy", prompt,
                                       BrandStrategy, BrandStrategy(), "Extract the Brand Strategy.")

    async def _extract_people_contact(self, content: str, current_data: str, instructions: str) -> BrandPeopleContactExtraction:
        prompt = self._render_prompt("brand_extract_people_contact", content, current_data, instructions, max_chars=65000)
        return await self._run_section("people_contact", "brand_extract_people_contact", prompt,
                                       BrandPeopleContactExtraction, BrandPeopleContactExtraction(),
                                       "Extract People and Contact information.")

    async def _extract_testimonials(self, content: str, current_data: str, instructions: str) -> BrandTestimonialsExtraction:
        prompt = self._render_prompt("brand_extract_testimonials", content, current_data, instructions)
        return await self._run_section("testimonials", "brand_extract_testimonials", prompt,
                                       BrandTestimonialsExtraction, BrandTestimonialsExtraction(),
                                       "Extract Testimonials.")

    async def extract_visuals_only(self, url: str) -> BrandVisuals:
        """Extract only visual identity (colors, fonts, style) from a URL.

        Uses CSS-enriched HTML (not stripped text) so the LLM can see actual
        colors, fonts, and class names from the website.
        """
        content = await self.crawl_content_with_styles(url)
        if not content.strip():
            raise ValueError("Could not crawl content from URL")
        prompt = self._render_prompt("brand_extract_visuals", content, "", "", max_chars=40000)
        return await self._run_section(
            "visuals", "brand_extract_visuals", prompt,
            BrandVisuals, BrandVisuals(), "Extract the visual identity (colors, fonts, design style).",
            policy=self._visuals_policy(),
        )

    async def _extract_authority(self, content: str, current_data: str, instructions: str) -> BrandAuthorityExtraction:
        prompt = self._render_prompt("brand_extract_authority", content, current_data, instructions)
        return await self._run_section("authority", "brand_extract_authority", prompt,
                                       BrandAuthorityExtraction, BrandAuthorityExtraction(),
                                       "Extract Authority elements.")

    async def _extract_visuals(self, content: str, current_data: str, instructions: str) -> BrandVisuals:
        """Extract visual identity (colors, fonts, design style) from CSS-enriched content."""
        prompt = self._render_prompt("brand_extract_visuals", content, current_data, instructions, max_chars=40000)
        return await self._run_section(
            "visuals", "brand_extract_visuals", prompt,
            BrandVisuals, BrandVisuals(), "Extract the visual identity (colors, fonts, design style).",
            policy=self._visuals_policy(),
        )

    async def _extract_positioning(self, content: str, current_data: str, instructions: str) -> BrandPositioning:
        """Extract Brand Love Key positioning from content."""
        prompt = self._render_prompt("brand_extract_positioning", content, current_data, instructions, max_chars=65000)
        return await self._run_section("positioning", "brand_extract_positioning", prompt,
                                       BrandPositioning, BrandPositioning(), "Extract Brand Love Key positioning.")

    async def _extract_narrative(self, content: str, current_data: str, instructions: str) -> BrandNarrative:
        """Extract StoryBrand narrative from content."""
        prompt = self._render_prompt("brand_extract_narrative", content, current_data, instructions, max_chars=65000)
        return await self._run_section("narrative", "brand_extract_narrative", prompt,
                                       BrandNarrative, BrandNarrative(), "Extract StoryBrand narrative.")

    def _communication_assets_policy(self) -> AIActionPolicy:
        """Policy for communication assets — needs more tokens and higher temperature."""
        return AIActionPolicy(
            retries=self.profile.retries,
            retry_delay_seconds=self.profile.retry_delay_seconds,
            model=AIModelPolicy(
                model_type=self.profile.model_type,
                temperature=0.3,
                max_output_tokens=6000,
            ),
        )

    async def _extract_communication_assets(
        self, content: str, current_data: str, instructions: str,
        positioning_ctx: str, narrative_ctx: str
    ) -> CommunicationAssets:
        """Generate communication assets using positioning + narrative as context."""
        try:
            rendered = prompt_loader.render(
                "brand_extract_communication_assets",
                content=self._truncate_at_page_boundary(content, max_chars=30000),
                positioning_context=positioning_ctx or "No disponible",
                narrative_context=narrative_ctx or "No disponible",
                current_data=current_data or "None",
                instructions=instructions or "None",
            )
        except Exception as e:
            logger.error("prompt_render_failed", template="brand_extract_communication_assets", error=str(e))
            return CommunicationAssets()

        return await self._run_section(
            "communication_assets", "brand_extract_communication_assets", rendered,
            CommunicationAssets, CommunicationAssets(),
            "Generate strategic communication assets for the brand.",
            policy=self._communication_assets_policy(),
        )

    @staticmethod
    def _is_empty(model: BaseModel) -> bool:
        """Check if a pydantic model has only default/empty values."""
        data = model.model_dump(exclude_unset=True, exclude_none=True)
        for value in data.values():
            if isinstance(value, list) and len(value) > 0:
                return False
            if isinstance(value, str) and value.strip():
                return False
            if isinstance(value, dict) and value:
                return False
            if value is not None and not isinstance(value, (str, list, dict)):
                return False
        return True

    def _append_schema_instruction(self, prompt: str, schema_model) -> str:
        schema_json = json.dumps(schema_model.model_json_schema(), indent=2)
        return f"{prompt}\n\nSCHEMA:\n{schema_json}\n\nReturn a valid JSON object matching this schema."

    def _merge_and_save(
        self,
        new_identity: BrandIdentity,
        new_story: BrandStory,
        new_strategy: BrandStrategy,
        new_people_contact: BrandPeopleContactExtraction,
        new_testimonials: BrandTestimonialsExtraction,
        new_authority: BrandAuthorityExtraction,
        new_visuals: Optional[BrandVisuals] = None,
        new_positioning: Optional[BrandPositioning] = None,
        new_narrative: Optional[BrandNarrative] = None,
        new_communication_assets: Optional[CommunicationAssets] = None,
        dry_run: bool = False
    ) -> BrandSettings:

        current_settings = self.repository.get_settings(self.tenant_id)

        # Merge Identity (Update non-null fields)
        updated_identity = current_settings.identity.model_dump() if current_settings.identity else {}
        new_identity_dict = new_identity.model_dump(exclude_unset=True, exclude_none=True)
        updated_identity.update(new_identity_dict)

        # Merge Story
        updated_story = current_settings.story.model_dump() if current_settings.story else {}
        new_story_dict = new_story.model_dump(exclude_unset=True, exclude_none=True)
        if "milestones" in new_story_dict and new_story_dict["milestones"]:
            updated_story["milestones"] = new_story_dict["milestones"]
            del new_story_dict["milestones"]
        updated_story.update(new_story_dict)

        # Merge Strategy
        updated_strategy = current_settings.strategy.model_dump() if current_settings.strategy else {}
        new_strategy_dict = new_strategy.model_dump(exclude_unset=True, exclude_none=True)
        if "competitors" in new_strategy_dict and new_strategy_dict["competitors"]:
            updated_strategy["competitors"] = new_strategy_dict["competitors"]
            del new_strategy_dict["competitors"]
        if "methodology_pillars" in new_strategy_dict and new_strategy_dict["methodology_pillars"]:
            updated_strategy["methodology_pillars"] = new_strategy_dict["methodology_pillars"]
            del new_strategy_dict["methodology_pillars"]
        updated_strategy.update(new_strategy_dict)

        # Merge Team (from people_contact)
        updated_team = current_settings.team
        if new_people_contact.key_leadership:
            updated_team = new_people_contact.key_leadership

        # Merge team_metadata (culture_vibe, locations)
        updated_team_metadata = current_settings.team_metadata
        if new_people_contact.culture_vibe or new_people_contact.locations:
            existing_meta = updated_team_metadata.model_dump() if updated_team_metadata else {}
            if new_people_contact.culture_vibe:
                existing_meta["culture_vibe"] = new_people_contact.culture_vibe
            if new_people_contact.locations:
                # BrandTeam.locations expects List[str], but LLM may return a plain string
                raw_locations = new_people_contact.locations
                if isinstance(raw_locations, str):
                    existing_meta["locations"] = [loc.strip() for loc in raw_locations.split(",") if loc.strip()]
                elif isinstance(raw_locations, list):
                    existing_meta["locations"] = raw_locations
                else:
                    existing_meta["locations"] = [str(raw_locations)]
            updated_team_metadata = BrandTeam(**existing_meta)

        # Merge Contact (from people_contact)
        updated_contact = current_settings.contact
        if new_people_contact.contact:
            if updated_contact:
                existing_contact_dict = updated_contact.model_dump()
                new_contact_dict = new_people_contact.contact.model_dump(exclude_unset=True, exclude_none=True)
                existing_contact_dict.update(new_contact_dict)
                updated_contact = BrandContact(**existing_contact_dict)
            else:
                updated_contact = new_people_contact.contact

        # Merge Testimonials (replace if non-empty)
        updated_testimonials = current_settings.testimonials or []
        if new_testimonials.testimonials:
            updated_testimonials = new_testimonials.testimonials

        # Merge Authority (replace if non-empty)
        updated_authority = current_settings.authority_vault or []
        if new_authority.authority_vault:
            updated_authority = new_authority.authority_vault

        # Merge Visuals
        updated_visuals = current_settings.visuals.model_dump() if current_settings.visuals else {}
        if new_visuals:
            new_visuals_dict = new_visuals.model_dump(exclude_unset=True, exclude_none=True)
            updated_visuals.update(new_visuals_dict)

        # Merge Positioning (deep merge — preserve existing if new is None/empty)
        updated_positioning = current_settings.positioning
        if new_positioning and not self._is_empty(new_positioning):
            if updated_positioning:
                existing_pos = updated_positioning.model_dump()
                new_pos = new_positioning.model_dump(exclude_unset=True, exclude_none=True)
                # Lists replace if non-empty
                for list_field in ("reasons_to_believe",):
                    if list_field in new_pos and new_pos[list_field]:
                        existing_pos[list_field] = new_pos.pop(list_field)
                # Nested objects: deep merge
                for nested in ("competitive_environment", "insight", "benefits", "values"):
                    if nested in new_pos and new_pos[nested]:
                        existing_nested = existing_pos.get(nested) or {}
                        existing_nested.update(new_pos.pop(nested))
                        existing_pos[nested] = existing_nested
                existing_pos.update(new_pos)
                updated_positioning = BrandPositioning(**existing_pos)
            else:
                updated_positioning = new_positioning

        # Merge Narrative (deep merge)
        updated_narrative = current_settings.narrative
        if new_narrative and not self._is_empty(new_narrative):
            if updated_narrative:
                existing_narr = updated_narrative.model_dump()
                new_narr = new_narrative.model_dump(exclude_unset=True, exclude_none=True)
                if "plan" in new_narr and new_narr["plan"]:
                    existing_narr["plan"] = new_narr.pop("plan")
                for nested in ("hero", "problem", "guide", "cta", "outcome"):
                    if nested in new_narr and new_narr[nested]:
                        existing_nested = existing_narr.get(nested) or {}
                        existing_nested.update(new_narr.pop(nested))
                        existing_narr[nested] = existing_nested
                existing_narr.update(new_narr)
                updated_narrative = BrandNarrative(**existing_narr)
            else:
                updated_narrative = new_narrative

        # Merge Communication Assets (replace concepts and assets if non-empty)
        updated_comm_assets = current_settings.communication_assets
        if new_communication_assets and not self._is_empty(new_communication_assets):
            if updated_comm_assets:
                existing_ca = updated_comm_assets.model_dump()
                if new_communication_assets.creative_concepts:
                    existing_ca["creative_concepts"] = new_communication_assets.model_dump()["creative_concepts"]
                if new_communication_assets.assets:
                    existing_ca["assets"] = new_communication_assets.model_dump()["assets"]
                if new_communication_assets.custom_asset_types:
                    existing_ca["custom_asset_types"] = new_communication_assets.model_dump()["custom_asset_types"]
                updated_comm_assets = CommunicationAssets(**existing_ca)
            else:
                updated_comm_assets = new_communication_assets

        # Construct new Settings
        final_settings = current_settings.model_copy(update={
            "identity": BrandIdentity(**updated_identity),
            "story": BrandStory(**updated_story),
            "strategy": BrandStrategy(**updated_strategy),
            "team": updated_team,
            "team_metadata": updated_team_metadata,
            "contact": updated_contact,
            "testimonials": updated_testimonials,
            "authority_vault": updated_authority,
            "visuals": BrandVisuals(**updated_visuals),
            "positioning": updated_positioning,
            "narrative": updated_narrative,
            "communication_assets": updated_comm_assets,
        })

        logger.info("merge_completed", tenant_id=str(self.tenant_id), summary=_summarize_settings(final_settings))

        if dry_run:
            logger.info("dry_run_extraction_completed", tenant_id=self.tenant_id)
            print("\n--- [DEBUG] LLM EXTRACTION RESULT (Dry Run) ---")
            print(json.dumps(final_settings.model_dump(mode='json'), indent=2))
            print("-------------------------------------------------\n")
            return final_settings

        saved = self.repository.save_settings(self.tenant_id, final_settings)
        logger.info("extraction_saved_to_db", tenant_id=str(self.tenant_id), summary=_summarize_settings(saved))
        return saved
