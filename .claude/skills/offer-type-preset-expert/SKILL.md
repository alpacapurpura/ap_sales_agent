---
name: offer-type-preset-expert
description: "Offer Studio preset catalog expert (7th SSoT axis). Use when: adding a new preset, modifying an existing preset's sections or conditional questions, adding a new conditional question or flag, debugging 'why this section doesn't appear for tenant X', extending the preset layer to a new ExpertBusinessType, or coordinating preset changes with wizard/landing generator/sales-agent. Triggers: 'agregar preset', 'nuevo preset', 'modificar preset', 'nuevo tipo de oferta', 'nueva pregunta condicional', 'section en expertise', 'preset para este negocio', 'offer-type-preset', 'ExpertBusinessType nuevo', 'wizard preset picker', 'archetype surfacing'."
---

# Offer Type Preset Catalog Expert

## Read this first

The preset catalog is the **7th SSoT axis** of the offer-studio system.
It hides `OfferArchetype` behind user-vocabulary presets so Latam
microempresarios don't have to classify their own offers.

| File | Role |
|---|---|
| `backend/src/modules/offer/domain/offer_type_preset_catalog.py` | Canonical catalog — 76 presets, 7 questions, 6 flags. **Single source of truth.** |
| `backend/src/modules/offer/api/offer_type_presets.py` | API `/api/v1/offer/type-presets/catalog` + `/catalog/all`. Contains `_CATALOG_VERSION`. |
| `backend/tests/architecture/test_offer_type_preset_catalog_completeness.py` | 168 arch test cases — enforces all invariants. |
| `frontend/src/features/offer-studio/api/offer-type-preset-catalog-api.ts` | Mirror types + `resolvePresetSections` / `resolvePresetFlags` pure functions. |
| `frontend/src/features/offer-studio/hooks/use-offer-type-preset-catalog.ts` | React Query hooks. |
| `docs/domains/offer/offer-type-preset-catalog.md` | Full design doc with decisions D26–D35. |
| `.claude/rules/offer-catalogs.md` | DAG rules (eight catalogs). |

## Mental model — the layered flow

```
Step 1.  Tenant declares business_types in Brand Studio
         (e.g. PROFESIONAL_SALUD + NEGOCIO_LOCAL)
              │
              ▼
Step 2.  Wizard: useOfferTypePresetCatalog(business_types)
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
Step 6.  Persist: Offer.preset_id + Offer.archetype
         (archetype derived from preset, internal tag only)
```

The archetype layer still exists — it drives validators, sales-agent
grounding, analytics segmentation, landing-generator templates, and the
format catalog. **Never remove it.** The preset layer only hides it from
the UX.

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

All 168 (or more, now 169 with the new preset) must pass. Common
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

### 6. Commit

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

## Debugging: "the tenant sees wrong presets"

Checklist (in order):

1. **Tenant's `business_types` correct?** → Query Brand Studio identity,
   or check `GET /api/v1/brand/identity`.
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
