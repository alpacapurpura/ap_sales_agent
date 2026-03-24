# Brand Studio Audit Report

**Date:** 2026-03-23
**Scope:** Full audit of the Brand Studio module to identify gaps that prevent the SDR (Sales Agent) from selling effectively with the brand.
**Files reviewed:** Backend domain models, frontend types, extraction prompts (10 templates), agent identity template, knowledge builder service.

---

## 1. Executive Summary

The Brand Studio has a rich data model covering identity, positioning (Brand Love Key), narrative (StoryBrand), communication assets, team, contact, testimonials, and authority. However, the **Sales Agent only consumes a fraction of this data**. The `agent_identity.j2` template — the sole bridge between Brand Studio and the SDR — ignores most of the strategic frameworks that exist in the domain. The SDR is effectively selling blind on positioning, narrative, benefits, objection-level brand context, and competitive differentiation.

---

## 2. Critical Gaps (SDR cannot sell effectively)

### GAP-01: Narrative framework (StoryBrand) is completely invisible to the SDR

**Severity:** CRITICAL

The `BrandNarrative` model contains the StoryBrand framework: hero, problem (villain + 3 layers), guide, plan, CTA, outcome, one-liner. None of this is rendered in `agent_identity.j2`. The template does not even receive `narrative` as a variable from `TenantKnowledgeBuilder`.

- `knowledge_builder.py` line 63: extracts `positioning` but **never extracts `narrative`**.
- `agent_identity.j2`: zero references to `narrative`, `hero`, `problem`, `guide`, `outcome`, or `one_liner`.

**Impact:** The SDR cannot articulate the customer's problem in 3 layers (external, internal, philosophical), cannot position the brand as a guide, and cannot paint success/failure outcomes — the core of persuasive sales conversation.

**Recommendation:** Pass `narrative` to the template. Add a "## Narrativa de Ventas" section that renders the StoryBrand framework for the agent to use during conversations.

---

### GAP-02: Positioning framework (Brand Love Key) is reduced to a single field

**Severity:** CRITICAL

`BrandPositioning` contains: competitive environment (technical + philosophical enemies, competitors), consumer insight (tension/observation/implication), benefits (functional + emotional), values, reasons to believe, discriminator, brand essence, and UVP. The template only renders `positioning.unique_value_proposition`.

The SDR is missing:
- **Competitive enemies** — cannot contrast against alternatives
- **Consumer insight** — cannot empathize with the customer's hidden tension
- **Functional/emotional benefits** — cannot articulate what the product delivers beyond features
- **Reasons to believe** — cannot provide proof points when credibility is challenged
- **Discriminator** — cannot explain why this brand is irreplaceable
- **Brand essence** — cannot anchor conversations in the brand's core identity

**Impact:** The SDR defaults to generic pitching instead of strategic brand-aligned selling.

**Recommendation:** Render the full positioning into the agent identity. At minimum: discriminator, brand essence, top 3 benefits (functional + emotional), top enemies, and reasons to believe.

---

### GAP-03: Testimonials template references legacy fields

**Severity:** HIGH

`agent_identity.j2` lines 102-104 render testimonials as:
```
"{{ t.quote }}" -- {{ t.author }}{% if t.role %}, {{ t.role }}{% endif %}
```

But the current `BrandTestimonial` model uses `content` (not `quote`), `author_name` (not `author`), and `author_role` (not `role`). The legacy fields exist as migration fallbacks but are `None` for any newly-created testimonial.

**Impact:** Any testimonial entered through the current UI renders as empty quotes in the SDR prompt. The SDR has zero social proof.

**Recommendation:** Update `agent_identity.j2` to use `t.content`, `t.author_name`, and `t.author_role`.

---

### GAP-04: No Health Score implementation exists

**Severity:** HIGH

The domain docs (`module_brand.md`) state: "Health Score: El sistema calcula un porcentaje de completitud. Si es bajo, los agentes de ventas pueden negarse a operar o funcionar con personalidad generica." However, no health score calculation exists anywhere in the codebase (searched for `health_score`, `completitud`, `completeness`, `brand_health` — zero results).

**Impact:** There is no mechanism to warn the business owner that their brand is incomplete, nor to prevent the SDR from operating with insufficient context (which leads to generic, off-brand conversations).

**Recommendation:** Implement a `BrandHealthScore` service that checks completeness of each section (identity, positioning, narrative, testimonials, offers). Surface this in the frontend and use it as a gate in `TenantKnowledgeBuilder.build_identity()`.

