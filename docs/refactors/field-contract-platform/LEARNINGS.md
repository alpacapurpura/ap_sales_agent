# Aprendizajes acumulados

Append-only. Cada fase suma entries. Cross-cutting arriba. Per-fase abajo.

---

## Cross-cutting (aplica a todo Nicolify)

### Heredados del workspace anterior (field-contract-ssot)

- **Pydantic default `extra="ignore"` es silent data loss trap.**
  `BaseEntity` config no declara `extra=`. Considerar `forbid` con
  arch test que permite legacy via migration `metadata_info`.

- **Schemas FE sin enforcement de paths contra BE domain = drift garantizado.**
  Capa A (9 paths huérfanos en field-contract-ssot Fase 00) lo demostró.

- **Allowlists de arch tests deben medirse, no estimarse.** Fase 00 SPEC
  predijo 9 paths y la realidad fue 59. Antes de fijar cap en ADR,
  correr el test contra el repo y contar.

- **Polling cap hardcoded 120s** rompió offer extraction >2min. Safety
  caps arbitrarios son frágiles. Poll hasta terminal con cap alto +
  backoff.

- **Scripts standalone que tocan SA deben importar `model_registry`
  primero**. Sin eso, primer query falla.

- **Fixtures golden de BE que necesitan DB corren dentro del container,
  no en WSL native.** Docker publica en Windows host, WSL2 no llega
  por `localhost`.

### Nuevos (descubiertos al pivotar a field-contract-platform)

- **Allowlist shrink no es proxy suficiente para cobertura de FieldContract
  registry.** Fase 02 del refactor anterior cerró sin notar 41 fields gap
  porque la métrica era "shrink de allowlist `KNOWN_UNRESOLVED_PATHS`",
  que mide paths huérfanos en codegen JSON (Pydantic-derived). Los 41
  fields legacy nunca aparecieron en la allowlist porque sus paths
  resolvían en el codegen. Solución: arch test independiente
  `Pydantic.model_fields ⊆ FieldContract paths` por módulo migrado.

- **Refactors estructurales empiezan con inventario completo de SSoT
  paralelos.** Antes de definir scope: grep cross-module por todos los
  registries que mencionan "field" o "section". Los 5 fuentes paralelas
  descubiertas en Fase 04 deberían haber sido inventario inicial.

- **`copilot/domain/schema_introspection.py` ya hace introspección
  Pydantic robusta** (`unwrap_optional`, `get_model_sections`,
  `validate_field_path`). Reutilizable en cualquier walker nuevo —
  no inventar.

- **Drift confirmado entre `OFFER_EDITABLE_FIELDS` y `FIELD_CONTRACT_REGISTRY`**
  al abrir Fase 04. Los nuevos pricing LATAM (tax_included,
  installments_available, accepted_payment_providers), authority fields,
  total_perceived_value_anchor, stack_positioning_statement viven en
  un registry pero no en el otro. Sin arch test que fuerce paridad,
  drift entre registries paralelos es inevitable.

- **`OFFER_FIELDS_BY_FE_SECTION` y similares dicts manuales son trampa
  recurrente.** Cualquier dict `{section: tuple[fields]}` que no se
  derive automáticamente acumula drift. Patrón evitar: si el dict tiene
  más de 5 entries y no está auto-generado, está mal.

---

## Fase 04 — Platform foundation

**Status**: done (2026-04-24)

### Pre-fase expectations vs realidad

- ✅ Promovido `FieldContract` a `shared/domain/`.
- ✅ Offer migrado completo end-to-end. Cerró drift entre los 5
  registries paralelos.
- ✅ Brand/buyer/copilot intactos (no se tocaron en Fase 04).
- ✅ UX preservado — 4217 tests pass (vs ~4200 baseline + nuevos arch).
- ✅ Arch tests cross-cutting que fuerzan cobertura (16 nuevos tests).

### Resultados cuantitativos

