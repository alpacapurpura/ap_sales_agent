# VariantStructure Catalog — the 6th SSoT Axis

**Status:** Sprint 7 design lock (2026-04-18)
**Author:** offer-studio
**Owner:** this doc is the single source of truth. `variant_structure_catalog.py`
is the executable mirror; this file is the reviewable mirror. Bump both
together.

## 1. Why this axis exists

The offer-studio "edition" concept was born for time-anchored cohorts
(PROGRAMA), events (EXPERIENCIA) and recurring intakes (SERVICIO). Every
other archetype (PRODUCTO, MEMBRESIA) was explicitly `supports_editions=False`,
and the domain enum `EditionStructure` carried only three temporal values
(`SINGLE_DATE`, `COHORT`, `RECURRING`) plus `NONE`.

Product-wise, this forces us to hard-code marketing surface to "launches
with dates". Real tenants want:

- A subscription plan ladder (MEMBRESIA: gold / platinum / bronze).
- SKU variants of a physical product (PRODUCTO: size / color / material).
- Geographic variants of the same service (REGIONAL: price, currency, tax,
  legal profile per country).
- Modality variants (PROGRAMA: presencial / online / híbrido of the same
  program).
- Language variants (LANGUAGE: ES / EN / PT of the same offer).

The commonality: **a single offer fragments into multiple sellable
instances with mostly overlapping fields.** That is the exact mental
model of a LaunchEdition. The temporal modelling is one specialization of
a more general axis; other specializations are structurally identical but
differ in their validation + ownership rules.

We introduce `VariantStructure` as the generalization of `EditionStructure`.

## 2. DAG integration

The offer-studio catalog system becomes a **DAG of 6 axes**: 4 pure base
axes, 1 intermediate axis, 1 composite axis.

```
ExpertBusinessType  OfferValueLevel  SectionCatalog  VariantStructure   ← 4 pure base
(shared/)           (offer/)         (offer/)        (offer/) ← NEW
        │                                   │                 │
        │                                   │                 │
        │                                   └─────────┬───────┘
        │                                             ▼
        │                                     OfferArchetype            ← 1 intermediate
        │                                             │                    FK to 2 axes
        │                                             ▼
        └───────────────── OfferFormat ───────────────┘                  ← 1 composite
```

`VariantStructure` sits at the bottom of the DAG with **zero outbound
FKs**. The coupling direction is strictly inbound:

- `ArchetypeCapabilities.supported_variant_structures: tuple[VariantStructure, ...]`
  (wired in Sprint 8).
- `SectionMetadata` MIXED ownership rules consult `VariantStructure` at
  runtime (wired in Sprint 9).

This inversion is deliberate. The downstream rework of Experts, Formats,
Sections and Archetypes (user-announced, post-Sprint-7) must not churn
the `VariantStructure` catalog. Any temptation to "depend on the section
or archetype catalog from here" is a design smell — the metadata lives
where the metadata is, not cross-referenced.

## 3. Decisions

### D26 — Sixth axis as pure base (not an extension of Archetype)

**Decision:** `VariantStructure` is a separate enum + catalog, not a new
field inside `ArchetypeCapabilities`.

