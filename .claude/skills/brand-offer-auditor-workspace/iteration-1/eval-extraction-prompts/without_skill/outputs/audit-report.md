# Brand Studio Extraction Prompts -- Audit Report

**Date:** 2026-03-23
**Scope:** 10 Jinja2 templates in `backend/src/modules/copilot/infrastructure/prompts/templates/brand_extract_*.j2`
**Objective:** Evaluate whether the prompts capture brand data at the correct atomic level, or produce overly generic output.

---

## Executive Summary

The extraction prompts are **well above average** for an AI-driven brand extraction system. They use professional branding frameworks (Brand Love Key, StoryBrand), enforce structured JSON output, and include detailed field-by-field instructions with examples. The system is designed to split extraction into 10 focused prompts rather than one monolithic call, which is a strong architectural choice for atomic precision.

However, the audit identifies **7 issues across 3 severity levels** that risk producing generic, shallow, or structurally inconsistent output in real-world usage.

**Overall Verdict:** The prompts produce data at a **good atomic level** for most fields. The main risk of generic output is concentrated in 3 prompts (Strategy, Story, and Positioning) and in the absence of input-quality guardrails across all prompts.

---

## Per-Prompt Analysis

### 1. `brand_extract_identity.j2`

**Rating: STRONG**

| Aspect | Score | Notes |
|---|---|---|
| Atomic specificity | 9/10 | Each field has precise extraction rules with examples of what NOT to do (e.g., "Educacion online para emprendedores digitales, NO Educacion") |
| Schema alignment | 10/10 | Perfect 1:1 mapping to `BrandIdentity` model |
| Anti-hallucination | 9/10 | Clear "NUNCA inventar" rules with explicit list of forbidden fabrications |
| Inference guidance | 9/10 | Explicit list of what CAN be inferred vs. what CANNOT |

**Strengths:**
- The `industry` field instruction is exemplary: "Nicho ESPECIFICO, no generico" with a concrete good/bad example.
- The `archetype` field forces inference with a closed set of valid values -- prevents freeform hallucination.
- Legal fields correctly scoped to footer/legal pages.

**Issues:**
- **(LOW) Missing `logo_url` extraction.** The `BrandVisuals` model has `logo_url` and `logos` dict, but identity extraction does not attempt to capture logo URLs from `<img>` tags in headers. This data is often available in scraped HTML.

---

### 2. `brand_extract_story.j2`

**Rating: MODERATE -- Risk of generic output**

| Aspect | Score | Notes |
|---|---|---|
| Atomic specificity | 6/10 | `origin_story` is a 400-word freeform narrative -- hard to validate atomically |
| Schema alignment | 9/10 | Maps to `BrandStory` correctly |
| Anti-hallucination | 7/10 | Allows "construir una narrativa coherente" from minimal data -- slippery slope |
| Inference guidance | 6/10 | Mission/vision can be entirely inferred, which often produces platitudes |

**Strengths:**
- The 4-part arc structure for `origin_story` (incidente detonante, punto de dolor, punto de giro, resolucion) is excellent framing.
- Mission uses a structured template: "Existimos para [verbo] [audiencia] mediante [metodo] para que [resultado]."
- Milestones are well-structured with year/title/description.

**Issues:**
- **(MEDIUM) `origin_story` invites hallucination for thin sites.** The instruction "construir una narrativa coherente con esos datos pero NO inventar detalles" is contradictory. Constructing a dramatic arc from "fundada en 2018 por Maria" will inevitably generate fabricated connective tissue. **Recommendation:** When data is minimal, return a factual summary flagged as `"(datos limitados)"` instead of asking the LLM to narrativize.
- **(MEDIUM) `mission` inference produces generic statements.** The template "Existimos para [verbo] [audiencia] mediante [metodo] para que [resultado]" is good, but when fully inferred from a landing page, the output tends toward: "Existimos para empoderar emprendedores mediante tecnologia para que alcancen su potencial (inferido)." This is useless. **Recommendation:** Add a quality gate: "Si la mission inferida contiene mas de 2 palabras genericas (empoderar, transformar, potenciar, impactar), reformular con verbos y sustantivos CONCRETOS del negocio."

---

### 3. `brand_extract_people_contact.j2`

**Rating: STRONG**