| Métrica | Pre-Fase 04 | Post-Fase 04 |
|---|---|---|
| Registries paralelos en offer | 5 (editable_fields, schema_introspection, PERSISTABLE_FIELDS, FIELD_CONTRACT_REGISTRY, OFFER_FIELDS_BY_FE_SECTION) | 1 (`OFFER_FIELD_CONTRACTS` derivado) |
| FieldContract entries | ~40 manual | 153 derivados |
| OFFER_EDITABLE_FIELDS entries | 36 manual | 149 derivados |
| PERSISTABLE_FIELDS paths | 25 manual | 149 derivados |
| Drift posible | sí (manual) | no (arch test enforces) |
| Tests arch totales | 432 | 448 (+16 platform coverage) |
| Tests totales backend | ~4200 | 4217 |

### Descubrimientos

- (Sub-paso A) Inventario confirma 5 fuentes paralelas + 1 dict legacy.
  Drift entre `OFFER_EDITABLE_FIELDS` (36 entries) y
  `FIELD_CONTRACT_REGISTRY` (40 entries con overlap parcial) — los
  pricing LATAM nuevos, authority fields, value-stack anchor estaban
  en uno pero no en el otro. Migrar a derivación cierra esto por
  construcción.

- (Sub-paso B) Walker Pydantic recursivo necesita manejar:
  `Optional[X]`, `X | None` (PEP 604), `list[X]`, `Enum`, `Annotated`,
  `Union[A, B, ..., None]` (polymorphic), composable nested. Reuso de
  patrones de `copilot/domain/schema_introspection.py` ahorró tiempo.

- (Sub-paso C) Cuando dos polymorphic variants comparten un sub-path
  con la **misma** section, el walker mergea (archetype_filter union).
  Cuando comparten path con **distinta** section (e.g.
  `specific_details.start_date` en ProgramDetails vs EventDetails),
  emite **dos contracts** archetype-aware. Solución: `dedup key` =
  `(path, section)` y `PolymorphicVariantSpec` declara la section
  correspondiente a cada variant. Esto preserva el comportamiento
  legacy de `resolve_details_section(archetype)` sin requerir runtime
  lookup.

- (Sub-paso D) `fields_to_fe_sections()` derivada del registry mantiene
  forward-compat con sub-fields no formalizados via `specific_details.*`
  catch-all per `resolve_details_section(archetype)`. Permite que LLM
  emite paths nuevos antes de que se agreguen overrides.

- (Sub-paso D) Cambio sutil: `headline_promise`, `primary_outcome`,
  `time_to_value` se mantienen en section `identity` (matching legacy
  `OFFER_FIELDS_BY_FE_SECTION` grouping), no `promise`. Preserva UX
  byte-identical en extraction badges.

- (Sub-paso E) Catalog `OFFER_EDITABLE_FIELDS` proyectado dedupea por
  `path` (no `(path, section)`) — el copilot surface es archetype-
  agnostic; cada path tiene 1 entry sin importar variant. Distinto de
  extraction grouping que ES archetype-aware.

- (Sub-paso F) `PERSISTABLE_FIELDS = set[str]` derivada — drop manual
  + ahora cubre 149 paths (vs 25 hand-written). Fields que el copilot
  podía proponer pero nunca persistir por falta del set ahora están
  cubiertos.

- (Sub-paso G) Anti-regression test del dict OFFER_FIELDS_BY_FE_SECTION
  combina: `hasattr` check del módulo + grep recursivo en src/ por
  asignaciones del nombre. Doble guard previene re-introducción.

- (Sub-paso H) Arch test cross-cutting `Pydantic ⊆ FieldContract` falla
  cuando alguien agrega un Offer Pydantic field sin entry en
  `OFFER_SECTION_MAP`. Lección clave del refactor anterior: este test
  es el que hubiera prendido la alarma temprano sobre el gap de 41
  fields.

- (Sub-paso I) Generic guards parametrizados sobre `_MIGRATED_SPECS`
  permiten que Fases 06/07 hereden todos los checks gratis con 1 nuevo
  spec entry.

### Decisiones nuevas

ADR-011..017 ya documentadas pre-implementación. Ninguna ADR nueva
durante la ejecución — el diseño cubrió bien los edge cases.

