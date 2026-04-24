# Fase 02 — Migrate sections (SPEC)

**Objetivo**: aplicar el patrón Fase 01 al resto de las secciones huérfanas.
Allowlist `KNOWN_UNRESOLVED_PATHS` baja de **56 → 21** (35 paths cerrados).

Los 21 restantes son cross-module federados y pertenecen a Fase 05.

## Contexto heredado

- Fase 00 instaló el arch test `test-fe-schema-paths-resolve` con allowlist
  ratcheted (ADR-007).
- Fase 01 introdujo `FieldContract` + registry + endpoint + codegen TS + pilot
  pricing LATAM (commits `fbe4bb08 → 92523a6e`).
- `generate_offer_field_paths.py` introspecciona `Offer.model_fields` (top-level)
  + `ARCHETYPE_TO_DETAILS_MAPPING.values()` (polimórficos con prefijo
  `specific_details.`). Para nuevos campos composables necesita extenderse.

## Bloques semánticos (un commit por bloque salvo notas)

| # | Bloque | Paths | Migration DB | Scope BE |
|---|---|---|---|---|
| A | Authority block | 2 | Sí (2 cols) | Offer top-level |
| B | Value-stack anchor | 2 | Sí (2 cols) | Offer top-level |
| C | Program narratives | 2 | No (JSONB) | `ProgramDetails` |
| D | SubscriptionDetails (2 renames + 5 nuevos) | 7 | Sí (JSONB rewrite rename) | `SubscriptionDetails` |
| E | ServiceDetails (3 nuevos) | 3 | No (JSONB) | `ServiceDetails` |
| F | ProductDetails (5 nuevos) | 5 | No (JSONB) | `ProductDetails` |
| G | PlatformDetails composable | 14 | Sí (1 JSONB col) | Offer composable + FE schema migration |
| H | Extraction prompts (opcional bundled) | — | — | `offer_extract_*.j2` updates |
| I | Close: golden refresh + STATE bump | — | — | docs |

### A · Authority block (2 paths)

Paths FE: `authority_positioning_for_sales`, `authority_notes`

- **Migration**: `+authority_positioning_for_sales TEXT NULL`,
  `+authority_notes TEXT NULL` (idempotente `ADD COLUMN IF NOT EXISTS`).
- **Domain `Offer`**: 2 campos `str | None = None` con Field description.
- **Model `ProductModel`**: 2 columnas `sa.Text` mapeo 1:1.
- **DTO**: extender `OfferInstructorsUpdate` con los 2 campos.
- **FieldContract**: nueva sección `INSTRUCTORS_SECTION = "instructors"` con 2
  entries (tipo `"text"`, `required=False`, notas cortas).
- **Extraction**: no wave dedicada en Fase 02 (quedará para Fase 05 downstream
  unify; no bloquea guardrail).
- **Regen**: `generate_offer_field_paths.py` captura 2 nuevos paths top-level.
- **Allowlist shrink**: remover los 2 entries.

### B · Value-stack anchor (2 paths)

Paths FE: `total_perceived_value_anchor`, `stack_positioning_statement`

- **Migration**: `+total_perceived_value_anchor NUMERIC(12,2) NULL`
  `+stack_positioning_statement TEXT NULL`.
- **Domain `Offer`**: `total_perceived_value_anchor: float | None`,
  `stack_positioning_statement: str | None`.
- **Model `ProductModel`**: mapping 1:1.
- **DTO**: extender `OfferValueStackUpdate` con 2 campos.
- **FieldContract**: nuevas entries en sección `value_stack`.
- **Extraction**: agregar a `offer_extract_value_stack.j2` — prompt LLM para
  sugerir anchor + positioning statement cuando `deliverables[]` con
  `perceived_value` están cargados. `OfferValueStackUpdate` ya es el schema de
  salida de W2 value_stack, sumar los 2 campos extiende automáticamente.
- **Regen / shrink**: como A.

### C · Program narratives (2 paths)

Paths FE: `specific_details.weekly_time_commitment_hours`,
`specific_details.prerequisites_text`

- **Migration**: ninguna (JSONB `specific_details`).
- **Domain `ProgramDetails`**: `weekly_time_commitment_hours: int | None`,
  `prerequisites_text: str | None`.
- **DTO**: ya fluye vía `OfferDetailsUpdate.specific_details`.
- **FieldContract**: entries en sección `program_details` con
  `archetype_filter=(OfferArchetype.PROGRAMA,)`.
