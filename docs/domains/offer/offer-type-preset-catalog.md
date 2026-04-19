# Offer Type Preset Catalog — 7th SSoT axis

**Status:** Sprint 12 (2026-04-19). Backend + types + hooks complete.
Wizard integration is a separate sprint (see "Pending work" below).

## 1. Why this catalog exists

Forcing a microempresario Latam to choose between `PRODUCTO`, `PROGRAMA`,
`SERVICIO`, `MEMBRESIA` or `EXPERIENCIA` is marketer jargon. A nutricionist
selling "consulta médica" maps to three different archetypes depending on
whether it's one-off (SERVICIO), multi-session (PROGRAMA) or a continuous
plan (MEMBRESIA). We were forcing them to categorize before they could
describe.

The preset catalog inverts the flow: the user declares their
`business_types`, the wizard surfaces **4-11 presets in their own
vocabulary** ("Consulta única", "Paquete de tratamiento", "Plan de
seguimiento"), and the archetype becomes an **internal tag** derived from
the preset — never shown in the UI.

## 2. Position in the catalog DAG

```
ExpertBusinessType  OfferValueLevel  SectionCatalog  VariantStructure   ← 4 pure base
        │                  │                │                 │
        │                  │                └────────┬────────┘
        │                  │                         ▼
        │                  │                   OfferArchetype           ← intermediate
        │                  │                         │
        │                  │        ┌────────────────┤
        │                  │        │                │
        │                  ▼        ▼                ▼
        ├───── OfferLadderHints ────┤         OfferFormat              ← composites
        │                           │
        └───── OfferTypePreset ─────┘                                   ← NEW composite
```

`OfferTypePreset` is a **composite** that depends on:

- `ExpertBusinessType` (who sells it)
- `OfferArchetype` (internal fulfillment model)
- `SectionCatalog` (which sections the preset surfaces)

It is the 7th catalog. It does not introduce new base axes — it composes
existing ones.

## 3. Data model

| Field | Type | Purpose |
|---|---|---|
| `preset_id` | `str` (snake_case, unique, prefixed) | Stable id, e.g. `salud_consulta_unica` |
| `business_type` | `ExpertBusinessType` | Who sells this preset |
| `archetype` | `OfferArchetype` | Internal tag — never shown |
| `label_es` | `str` | User-facing name ("Consulta única") |
| `description_es` | `str` | 1-3 sentence card subtitle |
| `icon_name` | `str` (Lucide PascalCase) | Visual cue on preset card |
| `base_sections` | `tuple[SectionKey, ...]` | Ordered sections always shown |
| `conditional_question_ids` | `tuple[str, ...]` | Q's to refine base_sections |
| `default_flags` | `tuple[PresetFlag, ...]` | Semantic flags always active |
| `suitability_note_es` | `str` | Latam-specific hint for help surfaces |
| `examples_es` | `tuple[str, ...]` (≥2) | Concrete examples on the card |

### Conditional questions — composition layer

Seven binary refinement questions (`QUESTION_REGISTRY`) can be referenced
by any preset. The wizard renders only the preset's referenced questions:

| question_id | Toggles on YES |
|---|---|
| `requires_physical_location` | `+LOCATION` section |
| `has_specific_dates` | `+EVENT_DETAILS`, flag `REQUIRES_START_DATE` |
| `delivers_downloadable_materials` | `+RESOURCES` |
| `has_team_or_speakers` | `+INSTRUCTORS` |
| `is_hybrid_modality` | `+LOCATION`, flag `DELIVERY_HYBRID` |
| `has_limited_capacity` | flag `SUPPORTS_CAPACITY` |
| `has_portfolio_cases` | `+PORTFOLIO` |

Additive only. Duplicates de-duped preserving first occurrence so base
sections stay atop the rail.

### Flags — semantic signals

`PresetFlag` values: `SUPPORTS_CAPACITY`, `REQUIRES_START_DATE`,
`DELIVERY_HYBRID`, `IS_LEAD_MAGNET`, `RECURRING_BILLING`, `HIGH_TICKET`.

Downstream consumers (landing generator, sales-agent grounding, analytics)
read these instead of hard-coding preset-by-preset logic.

## 4. Catalog size (Sprint 12 initial version)

76 presets across 9 business types:

| BusinessType | Presets | Distribution |
|---|---|---|
| PROFESIONAL_SALUD | 7 | 3·SERV, 1·PROG, 1·MEMB, 1·EXP, 1·PROD |
| CONSULTOR_PROFESIONAL | 8 | 3·SERV, 2·PROG, 2·MEMB, 1·PROD |
| COACH_MENTOR | 10 | 2·SERV, 4·PROG, 1·MEMB, 1·EXP, 2·PROD |
| ACADEMIA_INFOPRODUCTOR | 10 | 3·PROG, 1·MEMB, 1·EXP, 5·PROD |
| ANFITRION_PRODUCTOR | 8 | 5·EXP, 3·MEMB |
| AGENCIA_FREELANCE | 8 | 5·SERV, 1·PROG, 1·MEMB, 1·PROD |
| MARCA_ECOMMERCE | 7 | 3·PROD, 2·MEMB, 1·EXP, 1·SERV |
| NEGOCIO_LOCAL | 11 | 2·SERV, 2·PROG, 3·MEMB, 2·EXP, 2·PROD |
| SOFTWARE_SAAS | 7 | 2·SERV, 1·PROG, 4·MEMB |

All 5 archetypes are reachable via at least one preset.

## 5. Decisions D26–D35 (this catalog)

**D26 — Preset as composite, not base axis.** Could have replaced archetype
with preset_id at the domain level. Rejected: archetype is consumed by 5
downstream systems (validators, sales agent, analytics, landing generator,
format catalog). Preset adds a UX layer atop archetype without breaking
those contracts.

**D27 — preset_id snake_case + business_type prefix.** Rejected plain slug
(`consulta_unica`) because duplicate labels across business_types would
collide (`consulta_unica` fits salud AND consultor). Prefix makes ids
immediately readable and arch-testable.

**D28 — Questions as additive only.** Rejected boolean "remove if NO" because
it complicates mental model and doubles arch-test surface. If user doesn't
need a base section they leave it empty in the editor — validators won't
block non-required sections.

**D29 — Questions as registry, not inline.** Could have inlined
`ConditionalQuestion` records per preset. Rejected because the 7 questions
repeat across 40+ presets. Registry + id reference is ~4x smaller and
enables the wizard to group identical questions across preset switches.

**D30 — 76 presets, not fewer or more.** Less than 3 per business_type
(D30a) felt claustrophobic in user-testing mock-ups. More than 15 per
business_type (D30b) flooded the picker. 4-11 range keeps picker dense
but legible in a 2-column grid.

**D31 — Lead magnets are presets, not a flag on any preset.** Initial draft
had `is_lead_magnet` toggle on regular presets. Rejected because lead
magnets have genuinely different section sets (no PRICING, compressed
CLOSING) and different downstream flows (auto-nurture trigger, upsell
target). Cleaner as distinct presets with `IS_LEAD_MAGNET` default flag.

**D32 — Bifurcated presets (cohort vs self-paced certification,
event-masterclass vs recorded-masterclass, challenge-program vs
challenge-product).** Rejected collapsing to one preset + conditional Q
because the two paths produce different archetypes downstream, breaking
the arch test `test_preset_archetype_exists_in_archetype_catalog`.
Separate presets preserve DDD integrity.

**D33 — SUBSCRIPTION_DETAILS MIXED scope stays as-is.** Preset-level
`default_flags = (RECURRING_BILLING,)` communicates billing recurrence to
downstream systems without altering SectionCatalog's existing scope rules.

**D34 — Retainer = MEMBRESIA, not SERVICIO.** `consultor_retainer` and
`agencia_retainer` could have been SERVICIO with `default_flags =
(RECURRING_BILLING,)`. Rejected: conceptually retainer is continuous
access, matching MEMBRESIA semantics. Sales-agent grounding expects
MEMBRESIA prompts for recurring revenue conversations.

**D35 — Gift card as PRODUCTO edge case.** Considered new archetype
"VOUCHER". Rejected: only 1 preset uses it, doesn't justify 6th archetype.
Modeled as PRODUCTO with minimal sections (`local_gift_card`).

## 6. Arch test gates

Located in `backend/tests/architecture/test_offer_type_preset_catalog_completeness.py`.
168 test cases across 15 test functions:

1. `test_preset_id_is_snake_case_and_prefixed_by_business_type`
2. `test_every_business_type_has_at_least_three_presets`
3. `test_preset_archetype_exists_in_archetype_catalog`
4. `test_base_sections_exist_in_section_catalog`
5. `test_conditional_question_ids_exist_in_registry`
6. `test_base_sections_cover_universal_minimum` (IDENTITY + PROMISE + CLOSING)
7. `test_paid_presets_include_pricing`
8. `test_lead_magnets_exclude_pricing`
9. `test_examples_es_non_empty_and_varied` (≥2 examples)
10. `test_catalog_entries_self_reference_their_key`
11. `test_question_registry_self_references_and_points_to_real_sections`
12. `test_every_archetype_has_at_least_one_preset`
13. `test_descriptions_and_labels_are_non_empty`
14. `test_resolve_preset_sections_*` (behavior tests)
15. `test_every_preset_resolves_cleanly_*` (parametrized over all 76)

## 7. When to add a new preset

1. Open `backend/src/modules/offer/domain/offer_type_preset_catalog.py`.
2. Pick the business_type + decide the internal archetype.
3. Compose `base_sections` starting from `_base_{archetype}()` helper.
4. Pick 0-3 applicable `conditional_question_ids` from `QUESTION_REGISTRY`.
5. Write 2-5 concrete `examples_es` (users recognise offers by example).
6. Write a `suitability_note_es` with Latam-specific hints (payment,
   regulatory, cultural).
7. Bump `_CATALOG_VERSION` in `api/offer_type_presets.py`.
8. Run `cd backend && .venv/bin/pytest tests/architecture/test_offer_type_preset_catalog_completeness.py -x`.
9. If the preset introduces a new conditional question, add to
   `QUESTION_REGISTRY` first and document the section/flag it toggles.

## 8. When to modify sections of an existing preset

Modifying `base_sections` of an existing preset is a **product decision**,
not a refactor. Check whether:

- Every tenant who picked this preset before the change still gets a
  coherent editor — the sections you remove won't orphan data.
- The preset's `suitability_note_es` still matches reality.
- A migration is needed if you're removing a section that has persisted
  data under `Offer.preset_id = <this>`.

If adding a section is conditional on user profile, prefer adding a
conditional question over widening `base_sections`.

## 9. Pending work (not in Sprint 12 initial)

- **Wizard integration** (Sprint 13): consume the catalog in
  `offer-studio/components/wizard/*` — preset picker grid, question flow,
  dynamic section rail. Eliminate `ArchetypePicker` from the UI (archetype
  becomes internal).
- **Offer row persistence** (Sprint 13): add `Offer.preset_id` column,
  Alembic migration idempotent, backfill existing offers with a default
  preset_id per (business_type, archetype) pair.
- **Analytics segmentation by preset** (Sprint 14): dashboard filters and
  performance metrics can group by preset_id for granular insights ("¿qué
  tipo de oferta de salud convierte mejor?").
- **Sales-agent grounding per preset** (Sprint 14): prompts loaded by
  `(business_type, preset_id)` pair instead of archetype alone.
- **Landing generator per preset** (Sprint 14): template selection
  informed by preset_id and its flags (HIGH_TICKET triggers long-form
  landing, IS_LEAD_MAGNET triggers opt-in page).

## 10. Related rules + docs

- `.claude/rules/offer-catalogs.md` — updated with 7th axis entry.
- `docs/domains/offer/catalogs-consolidation.md` — Phase 13 section added.
- `docs/domains/offer/variant-structure-catalog.md` — unchanged, structural
  axes remain pure.

## 11. Skill for ongoing maintenance

A Claude Code skill `offer-type-preset-expert` is registered in
`.claude/skills/`. Trigger phrases: "agregar preset", "nuevo tipo de
oferta", "modificar preset", "nueva pregunta condicional", "section en un
expertise". The skill guides the add/modify workflow end-to-end: backend
entry + arch test run + doc update + commit format.