### Deuda técnica encontrada (en scope)

- **`copilot/domain/schema_introspection.py` mantiene su propio
  `unwrap_optional` + `is_pydantic_model` + `is_list_of_pydantic`**
  paralelo al walker shared. Fase 08 puede consolidar — por ahora
  cada uno funciona independiente (cero coupling). No es bloqueante,
  solo over-DRY.

- **`copilot/domain/offer_fields.py` sigue existiendo como archivo
  separado** que solo proyecta `PERSISTABLE_FIELDS = set[str]`.
  Consumers (offer_persister, schema_introspection) podrían leer
  `get_module_contracts("offer")` directo. Fase 08 evalúa drop.

- **`src/modules/offer/api/offer_field_contract.py` DTO mantiene
  shape compat** (`owner` string, `required` bool) en lugar de exponer
  el shape rico nuevo (`status`, `human_question_es`, etc.). Decisión
  pragmática para no tocar FE schemas en Fase 04. Fase 09 puede
  expandir el shape cuando consumers FE estén listos para multi-channel.

### Deuda técnica (tangencial — entry en `docs/mejoras-proceso/to-do.md`)

- Test `test_streaming_integration.py::test_tool_call_produces_tool_events`
  es flaky (passes isolated, fails en suites largas con side-effects).
  No relacionado al refactor (el copilot streaming no consume
  FieldContract). Anteriormente reportado.

- `src/modules/offer/api/offer_type_presets.py:28` — `# noqa` directive
  con formato inválido. Pre-existing desde Fase 01 del refactor anterior.

### Para Fase 05

- Sales-agent `agent_identity.j2` + landing builders + completion service
  consumen `get_module_contracts("offer")` directamente. Inventario
  detallado en `phases/05-downstream-data-driven/PRE_INVESTIGATION.md`.
- Golden snapshot offer `a96403b5-c1db-4b31-97aa-cb18d08ad9f9` baseline
  capturado pre-Fase-05 para diff byte-identical post.

### Closing commit hash

Last green commit Fase 04: (TBD by 04.J).

---

## Fase 05 — Downstream data-driven

**Status**: done (2026-04-24)

### Pre-fase expectations vs realidad

- ✅ Golden snapshots establecidos para los 3 consumers downstream
  (agent_identity render, landing builders, completion service).
- ✅ Lifecycle gate operativo: `knowledge_builder` strippea offer-dict
  keys cuyo `FieldContract.status != ACTIVE` antes de pasar al template.
- ✅ Arch tests cross-cutting que aseguran cada path consumido por los
  3 consumers existe + ACTIVE en el contract.
- ⚠️ NO se reemplazó el chain de `{% if offer.X %}` en `agent_identity.j2`
  por un loop sobre contracts. Razón: el handling de whitespace de
  Jinja2 con `trim_blocks=True, lstrip_blocks=True` produce líneas
  *intencionalmente squashed* (markers concatenados sin newline cuando
  un bloque inline `{% endif %}` precede el `\n` implícito del cuerpo
  del for-loop o de un `{%- if %}`). Reproducir byte-identical en
  Python requiere un renderer custom por field + serializar todo el
  body en un string, fuera del scope del lifecycle gate. Diferido a
  una fase futura — likely Fase 09 (multi-channel projection) cuando
  el agent prompt deje de ser j2-driven.
- ⚠️ NO se alineó `_SECTION_VALIDATORS` del completion service con
  `is_required_semantic`. Razón: el completion usa una taxonomía de
  *completion-section* propia que no es 1:1 con la *contract-section*
  taxonomy (e.g. completion's `promise` valida solo `headline_promise`
  mientras la contract section `promise` cubre `before_state` /
  `after_state` / `why_now` / etc.). Consolidar requiere o un mapping
  layer (`completion_section: str | None` en override) o reformular
  el completion validator. Diferido — el arch test ya garantiza el
  subset de paths.

### Resultados cuantitativos