- **Extraction**: opcionalmente a `offer_extract_details.j2` (Block H).
- **Regen**: codegen JSON+TS detecta automáticamente (walk
  `ARCHETYPE_TO_DETAILS_MAPPING.values()`).
- **Allowlist shrink**: 2 entries.

### D · SubscriptionDetails (7 paths: 2 renames + 5 nuevos)

Paths FE:
- Renames: `specific_details.billing_frequency` (was `billing_cycle`),
  `specific_details.content_update_frequency` (was `content_update_freq`).
- Nuevos: `specific_details.auto_renewal_with_notice_days`,
  `specific_details.cancellation_anticipation_days`,
  `specific_details.grace_period_days_on_failed_payment`,
  `specific_details.member_benefits`,
  `specific_details.primary_communication_channel`.

- **Migration**: JSONB rewrite idempotente (2 passes). Ejemplo idempotente:
  ```sql
  UPDATE products SET specific_details =
      (specific_details - 'billing_cycle')
      || jsonb_build_object('billing_frequency', specific_details->'billing_cycle')
  WHERE specific_details ? 'billing_cycle'
    AND NOT specific_details ? 'billing_frequency';
  ```
  Idem para `content_update_freq`. Agregar defaults null para los 5 nuevos no
  hace falta (Pydantic default `None`).
- **Domain `SubscriptionDetails`**: renombrar 2 campos, sumar 5 nuevos con
  tipos (int / str / str). `primary_communication_channel` enum libre string
  hasta Fase 03/04 (no extraemos; UI-configured). `member_benefits` multi-line
  textarea → `str | None` (no list).
- **Infra**: ajustar arch tests / mocks si comparan estructura.
- **FieldContract**: 7 entries sección `subscription_details` con
  `archetype_filter=(OfferArchetype.MEMBRESIA,)`.
- **Regen / shrink**: 7 entries.

### E · ServiceDetails (3 nuevos)

Paths FE: `specific_details.response_time_hours`,
`specific_details.onboarding_flow`, `specific_details.scope_excluded`.

- **Migration**: ninguna.
- **Domain `ServiceDetails`**: 3 campos (`int | None`, `str | None`, `str | None`).
- **FieldContract**: 3 entries `service_details` con
  `archetype_filter=(OfferArchetype.SERVICIO,)`.
- **Regen / shrink**: 3 entries.

### F · ProductDetails (5 nuevos)

Paths FE: `specific_details.sample_preview_url`,
`specific_details.packaging_description`,
`specific_details.return_policy_days`,
`specific_details.shipping_carriers_accepted`,
`specific_details.shipping_estimate_by_region`.

- **Migration**: ninguna.
- **Domain `ProductDetails`**: 5 campos (`HttpUrl | None`, `str | None`,
  `int | None`, `str | None`, `str | None`).
- **FieldContract**: 5 entries `product_details` con
  `archetype_filter=(OfferArchetype.PRODUCTO,)`.
- **Regen / shrink**: 5 entries.

### G · PlatformDetails composable (14 paths) — ADR-010

Paths FE (actualmente flat): `platform_features`, `platform_integrations`,
`security_compliance`, `data_residency`, `uptime_guarantee`,
`status_page_url`, `support_channels`, `api_available`, `api_docs_url`,
`migration_tools`, `public_roadmap_url`, `changelog_url`,
`ai_features_disclosure`, `data_export_capability`.

**Decisión ADR-010 (nueva)**: NO crear `OfferArchetype.PLATFORM` ni 6ta entry
en `ARCHETYPE_TO_DETAILS_MAPPING`. Los campos son ortogonales al archetype
(cualquier oferta puede ser SaaS-flavored). Introducir `PlatformDetails`
como **composable** `Offer.platform_details: PlatformDetails | None` en
columna JSONB aparte de `specific_details`. Migrar FE paths a
`platform_details.X`.

- **Migration**: `+platform_details JSONB NULL` en `products` (idempotente).
- **Domain `PlatformDetails`**: clase nueva en `details.py`. 14 campos con
  tipos apropiados (algunos `bool`, `str`, `HttpUrl`). Arrays `platform_features`
  y `platform_integrations` como `list[Feature] / list[Integration]` con
  `BaseEntity` interno (nombres simples) — O `list[dict]` si preferís pospone
  tipado hasta Fase 03. **Decisión**: tipado estructurado, matches FE itemSchema.
- **Offer**: `platform_details: PlatformDetails | None = None`.
- **ProductModel**: `platform_details` JSONB column.
- **Repo offer_repository**: serializar/deserializar por model_dump /
  PlatformDetails(**data).
