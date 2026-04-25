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

**Status**: done (2026-04-24)

### Pre-fase expectations vs realidad

- ✅ Buyer-persona FieldContract registry derivado completo (18 contracts,
  12 proposable) — mantiene byte-identical el catálogo pre-fase de 12
  entries.
- ✅ Walker shared extendido con `dict_subkeys` arg (Patrón B) — habilita
  cualquier futuro módulo con JSONB sub-keys sin duplicar boilerplate.
- ✅ BUYER_PERSONA_EDITABLE_FIELDS proyectado del registry — drop tuples
  manuales _IDENTITY/_DEMOGRAPHICS/_PSYCHOGRAPHICS/_JOURNEY.
- ✅ UX byte-identical: 12/12 paths preservados, 12/12 labels intactos,
  12/12 descriptions intactos, 12/12 sections intactos. 6 tests
  baseline GREEN pre y post.
- ✅ MIGRATED_MODULES = ("offer", "brand", "buyer_persona"). Generic
  fitness gates (template) corren para 3 módulos sin cambios — pattern
  Fase 04.I confirmado por tercera vez.
- ✅ Coordinación con `project_brand_studio_refactor` confirmada cero
  overlap (Sprint 6.E es FE offer-studio).

### Resultados cuantitativos

| Métrica | Pre-Fase 07 | Post-Fase 07 |
|---|---|---|
| Buyer-persona catalog entries | 12 (manual) | 12 (proyectado) |
| BUYER_PERSONA_FIELD_CONTRACTS | n/a | 18 derivados |
| Drift Pydantic ↔ catalog | latente (catalog manual) | cero (proyección) |
| Manual hand-written tuples buyer | 4 (_IDENTITY/_DEMOGRAPHICS/...) | 0 |
| Tests arch totales | 471 | 491 (+20: 6 baseline + 6 dict_subkeys + 5 cross-cutting + 3 generic-template) |
| Tests totales backend | 4261 | 4286 |
| Tests shared platform unit | 17 | 23 (+6 dict_subkeys) |
| MIGRATED_MODULES | `("offer", "brand")` | `("offer", "brand", "buyer_persona")` |

### Descubrimientos

- (07.A) `_build_buyer_persona_paths` (validator) declara 24 paths,
  catalog declara 12, FE schema declara 16. La intersección de los 3
  fue la fuente canónica para SECTION_MAP. Validator legacy se
  reemplazará en Fase 08.
- (07.A) Drifts catalogados:
  - `demographics.income` (catalog/FE) vs `demographics.income_range`
    (validator). Canónico = `income` (FE-driven).
  - `psychographics.aspirations` (catalog/FE) ausente del validator
    dotted set. Validator tiene beliefs/personality_traits/
    media_consumption no en catalog.
  - List fields (`pain_points`/`desires`/`objections`/
    `preferred_channels`) en FE+Pydantic pero NO en catalog (decisión
    UX preservada): `can_propose=False`.
  - List[str] (`purchase_triggers`/`anti_patterns`) en Pydantic pero
    sin UX surface hoy: `can_propose=False`.

- (07.B) Patrón B walker dict_subkeys validó la decisión de Fase 06
  LEARNINGS. Implementación: 15 LOC en shared (`_walk_dict_subkeys` +
  arg + 1-line dispatch). Tests platform unit (+6) cubren: emisión por
  sub-key, parent skip, default TEXT type, override merge, drop sin
  section_map, default-None preserva DICT bare. Reutilizable: cualquier
  módulo futuro con JSONB declara `dict_subkeys={"<field>": (sub_keys)}`
  sin tocar shared.

- (07.B) Sub-keys sin entry en `section_map` se dropean silencioso
  (consistente con top-level fields). Coverage gate en 07.E
  (`test_buyer_persona_dict_subkeys_have_section_map_entry`) hace
  visible este caso para evitar drops invisibles.

- (07.C) BuyerPersona vive bajo `brand/domain/` (aggregate co-resides
  con brand) pero registra bajo module key `"buyer_persona"` —
  consistente con port editable_fields, schema_introspection,
  extraction_domain_registry. No requiere módulo BE separado. Path
  archivo: `brand/domain/buyer_persona_field_contract.py`.