| Aspect | Score | Notes |
|---|---|---|
| Atomic specificity | 9/10 | Excellent personal vs. brand social media distinction |
| Schema alignment | 10/10 | Maps to `BrandTeamWrapper`, `BrandContact`, `KeyFigure` perfectly |
| Anti-hallucination | 10/10 | "NUNCA fabricar datos de contacto" is unambiguous |
| Inference guidance | 8/10 | Gender/communication_style inference is well-scoped |

**Strengths:**
- The "REGLA CRITICA DE DISTINCION" block that separates personal vs. brand social handles is the best instruction in the entire prompt suite. It uses concrete examples (Juan Lopez @juanlopez vs. MiEmpresa @miempresa) that eliminate ambiguity.
- Personal brand detection rule ("Si el sitio web ES una marca personal...") handles the most common edge case.

**Issues:**
- **(LOW) `headshot_url` missing from prompt.** The `KeyFigure` model has `headshot_url` and `gallery` fields, but the prompt never mentions extracting image URLs for team members. Many "About" pages include headshots in `<img>` tags.

---

### 4. `brand_extract_testimonials.j2`

**Rating: STRONG**

| Aspect | Score | Notes |
|---|---|---|
| Atomic specificity | 9/10 | Captures type, content, author, role, rating per testimonial |
| Schema alignment | 9/10 | Maps to `BrandTestimonial`; `author_avatar` in model but not extracted (acceptable -- rarely in HTML text) |
| Anti-hallucination | 10/10 | "NUNCA inventar testimonios, nombres de personas, citas textuales" |
| Inference guidance | 8/10 | Rating inference (positive=5, neutral=3) is practical |

**Strengths:**
- The "NUMEROS DE IMPACTO como testimonios de marca" rule is clever -- it captures social proof stats that aren't traditional testimonials but serve the same function.
- Cap of 10 testimonials with prioritization criteria prevents noise.
- Broad search scope (hero, about, servicios, not just testimonials section).

**Issues:**
- No significant issues. This is one of the best prompts in the suite.

---

### 5. `brand_extract_authority.j2`

**Rating: STRONG**

| Aspect | Score | Notes |
|---|---|---|
| Atomic specificity | 9/10 | Typed taxonomy (Prensa, Certificacion, Partner, Premio, Cliente) is excellent |
| Schema alignment | 9/10 | `logo_url` exists in model but not mentioned in prompt extraction instructions |
| Anti-hallucination | 9/10 | Clear boundary on what counts as authority |
| Inference guidance | 8/10 | Implicit certifications in bios is a smart capture rule |

**Strengths:**
- The closed type taxonomy prevents the LLM from inventing categories.
- "CERTIFICACIONES IMPLICITAS en bios" is a sophisticated extraction rule that catches authority signals most scrapers miss.
- Technology integrations mapped to "Partner" type is practical.

**Issues:**
- **(LOW) `logo_url` not extracted.** The `BrandAuthorityItem` model has a `logo_url` field, but the prompt never instructs the LLM to capture logo image URLs from "As seen in" bars or partner sections.

---

### 6. `brand_extract_visuals.j2`

**Rating: EXCELLENT**

| Aspect | Score | Notes |
|---|---|---|
| Atomic specificity | 10/10 | The most detailed prompt in the suite -- covers 30+ fields with surgical precision |
| Schema alignment | 10/10 | Perfect coverage of `BrandVisuals` model |
| Anti-hallucination | 9/10 | "#FFFFFF as primary" guard is a real-world save |
| Inference guidance | 9/10 | Layered priority system (CSS vars > meta > hex > Tailwind > inference) |

**Strengths:**
- This is the crown jewel of the prompt suite. The "PROTOCOLO DE EXTRACCION DE COLORES" with its 8-level priority hierarchy is production-grade.
- The "piensa como un disenador grafico" instruction with 60-30-10 analysis is excellent framing.
- Typography extraction handles Google Fonts URL parsing, WebFont.load(), @font-face, and Tailwind classes.
- Design system extraction (border-radius, shadows, spacing, density) goes far beyond typical brand scrapers.

**Issues:**
- **(LOW) `style_preset` in model but absent from prompt.** The `BrandVisuals` model has a `style_preset` field that the prompt never addresses. If this field serves a purpose, the prompt should set it.

---

### 7. `brand_extract_positioning.j2`

**Rating: STRONG, with one structural concern**

