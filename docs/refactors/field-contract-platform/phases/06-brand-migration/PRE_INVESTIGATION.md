# Pre-investigación obligatoria — Fase 06

**Status**: completed (2026-04-24).

## Sección 1 — Brand Pydantic surface

### Q1.1 — Lista exhaustiva `BrandSettings.model_fields` y nested models

Master entity: `src/modules/brand/domain/aggregates.py::BrandSettings`.

**Top-level fields user-facing** (12 total):

| Field | Annotation | Walker handling |
|---|---|---|
| `identity` | `BrandIdentity \| None` | composable (1 level) |
| `strategy` | `BrandStrategy \| None` | composable |
| `story` | `BrandStory \| None` | composable |
| `team` | `list[KeyFigure] \| None` | LIST top-level |
| `contact` | `BrandContact \| None` | composable |
| `testimonials` | `list[BrandTestimonial]` | LIST top-level |
| `authority_vault` | `list[BrandAuthorityItem]` | LIST top-level |
| `visuals` | `BrandVisuals \| None` | composable |
| `positioning` | `BrandPositioning \| None` | composable |
| `narrative` | `BrandNarrative \| None` | composable |
| `communication_assets` | `CommunicationAssets \| None` | composable |
| `brand_personality` | `BrandPersonality \| None` | composable |

**Sub-model field counts** (after `composable_fields` walker, 1 level deep):

| Composable | Class | Field count | Notas |
|---|---|---|---|
| `identity.*` | `BrandIdentity` | 32 | incluye 23 legal/regulated + sales-agent guardrails |
| `strategy.*` | `BrandStrategy` | 3 | methodology_name/description + list pillars |
| `story.*` | `BrandStory` | 5 | inc. milestones_legacy (deprecated) |
| `contact.*` | `BrandContact` | 14 | redes sociales + email/whatsapp + legacy email/social dict |
| `visuals.*` | `BrandVisuals` | 35 | colors + typography + design tokens + assets |
| `positioning.*` | `BrandPositioning` | 8 | 4 nested objects + 3 scalar + 1 list |
| `narrative.*` | `BrandNarrative` | 7 | 5 nested + 1 list + 1 scalar |
| `communication_assets.*` | `CommunicationAssets` | 3 | 2 lists + custom_asset_types list |
| `brand_personality.*` | `BrandPersonality` | 3 | core_values list + traits list + archetype |

**Total derivable paths**: 113 (top-level 12 — composable handles 9 + 3 lists =
3 list contracts; nested 110).

### Q1.2 — Composición nested

**Confirmado**: composición. Cada top-level es `SubModel | None` (1 non-None
variant). Walker invoca `_walk_union_or_composable` con
`composable=True`, ramifica a `_walk_nested` con prefix.

**Nested-of-nested** (BrandPositioning, BrandNarrative): walker NO recurse
2 niveles. Sub-objects emitten como `FieldType.OBJECT`. Ej:
`positioning.insight` se emite como OBJECT, no se recurse a `positioning.insight.tension`.

Esto matchea el patrón offer (`platform_details: PlatformDetails`,
1 level only). Mantiene scope manejable.

## Sección 2 — Section catalog brand

### Q2.1 — Sections válidas

Source: `src/modules/brand/domain/section_catalog.py` (`BrandSectionKey`).

14 sections:
- `publico` (buyer-personas, COLLECTION — out of Fase 06 scope)
- `identity`, `estilo`, `positioning`, `narrative`, `methodology`,
  `story`, `team`, `authority`, `testimonials`, `visuals`,
  `communication-assets`, `contact`, `legal`

**Mapping path → section** (decided):

| Pydantic path prefix | Section slug |
|---|---|
| `identity.{brand-meta}` (brand_name, tagline, description, industry, website, founding_year, language, timezone, voice_tone) | `identity` |
| `identity.{legal-meta}` (legal_name, legal_entity_type, tax_id, tax_regime, country_of_registration, commercial_registry_number, fiscal_address, legal_representative, legal_email, dpo_email, terms_url, privacy_url, cookies_url, refund_policy_url, acceptable_use_url, regulated_profession_body, professional_license_number, professional_license_holder, operating_authorization, liability_insurance_carrier, sales_agent_disclaimer, sales_agent_out_of_scope, escalation_contact) | `legal` |
| `strategy.*` | `methodology` |
| `story.*` | `story` |
| `contact.*` | `contact` |
| `visuals.*` | `visuals` |
| `positioning.*` | `positioning` |
| `narrative.*` | `narrative` |
| `communication_assets.*` | `communication-assets` |
| `brand_personality.*` | `personality` (estilo) |
| `team` (list) | `team` |
| `testimonials` (list) | `testimonials` |
| `authority_vault` (list) | `authority` |

