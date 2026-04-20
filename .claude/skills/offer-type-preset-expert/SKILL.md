---
name: offer-type-preset-expert
description: "Offer Studio preset catalog expert (7th SSoT axis). Use when: adding a new preset, modifying an existing preset's sections or conditional questions, adding a new conditional question or flag, debugging 'why this section doesn't appear for tenant X', extending the preset layer to a new ExpertBusinessType, or coordinating preset changes with wizard/landing generator/sales-agent. Triggers: 'agregar preset', 'nuevo preset', 'modificar preset', 'nuevo tipo de oferta', 'nueva pregunta condicional', 'section en expertise', 'preset para este negocio', 'offer-type-preset', 'ExpertBusinessType nuevo', 'wizard preset picker', 'archetype surfacing'."
---

# Offer Type Preset Catalog Expert

## Read this first

The preset catalog is the **7th SSoT axis** of the offer-studio system.
It hides `OfferArchetype` behind user-vocabulary presets so Latam
microempresarios don't have to classify their own offers.

**Current state (2026-04-20):** 84 presets · 7 questions · 6 flags · 187 arch tests.
**Important (2026-04-20):** tenant `business_types` no longer lives on
`BrandIdentity`. Read via `shared/links/ports/tenant_profile.py`
(`get_tenant_business_types(db, tenant_id)`) in backend or
`useTenantProfile()` in frontend. See `docs/domains/tenant-profile/`.
Distribución archetype: servicio=16 · programa=18 · membresia=22 · experiencia=13 · producto=15.
Questions: `requires_physical_location`, `has_specific_dates`, `delivers_downloadable_materials`, `has_team_or_speakers`, `is_hybrid_modality`, `has_limited_capacity`, `has_portfolio_cases`.
Flags: `SUPPORTS_CAPACITY`, `REQUIRES_START_DATE`, `DELIVERY_HYBRID`, `IS_LEAD_MAGNET`, `RECURRING_BILLING`, `HIGH_TICKET`.

### Catalog + API + tests
| File | Role |
|---|---|
| `backend/src/modules/offer/domain/offer_type_preset_catalog.py` | Canonical catalog — 84 presets, 7 questions, 6 flags. **Single source of truth.** |
| `backend/src/modules/offer/api/offer_type_presets.py` | API `/api/v1/offer/type-presets/catalog` + `/catalog/all`. Contains `_CATALOG_VERSION`. |
| `backend/tests/architecture/test_offer_type_preset_catalog_completeness.py` | 187 arch test cases — enforces all invariants. |

### Persistence + DDD bridge (Sprint 14)
| File | Role |
|---|---|
| `backend/src/modules/offer/domain/offer.py` | `Offer.preset_id: str \| None` — persistence anchor. |
| `backend/alembic/versions/050_add_offer_preset_id.py` | Migration adding `offers.preset_id` column + index. |
| `backend/src/shared/links/ports/offer.py` | `get_offer_type_preset(id)` + `get_preset_flag_values()` — cross-module access without DDD boundary break. |
| `backend/src/modules/offer/application/offer_service.py` | `create_offer(preset_id=..., conditional_answers=...)` — derives archetype from catalog (preset-primary). |

### Downstream consumers (MUST review when editing presets/flags)
| File | Reads |
|---|---|
| `backend/src/modules/sales_agent/application/services/knowledge_builder.py` | `preset.label_es`, `description_es`, `default_flags` → feeds `agent_identity.j2` |
| `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2` | Renders `preset_label`, `preset_description`, `preset_flags` defensively |
| `backend/src/modules/landing/application/landing_service.py::_select_landing_archetype_from_preset` | Branches template by flag: `IS_LEAD_MAGNET` / `REQUIRES_START_DATE` / `HIGH_TICKET` / `RECURRING_BILLING` |
| `frontend/src/features/offer-studio/components/dashboard/PresetBadge.tsx` | Renders user-facing label on `OfferCatalogCard` |