- (07.C) Sections inline (no `buyer_persona_section_catalog.py`):
  identity (2), demographics (4), psychographics (3), journey (3),
  pain_points/desires/objections/channels/triggers/anti_patterns
  (6 lists). 10 sections totales — cuando Fase 09+ unifique
  section_catalog cross-module, alinear.

- (07.D) Mismo pattern brand 06.D para projection: `_to_field_spec(c)`
  con `label = c.label_es or _humanize(c.path)` + `description =
  c.human_question_es or c.notes`. Para JSONB sub-keys (sin Pydantic
  description) las notes vienen del override.

- (07.E) `_buyer_persona_spec()` con `composable_handles =
  frozenset(BUYER_PERSONA_DICT_SUBKEYS.keys())`. Las 3 dict parents
  actúan exactamente igual que offer's `specific_details` /
  `platform_details`: el bare name no aparece en el registry, las
  sub-keys sí.

- (07.F) Anti-regression test mirror de 06.F. Catch incluye chequeo
  de que el archivo importa `BUYER_PERSONA_FIELD_CONTRACTS` (proof of
  projection) + ratchet `FieldSpec(` calls ≤ 1.

### Decisiones nuevas

Ninguna ADR formal. La decisión `dict_subkeys` walker arg estaba
pre-aprobada en LEARNINGS Fase 06 §Para Fase 07 (Patrón B) — solo
implementación.

### Deuda técnica encontrada (en scope, resuelta)

- ✅ Drift `demographics.income` vs `income_range`: canónico `income`
  per FE schema, contract no expone `income_range` (validator legacy
  lo aceptaba via prefix match — irrelevante post-Fase 08).
- ✅ Anti-regression test (07.F) previene re-introducción de manual
  tuples.
- ✅ List fields can_propose=False documentado en overrides (form-runtime
  CRUD UX preservado).

### Deuda técnica (tangencial — entry en `docs/mejoras-proceso/to-do.md`)

- `_build_buyer_persona_paths` en `copilot/domain/schema_introspection.py`
  sigue manteniendo set hand-authored de paths. Convertirlo a
  derivación de `get_module_contracts("buyer_persona")` es scope
  Fase 08 (copilot unification). Hoy convive con el contract sin
  conflicto.
- `pain_points.emotional_impact` y `desires.urgency` (sub-keys de
  list[dict] items) viven en `_build_buyer_persona_paths` pero no en
  el contract. No son JSONB-dict-parent → no aplica `dict_subkeys`
  arg. Walker extension separado para list[dict] item sub-keys queda
  diferida si aparece demanda real.
- `BuyerPersonaPersister` accepted paths abierto via prefix matching
  de dict parents. Después de Fase 08 (cuando validator consuma
  contract) el persister puede strict-validate path ∈ contract.

### Para Fase 08

- Copilot unification scope: `editable_fields` port + `schema_introspection`
  consumen `get_module_contracts(domain)` directo. 3 módulos migrados
  (offer/brand/buyer_persona) listos.
- Pre-investigación obligatoria: inventario call sites de `get_catalog`,
  `validate_field_path`, `is_editable_path`, `get_model_sections`.
  Tests acceptance copilot existentes deben pasar idéntico.
- Riesgo medio-alto — copilot en producción. Tests acceptance
  exhaustivos requeridos antes de tocar nada.
- `PERSISTABLE_FIELDS` (offer) ya derivada — evaluar si
  `copilot/domain/offer_fields.py` archivo sigue necesitándose o se
  promociona consumer a leer `get_module_contracts("offer")` directo.

### Closing commit hash

Last green commit Fase 07: `e4714606`. Close commit en 07.G.

---

## Fase 08 — Copilot unification

**Status**: done (2026-04-24)

### Pre-fase expectations vs realidad

- ✅ `editable_fields` port deriva de `get_module_contracts(domain)` con
  filtros `can_propose=True` + `status=ACTIVE` + dedupe por path. Default
  behavior; `register_catalog` retenido para test stubs.
- ✅ Drop de 3 archivos `copilot_editable_fields*.py` (offer/brand/
  buyer_persona) — boilerplate idéntico que ahora vive 1 vez en el port
  como `_derive_from_contracts`.