⚠️ Decisión: catalog actual usa `personality` como section pero
section_catalog tiene `estilo`. Mapear `brand_personality.*` → `personality`
(matching catalog actual) y dejar `estilo` para fase futura si se decide
unificar.

Section `publico` (buyer-personas) NO se cubre en Fase 06 — pertenece a
Fase 07.

## Sección 3 — Drift audit

### Q3.1 — Diff `BRAND_EDITABLE_FIELDS` vs `BrandSettings.model_fields`

**Catalog actual** (78 entries, post-conteo): identity (8), story (3),
positioning (8), narrative (13), methodology (2 → `strategy.*`), personality
(3), visuals (6), contact (12), legal (23 → catalog dice `contact.legal_*`
pero Pydantic `identity.legal_*`).

**Drift confirmado severo**:

#### Drift A: shorthand a paths inexistentes
8 entries del catalog usan paths "shorthand" que NO resuelven en Pydantic:

| Catalog path | Pydantic real path | Estado |
|---|---|---|
| `positioning.insight_tension` | `positioning.insight.tension` | shorthand 2-level → broken |
| `positioning.insight_observation` | `positioning.insight.observation` | broken |
| `positioning.insight_implication` | `positioning.insight.implication` | broken |
| `positioning.technical_enemy` | `positioning.competitive_environment.technical_enemy` | broken |
| `positioning.philosophical_enemy` | `positioning.competitive_environment.philosophical_enemy` | broken |
| `narrative.hero_identity` | `narrative.hero.identity` | broken |
| `narrative.hero_desire` | `narrative.hero.desire` | broken |
| `narrative.problem_villain` | `narrative.problem.villain` | broken |
| `narrative.problem_external` | `narrative.problem.external_problem` | broken (rename + nest) |
| `narrative.problem_internal` | `narrative.problem.internal_problem` | broken |
| `narrative.problem_philosophical` | `narrative.problem.philosophical_problem` | broken |
| `narrative.guide_empathy` | `narrative.guide.empathy_statement` | broken |
| `narrative.guide_authority` | `narrative.guide.authority_statement` | broken |
| `narrative.cta_direct` | `narrative.cta.direct_cta` | broken |
| `narrative.cta_transitional` | `narrative.cta.transitional_cta` | broken |
| `narrative.outcome_success` | `narrative.outcome.success_transformation` | broken |
| `narrative.outcome_failure` | `narrative.outcome.failure_consequence` | broken |

**Confirmación de "broken"**: `validate_field_path("brand", path)` consume
`_build_brand_paths()` que enumera `get_model_sections(BrandSettings)`. Solo
acepta `section` y `section.field` 1-level. Estos shorthand 2-level NO
validan → `propose_field_updates` falla → ningún cambio user-facing al
removerlos.

#### Drift B: section mismatch (`contact.*` ↔ `identity.*`)
23 entries declaran `contact.legal_name`, `contact.tax_id`, etc., pero
Pydantic los tiene en `BrandIdentity` (i.e. `identity.legal_name`,
`identity.tax_id`). Mismas observaciones — `propose_field_updates`
rechaza estos paths. Drift cosmético — la sección "legal" sí existe en
section_catalog, pero la persistencia es vía `identity`.

#### Drift C: missing Pydantic fields del catalog
Catalog no incluye:
- `identity.voice_tone`
- `identity.regulated_*`, `identity.professional_*`, `identity.operating_authorization`,
  `identity.liability_insurance_carrier`, `identity.sales_agent_*`,
  `identity.escalation_contact` (estos sí están en catalog vía `contact.*`
  pero la persistencia es `identity.*`).