| Métrica | Pre-Fase 05 | Post-Fase 05 |
|---|---|---|
| Golden snapshots downstream | 0 | 3 (agent_identity, landing, completion) |
| Arch tests cross-cutting downstream | 0 | 5 (paths ⊆ contract) |
| Tests arch totales | 448 | 453 |
| Lifecycle gate sales-agent | manual (sin gate) | automático via `filter_offer_for_prompt` |
| Drift detector new fields | no | sí (template + completion + landing) |

### Descubrimientos

- (05.A) El test `test_offer_a96403b5_baseline.py` que ya existía solo
  verifica `public_name in prompt` — no byte-identical. Para garantizar
  byte-identical hubo que crear goldens nuevos con offer sintético
  cubriendo los 30+ markers del template.

- (05.A) La huella whitespace del template actual de `agent_identity.j2`
  squashea Tipo + Qué es + Señales clave + Promesa en una sola línea
  (sin `\n` entre markers) por el efecto combinado de `{%-` strip-before
  y `trim_blocks=True` después de `{% endif %}` inline. Lo mismo pasa
  con `pricing_options` for-loop: las dos pricing options + Impuestos +
  Cuotas + Métodos + Garantía + Incluye terminan squashed en una sola
  línea. Esto es un accidente histórico que el LLM probablemente parsea
  igual, pero a nivel byte-identical es la huella a reproducir.

- (05.B) Los 4 fields del template que no están en contract son enrichment-
  only (`preset_label`, `preset_description`, `preset_flags` inyectados
  por `_enrich_with_preset_metadata`) más `type` que es legacy fallback
  cuando archetype/format_hint/preset_label no aplican. Whitelisted en
  arch test.

- (05.D) Drift entre legacy completion sections y contract sections:
  `headline_promise` legacy=promise contract=identity, `value_level`
  legacy=identity contract=strategy. La completion section es
  user-experience-driven (qué progreso ve el usuario), la contract
  section es estructural-FE. Necesitan layer de translation, no merge.

- (05.E) Landing builders leen vía raw-SQL `data.get("name")` y
  `data.get("pricing")` (legacy DB columns) en vez del Offer aggregate.
  Migrarlos al aggregate Pydantic (drop el raw SQL en `landing_service.generate_landing_for_offer`)
  fue OUT of scope — only documented en el legacy allowlist del arch
  test.

### Decisiones nuevas

Ninguna ADR formal. Decisiones de scope reduction documentadas in-line
en commits + arch tests. Próxima fase puede revisitar:

- ADR-018 (futuro): renderer-spec metadata para sales-agent prompt
  (`prompt_label_es`, `prompt_renderer_kind`, `prompt_priority`).
- ADR-019 (futuro): completion-section translation layer.

### Deuda técnica encontrada (en scope, no resuelta)

1. **Reemplazar `{% if offer.X %}` por loop sobre contracts** en
   `agent_identity.j2`. Diferido por whitespace handling complexity.
   Plan tentativo: porting completo del offer body a Python con
   renderer per-field + override metadata `prompt_label_es`. Refresh
   del golden + audit del diff. Realmente deja de ser byte-identical
   (los squashes desaparecen) pero el LLM debería tomarlo igual o
   mejor (markers en líneas separadas).

2. **Alineación `is_required_semantic` ↔ `_SECTION_VALIDATORS`**.
   Hoy hay overlap parcial pero no isomorphism. Aligning requires
   completion_section translation map o reformular completion-section
   taxonomy. Plan tentativo: agregar `completion_section: str | None`
   a `FieldContractOverride`; cuando set, override el contract section
   for completion-service-only. Cuando null, usar contract section.

3. **Migrar landing builders al Offer aggregate**. Drop el raw-SQL en
   `landing_service.generate_landing_for_offer`. Drop legacy `pricing`
   JSONB column read (mapping a `pricing_options` desde el aggregate).
   Drop el alias `name` (usar `public_name`). Eliminar la
   `LEGACY_SQL_ALIASES` allowlist del arch test.

### Deuda técnica (tangencial — entry en `docs/mejoras-proceso/to-do.md`)

- `agent_identity.j2` whitespace artifacts (markers squashed). Si el
  refactor de tech debt (1) procede, el output mejora naturalmente.