- ✅ `schema_introspection._build_*_paths` derivan: brand consume
  contracts + sections (preserva validate_field_path("brand", "identity")
  bare section), offer consume contracts directo (drop indirección
  PERSISTABLE_FIELDS), buyer_persona consume contracts (drop hand-authored
  set de 24 paths).
- ✅ `_DOMAIN_DICT_PARENTS["buyer_persona"]` derivado de
  `BUYER_PERSONA_DICT_SUBKEYS.keys()` via `_get_dict_parents()` lazy
  getter. Mantiene API privada para field_paths_hint consumer.
- ✅ UX byte-identical: 52/52 acceptance copilot tests pre/post idéntico.
  propose_field_updates valida con la misma surface; extract_structured
  también; field_paths_hint produce same markdown.
- ✅ 3 arch tests anti-regression: derivation projection check +
  no_catalog_projection_files + no hand-authored paths AST scan.
- ✅ `offer_fields.py` mantenido como alias documentado (decisión
  PRE_INVESTIGATION §5: 4 consumers + critical-path persister, drop
  introduce riesgo > beneficio en Fase 08; schema_introspection ya no
  consume PERSISTABLE_FIELDS, otra deuda menos).

### Resultados cuantitativos

| Métrica | Pre-Fase 08 | Post-Fase 08 |
|---|---|---|
| Catalog projection files (boilerplate) | 3 (offer + brand + buyer_persona) | 0 |
| Líneas de código (catalog projections) | ~270 (90 LOC × 3 archivos) | 0 |
| `_DOMAIN_BUILDERS` fuente | mixto (3 backends) | 1 (FieldContract registry) |
| Tests arch totales | 491 (post 07.G) → 490 (medido baseline) | 507 |
| Tests arch nuevos en 08 | n/a | +25 derivation/anti-regression |
| Tests arch dropped en 08 | n/a | -8 (2 catalog_projection files × 4 tests) |
| Tests copilot acceptance | 52 | 52 (byte-identical) |
| Tests copilot total | 695 | 695 |
| SSoT paths cross-module | 5+ (port catalog + 3 module files + offer_fields + schema_introspection sets) | 1 (FieldContract registry) |

### Descubrimientos

- (08.A) PRE_INVESTIGATION reveló que los 3 catalog files
  `copilot_editable_fields*.py` eran **literalmente idénticos** modulo
  el dedupe que offer agregaba (polymorphic). Refactor obvio: un solo
  helper en el port.

- (08.B) Drop de los 3 catalog files rompió 5 arch tests por imports
  rotos. Refactor / drop:
  - `test_brand_editable_fields_baseline.py`: import via `get_catalog("brand")`.
  - `test_buyer_persona_editable_fields_baseline.py`: idem.
  - `test_field_contract_platform_coverage.py`: usa `get_catalog("offer")`.
  - `test_brand_catalog_projection.py`: DROP — funcionalidad folded
    en 08.D test_editable_fields_derivation (proyección por construcción).
  - `test_buyer_persona_catalog_projection.py`: DROP idem.

- (08.C) `_build_brand_paths` derivado necesita union `paths | sections`.
  Sin la union, `validate_field_path("brand", "identity")` retornaría
  False — rompiendo 5 assertions en `test_extract_validation.py`.
  Solución: `paths = {c.path for c in contracts} | {c.section for c in contracts}`.

- (08.C) `_DOMAIN_DICT_PARENTS` consumer privado en
  `field_paths_hint.py:24`. Cambiar la inicialización de eager a lazy
  rompería el consumer (returns None en first call). Solución:
  `_get_dict_parents(domain)` lazy getter + cache; field_paths_hint
  migrado a usar el getter (drop import directo del private dict).

- (08.C) Brand contract surface tiene tanto OBJECT contracts (sub-objects
  con can_propose=False, paths como "identity", "story") como nested
  paths ("identity.brand_name"). Para validate_field_path("brand", "identity")
  bastaría incluir solo OBJECT paths del registry, pero el path
  "identity" en el OBJECT contract tiene section=identity (proper),
  por lo que la union `paths | sections` es equivalente y más robusta.

