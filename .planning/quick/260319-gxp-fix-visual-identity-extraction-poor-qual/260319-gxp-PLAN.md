---
phase: quick-260319-gxp
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/src/modules/brand/application/extraction_service.py
  - backend/src/modules/copilot/infrastructure/prompts/templates/brand_extract_visuals.j2
  - backend/src/modules/brand/domain/identity.py
autonomous: true
requirements: [VISUAL-EXTRACTION-FIX]

must_haves:
  truths:
    - "Visual identity extraction returns real colors from the website, not white/empty defaults"
    - "CSS data (inline styles, style tags, class names, Google Font links, meta theme-color) is preserved and passed to the visual extraction prompt"
    - "extract_visuals_only() uses enriched HTML with styles, not stripped text"
    - "Main extract_all() pipeline includes visual extraction as 7th section when URL is provided"
  artifacts:
    - path: "backend/src/modules/brand/application/extraction_service.py"
      provides: "_extract_html_with_styles() method, _extract_visuals() as 7th pipeline section, updated extract_visuals_only()"
    - path: "backend/src/modules/copilot/infrastructure/prompts/templates/brand_extract_visuals.j2"
      provides: "Rewritten brandbook-specialist prompt with CSS-aware and inference-fallback rules"
    - path: "backend/src/modules/brand/domain/identity.py"
      provides: "Extended BrandVisuals with color_palette and border_radius_style fields"
  key_links:
    - from: "extraction_service.py::extract_visuals_only"
      to: "_extract_html_with_styles"
      via: "Uses enriched HTML instead of stripped text for visual prompt"
      pattern: "_extract_html_with_styles"
    - from: "extraction_service.py::extract_all"
      to: "_extract_visuals"
      via: "7th concurrent section in wave 1 when URL provided"
      pattern: "_extract_visuals"
---

<objective>
Fix visual identity extraction that returns white/empty colors by: (1) preserving CSS/style data from crawled HTML, (2) adding visual extraction to the main pipeline, and (3) rewriting the visual prompt to brandbook-specialist quality.

Purpose: The current visual extraction is fundamentally broken because `_extract_text_from_html()` strips all `<style>` tags and inline styles before the LLM sees them, making color/font extraction impossible. Additionally, the main `extract_all()` pipeline never runs visual extraction at all.

Output: Working visual identity extraction that returns accurate colors, fonts, and design style from any website.
</objective>

<execution_context>
@/home/chris/AISALESHT/.claude/get-shit-done/workflows/execute-plan.md
@/home/chris/AISALESHT/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@backend/src/modules/brand/application/extraction_service.py
@backend/src/modules/copilot/infrastructure/prompts/templates/brand_extract_visuals.j2
@backend/src/modules/brand/domain/identity.py
@backend/src/modules/brand/api/extraction.py
@backend/src/modules/copilot/application/services/brand_ai_actions_service.py

<interfaces>
<!-- Key types the executor needs -->

From backend/src/modules/brand/domain/identity.py:
```python
class BrandVisuals(BaseEntity):
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_color: Optional[str] = None
    text_primary_color: Optional[str] = None
    text_on_primary: Optional[str] = None
    font_heading: Optional[str] = None
    font_body: Optional[str] = None
    style_preset: Optional[str] = None
    design_style: Optional[str] = None
    usage_guidelines: List[str] = Field(default_factory=list)
    logo_url: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    logos: Optional[Dict[str, Optional[str]]] = Field(default_factory=dict)
    model_config = ConfigDict(extra='allow')
```

From extraction_service.py - key method signatures:
```python
async def crawl_content(self, url: str) -> str  # Returns labeled text (CSS stripped)
def _extract_text_from_html(html: str) -> str  # Strips <style> tags on line 279
def _render_prompt(self, template_name, content, current_data, instructions, max_chars=50000) -> str
async def _run_section(self, section_name, action_name, prompt, response_model, default_result, user_prompt, per_call_timeout=120.0)
async def extract_visuals_only(self, url: str) -> BrandVisuals  # Called by frontend visual DNA scan
async def extract_all(self, url, text, mode, update_instructions, dry_run, include_visuals) -> BrandSettings  # Main pipeline
```

Frontend flow: `brandApi.extractBrandVisuals(url, token)` -> `/api/v1/brand/extraction/extract` -> `extract_brand_identity()` -> `extract_visuals_only(url)` -> `crawl_content()` (strips CSS) -> visual prompt (has no CSS data) -> poor results.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add CSS-preserving HTML extractor and extend BrandVisuals model</name>
  <files>backend/src/modules/brand/domain/identity.py, backend/src/modules/brand/application/extraction_service.py</files>
  <action>
**In `backend/src/modules/brand/domain/identity.py`:**
Add two new fields to `BrandVisuals` class (before `model_config`):
- `color_palette: List[str] = Field(default_factory=list)` — additional hex colors beyond the 5 primary ones (gradients, section backgrounds, accent variants)
- `border_radius_style: Optional[str] = None` — e.g. "rounded", "sharp", "pill", "mixed"

**In `backend/src/modules/brand/application/extraction_service.py`:**