### Para Fase 06

- Brand migration sigue patrón offer (Fase 04). Pre-investigación
  obligatoria — inventario de `BRAND_EDITABLE_FIELDS` + drift audit
  vs `BrandIdentity` Pydantic.
- Coordinación con `project_brand_studio_refactor` activo.
- Aplicar lessons de Fase 05: golden snapshots cross-consumer ANTES
  de tocar overrides.

### Closing commit hash

Last green commit Fase 05: `d0d121f1`.



---

## Fase 06 — Brand migration

**Status**: done (2026-04-24)

### Pre-fase expectations vs realidad

- ✅ Brand FieldContract registry derivado completo (113 contracts) —
  drift A/B/C cerrado por construcción.
- ✅ BRAND_EDITABLE_FIELDS proyectado del registry — sin tuples manuales.
- ✅ UX byte-identical: 38/38 WORKING_PATHS_BASELINE preservados, 60
  curated Spanish labels intactos en proyección.
- ✅ Buyer-persona NO se tocó (Fase 07 lo migra independiente).
- ✅ Coordinación con `project_brand_studio_refactor` activo confirmada
  cero overlap (Sprint 6.E es FE offer-studio).
- ✅ Generic platform fitness gates (template) corren para brand sin
  cambios (1 entry: `_brand_spec()` builder).

### Resultados cuantitativos

| Métrica | Pre-Fase 06 | Post-Fase 06 |
|---|---|---|
| Brand catalog entries | 78 (mixto: 38 working + 40 broken) | 86 (todas válidas) |
| BRAND_FIELD_CONTRACTS | n/a | 113 derivados |
| Drift entre catalog y Pydantic | severa (40/78 broken) | cero (proyección) |
| Manual hand-written tuples brand | 9 (`_IDENTITY/_STORY/.../_LEGAL`) | 0 |
| Tests arch totales | 453 | 471 (+18 brand-specific + cross-cutting) |
| Tests totales backend | 4217+ | 4261 |
| MIGRATED_MODULES | `("offer",)` | `("offer", "brand")` |

### Descubrimientos

- (06.A) Drift audit reveló 3 categorías:
  - **A**: 17 paths shorthand 2-level (`positioning.insight_tension`
    intentando flatten `positioning.insight.tension`). Validador
    `validate_field_path` los rechaza — dead silent.
  - **B**: 23 paths con wrong section (`contact.legal_*` cuando
    Pydantic tiene `identity.legal_*`). Validador rechaza también.
  - **C**: ~75 Pydantic fields user-facing sin entry catalog
    (visuals derivative tokens, regulated/professional fields,
    communication_assets, team CRUD, etc.).

  Confirmación empírica vía `validate_field_path("brand", ...)`:
  Drift A/B paths return False → catalog drop = UX byte-identical
  (INVARIANT 4).

- (06.C) BrandSettings es estrictamente composable: 9 sub-models con
  shape `SubModel | None`, sin polymorphic unions. Walker config:
  `composable_fields=("identity","strategy","story","contact","visuals","positioning","narrative","communication_assets","brand_personality")`,
  walker depth = 1 level. Match exacto con offer's `platform_details`
  pattern.

- (06.C) Sub-objects nested (BrandPositioning.insight, BrandNarrative.hero,
  etc.) emitten como `FieldType.OBJECT` con `can_propose=False`.
  Mantiene la profundidad de exposición consistente con offer y matchea
  lo que el copilot puede realmente proponer (validador acepta solo
  1-level paths).

- (06.D) Preservación de labels curados es **clave para UX byte-identical**.
  Walker default labels via `_humanize()` produce "Brand Name", "Tax Id".
  Los 60 labels curados ("Razón social", "Email DPO", "Tagline") viven
  en `BRAND_FIELD_OVERRIDES` con `label_es=...` para cubrir el surface
  del system prompt. Los 26 paths nuevos (Drift C) usan humanize
  fallback — newly-exposed, no UX prior preserva.