### Frontend (wizard preset-first, Sprint 13)
| File | Role |
|---|---|
| `frontend/src/features/offer-studio/api/offer-type-preset-catalog-api.ts` | Mirror types + `resolvePresetSections` / `resolvePresetFlags` pure functions. |
| `frontend/src/features/offer-studio/hooks/use-offer-type-preset-catalog.ts` | React Query hooks. |
| `frontend/src/features/offer-studio/components/wizard/PresetPickerStep.tsx` | Step 1 — preset grid filtered by `business_types` (from `useTenantProfile`). |
| `frontend/src/features/offer-studio/components/wizard/ConditionalQuestionsStep.tsx` | Step 2 — renders 0-3 conditional questions; answers feed `resolvePresetSections`. |
| `frontend/src/features/offer-studio/components/wizard/CreateOfferWizard.tsx` | Orchestrates preset-first flow. Reads `business_types` via `useTenantProfile()` — gating middleware guarantees non-empty. Passes `preset_id` + `conditional_answers` to `create_offer`. Archetype NO surfaced. |

### Tenant input — business_types (new 2026-04-20)
| File | Role |
|---|---|
| `backend/src/shared/links/ports/tenant_profile.py` | `get_tenant_business_types(db, tenant_id)` — ONLY cross-module read. Never import `tenant_profile` directly. |
| `backend/src/modules/tenant_profile/api/business_types_catalog.py` | `GET /api/v1/catalogs/business-types` (legacy `/api/v1/brand/expert-business-types/catalog` still 301s until 2026-05-04). |
| `frontend/src/features/tenant-profile/hooks/use-tenant-profile.ts` | `useTenantProfile()` — returns `{business_types, is_complete, can_change_now, ...}`. |
| `frontend/src/features/tenant-profile/hooks/use-business-types-catalog.ts` | `useBusinessTypesCatalog()` — replaces the retired `useExpertBusinessTypesCatalog`. |

### Docs + rules
| File | Role |
|---|---|
| `docs/domains/offer/offer-type-preset-catalog.md` | Design doc decisions D26–D35. |
| `docs/domains/offer/sprint-14-preset-backfill-and-downstream.md` | Sprint 14 — preset_id column + backfill + downstream wiring. |
| `docs/domains/offer/sprint-13-wizard-preset-first.md` | Sprint 13 — wizard rehaul. |
| `docs/domains/offer/schemas-latam-refinement.md` | Task B (2026-04-19) — 15 schemas Latam + ratchet tests. |
| `.claude/rules/offer-catalogs.md` | DAG rules (eight catalogs). |
| `frontend/src/features/offer-studio/schemas/__tests__/quality.test.ts` | 7 ratchet tests — hint coverage, no jargon, uniqueness, enum sanity, scope/owner coherence. |

## Mental model — the layered flow

```
Step 1.  Tenant declares business_types in the tenant_profile BC
         (at /onboarding/perfil-negocio or /settings/perfil-negocio,
         e.g. PROFESIONAL_SALUD + NEGOCIO_LOCAL).
         Backend reads via `shared/links/ports/tenant_profile.py`.
         Frontend reads via `useTenantProfile()`.
              │
              ▼
Step 2.  Wizard: useOfferTypePresetCatalog(useTenantProfile().business_types)
         → 4-11 presets filtered, shown in user's language
              │
              ▼
Step 3.  User picks preset (e.g. "salud_paquete_tratamiento")
              │
              ▼
Step 4.  Wizard renders conditional_question_ids (1-3 Q's)
              │
              ▼
Step 5.  resolvePresetSections(preset, questions, answers)
         → final ordered section tuple for the editor rail
              │
              ▼
Step 6.  create_offer(preset_id, conditional_answers, ...)
         → derives archetype from OFFER_TYPE_PRESET_CATALOG[preset_id]
         → resolves default_flags + conditional flags via resolve_preset_flags
         → persists Offer.preset_id + Offer.archetype
              │
              ▼
Step 7.  Downstream reads preset (NEVER persists archetype alone):
         - sales_agent.knowledge_builder → preset_label/description/flags
         - landing.landing_service → template selected by PresetFlag
         - dashboard PresetBadge → user-facing label
```

The archetype layer still exists — it drives validators, analytics
segmentation, and the format catalog. **Never remove it.** The preset
layer hides it from UX; Sprint 14 made preset the primary input to
`create_offer` (archetype derived, not user-chosen).