- `strategy.methodology_pillars` (list)
- `story.milestones`, `story.milestones_legacy`
- `contact.email`, `contact.social` (legacy)
- `visuals.{29 fields}`: secondary_color, accent_color, background_color,
  surface_color, text_primary_color, text_on_primary, text_on_secondary,
  color_palette, neutral_colors, semantic_colors, gradient_definitions,
  color_usage_rules, font_*, typography_*, border_radius_*, shadow_style,
  spacing_base, visual_density, brand_mood, icon_style, style_preset,
  design_style, usage_guidelines, images, logos
- `positioning.benefits, .competitive_environment, .insight, .reasons_to_believe, .values`
  (objects/lists)
- `narrative.{hero, problem, guide, cta, outcome}` como objects (los
  shorthand en catalog intentaban exponerlos pero broken)
- `narrative.plan` (list)
- `communication_assets.*` (3 list fields — toda la sección)
- `team`, `testimonials`, `authority_vault` (list top-level — todo el
  surface CRUD)

**Conclusión drift**: catalog actual cubre ~25-30 paths real-funcionales
de los ~113 derivables. Refactor cierra el gap por construcción.

## Sección 4 — Buyer-persona handling

### Q4.1 — Aggregate o módulo separado

**Realidad actual**: `BuyerPersona` es entidad standalone en
`src/modules/brand/domain/buyer_persona.py`, NO sub-model de
`BrandSettings`. Tiene su propio catalog
(`copilot_editable_fields_buyer_persona.py`) registrado como
`register_catalog("buyer_persona", ...)` (domain key independiente).

**Decisión Fase 06**: buyer-persona OUT of scope. Fase 07 lo migra como
módulo virtual `"buyer_persona"` en su propia file
`brand/domain/buyer_persona_field_contract.py` (ubicación física en `brand/`
para evitar mover archivos pero key registry independiente). Esto matchea
el patrón existente de catálogos separados.

Bloqueante resuelto.

## Sección 5 — `project_brand_studio_refactor` status

### Q5.1 — Sprint en curso

Memoria `project_brand_studio_refactor.md` (last update 2026-04-18):
- Sprints 0-5 + 2.D + 4a/4b/4c **DONE** (last commit `280e43aa`).
- Sprint activo: **6.E** — per-section editor migration (offer-studio, no
  brand). Sprint 6.D.5-D.11, 6.F, 6.H pendientes — todos FE-side.
- 4d-h (5 copilot tools) pendientes.

**Coordinación**: zero overlap con scope Fase 06. Fase 06 toca
backend brand domain (FieldContract registry); el brand-studio refactor
trabaja FE schemas + offer-studio editor + copilot routing.

Cero conflicto.

## Output

- [x] Lista completa Pydantic brand fields (113 paths derivables, 12
  top-level, 9 composables + 3 lists).
- [x] Section catalog brand confirmado (14 sections, mapping decidido).
- [x] Drift audit completo (3 categorías: shorthand broken, section
  mismatch, missing Pydantic fields).
- [x] Decisión buyer-persona: out of Fase 06, módulo virtual independiente
  en Fase 07.
- [x] Coordinación con brand-studio refactor: zero overlap (Sprint 6.E es
  FE-side offer-studio).

## Decisiones derivadas para SPEC + ACCEPTANCE

1. Walker config: `composable_fields=("identity", "strategy", "story",
   "contact", "visuals", "positioning", "narrative", "communication_assets",
   "brand_personality")`. Sin `polymorphic_prefix_map` (brand no usa
   polymorphic unions). Walker depth = 1 level (matching offer pattern).
2. Section map: 113 entries cubriendo cada Pydantic path derivable.
3. Ignore paths: `id`, `tenant_id`, `deleted_at`, `created_at`,
   `updated_at`, `metadata_info` (BaseEntity audit), más legacy fields
   marcados deprecated (`milestones_legacy`, `email`, `social` en
   contact) o internal-only.
4. Override `can_propose=False` para visuals derivative tokens (font_weights,
   typography_scale, border_radius_values, spacing_base, etc.) — el LLM
   no debería proponerlos.
5. BRAND_EDITABLE_FIELDS proyectado del registry → catalog post-refactor
   refleja Pydantic real (drift A/B/C cerrado por construcción).
6. UX byte-identical: las entries broken (drift A/B) no validaban antes
   y no validan después → cero cambio user-facing. Drift C agrega
   capabilities nuevas (no regresión).
7. `brand_personality.*` mapea section `personality` (catalog actual);
   alineación con section_catalog `estilo` queda diferida.