- **Codegen extension**: `generate_offer_field_paths.py` debe walk
  `Offer.model_fields['platform_details'].annotation` y emitir
  `platform_details.{field}` paths.
- **FE schema platform-details.schema.ts**: migrar TODOS los paths
  `platform_X` → `platform_details.X`. (Y `security_compliance` →
  `platform_details.security_compliance`, etc.)
- **FieldContract**: 14 entries sección `platform_details`.
- **Regen / shrink**: 14 entries.

### H · Extraction prompts (bundled, opcional)

Si queda tiempo, actualizar prompts para que LLM extraiga campos nuevos:
- `offer_extract_value_stack.j2` → `total_perceived_value_anchor`,
  `stack_positioning_statement`.
- `offer_extract_details.j2` → `weekly_time_commitment_hours`,
  `prerequisites_text`, `onboarding_flow`, `scope_excluded`,
  `response_time_hours`, `sample_preview_url`, `packaging_description`,
  `return_policy_days`.
- `authority_*` + `platform_*` NO extraer (manual / UI).

Este bloque puede diferirse a Fase 05 (downstream unify) — no bloquea guardrail.

### I · Close (golden refresh + STATE bump)

- Regenerar golden fixture `offer_a96403b5_baseline.md`.
- Correr roundtrip PATCH → GET end-to-end (si se sembraron campos nuevos).
- `STATE.md::last_green_commit` bump.
- `STATUS.md` → `status: done`.
- `phases/03-section-catalog/STATUS.md` abrir (`status: ready-to-start`).
- `LEARNINGS.md` append sección Fase 02 (expectations / descubrimientos /
  decisiones / tech debt).
- `DECISIONS.md` append ADR-010 (PlatformDetails composable).

## ADR-010 (propuesta)

**Título**: PlatformDetails composable, no 6ta entry de ARCHETYPE_TO_DETAILS_MAPPING.

**Razón**: Los 14 campos SaaS son ortogonales al archetype. Crear
`OfferArchetype.PLATFORM` cascadearía en:
- `ARCHETYPE_CATALOG` (nueva entry completa con sections + preguntas wizard)
- `format_catalog.py` (`suitable_for` por archetype)
- `offer_type_preset_catalog.py` (nuevos presets PLATFORM)
- `archetype_catalog.py::sections` para MEMBRESIA perdería PLATFORM_DETAILS
- Wizard UI (archetype picker)
- Edition / variant mechanics

Fuera de scope refactor. La solución composable preserva SSoT estructural
sin introducir scope creep de producto. `PLATFORM_DETAILS` section sigue
surfacéable por preset catalog (`_base_membresia() + SK.PLATFORM_DETAILS`).

**Alternativa rechazada**: PLATFORM archetype polimórfico — cascade scope.
**Alternativa rechazada**: 14 columns flat en Offer — modeling sucio.

## Out of scope Fase 02

- Cross-module federated paths (Fase 05).
- `OFFER_FIELDS_BY_FE_SECTION` dict removal (Fase 04).
- FE consumir section catalog (Fase 03).
- Nuevo `OfferArchetype.PLATFORM` (ADR-010 defer).
- Sales-agent prompt render data-driven (Fase 05).
- Landing content builders consumen FieldContract (Fase 05).

## Orden de ejecución sugerido (sub-steps)

0. PRE_FLIGHT — baseline tests verde (✅ captured at open)
1. Block A — Authority (commit `A`)
2. Block B — Value-stack anchor (commit `B`)
3. Block C — Program narratives (commit `C`)
4. Block D — SubscriptionDetails (commit `D`)
5. Block E — ServiceDetails (commit `E`)
6. Block F — ProductDetails (commit `F`)
7. Block G — PlatformDetails composable (commit `G`)
8. Block H — Extraction prompts (commit `H` si scope)
9. Block I — Close (commit `I` + ADR-010 append en DECISIONS.md)

## Métricas éxito

- `KNOWN_UNRESOLVED_PATHS.size === 21` post-Fase 02.
- BE arch 425 → 425+ (todos verdes; sumo al menos 1 test per block si nuevo
  código introduce riesgo — e.g. JSONB rename migration idempotency test).
- FE arch 37 → 37 (estable).
- TSC green.
- Offer `a96403b5...` round-trip igual o mejor.
- Sales-agent prompt additive only.
- Landing output byte-identical sin data nueva.