1. Add a NEW static method `_extract_html_with_styles(html: str) -> str` that preserves CSS data for visual analysis. This method should:
   - Parse HTML with BeautifulSoup
   - Remove ONLY `<script>` tags (NOT `<style>` — that's the whole point)
   - Extract and preserve in a `[CSS_STYLES]` section:
     - All `<style>` tag contents
     - `<meta name="theme-color">` values
     - `<link>` tags with `href` containing "fonts.googleapis.com" (extract font family names from the URL)
   - Extract and preserve in a `[INLINE_STYLES]` section:
     - All elements with `style=` attributes, formatted as `tag.class: style_value` (limit to first 50 elements to avoid bloat)
   - Extract and preserve in a `[KEY_ELEMENTS]` section:
     - `class=` attributes from: body, header, nav, footer, main, h1-h6, button, a (first 5 of each)
     - Format as `<tag class="classes">` so the LLM can see Tailwind/CSS class names
   - After extracting style data, get the regular text content (same as `_extract_text_from_html` but lighter — just body text for context)
   - Combine: `[CSS_STYLES]\n{css}\n[/CSS_STYLES]\n\n[INLINE_STYLES]\n{inline}\n[/INLINE_STYLES]\n\n[KEY_ELEMENTS]\n{elements}\n[/KEY_ELEMENTS]\n\n[TEXT_CONTENT]\n{text}\n[/TEXT_CONTENT]`

2. Add a NEW method `crawl_content_with_styles(url: str) -> str` that works like `crawl_content` but:
   - Only fetches the MAIN page (no subpages — visual identity is on the homepage)
   - Calls `_extract_html_with_styles()` instead of `_extract_text_from_html()`
   - Returns the enriched content with CSS data preserved
   - Limit output to 40000 chars (visual data is denser)

3. Update `extract_visuals_only()` to:
   - Call `crawl_content_with_styles(url)` instead of `crawl_content(url)`
   - This is the key fix — now the visual prompt will receive CSS data
  </action>
  <verify>
    <automated>docker exec -t visionarias_brain_dev python -c "from src.modules.brand.domain.identity import BrandVisuals; v = BrandVisuals(color_palette=['#ff0000'], border_radius_style='rounded'); print('OK:', v.color_palette, v.border_radius_style)"</automated>
  </verify>
  <done>BrandVisuals has color_palette and border_radius_style fields. _extract_html_with_styles() exists and preserves CSS data. extract_visuals_only() uses enriched HTML.</done>
</task>

<task type="auto">
  <name>Task 2: Rewrite visual extraction prompt and add visuals to main pipeline</name>
  <files>backend/src/modules/copilot/infrastructure/prompts/templates/brand_extract_visuals.j2, backend/src/modules/brand/application/extraction_service.py</files>
  <action>
**Rewrite `brand_extract_visuals.j2` completely:**

Role: "Eres un disenador grafico senior especializado en ingenieria inversa de identidad visual de marcas. Tu trabajo es analizar sitios web y producir un manual de identidad visual (brandbook) preciso."

Structure the prompt with these sections:

1. **CONTENIDO DEL SITIO** — `{{ content }}` / `{{ current_data }}` / `{{ instructions }}` (same template vars)

2. **PROTOCOLO DE EXTRACCION DE COLORES:**
   - Priority 1: CSS variables (`--primary`, `--accent`, `--brand-*`), `theme-color` meta
   - Priority 2: Explicit hex/rgb in `<style>` blocks and inline `style=` attributes
   - Priority 3: Tailwind/framework classes (e.g., `bg-blue-600` -> `#2563eb`, `bg-primary` -> look for its definition)
   - Priority 4: Color inference from brand context (luxury brand without CSS -> likely dark palette)
   - For `primary_color`: the most prominent brand color (buttons, headers, links, CTAs)
   - For `accent_color`: secondary/complementary color (highlights, badges, hover states)
   - For `background_color`: main page background
   - For `text_primary_color`: body text color
   - For `text_on_primary`: text that sits ON the primary color (e.g., white text on blue button)
   - For `color_palette`: ALL other colors found — section backgrounds, gradients, borders, footer background, card backgrounds. Return as list of hex values. Aim for 5-15 additional colors.
   - RULE: If CSS data is available, extract EXACT hex values. Never round or approximate.
   - RULE: If no CSS data, infer from visual context but add "(inferido)" suffix to design_style only. Colors must still be valid hex.
   - RULE: NEVER return #FFFFFF as primary_color or accent_color unless the brand genuinely uses white as its primary identity color (rare — verify against other evidence).

3. **PROTOCOLO DE EXTRACCION TIPOGRAFICA:**
   - Priority 1: Google Fonts links (parse family names from URL)
   - Priority 2: `font-family` declarations in CSS
   - Priority 3: Tailwind font classes (`font-sans`, `font-serif`, `font-mono` -> map to common defaults)
   - Priority 4: If no font data, infer from design style: luxury -> serif for headings, tech -> geometric sans, etc.
   - `font_heading`: heading/display font family name
   - `font_body`: body/paragraph font family name

4. **PROTOCOLO DE ESTILO DE DISENO:**
   - `design_style`: 1-2 descriptors in Spanish. Options: "Minimalista", "Corporativo", "Creativo", "Elegante", "Moderno", "Playful", "Luxury", "Tech", "Organico", "Brutalist", "Neomorfismo". Can combine: "Moderno Elegante"
   - `border_radius_style`: Analyze button/card border-radius. "sharp" (0-2px), "rounded" (4-8px), "pill" (16px+/full), "mixed"
   - `usage_guidelines`: 5-7 actionable brandbook rules in Spanish. Examples:
     - "Color primario reservado exclusivamente para CTAs principales y headers de seccion"
     - "Tipografia serif para titulos de alto impacto, sans-serif para cuerpo y navegacion"
     - "Mantener ratio de contraste minimo 4.5:1 entre texto y fondo"
     - "Esquinas redondeadas (8px) en tarjetas y botones para coherencia visual"
     - "Gradientes lineales de primario a acento solo en heroes y banners principales"

5. **REGLAS FINALES:**
   - EVIDENCIA DIRECTA: valor en CSS/HTML -> extraer tal cual
   - INFERENCIA: deducible del contexto -> extraer con confianza
   - SIN EVIDENCIA: null (pero INTENTAR inferir antes de null)
   - Colores SIEMPRE en formato HEX valido (#RRGGBB)
   - Guidelines SIEMPRE en ESPANOL
   - OUTPUT: JSON valido del schema BrandVisuals. SOLO JSON, sin markdown, sin code blocks

**In `extraction_service.py` — add visuals to main pipeline:**

1. Add `_extract_visuals()` method (same pattern as `_extract_identity`, etc.):
   ```python
   async def _extract_visuals(self, content: str, current_data: str, instructions: str) -> BrandVisuals:
       prompt = self._render_prompt("brand_extract_visuals", content, current_data, instructions)
       return await self._run_section(
           "visuals", "brand_extract_visuals", prompt,
           BrandVisuals, BrandVisuals(), "Extract the visual identity (colors, fonts, design style)."
       )
   ```

2. Update `extract_all()`:
   - When `url` is provided, ALSO call `crawl_content_with_styles(url)` to get enriched HTML for visuals (do this in the parallel gather with `safe_crawl` and `safe_visuals`)
   - Add `_extract_visuals(enriched_content, ...)` as part of the LLM extraction waves
   - In the 2-wave strategy: add `_extract_visuals` to Wave 1 (it's lightweight, uses enriched_content not regular content)
   - In the 1-wave strategy: add it as the 7th concurrent call
   - If URL was not provided (text-only mode), skip visuals (no CSS data to extract from text)
   - Pass the result to `_merge_and_save()` as `new_visuals` parameter (this already exists and handles merge)

3. Remove the `include_visuals` guard — visuals should ALWAYS be extracted when a URL is provided. The `safe_visuals()` LangGraph path can be removed since we now have our own `_extract_visuals()`.

4. Update the extraction log from "sections=6" to "sections=7" when URL is provided, "sections=6" when text-only.
  </action>
  <verify>
    <automated>docker exec -t visionarias_brain_dev python -c "from src.modules.brand.application.extraction_service import BrandExtractionService; print('OK: service imports cleanly')"</automated>
  </verify>
  <done>Visual extraction prompt is rewritten with brandbook-specialist depth. Main extract_all() pipeline includes visuals as 7th section when URL is provided. extract_visuals_only() uses CSS-enriched HTML. The include_visuals flag is no longer needed for basic visual extraction.</done>
</task>

</tasks>

<verification>
1. `docker exec -t visionarias_brain_dev python -c "from src.modules.brand.application.extraction_service import BrandExtractionService; print('OK')"` — service imports cleanly
2. `docker exec -t visionarias_brain_dev python -c "from src.modules.brand.domain.identity import BrandVisuals; v = BrandVisuals(); print('Fields:', [f for f in v.model_fields if f in ('color_palette', 'border_radius_style')])"` — new fields exist
3. `docker exec -t visionarias_brain_dev python -c "from src.modules.brand.application.extraction_service import BrandExtractionService; assert hasattr(BrandExtractionService, '_extract_html_with_styles'); print('OK: style extractor exists')"` — CSS extractor method exists
4. Manual: trigger visual DNA scan from Brand Studio UI and verify colors are real (not white/empty)
</verification>

<success_criteria>
- BrandVisuals model has `color_palette` (List[str]) and `border_radius_style` (Optional[str]) fields
- `_extract_html_with_styles()` preserves CSS data (style tags, inline styles, class names, Google Font links)
- `extract_visuals_only()` uses enriched HTML (not stripped text)
- `extract_all()` includes visual extraction as 7th section when URL is provided
- Visual extraction prompt is comprehensive with CSS-aware extraction priorities and inference fallbacks
- All imports clean, no runtime errors
</success_criteria>

<output>
After completion, create `.planning/quick/260319-gxp-fix-visual-identity-extraction-poor-qual/260319-gxp-SUMMARY.md`
</output>