| Aspect | Score | Notes |
|---|---|---|
| Atomic specificity | 8/10 | Brand Love Key framework is inherently structured |
| Schema alignment | 9/10 | Clean mapping to `BrandPositioning` and sub-models |
| Anti-hallucination | 7/10 | Consumer insight and brand essence are highly inference-heavy |
| Inference guidance | 8/10 | "SI se puede inferir: enemigos, insight, beneficios" is broad permission |

**Strengths:**
- The Brand Love Key framework is an excellent choice -- it forces structured thinking (enemies, insight, benefits, values, RTBs, discriminator, essence).
- The `tension` template "Quiere [deseo] pero [barrera real]" is the right level of constraint.
- `reasons_to_believe` with typed categories (dato, caso_exito, certificacion, tecnologia, proceso) prevents vague claims.

**Issues:**
- **(MEDIUM) `brand_essence` risks platitudes.** "La esencia de la marca en 2-3 palabras" with examples like "Justicia Comercial" or "Libertad Creativa" is good, but there's no quality gate. Most LLM outputs will produce something like "Excelencia Digital" or "Innovacion Humana" -- words that could apply to any brand. **Recommendation:** Add: "La brand_essence debe ser UNICA para esta marca -- si pudiera aplicarse a cualquier otra empresa del sector, es demasiado generica. Reformular."
- **(LOW) Redundant `archetype` field.** Both `brand_extract_identity.j2` (field #9) and `brand_extract_positioning.j2` (inside `values`) extract archetype. This could produce contradictory values. **Recommendation:** Pick one authoritative source (positioning is the better home) and remove from identity, or add a reconciliation note.

---

### 8. `brand_extract_narrative.j2`

**Rating: EXCELLENT**

| Aspect | Score | Notes |
|---|---|---|
| Atomic specificity | 10/10 | StoryBrand's 7 elements are naturally atomic |
| Schema alignment | 10/10 | Perfect match to `BrandNarrative` and sub-models |
| Anti-hallucination | 8/10 | Most fields allow inference, but the framework constrains it well |
| Inference guidance | 9/10 | Clear templates for each field (villain, 3-layer problem, etc.) |

**Strengths:**
- StoryBrand is the right framework for narrative extraction -- it forces the LLM to identify hero, villain, three-layer problem, guide, plan, CTAs, and outcomes.
- The `one_liner` template is perfectly structured: "[Cliente] que [problema] merece [solucion]. [Marca] [como] para que [resultado]."
- "El HEROE siempre es el CLIENTE, nunca la marca" prevents the #1 StoryBrand mistake.
- Three-layer problem (external, internal, philosophical) ensures depth.

**Issues:**
- No significant issues.

---

### 9. `brand_extract_strategy.j2`

**Rating: WEAK -- Thin scope, risk of empty output**

| Aspect | Score | Notes |
|---|---|---|
| Atomic specificity | 5/10 | Only 3 fields (name, description, pillars) |
| Schema alignment | 10/10 | Maps to `BrandStrategy` correctly |
| Anti-hallucination | 8/10 | Correctly allows null/empty when no methodology exists |
| Inference guidance | 5/10 | Limited guidance on what constitutes a "methodology" |

**Strengths:**
- The `NOTA` clarifying that UVP/competitors/etc. are in positioning is a good separation of concerns.
- Detection patterns ("nuestro metodo de 3 pasos", "los 5 pilares de") are practical.

**Issues:**
- **(MEDIUM) Most websites don't have a named methodology.** For ~80% of solopreneur/creator sites, this prompt will return null/null/[]. That's correct behavior, but it means this is an LLM call with almost no value for most users. **Recommendation:** Either (a) merge this into positioning extraction as an optional section, or (b) expand the scope to extract implicit methodologies from "How it works" sections even when not branded.
- **(LOW) No pillar `description` guidance.** The prompt says "que cubre ese pilar (1 oracion)" but doesn't give examples of good vs. bad descriptions. For a prompt that already struggles with thin input, this matters.

---

### 10. `brand_extract_communication_assets.j2`

**Rating: STRONG**

| Aspect | Score | Notes |
|---|---|---|
| Atomic specificity | 9/10 | Funnel-stage distribution with typed assets and copy drafts |
| Schema alignment | 10/10 | Clean match to `CommunicationAssets`, `CreativeConcept`, `FunnelAsset` |
| Anti-hallucination | N/A | This is generative, not extractive -- hallucination rules don't apply the same way |
| Creative quality | 8/10 | Good funnel distribution, but concepts may be disconnected from brand voice |

**Strengths:**
- This is the only GENERATIVE prompt, and it correctly takes positioning and narrative as input context rather than just raw HTML.
- Funnel distribution (TOFU 2-3, MOFU 2-3, BOFU 2-3, Retention 1-2) ensures strategic coverage.
- Each asset includes `idea`, `copy_draft`, and `objective` -- actionable output.

**Issues:**
- **(LOW) No voice/tone constraint.** The prompt says "como si la marca hablara" but doesn't inject the actual `voice_tone` from identity extraction. If the brand's tone is "tecnico y formal" but the creative concepts come out "casual y empatico," there's a disconnect. **Recommendation:** Add `{{ voice_tone }}` as an input variable and enforce: "El tono de TODOS los copies debe ser consistente con: {{ voice_tone }}."

---

## Cross-Cutting Issues

### Issue A: No Input Quality Gate (MEDIUM)

None of the 10 prompts evaluate the quality/quantity of `{{ content }}` before attempting extraction. If the scraped HTML is a 404 page, a cookie consent wall, or a single-page site with 50 words, the LLM will still attempt to extract and infer, producing confident-sounding garbage.

**Recommendation:** Add a preamble to all prompts:
```
PASO 0 - EVALUACION DE CONTENIDO:
Antes de extraer, evalua la calidad del contenido:
- Si el contenido tiene < 100 palabras utiles, devolver {"_quality": "insufficient", ...} con todos los campos null.
- Si el contenido parece una pagina de error, login, o cookie wall, devolver {"_quality": "error_page", ...}.
```

### Issue B: Archetype Extracted Twice (LOW)

`brand_extract_identity.j2` (field #9) and `brand_extract_positioning.j2` (inside `values.archetype`) both extract the brand archetype. The identity prompt lists 12 Jungian archetypes; the positioning prompt uses informal names ("El Rebelde", "El Sabio"). These could produce conflicting values.

### Issue C: No Cross-Prompt Coherence Check (LOW)

The 10 prompts run independently. There is no mechanism to ensure that:
- The `voice_tone` from identity matches the `tone` of creative concepts
- The `archetype` from identity matches the one in positioning
- The `hero` from narrative aligns with the `insight.tension` from positioning
- The `competitors` in positioning align with what's visible in the content

This is acceptable for v1 but will become a quality issue as the product matures.

---

## Summary Scorecard

| Prompt | Rating | Atomic Level | Schema Match | Risk of Generic Output |
|---|---|---|---|---|
| identity | STRONG | 9/10 | 10/10 | Low |
| story | MODERATE | 6/10 | 9/10 | **Medium** -- origin_story and mission |
| people_contact | STRONG | 9/10 | 10/10 | Low |
| testimonials | STRONG | 9/10 | 9/10 | Low |
| authority | STRONG | 9/10 | 9/10 | Low |
| visuals | EXCELLENT | 10/10 | 10/10 | Very Low |
| positioning | STRONG | 8/10 | 9/10 | Medium -- brand_essence |
| narrative | EXCELLENT | 10/10 | 10/10 | Low |
| strategy | WEAK | 5/10 | 10/10 | **High** -- usually empty |
| communication_assets | STRONG | 9/10 | 10/10 | Low (generative) |

---

## Prioritized Recommendations

| # | Severity | Prompt(s) | Recommendation |
|---|---|---|---|
| 1 | MEDIUM | ALL | Add input quality gate (PASO 0) to reject garbage input before extraction |
| 2 | MEDIUM | story | Replace "construir narrativa coherente" with factual summary when data is minimal |
| 3 | MEDIUM | story | Add anti-platitude gate for inferred missions ("empoderar" / "transformar" = too generic) |
| 4 | MEDIUM | positioning | Add uniqueness gate for `brand_essence` -- reject if it could apply to any company |
| 5 | MEDIUM | strategy | Consider merging into positioning or expanding scope to implicit methodologies |
| 6 | LOW | communication_assets | Inject `{{ voice_tone }}` as input and enforce tone consistency |
| 7 | LOW | identity + positioning | Deduplicate archetype extraction -- pick one authoritative source |
| 8 | LOW | people_contact | Add `headshot_url` extraction from `<img>` tags in team/about sections |
| 9 | LOW | authority | Add `logo_url` extraction from partner/press logo sections |
| 10 | LOW | visuals | Address `style_preset` field -- either populate or deprecate from model |