**Cross-module reads MUST go via `shared/links/ports/offer.py`** — never
`from src.modules.offer.domain.offer_type_preset_catalog import …`
outside the offer module. The DDD arch test ratchet will fail.

## SOP: Adding a new preset

### 1. Decide the shape

Before touching code, answer:

- **Which `ExpertBusinessType`?** Must be one of the 9 in
  `src/shared/domain/expert_business_type.py`. If the answer is "all /
  multiple", you're probably describing a generic pattern — skip the
  preset and rely on existing ones.
- **Which `OfferArchetype` is the internal tag?** The preset is a façade;
  the fulfillment model underneath must be one of the 5.
- **What sections?** Start from `_base_{archetype}()` helper. Only deviate
  when there's a concrete Latam-specific reason (documented in
  `suitability_note_es`).
- **Which conditional questions apply?** Pick 0-3 from `QUESTION_REGISTRY`.
  More than 3 is a flag that the preset is too generic.
- **Default flags?** Set `RECURRING_BILLING`, `HIGH_TICKET`, `IS_LEAD_MAGNET`
  if they always apply to this preset.

### 2. Write the entry

```python
"local_gym_corporativo": OfferTypePreset(
    preset_id="local_gym_corporativo",
    business_type=_EBT.NEGOCIO_LOCAL,
    archetype=_A.MEMBRESIA,
    label_es="Plan corporativo gimnasio",
    description_es=(
        "Convenio con una empresa para que sus empleados usen el gym "
        "con descuento grupal. Contrato mensual con RR.HH."
    ),
    icon_name="Building2",
    base_sections=_base_membresia() + (SK.LOCATION, SK.PORTFOLIO),
    conditional_question_ids=("has_team_or_speakers",),
    default_flags=(PresetFlag.RECURRING_BILLING,),
    suitability_note_es=(
        "Facturación B2B a la empresa. Mínimo de empleados activos "
        "sostiene el modelo. Reporte trimestral de uso renueva el contrato."
    ),
    examples_es=(
        "Gym corporativo empresa 50+ empleados",
        "Plan wellness para equipo",
        "Convenio gimnasio con la mutual",
    ),
),
```

### 3. Bump the catalog version

Edit `_CATALOG_VERSION` in `backend/src/modules/offer/api/offer_type_presets.py`.
Format: `YYYY-MM-DD.N` where N increments per same-day bump.

### 4. Run the arch tests

```bash
cd /home/chris/AISALESHT/backend && .venv/bin/pytest \
  tests/architecture/test_offer_type_preset_catalog_completeness.py -x -q
```

All 187 (or more, now 188 with the new preset) must pass. Common
failures and fixes:

| Failure | Cause | Fix |
|---|---|---|
| `test_preset_id_is_snake_case_and_prefixed_by_business_type` | wrong prefix | use correct prefix (`salud_`, `consultor_`, `coach_`, `academia_`, `anfitrion_`, `agencia_`, `ecom_`, `local_`, `saas_`) |
| `test_base_sections_cover_universal_minimum` | missing IDENTITY/PROMISE/CLOSING | add them to `base_sections` |
| `test_paid_presets_include_pricing` | no PRICING in base_sections | add `SK.PRICING` or mark as lead magnet |
| `test_lead_magnets_exclude_pricing` | PRICING in lead-magnet base_sections | remove PRICING; lead magnets are free |
| `test_examples_es_non_empty_and_varied` | < 2 examples | add more |
| `test_preset_archetype_exists_in_archetype_catalog` | typo / stale archetype | fix the `archetype=` value |

### 5. Update the doc

Open `docs/domains/offer/offer-type-preset-catalog.md`. Add a row to the
distribution table. If the preset introduces a novel decision (new
bifurcation rule, new archetype coupling), append a new D-number entry.

### 6. Review downstream consumers (Sprint 14)

Changes to `default_flags` or `label_es` / `description_es` propagate to:

- **sales-agent prompt** — `agent_identity.j2` renders preset context.
  Confirm flag changes don't break agent narrative (run a conversation).
- **landing template selection** — `_select_landing_archetype_from_preset`
  branches on `IS_LEAD_MAGNET` → `REQUIRES_START_DATE` → `HIGH_TICKET` →
  `RECURRING_BILLING`. A new flag combination may shift template.