**Rationale:** Orthogonality. Same archetype supports multiple structures
(PROGRAMA cohort vs modality vs language), and the same structure spans
archetypes (TIER for MEMBRESIA and SERVICIO packages). If it were a field
on archetype, either we would deny the many-to-many or encode it as
combinatorial tuples. The DAG test ("can this be derived by joining
existing axes?") fails, therefore it is a new axis.

### D27 — No outbound FK, architecturally enforced

**Decision:** The catalog module has zero imports from `section_catalog`,
`archetype_catalog`, `format_catalog`, `value_level_catalog`, or
`expert_business_type`. The arch test
`test_variant_structure_catalog_purity.py` AST-parses the module and
rejects any such import.

**Rationale:** Survives the upcoming catalog rework. The user will
rewrite Experts entirely, reshape Sections, and expand Formats. Any
outbound dependency would have us updating the variant catalog every
time one of those moves. Pure base stays stable.

### D28 — Hybrid storage: indexable common columns + typed JSONB payload

**Decision:** The `launch_editions` table gains three new columns
(`variant_structure TEXT NOT NULL`, `structure_data JSONB NOT NULL
DEFAULT '{}'`, `sort_rank INTEGER`). Common-path columns (dates,
capacity, visibility, pricing_tiers, location_override) stay as typed
columns. Structure-specific fields (TIER features, SKU attributes,
REGIONAL country codes, MODALITY mode, LANGUAGE locale) live in
`structure_data`.

**Rationale:** Robustness + velocity.

- Indexable columns support the high-frequency queries (filter by
  status, capacity, date range) without GIN traversal.
- JSONB supports the long tail of per-structure fields without a schema
  migration per structure.
- Each structure declares its `required_structure_data_fields` in the
  catalog so the service layer validates the payload against a known
  shape — not the wild west of "whatever JSONB holds".
- If a structure's JSONB payload grows complex enough to warrant a
  child table (e.g. TIER features with per-feature metadata), the
  extraction is local: move the column, update the validator, leave
  everything else alone.

### D29 — `forbidden_base_fields` is catalog-declared, service-enforced

**Decision:** Each structure lists the base columns it must not
persist. TIER / SKU_VARIANT / REGIONAL forbid `start_date`, `end_date`,
`registration_start`, `registration_end` — because those columns make no
semantic sense for a non-temporal variant.

**Rationale:** Catalogs should declare their own invariants.
Service-layer validators call `get_variant_structure_metadata(structure).forbidden_base_fields`
and reject writes that set forbidden columns. Arch test
`test_forbidden_base_fields_reference_known_columns` guards typos.

### D30 — Clone policy in metadata, not in code

**Decision:** `CloneCopyPolicy` enum (`TEMPORAL_SHIFT`,
`PRESERVE_WITH_SUFFIX`, `RESET_IDENTIFIERS`, `STRUCTURAL_ONLY`) lives in
the catalog. The clone endpoint (Sprint 11) reads the policy from the
source variant's structure and dispatches the copy strategy.

**Rationale:** Clone logic was going to grow `if structure == X` chains
in the endpoint. Moving the policy into metadata lets the catalog
change independently — add a new structure, declare its clone policy,
the endpoint handles it without modification.

## 4. Inventory — 8 structures

### Temporal (require a start date)

| Key | Noun ES | Archetype (Sprint 8 default) | Typical cardinality | Clone policy |
|---|---|---|---|---|
| `temporal_cohort` | cohorte | PROGRAMA | MANY | TEMPORAL_SHIFT |
| `temporal_single_date` | salida | EXPERIENCIA | SINGULAR | TEMPORAL_SHIFT |
| `recurring_intake` | convocatoria | SERVICIO | MANY | TEMPORAL_SHIFT |

### Non-temporal (parallel instances)

| Key | Noun ES | Intended archetype (Sprint 10+) | Typical cardinality | Clone policy |
|---|---|---|---|---|
| `tier` | plan | MEMBRESIA, SERVICIO | FEW | PRESERVE_WITH_SUFFIX |
| `sku_variant` | variante | PRODUCTO | MANY | RESET_IDENTIFIERS |
| `regional` | región | any | FEW | PRESERVE_WITH_SUFFIX |
| `modality` | modalidad | PROGRAMA, SERVICIO, EXPERIENCIA | FEW | PRESERVE_WITH_SUFFIX |
| `language` | idioma | any | FEW | PRESERVE_WITH_SUFFIX |

See `backend/src/modules/offer/domain/variant_structure_catalog.py` for
the full record per structure.

## 5. Storage contract

Column shape in `launch_editions`:

| Column | Type | Null | Default | Populated by |
|---|---|---|---|---|
| `variant_structure` | TEXT | NOT NULL | `'temporal_cohort'` (server default) | Service at creation; backfilled by migration 049 from parent archetype |
| `structure_data` | JSONB | NOT NULL | `'{}'` | Service — validated against `required_structure_data_fields` |
| `sort_rank` | INTEGER | NULL | — | Service for structures where `supports_sort_rank=True` |

Indexes:

- `ix_launch_editions_offer_structure (offer_id, variant_structure)` —
  per-offer per-structure filtering ("all TIER rows for this offer").
- `ix_launch_editions_structure_data_gin (structure_data jsonb_path_ops)` —
  containment queries on structure-specific payload (SKU attributes,
  REGIONAL country codes).
- `ix_launch_editions_sort_rank (offer_id, variant_structure, sort_rank)
  WHERE sort_rank IS NOT NULL` — partial index for ordered-listing
  queries on non-temporal structures.

## 6. Invariants (arch-test-enforced)

From `tests/architecture/test_variant_structure_catalog_completeness.py`:

1. Every `VariantStructure` enum value has a `VARIANT_STRUCTURE_CATALOG`
   entry.
2. No orphan catalog entries.
3. Every record self-references its own key.
4. `order` values are unique and contiguous from 0.
5. `label_es`, `description_es`, `noun_es`, `noun_plural_es`, and
   `icon_name` are all non-empty.
6. `icon_name` is PascalCase (Lucide React convention).
7. `clone_policy` is a valid `CloneCopyPolicy`.
8. `cardinality` is a valid `VariantCardinality`.
9. `forbidden_base_fields` names real `LaunchEditionModel` columns.
10. Every TEMPORAL_* structure has `requires_temporal_anchor=True`.
11. Every non-temporal structure forbids `start_date`, `end_date`,
    `registration_start`, `registration_end`.

From `tests/architecture/test_variant_structure_catalog_purity.py`:

12. The catalog module imports **zero** other catalogs.
13. The only offer-module import allowed is `enums.VariantStructure`.

## 7. Extension rules

### Adding a new structure

1. Add the enum value to `VariantStructure` in
   `offer/domain/enums.py`. Pick a snake_case value that is
   architecture-agnostic (not "the_dropbox_case" but "subscription_tier").
2. Add the metadata record to `VARIANT_STRUCTURE_CATALOG`. Declare
   `order` (next available integer), Spanish copy, mechanics flags,
   clone policy, cardinality, required and forbidden fields, wizard
   prompt.
3. Bump `_CATALOG_VERSION` in `api/variant_structures.py`.
4. Run arch tests — they fail fast if any field is missing or malformed.
5. Run domain unit tests — they check semantic coherence across all
   structures (temporal anchor logic, sort_rank support, forbidden
   fields).
6. Update Archetype catalog (Sprint 8+) to add the new structure to
   relevant archetypes' `supported_variant_structures` tuples.
7. Update `docs/domains/offer/variant-structure-catalog.md` (this file)
   with the new row in §4 Inventory.

### Adding a new mechanics flag

Only when a flag genuinely describes the variant mechanism (not an
ownership rule, not a UX hint). Examples of legit flags: "supports
inventory tracking", "requires payment provider integration", "supports
trial period". Examples that don't belong here: "label colour" (UX),
"copy template" (content), "pricing_override on offer" (ownership —
belongs in SectionCatalog.MIXED rules).

### Adding a new `CloneCopyPolicy` value

Reserve for fundamentally different copy strategies. The four policies
currently cover "shift dates", "copy everything with suffix", "reset
unique identifiers", and "copy structure only" — the combinatorial
space is small. New policies should only appear if a new structure has
genuinely new clone semantics.

## 8. What comes next

Sprint 8 (`ArchetypeCapabilities.supported_variant_structures`):
    Wire archetype → structure fan-out. PROGRAMA will support
    `(TEMPORAL_COHORT, MODALITY, REGIONAL, LANGUAGE)`, MEMBRESIA will
    initially stay `()` until TIER UX lands in Sprint 10.

Sprint 9 (MIXED section ownership):
    Introduce `FieldOwnerRule` on `SectionMetadata`. Each MIXED section
    (PRICING, PROGRAM_DETAILS, SERVICE_DETAILS, RESOURCES) declares which
    of its fields belong on the Offer vs the LaunchEdition per
    `(archetype, variant_structure)` combination. Sprint 9 is deliberately
    scheduled **after** the user's catalog rework so field ownership is
    declared once on the final shape.

Sprint 10 (TIER pilot — MEMBRESIA end-to-end):
    First non-temporal UX. Wizard step, editor form (features list,
    price, highlight flag), pricing conversion. Proves the generalization.

Sprint 11 (clone API + UX):
    The `cloned_from_edition_id` FK already exists — this sprint gives
    it an endpoint and a "Duplicar" button, dispatching on
    `CloneCopyPolicy`.

Sprint 12 (SKU_VARIANT pilot — PRODUCTO end-to-end):
    Physical-product variants. Second non-temporal UX; the pattern is
    locked by then.

Sprint 13+: REGIONAL, MODALITY, LANGUAGE — prioritized by product demand.

## 9. Related

- `backend/src/modules/offer/domain/variant_structure_catalog.py` —
  executable SSoT.
- `backend/src/modules/offer/domain/enums.py` — `VariantStructure`
  + `FieldOwner` enums.
- `backend/src/modules/offer/api/variant_structures.py` — public
  cacheable endpoint.
- `backend/alembic/versions/049_variant_structure_columns.py` —
  migration.
- `.claude/rules/offer-catalogs.md` — regla resumida, incluye el 6to eje.
- `docs/domains/offer/catalogs-consolidation.md` — historial D1–D25.