---

### GAP-05: Communication Assets have no downstream consumer

**Severity:** MEDIUM

`CommunicationAssets` (creative concepts, funnel-stage assets with copy drafts) are modeled, extracted, and stored but never consumed by any downstream system. The SDR does not reference them. The asset/landing module does not import them.

**Impact:** The business owner fills out or auto-generates communication assets that sit unused. No module leverages the funnel-stage copy drafts for actual content delivery, ad copy, or SDR talking points.

**Recommendation:** At minimum, expose BOFU assets to the SDR as situational talking points. Long-term, connect them to the asset generation pipeline and advertising module.

---

## 3. Structural Issues

### STRUCT-01: Frontend `BrandIdentity` still carries visual fields

`frontend/src/features/brand/types/index.ts` lines 26-34: `BrandIdentity` still includes `primary_color`, `accent_color`, `font_heading`, `font_body`, `background_color`, `text_primary_color`, `text_on_primary`, `design_style`, and `usage_guidelines` with a comment "kept for legacy/backward compatibility with wizard extraction flow." Meanwhile the backend `BrandIdentity` model does NOT have these fields (they live in `BrandVisuals`).

**Impact:** Frontend may write visual data into `identity` which the backend silently drops (because `BrandIdentity` has `extra='allow'`), or the data diverges between identity and visuals.

**Recommendation:** Remove visual fields from the frontend `BrandIdentity` type. Ensure the extraction wizard writes visuals to `BrandSettings.visuals`.

---

### STRUCT-02: `identity.archetype` duplicated in `positioning.values.archetype`

Both `BrandIdentity.archetype` and `BrandValues.archetype` (inside `BrandPositioning.values`) store the brand archetype. The extraction prompts for identity and positioning both extract archetype independently.

**Impact:** Possible data inconsistency — one says "El Rebelde" and the other says "Hero". The SDR template does not use either.

**Recommendation:** Make `positioning.values.archetype` the canonical source. Deprecate `identity.archetype` with a migration validator. Surface the archetype in the SDR template to shape conversational tone.

---

### STRUCT-03: `strategy.mission` referenced in SDR template but field lives in `story.mission`

`agent_identity.j2` line 15: `{% if strategy.mission %}`. But `BrandStrategy` does NOT have a `mission` field — it only has `methodology_name`, `methodology_description`, and `methodology_pillars`. The `mission` field lives in `BrandStory.mission`.

**Impact:** The mission statement is never rendered in the SDR prompt because the template looks for it in the wrong place.

**Recommendation:** Change `agent_identity.j2` line 15 to `{% if story.mission %}**Mision:** {{ story.mission }}{% endif %}`.

---

### STRUCT-04: `identity.voice_tone` is a flat string, SDR needs structured tone directives

`BrandIdentity.voice_tone` is a single string like "conversacional, aspiracional". The SDR could benefit from structured tone directives: what to do, what to avoid, emotional register, formality level. The `Avatar.voice_tone_config` is a `Dict[str, Any]` that could carry this, but it is not rendered in the agent template.

**Impact:** The SDR gets a vague tone descriptor with no actionable guidance.