- **dashboard PresetBadge** — label change is visible immediately.

If you added a new `PresetFlag`, wire a consumer (landing branch or
sales-agent render). Otherwise the flag is dead weight.

### 7. Commit

Single commit touching:
- `offer_type_preset_catalog.py`
- `offer_type_presets.py` (version bump)
- `offer-type-preset-catalog.md` (doc)

```
feat(offer-studio): +preset {preset_id} — {short reason}

- {business_type}: 3-line why it's needed (pain it solves)
- archetype tag: {ARCHETYPE}
- base_sections: list key additions vs default
- conditional_questions: list if any new
```

## SOP: Adding a new conditional question

Questions live in `QUESTION_REGISTRY` at the top of
`offer_type_preset_catalog.py`. Add one only when:

- The same refinement applies to **≥3 existing presets**. A one-off
  refinement belongs in `base_sections` of the single preset, not in a
  new question.
- The on_yes change is a **pure addition** (section or flag). Questions
  are additive-only by design — see D28.

```python
"has_physical_deliverable": ConditionalQuestion(
    question_id="has_physical_deliverable",
    question_es="¿Entregás un producto físico al cliente?",
    help_es=(
        "Material impreso, merchandising, kit físico enviado a domicilio."
    ),
    on_yes_sections=(SectionKey.PRODUCT_DETAILS,),
    on_yes_flags=(),
),
```

Then register the id in the `conditional_question_ids` tuple of every
preset where it applies. Run arch tests.

## SOP: Adding a new `PresetFlag`

Flags are enum values in `PresetFlag`. Add one only when a downstream
consumer (landing generator, sales-agent, analytics) needs to branch on
a semantic signal that isn't captured by existing flags.

```python
class PresetFlag(StrEnum):
    SUPPORTS_CAPACITY = "supports_capacity"
    ...
    REQUIRES_PHYSICAL_SHIPPING = "requires_physical_shipping"  # NEW
```

Document the consumer that reads the flag in the doc file's D-number
history so future authors know whether the flag is still load-bearing.

## SOP: Modifying an existing preset's sections

Modifying `base_sections` of an existing preset is a **product decision**,
not a refactor. Ensure:

1. Current tenants who picked this preset still get a coherent editor.
2. Data persisted under `Offer.preset_id = <this>` won't orphan after the
   change. Sections being removed may have content users wrote — check
   for usage before dropping.
3. A migration may be needed if you drop a section heavily used.

If the change is additive-but-conditional (e.g. PORTFOLIO only applies to
tenants with case studies), **prefer adding a conditional question** over
widening `base_sections`.

## SOP: Adding a new `ExpertBusinessType`

This is a **shared-domain** change with cross-cutting impact. Follow
`.claude/rules/offer-catalogs.md` → "Extending the system" first.
Specific to preset catalog:

1. After the new `ExpertBusinessType` is in `expert_business_type.py`
   and arch tests for that catalog pass…
2. Add its slug to `_BUSINESS_TYPE_SLUG` in
   `test_offer_type_preset_catalog_completeness.py`.
3. Add **at least 3 presets** for the new business_type (arch test
   requirement). Typically aim for 5-8.
4. Update the distribution table in `offer-type-preset-catalog.md`.
5. Regenerate the backend catalog version.
6. **Update the tenant-profile frontend mirror.** `frontend/src/features/tenant-profile/types/tenant-profile.ts` declares `ExpertBusinessTypeSlug` as a string-literal union and `EXPERT_BUSINESS_TYPE_SLUGS` as the frozen array — both must mirror the backend enum verbatim. Miss this and the onboarding selector will hide the new type.

## Debugging: "the tenant sees wrong presets"

Checklist (in order):

1. **Tenant's `business_types` correct?** → `GET /api/v1/tenant/profile`
   (since 2026-04-20 — no longer on `BrandIdentity`). Or via port
   `shared/links/ports/tenant_profile.get_tenant_business_types(db, tenant_id)`.
2. **Catalog version fresh?** → Compare `response.version` vs
   `_CATALOG_VERSION`. Force-refresh if different.