- (06.D) `identity.voice_tone` está en `_DEPRECATED_PATHS` del
  arch test `test_no_legacy_paths_in_any_catalog`. Se marca DEPRECATED
  + can_propose=False en `BRAND_FIELD_OVERRIDES`. Walker derivation
  lo emite igualmente como contract pero la projection lo filtra. UI
  ya no lo renderiza — alineamiento completo.

- (06.D) `BrandStrategy` removed `unique_value_proposition` /
  `competitors` / `value_proposition` / `target_audience` /
  `differentiation` / `offerings` (model_validator migra-on-load a
  positioning). Esos campos NO están en model_fields actualmente —
  walker no los emite, no aparecen en registry. UVP vive en
  `positioning.unique_value_proposition`. Migración legacy intacta.

- (06.E) Las 6 fitness gates parametrizadas heredadas de Fase 04.I
  corrieron para brand sin cambios (`_brand_spec` registrado en
  `_build_module_registry`). Pattern validado: agregar módulo nuevo
  = 1 spec entry + 1 entry en MIGRATED_MODULES + sus arch tests
  específicos opcionales.

- (06.F) Anti-regression brand: ratchet test que prohíbe múltiples
  `FieldSpec(` calls en `copilot_editable_fields.py` (solo 1 dentro
  del projection helper) + assert que importa BRAND_FIELD_CONTRACTS.
  Mirror del pattern offer.

### Decisiones nuevas

Ninguna ADR formal. Decisiones de scope reduction documentadas in-line:

- 06.B fold-into-06.C: walker shared ya validado por offer Fase 04
  con casos polymorphic + composable. Brand es estrictamente composable
  (caso más simple).
- Buyer-persona out of Fase 06: confirma plan original (Fase 07).
- `brand_personality.*` mapea section `personality` (catalog actual),
  no `estilo` (section_catalog editor key) — alineación diferida.

### Deuda técnica encontrada (en scope, resuelta)

- ✅ Drift A/B/C cerrado por construcción (catalog ahora projection).
- ✅ Anti-regression test (06.F) previene re-introducción de manual tuples.
- ✅ `identity.voice_tone` lifecycle DEPRECATED status documentado.
- ✅ Legacy aliases `contact.email`, `contact.social`, `story.milestones_legacy`
  marcadas DEPRECATED con `replaced_by`/`notes`.

### Deuda técnica (tangencial — entry en `docs/mejoras-proceso/to-do.md`)

- Section `personality` (catalog) vs `estilo` (section_catalog editor key)
  drift cosmético. Unificación requiere coordinación con FE form-runtime.
- Nested-of-nested propuesta (e.g. `positioning.insight.tension` como
  proposable path) — hoy emitidos como OBJECT can_propose=False.
  Habilitarlo requiere extender walker a depth 2 para módulos selectos
  + actualizar `validate_field_path._build_brand_paths` a 2-level.
  Probable fase futura.

### Para Fase 07

- Buyer-persona standalone — Pydantic con dict-typed JSONB
  (demographics, psychographics, buyer_journey, pain_points, etc.).
- Walker actual no maneja dict sub-keys. Fase 07 decide:
  - Patrón A: hand-author paths para campos JSONB sub-keys
    (mantener validate_field_path _build_buyer_persona_paths como
    referencia).
  - Patrón B: extender walker con `dict_subkeys: dict[str, tuple[str,...]]`
    arg para declarar sub-keys conocidos (demographics.age_range, etc.).
- Recomendación: B — más sostenible. Sub-keys conocidos viven en
  `BUYER_SECTION_MAP` como entries explícitas; walker emite contracts
  con el path completo.
- Catalog `BUYER_PERSONA_EDITABLE_FIELDS` ya tiene 12 entries hand-authored
  (4 demographics + 3 psychographics + 3 journey + 2 identity).

### Closing commit hash

Last green commit Fase 06: `ed8a3a4f`. Close commit en 06.G.

---

## Fase 07 — Buyer-persona migration

**Status**: pending

---

## Fase 08 — Copilot unification

**Status**: pending

---

## Fase 09 — Multi-channel projection

**Status**: pending