- (08.C) `validate_field_path("buyer_persona", "demographics.income_range")`
  (legacy, NO en contract) sigue True via prefix match: parent
  "demographics" es dict_parent. Comportamiento legacy preservado por
  diseño — la prefix match acepta sub-keys nuevos sin code change
  (ver schema_introspection docstring).

- (08.D) AST scan para detectar set literals con >5 strings es robusto:
  el viejo `top_level = {"name", "tagline", "pain_points", ...}` (8
  strings) quedaba con 8 entries; el nuevo derivation es 1 set comp.
  Threshold 5 da margen sin falsos positivos.

### Decisiones nuevas

Ninguna ADR formal. Decisiones de scope reduction documentadas in-line:

- Mantener `offer_fields.py` como alias (decisión PRE_INVESTIGATION §5).
  4 consumers críticos (incluso offer_persister) — drop introduce
  cambios en código de persistencia con riesgo > beneficio.
- `register_catalog` API mantenida (test stubs, custom catalogs futuros).
  Default es derivación pero override sigue posible.
- `_get_dict_parents()` lazy getter en lugar de eager population de
  `_DOMAIN_DICT_PARENTS`. Mantiene contrato lazy del módulo + private
  consumer field_paths_hint.

### Deuda técnica encontrada (en scope, resuelta)

- ✅ Drift potencial entre 3 catalog projection files paralelos cerrado
  por construcción (port deriva).
- ✅ Drift potencial entre `validate_field_path` (schema_introspection
  hand-authored) y FieldContract registry cerrado (builders derivan).
- ✅ Anti-regression tests previenen re-introducción de catalog files
  (test_no_catalog_projection_files) o hand-authored sets
  (test_schema_introspection_derives_from_registry).

### Deuda técnica (tangencial — entry en `docs/mejoras-proceso/to-do.md`)

- `offer_fields.py` mantenido como alias de PERSISTABLE_FIELDS. 38 LOC
  triviales. Drop futuro requiere migrar offer_persister a
  `get_module_contracts("offer")` directo + golden snapshot tests más
  amplios. Diferido — no bloqueante.
- `get_model_sections(model_class)` opera 1:1 sobre Pydantic. 6+
  consumers (admin tenant_health, awareness, module_tools, procedures,
  graph snapshot, nudge api). Migración al FieldContract requiere que
  el contract incluya rich Pydantic-equivalent metadata (sub_fields,
  field_descriptions). Out of scope Fase 08 — Fase 09+ cuando Fase 9
  necesite contract-driven section views.
- Diferidos Fase 05 (LEARNINGS Fase 05): data-driven loop full,
  completion alignment, landing aggregate migration. Siguen pendientes.
  Fase 09 puede evaluarlos en sub-fase dedicada.

### Para Fase 09

- Multi-channel projection (whatsapp/telegram conversational copilot).
  PRE_INVESTIGATION debe inventariar:
  - Estado actual del copilot conversacional cross-channel.
  - Channel adapters (si ya existen) y cómo bind tools.
  - Trade-off determinístico vs LLM-driven question selection.
  - Compat web ↔ chat: form-runtime web sigue idéntico.
- Diferidos posibles a tomar en una sub-fase de Fase 09:
  - Full data-driven `agent_identity.j2` loop (LEARNINGS Fase 05).
  - Completion ↔ contract semantic alignment (LEARNINGS Fase 05).
  - Landing aggregate migration (LEARNINGS Fase 05).
  - Walker extension para list[dict] item sub-keys (LEARNINGS Fase 07).

### Closing commit hash

Last green commit Fase 08: `e1f44284`. Close commit en 08.F.

---

## Fase 09 — Multi-channel projection

**Status**: done (2026-04-24)

### Pre-fase expectations vs realidad

- ✅ Algoritmo `next_question(module, state, section=None)` channel-agnostic
  pure-function implementado en
  `copilot/application/orchestrator/conversational_questioning.py`. 40
  unit tests cubren todas las selection rules.
- ✅ `build_question_hint` helper proyecta hint dict ui_action-ready
  con precedence `human_question_es → label_es → humanize(path)` (9 unit
  tests).