3. **Preset in catalog?** → Search
   `OFFER_TYPE_PRESET_CATALOG` by `preset_id`. Absent = stale deploy.
4. **Preset's `business_type` matches filter?** → Verify via
   `get_presets_for_business_types((tenant_bt,))`.
5. **Question on the preset but not in registry?** → Run
   `test_conditional_question_ids_exist_in_registry`.
6. **Frontend uses hook correctly?** → `useOfferTypePresetCatalog(bts)` —
   not `useOfferTypePresetCatalogAll()` which ignores business_types.

## Debugging: "section missing after preset selection"

1. Section in preset's `base_sections`? → it should appear unconditionally.
2. Section expected via conditional Q? → Check Q was answered YES.
3. `resolvePresetSections` being called? → Front-end wizard must call it
   and feed the result to the editor rail. Direct reading of
   `base_sections` ignores the conditional layer.
4. Section in `SECTION_CATALOG`? → Missing section-key silently drops on
   backend side; arch test catches this, but during development make
   sure to run it.

## Anti-patterns (PROHIBITED)

- ❌ Adding an archetype label ("Elegí tu archetype") in wizard UX.
  Archetype is internal — tenants see presets.
- ❌ Duplicating `ConditionalQuestion` or preset metadata client-side.
- ❌ Making a preset with < 2 `examples_es`. Users recognise by example.
- ❌ Marking as lead magnet while including `SectionKey.PRICING`.
- ❌ Adding a question that on_yes *removes* sections. Questions are
  additive only.
- ❌ Hard-coding preset_id logic in downstream services. Read flags,
  archetype, or section presence — never match on preset_id string.
- ❌ Creating a preset whose archetype isn't in `ARCHETYPE_CATALOG`.
- ❌ Letting `_CATALOG_VERSION` drift behind an entry change — clients
  won't invalidate cached responses.
- ❌ Importing `OFFER_TYPE_PRESET_CATALOG` or `PresetFlag` directly from
  another module (sales_agent, landing, analytics). Use the port
  `src/shared/links/ports/offer.py` (`get_offer_type_preset`,
  `get_preset_flag_values`) — DDD arch test fails otherwise.
- ❌ Adding new `PresetFlag` without at least one consumer branching on
  it. Dead flag = catalog rot.
- ❌ Surfacing archetype in wizard UX (ArchetypePickerStep is legacy —
  the preset-first wizard uses `PresetPickerStep` + `ConditionalQuestionsStep`).
- ❌ Reading `business_types` from `BrandIdentity`, `settings.identity.business_types`,
  or `config_json['brand_settings']['identity']['business_types']`. The field
  moved to the `tenant_profile` BC on 2026-04-20. Backend: `shared/links/ports/tenant_profile.get_tenant_business_types`.
  Frontend: `useTenantProfile()`. The arch test `test_business_types_ssot.py`
  fails the build if any module outside `tenant_profile` declares the field.

## Catalog navigation cheatsheet

**"I want to see all presets for a business type":**
```bash
curl 'http://localhost:8000/api/v1/offer/type-presets/catalog?business_types=profesional_salud' | jq '.presets[] | {preset_id, label_es, archetype}'
```

**"I want to see distribution per archetype":**
```python
from collections import Counter
from src.modules.offer.domain.offer_type_preset_catalog import OFFER_TYPE_PRESET_CATALOG
print(Counter(p.archetype.value for p in OFFER_TYPE_PRESET_CATALOG.values()))
```

**"I want to see which presets use a question":**
```python
from src.modules.offer.domain.offer_type_preset_catalog import OFFER_TYPE_PRESET_CATALOG
for p in OFFER_TYPE_PRESET_CATALOG.values():
    if "has_physical_deliverable" in p.conditional_question_ids:
        print(p.preset_id)
```

## Final checklist before you close the conversation

- [ ] Backend catalog change in a single commit.
- [ ] `_CATALOG_VERSION` bumped.
- [ ] `tests/architecture/test_offer_type_preset_catalog_completeness.py` passes.
- [ ] `offer-type-preset-catalog.md` updated (distribution + decisions).
- [ ] If you changed questions or flags: downstream consumers reviewed.
- [ ] `working tree clean`, commits pushed to `development`.