**Recommendation:** Either structure `voice_tone` into a typed model (register, do/don't, formality) or render `Avatar.voice_tone_config` in the SDR template when available.

---

### STRUCT-05: `BrandContact` not rendered for the SDR

The `contact` data (support email, sales email, phone, WhatsApp, social links) is extracted by `knowledge_builder.py` (line 61) but **never rendered** in `agent_identity.j2`. The template has no `{% if contact %}` block.

**Impact:** The SDR cannot redirect prospects to support channels, cannot share WhatsApp links, cannot provide the sales email when asked.

**Recommendation:** Add a contact section to the agent identity template.

---

### STRUCT-06: Authority Vault not rendered for the SDR

`brand_data.authority_vault` (press mentions, certifications, partners, awards, client logos) is stored but not passed to the template and not rendered.

**Impact:** The SDR cannot drop credibility proof points in conversation ("We're Google Partners", "Featured in Forbes", "ISO 9001 certified").

**Recommendation:** Pass `authority_vault` to the template. Render as a "## Credenciales" section.

---

## 4. Extraction Prompt Issues

### EXTRACT-01: No extraction prompt for the full `BrandNarrative` within the identity flow

There are separate prompts for `brand_extract_positioning.j2` and `brand_extract_narrative.j2`, but `brand_extract_communication_assets.j2` depends on both positioning and narrative as input context (`{{ positioning_context }}`, `{{ narrative_context }}`). If the extraction pipeline runs them in parallel rather than sequentially (positioning + narrative first, then communication assets), the communication assets prompt gets empty context.

**Impact:** Communication assets may be generated without the strategic context they need.

**Recommendation:** Verify the extraction pipeline enforces sequencing: identity -> story -> strategy -> positioning -> narrative -> communication_assets.

---

### EXTRACT-02: Extraction prompts produce Spanish-only output

All 10 extraction prompts enforce: "TODO el texto DEBE estar en ESPANOL." But `BrandIdentity.language` captures the brand's primary language, which could be English, Portuguese, etc.

**Impact:** A Brazilian brand's SDR speaks in Spanish-extracted brand data, creating a linguistic mismatch.

**Recommendation:** Make extraction language dynamic based on `BrandIdentity.language` or the site's detected language.

---

## 5. Gap Summary Matrix

| # | Gap | Severity | Area | Effort |
|---|-----|----------|------|--------|
| GAP-01 | StoryBrand narrative invisible to SDR | CRITICAL | agent_identity.j2 + knowledge_builder.py | Small |
| GAP-02 | Brand Love Key positioning reduced to 1 field | CRITICAL | agent_identity.j2 | Small |
| GAP-03 | Testimonials use legacy field names in template | HIGH | agent_identity.j2 | Trivial |
| GAP-04 | No Health Score implementation | HIGH | brand module (new service) | Medium |
| GAP-05 | Communication Assets have no consumer | MEDIUM | architecture / cross-module | Large |
| STRUCT-01 | Frontend identity carries visual fields | MEDIUM | frontend types | Small |
| STRUCT-02 | Archetype duplicated in identity + positioning | LOW | domain models | Small |
| STRUCT-03 | Mission referenced from wrong model in template | HIGH | agent_identity.j2 | Trivial |
| STRUCT-04 | Voice tone is unstructured | MEDIUM | domain model + template | Medium |
| STRUCT-05 | Contact data not rendered for SDR | HIGH | agent_identity.j2 | Small |
| STRUCT-06 | Authority Vault not rendered for SDR | HIGH | agent_identity.j2 | Small |
| EXTRACT-01 | Communication assets may lack context | MEDIUM | extraction pipeline | Small |
| EXTRACT-02 | Extraction hardcoded to Spanish | LOW | extraction prompts | Medium |

---

## 6. Recommended Priority Order

1. **Fix `agent_identity.j2`** (GAP-01, GAP-02, GAP-03, STRUCT-03, STRUCT-05, STRUCT-06) — these are all template changes plus one line in `knowledge_builder.py`. One PR, high ROI. The SDR goes from "brand-blind" to "brand-powered".
2. **Implement Brand Health Score** (GAP-04) — enables the system to warn users about incomplete brands and prevent low-quality SDR conversations.
3. **Clean up frontend type drift** (STRUCT-01, STRUCT-02) — reduces confusion and prevents silent data loss.
4. **Structure voice tone** (STRUCT-04) — gives the SDR actionable personality directives.
5. **Connect Communication Assets** (GAP-05) — long-term value for content automation.
6. **Dynamic extraction language** (EXTRACT-02) — enables non-Spanish markets.

---

## 7. Key Files Referenced

- `/home/chris/AISALESHT/backend/src/modules/brand/domain/aggregates.py` — BrandSettings root aggregate
- `/home/chris/AISALESHT/backend/src/modules/brand/domain/positioning.py` — Brand Love Key framework
- `/home/chris/AISALESHT/backend/src/modules/brand/domain/narrative.py` — StoryBrand framework
- `/home/chris/AISALESHT/backend/src/modules/brand/domain/communication_assets.py` — Funnel assets
- `/home/chris/AISALESHT/backend/src/modules/brand/domain/identity.py` — Core identity + visuals
- `/home/chris/AISALESHT/backend/src/modules/brand/domain/team.py` — Team, contact, testimonials, authority
- `/home/chris/AISALESHT/backend/src/modules/sales_agent/application/services/knowledge_builder.py` — Bridge between Brand and SDR
- `/home/chris/AISALESHT/backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2` — SDR identity prompt
- `/home/chris/AISALESHT/frontend/src/features/brand/types/index.ts` — Frontend type definitions
- `/home/chris/AISALESHT/backend/src/modules/copilot/infrastructure/prompts/templates/brand_extract_*.j2` — 10 extraction prompts