- ✅ Web integration: `advance_guided_block` enriches payload con
  optional `suggested_question` via `read_entity_state` (best-effort)
  + `build_question_hint`. Backward compat preservada — flow legacy
  sin cambios cuando hint no se puede computar (7 unit tests).
- ✅ `ConversationalChannelPort` abstract en `shared/links/ports/`.
  `InMemoryConversationalChannel` impl en
  `copilot/infrastructure/channels/`. 6 unit tests cubren contract
  abstract + ordering + context + clear.
- ✅ E2E channel-agnostic: 6 tests verifican loop `next_question →
  ask → state update → next_question` y assert misma secuencia
  cross-adapters (channel-agnostic invariant).
- ✅ `human_question_es` enrichment: brand 12 fields (was 0), buyer 12
  fields (was 0), offer mantenido en 25 (no nuevos requeridos). Total
  ≥30 enriched cross-module. Spanish neutro LATAM (sin voseo).
- ✅ Wiring real copilot↔whatsapp/telegram OUT of scope per SPEC —
  deferred a sprint product-level. Algoritmo + port + adapter pattern
  listos para drop-in cuando exista.

### Resultados cuantitativos

| Métrica | Pre-Fase 09 | Post-Fase 09 |
|---|---|---|
| `next_question` channel-agnostic algorithm | inexistente | 1 (pure function) |
| Channel adapter port | inexistente | 1 (`ConversationalChannelPort`) |
| Channel adapter impls | 0 | 1 (`InMemoryConversationalChannel`) |
| Unit tests Fase 09 | 0 | 61 (40 algorithm + 9 helper + 7 advance + 6 channel + 6 E2E + 4 isolation overhead) |
| `human_question_es` populated brand | 0/113 | 12/113 |
| `human_question_es` populated buyer | 0/18 | 12/18 |
| `human_question_es` populated offer | 25/153 | 25/153 (sin nuevos en este sprint) |
| Tests arch totales | 507 | 507 (sin nuevos arch tests Fase 09) |
| Tests copilot | 695 | 760 (+65 net Fase 09) |

### Descubrimientos

- (09.A PRE_INVESTIGATION) Channel infra ya existe en `connections/` —
  Whatsapp, Telegram, Instagram adapters + `MessageHandlerPort`. Pero
  el `MessageHandlerPort` despacha SOLO al `sales_agent` (vende a
  leads). El **copilot** (asiste al tenant owner) NO está conectado
  a canales. Wire-up real copilot↔chat = sprint dedicado, fuera scope
  de Fase 09.
- (09.A) Block-level question selection ya existía (Fase pre-existing)
  en `copilot/application/guided/block_generator.py`. Fase 09 agrega
  granularidad **field-level** ortogonal — el bloque sigue
  navegándose, dentro del bloque `next_question` selecciona el field
  candidate.
- (09.A) `FieldContract.human_question_es` populated solo en offer
  (25/153). Brand 0/113, buyer 0/18. Sub-fase 09.F enriquece top
  required cross-module.
- (09.B) Diseño híbrido determinístico-asistido confirmed: algoritmo
  selecciona candidate field, adapter (web/chat/voz) decide cómo
  presentarlo (LLM puede reformular usando `human_question_es` como
  seed). Algoritmo puro = trivialmente testeable + reproducible.
- (09.B) `_is_missing` debate: false/0 NO son missing. Solo None /
  blank-string / empty-container. Razón: una bool field con `False`
  es respuesta válida; una numeric con `0` también. Tests cubren
  ambos casos para evitar regresión.
- (09.B) Required-first ordering: candidates con
  `is_required_semantic=True` ganan sobre opcionales. Razón: copilot
  prioriza completar el setup mínimo viable antes de pedir nice-to-haves.
  Tie-break por `(section, -priority, path)` — alfabético sobre
  section, priority alta gana, lex sobre path para reproducibilidad.
- (09.C) State reading necesita per-domain: brand singleton via
  `BrandRepository.get_settings`, offer/buyer entity via UUID.
  Best-effort (catches all exceptions → None) — guided flow nunca
  rompe por no poder computar hint.
