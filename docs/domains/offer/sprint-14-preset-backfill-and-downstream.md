# Sprint 14 — Preset backfill + downstream consumers

**Date:** 2026-04-19
**Branch:** development
**Goal:** Make the 7th SSoT axis (OfferTypePreset, shipped Sprint 12) visible
to existing tenants and wire its signal into sales-agent grounding + landing
generation, without waiting for the Sprint 13 wizard rehaul.

## What shipped

### 14.1 — Backend column + migration + backfill script

- `ProductModel.preset_id`: String nullable, indexed partial on
  `(tenant_id, preset_id) WHERE preset_id IS NOT NULL`.
- Migration `050_add_offer_preset_id.py` (idempotent: ADD COLUMN + CREATE
  INDEX with IF NOT EXISTS; downgrade reverses).
- Script `backend/scripts/backfill_offer_preset_id.py`:
  - Builds `(business_type, archetype) → preset_id` defaults from the
    catalog (first match wins in insertion order).
  - Reads tenant `business_types` from
    `tenants.config_json->brand_settings->identity->business_types`.
  - Applies archetype-first, business-type-fallback lookup; leaves NULL
    when no match (conservative, no bad guesses).
  - Flags: `--dry-run`, `--tenant <UUID>`.
  - Idempotent (only writes `WHERE preset_id IS NULL`).

Applied on development DB:
- 20 offers scanned
- 15 tagged (all COACH_MENTOR tenants)
- 6 skipped (tenants without `business_types` declared — wizard will prompt)

### 14.2 — DTO / frontend / visible badge

- DTOs: `ProductResponse / ProductCreate / ProductUpdate` expose `preset_id`.
- Domain `Offer` class: `preset_id: str | None = None` with docstring.
- Repository `_to_domain` + `_to_model` pass preset_id end-to-end.
- Service `OfferService.create_offer` accepts `preset_id` kwarg.
- `test_archetype_sections.py` refactored from brittle tuple assertions
  (stale since Sprint 11) to semantic invariants (universal minimum,
  archetype core section, scope rules D22).
- Frontend: `Offer` type + `BackendOffer` + adapter carry preset_id;
  `OfferSchema` (zod) has `preset_id` nullable.
- **`<PresetBadge>` component** (new): resolves preset via catalog hook,
  renders emerald badge with Sparkles icon + tooltip with description.
  Null-safe. Inserted into `OfferCatalogCard` next to the archetype badge.

### 14.3 — Sales-agent grounding + landing flag-based template selection

- `shared/links/ports/offer.py` exports two new lazy-import ports:
  `get_offer_type_preset(preset_id)` and `get_preset_flag_values()`. This
  keeps DDD boundaries intact — `sales_agent` and `landing` consume the
  catalog through ports, never directly.
- Sales-agent `TenantKnowledgeBuilder._enrich_with_preset_metadata`
  injects `preset_label`, `preset_description`, `preset_flags` on each
  offer dict before Jinja render.
- `agent_identity.j2` uses `preset_label` as the offer type tag (falling
  back to the archetype for legacy). Displays "Qué es" (description) and
  "Señales clave" (flags).
- Landing service `_select_landing_archetype_from_preset` maps preset
  flags to `LandingPageArchetype`:
  - `IS_LEAD_MAGNET` → THE_SQUEEZE
  - `REQUIRES_START_DATE` → THE_EVENT
  - `HIGH_TICKET` → THE_TRANSFORMER
  - `RECURRING_BILLING` → THE_VELVET_ROPE
  - default → THE_BROCHURE
- `generate_landing_for_offer` now reads `preset_id` in its SQL and
  picks the matching landing archetype at creation.
- Legacy default fixed: `THE_SQUEEZE` → `THE_BROCHURE` (opt-in focus
  was a wrong assumption for non-lead-magnet offers).

## Analytics segmentation

`preset_id` is indexed composite with `tenant_id`. Any current or future
analytics query can group/filter by preset:

```sql
SELECT preset_id, COUNT(*) AS n, AVG(...) AS avg_x
FROM products
WHERE tenant_id = :tenant_id AND preset_id IS NOT NULL
GROUP BY preset_id;
```

No new endpoint was shipped — the data is ready for existing dashboards
to consume via the existing offer list endpoints (which now return
`preset_id` in the response DTO).

## DDD compliance

All cross-module access goes through `shared/links/ports/offer.py`:
- `sales_agent` → `get_offer_type_preset` + `get_preset_flag_values`
- `landing` → `get_offer_type_preset` + `get_preset_flag_values`

Arch test `test_no_new_cross_module_imports` passes.

## Commits

| SHA | Concept |
|---|---|
| `413eca66` | 14.1 — column + migration 050 + backfill script |
| `3d454bf2` | 14.2 — DTOs + frontend types + PresetBadge |
| `1fe26fd9` | 14.3 — sales-agent + landing gen flag routing |

## Validation

| Suite | Result |
|---|---|
| Backend arch tests | 332/332 ✅ |
| Backend offer module tests | 514/514 ✅ |
| Backend sales_agent (-test_conversation_context, -test_tools) | 267/267 ✅ |
| Backend landing tests | 12/12 ✅ |
| Frontend arch tests | 16/16 ✅ |
| Frontend schema tests | 97/97 ✅ |
| TypeScript | 0 errors ✅ |
| Ruff | 0 errors ✅ |

## User-visible changes on development tenants

1. **Offer Ladder dashboard**: every offer card now shows an emerald
   badge with the preset's label_es (e.g. "Sesión 1:1", "Curso grabado",
   "Mastermind") — right next to the archetype chip.
2. **Sales-agent conversations**: when the agent explains an offer, it
   says "tipo: Curso grabado" instead of "tipo: Producto". Reads the
   preset description so pitch copy is specific.
3. **Landing generation**: new offers created with a preset whose flags
   include HIGH_TICKET get THE_TRANSFORMER; lead magnets get THE_SQUEEZE;
   event-based get THE_EVENT. No more one-size-fits-all.

## Pending for Sprint 15+

- **Wizard integration (Sprint 13 — still pending)**: the wizard should
  use preset_id as the primary picker instead of archetype. Archetype
  becomes invisible to the user, derived from preset.
- **Per-archetype landing content builders**: right now every archetype
  renders SqueezeContent (structural superset). Sprint 15 should ship
  `EventContent`, `TransformerContent`, `VelvetRopeContent`, `BrochureContent`
  builders that consume preset_description and preset_flags to adapt
  copy automatically.
- **Analytics dashboards**: add a "Performance by preset" widget that
  groups conversion metrics by preset_id.
- **Sales-agent prompts per preset**: specialist prompts could load a
  preset-specific playbook from Qdrant when the active offer's
  preset_id matches a known pattern (e.g. "retainer-sales" playbook
  for consultor_retainer + agencia_retainer).

## Related docs

- `docs/domains/offer/offer-type-preset-catalog.md` — original axis design
- `docs/domains/offer/schemas-latam-refinement.md` — Task B (schemas)
- `.claude/skills/offer-type-preset-expert/SKILL.md` — maintenance skill