- (09.D) `ConversationalChannelPort` minimal: 1 método abstract `ask`.
  Cualquier extra state (lead_id, conversation_id, locale) flows via
  optional `context: dict` — keeps port stable cross adapters.
- (09.E) Channel-agnostic invariant probado: 2 InMemory adapters
  emiten misma secuencia para mismo state. Real assertions cubren
  required-first + gate satisfaction + deprecated/readonly excluded
  + termination.
- (09.F) Updating `BUYER_PERSONA_CATALOG_BASELINE` descriptions tras
  agregar `human_question_es` es **intencional**, no regression. Catalog
  projection usa `description = human_question_es or notes` (Fase 08
  helper). Fase 09 mejora copilot system prompt enumeration con
  natural-Spanish prompts. Documentado en commit message + LEARNINGS.
- (09.fix) Synthetic FieldContract registries en tests pollutaban
  `_MODULE_CONTRACTS` global. `test_no_cross_domain_duplicates`
  iteraba todos los modules registered y veía `name` colisión entre
  `_synthetic_e2e` y `buyer_persona`. Fix: `teardown_module` clears
  synthetic module post-test (`register_module_contracts(_MODULE, ())`).
  Patrón ahora documentado en synthetic test files.

### Decisiones nuevas

Ninguna ADR formal. Decisiones de scope reduction documentadas
in-line:

- Wiring real copilot ↔ whatsapp/telegram **out of scope** — requiere
  copilot orchestrator channel-aware + tenant-owner identity en
  webhook. Sprint product-level dedicado. Fase 09 entrega algoritmo
  + adapter pattern listos.
- `redo_if_changes` invalidation **out of scope** — documentado en
  contract pero state manager que lo honra es futura ADR.
- LLM-driven question reformulation **out of scope** del algoritmo —
  caller adapter puede agregar reformulación, pero no es parte de
  `next_question`.
- Diferidos Fase 05/07 NO tomados este sprint per SPEC: full
  data-driven `agent_identity.j2`, completion alignment, landing
  aggregate migration, walker list[dict] item sub-keys.

### Deuda técnica encontrada (en scope, resuelta)

- ✅ `human_question_es` populated en brand + buyer top required
  fields (12 + 12).
- ✅ Cross-domain test pollution prevenida via teardown_module patrón.

### Deuda técnica (tangencial — entry en `docs/mejoras-proceso/to-do.md`)

- `test_streaming_integration.py::test_tool_call_produces_tool_events`
  sigue flaky (passes isolated, fails en suites largas con
  side-effects). Pre-existing, documented Fase 04.
- `human_question_es` enrichment puede continuar — solo cubrimos top
  required this sprint. Optional fields cross-module (story.values,
  visuals.secondary_color, etc.) sin populated. Future enrichment
  sprints conforme demanda real.
- `expects` field hint type/format populated parcialmente. Más
  enrichment posible.

### Para próxima fase / cierre del refactor

**Refactor field-contract-platform CIERRA con Fase 09.** Plan original
6 fases (04-09) completado:

| Fase | Status | Closing commit |
|---|---|---|
| 04 — Platform foundation | done | `c8ddd79e` |
| 05 — Downstream data-driven | done | `d0d121f1` |
| 06 — Brand migration | done | `bd7bfd31` |
| 07 — Buyer-persona migration | done | `1f210a5d` |
| 08 — Copilot unification | done | `e1f44284` |
| 09 — Multi-channel projection | done | `f866cd17` (close commit pendiente) |

3 módulos migrados al FieldContract platform (offer + brand + buyer).
Copilot read+write surfaces unificadas. Algoritmo conversational
data-driven channel-agnostic. Channel adapter port para futuro
wire-up real.

Posible Fase 10 (futuro, fuera scope este refactor):
- Wire copilot↔whatsapp/telegram real (separado del refactor —
  product sprint).
- Fase 05 deferrals: data-driven agent_identity.j2 loop completo,
  completion alignment, landing aggregate migration.
- Walker extension list[dict] item sub-keys.
- More `human_question_es` enrichment cross-module conforme demand.

### Closing commit hash

Last green commit Fase 09: `f866cd17` (test isolation fix). Close
commit en 09.G.
