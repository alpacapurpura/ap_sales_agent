---
name: offer-expert
description: "Expert en arquitectura completa Offer Studio (post-refactor field-contract-platform). Cubre fields/secciones/expertise/presets/relaciones/descripciones. Habla lenguaje de negocio. Use cuando user pide modificar/agregar/fusionar/eliminar offers, expertise (ExpertBusinessType), presets, secciones, fields, descripciones, conditional questions, flags, variant structures, relaciones (upsell/downsell/lead-magnet), o quiere entender cómo Nicolify maneja offers a cualquier nivel. Triggers: 'modificar oferta', 'cambiar preset', 'fusionar offers', 'combinar expertise', 'nuevo tipo de negocio', 'cambiar descripción', 'agregar campo a oferta', 'sección nueva', 'lead magnet', 'upsell', 'downsell', 'archetype', 'value level', 'ladder', 'offer ladder', 'tipo de oferta', 'ofertas latam', 'expertise', 'qué le pregunto al cliente'."
---

# Offer Expert — Skill

## Modo conversación

User pide cambio offer → habla **español neutro LATAM**, tono experto negocio (microempresario LATAM), NO caveman. Caveman solo aplica al body de este SKILL.md (eficiencia tokens). Cuando dudes producto-side, **preguntá** antes de codear. Cuando dudes copy/descripción para microempresario, **buscá web 2026 best practices** según expertise (ej. "high-ticket coaching copy 2026", "lead magnet ecommerce 2026 LATAM").

## Mental model — 11 capas SSoT

```
L0  Pydantic Offer (offer/domain/offer.py)              estructural · qué se persiste
L1  FieldContract (shared/domain/field_contract.py)     semántico · cross-module
L2  SectionKey + SECTION_CATALOG (21 secciones)         agrupación UX
L3  OfferArchetype (5 internal)                         fulfillment model
L4  OfferFormat (composite per archetype × EBT)         refinamiento
L5  OfferValueLevel (5: lead_magnet/trial/core/premium/enterprise)  pricing tier
L6  OfferLadderHints (per EBT × ValueLevel)             ejemplo+precio típico
L7  OfferTypePreset (84 presets · facade archetype)     UX user-vocabulary
L8  ConditionalQuestion (7) + on_yes_sections/flags     preset refinement
L9  PresetFlag (6: SUPPORTS_CAPACITY, REQUIRES_START_DATE, DELIVERY_HYBRID, IS_LEAD_MAGNET, RECURRING_BILLING, HIGH_TICKET) downstream signal
L10 VariantStructure (4: PERIOD/SCOPE/TIER/PACK)        editions
L11 ExpertBusinessType (9 EBTs · vive en tenant_profile BC) target market
```

DAG completo en `.claude/rules/offer-catalogs.md`. Lectura obligatoria primer turno.

## Files canon SSoT

| Capa | File |
|---|---|
| L0 | `backend/src/modules/offer/domain/offer.py` (Offer aggregate root) |
| L0 | `backend/src/modules/offer/domain/details.py` (specific_details polymorphic) |
| L0 | `backend/src/modules/offer/domain/assets.py` (deliverables/instructors/etc) |
| L0 | `backend/src/modules/offer/domain/launch_edition.py` (variant editions) |
| L1 | `backend/src/modules/offer/domain/field_contract.py` (OFFER_SECTION_MAP + OFFER_FIELD_OVERRIDES + derive) |
| L1 | `shared/domain/field_contract.py` (platform: walker, override merge, registry) |
| L2 | `offer/domain/section_catalog.py` (SectionKey enum + SECTION_CATALOG dict) |
| L3 | `offer/domain/archetype_catalog.py` (5 archetypes + sections per archetype) |
| L4 | `offer/domain/format_catalog.py` (composite, suitable_for[EBT]=0..1) |
| L5 | `offer/domain/value_level_catalog.py` |
| L6 | `offer/domain/offer_ladder_hints.py` (tuple key (EBT, ValueLevel) → hint) |
| L7 | `offer/domain/offer_type_preset_catalog.py` (84 presets) |
| L7 | `offer/api/offer_type_presets.py` (`_CATALOG_VERSION`) |
| L8 | `QUESTION_REGISTRY` en preset_catalog.py top |
| L9 | `PresetFlag` enum en preset_catalog.py |
| L10 | `offer/domain/variant_structure_catalog.py` (pure base, no FK out) |
| L11 | `shared/domain/expert_business_type.py` (9 EBTs + metadata) |
| L11 | `shared/links/ports/tenant_profile.py` (`get_tenant_business_types`) — **NUNCA** importar `tenant_profile` directo |

## ExpertBusinessType (9 EBTs)

```
profesional_salud           consultorio salud, cita
consultor_profesional       servicio especializado B2B
coach_mentor                programas transformación 1:1 / grupo
academia_infoproductor      cursos / membresías / cohortes online
anfitrion_productor         eventos / experiencias presenciales
agencia_freelance           servicios productizados / proyectos
marca_ecommerce             productos físicos / digitales D2C
negocio_local               establecimiento físico
software_saas               producto suscripción + tiers
```

Multi-select. Tenants reales blendean 2-3.

## OfferArchetype (5 internal)

```
SERVICIO    one-shot delivery, custom scope
PROGRAMA    cohort/transformación, fechas + curriculum
MEMBRESIA   acceso recurrente, billing cycle
EXPERIENCIA evento puntual, fecha + lugar + capacity
PRODUCTO    bien/digital, una venta cierra ciclo
```

UX **NUNCA** muestra archetype. User ve preset.

## OfferValueLevel (5 niveles)

```
LEAD_MAGNET   gratis · email opt-in · lead capture
TRIPWIRE      < tenant-baseline · ramp warmer
CORE          oferta principal · revenue base
PREMIUM       > 3× core · alta conversión bajo volumen
ENTERPRISE    custom B2B · nego 1:1
```

`is_lead_magnet` derivado del value_level (NUNCA checkbox lateral).

## SectionKey (21 secciones post-consolidación 2026)

```
Universales (9):
  IDENTITY, STRATEGY, PSYCHOLOGY, PROMISE, VALUE_STACK,
  INSTRUCTORS, KNOWLEDGE, CLOSING, GALLERY

Archetype-specific (7):
  PRODUCT_DETAILS, SUBSCRIPTION_DETAILS, EVENT_DETAILS, PRICING,
  PROGRAM_DETAILS, SERVICE_DETAILS, RESOURCES

LATAM mass-market (5):
  FAQ, TESTIMONIALS, PORTFOLIO, LOCATION, PLATFORM_DETAILS
```

Eliminadas: `METHODOLOGY`, `CREDENTIALS` (duplicaban brand).

3 secciones referencian módulos externos:
- `LOCATION` → scheduling/event-types via `scheduling_event_type_id`
- `PRICING` → `accepted_payment_providers` via connections
- `INSTRUCTORS` → `brand-studio/team` via `instructors[]`

## SOPs por operación de negocio

### "Quiero crear/modificar/eliminar un preset"

→ Skill **offer-type-preset-expert** (peer skill). Usa esa para presets puros. Si trabaja también field-level, ambas. Pasos canon:
1. Decidir EBT + archetype (preset = facade del archetype).
2. Editar `OFFER_TYPE_PRESET_CATALOG` en `offer_type_preset_catalog.py`.
3. Bump `_CATALOG_VERSION` en `offer/api/offer_type_presets.py`.
4. Run arch tests (187+) en `tests/architecture/test_offer_type_preset_catalog_completeness.py`.
5. Update doc `docs/domains/offer/offer-type-preset-catalog.md`.
6. Review consumers: `sales_agent.knowledge_builder` + `landing_service._select_landing_archetype_from_preset` + `PresetBadge.tsx`.
7. **Copilot: zero-touch.** Preset_label/description leen del catalog en runtime via `shared/links/ports/offer.get_offer_type_preset(id)`. Catalog reactive.

### "Quiero combinar/fusionar 2 expertises"

Decisión PRODUCTO. Antes:
1. Identificar overlap real de presets entre los 2 EBTs (¿hay dup semántico?).
2. Si overlap >50% → considerar **eliminar uno** (consolidar tenants en otro). Migración riesgosa.
3. Si overlap <50% → mantener 2, agregar **conditional question** que bridges.

Si user persiste fusión:
- Drop EBT en `expert_business_type.py` enum + tests.
- Migrar presets del EBT eliminado: cambiar `business_type=` al EBT consolidador.
- Migrar tenants existentes con ese EBT en `tenant_profile.business_types` (script + Alembic data migration).
- Update `frontend/src/features/tenant-profile/types/tenant-profile.ts` (string-literal union mirror).
- Bump catalog version.

**Riesgo alto**: tenants con offers persisted en `preset_id` cuyo preset asume EBT viejo se quiebran. **Pregunta primero**: ¿hay tenants en prod con ese EBT?

### "Quiero crear un nuevo expertise (EBT)"

Cross-cutting. Sigue `.claude/rules/offer-catalogs.md` → "Extending the system". Pasos:
1. Add enum value + metadata en `expert_business_type.py`.
2. **Mínimo 3 presets** para nuevo EBT (arch test enforce).
3. Update `_BUSINESS_TYPE_SLUG` en preset completeness test.
4. Distribución table en `offer-type-preset-catalog.md`.
5. **FE mirror** `frontend/src/features/tenant-profile/types/tenant-profile.ts` (string-literal union + frozen array).
6. Update wizard preset picker filter (auto si registry agnóstico).
7. Considerá ladder hints: `offer_ladder_hints.py` — agregá entries `(NEW_EBT, value_level)` para cada nivel típico.

### "Quiero eliminar un expertise"

Pregunta primero: tenants en prod con ese EBT? Si sí, **NO** elimines:
- Marca DEPRECATED (no existe enum-level deprecation; usa flag en metadata + arch test allowlist).
- Plan migración con UI banner "Tu expertise cambia a X — confirmá".
- Window de deprecación (sprint dedicado).

Si zero tenants: drop enum, drop presets de ese EBT, drop tests. Bump catalog version.

### "Quiero modificar/agregar un field a una sección"

Workflow refactor field-contract-platform:
1. Decidir si Pydantic model nuevo / extender existente. Files: `offer/domain/offer.py`, `details.py`, `assets.py`, `launch_edition.py`.
2. Agregar field a Pydantic model (estructura).
3. **Add path → section** en `OFFER_SECTION_MAP` (`offer/domain/field_contract.py`).
4. **Add Override** en `OFFER_FIELD_OVERRIDES` con metadata semántica:
   ```python
   "specific_details.<field>": Override(
       priority=80,
       is_required_semantic=True,
       human_question_es="¿…?",          # copilot conversacional
       expects="hint formato",            # opcional
       gate="specific_details.archetype", # opcional precondición
       label_es="Etiqueta",               # FE label
       archetype_filter=("PRODUCTO",),    # si specific
   ),
   ```
5. Migration Alembic idempotente (`ADD COLUMN IF NOT EXISTS`) si Pydantic field se persiste como column. Si vive en JSONB (specific_details, platform_details), zero migration.
6. Run arch tests `tests/architecture/test_field_contract_platform.py` + `tests/architecture/test_field_contract_completeness.py`. Pydantic ⊆ FieldContract enforced.
7. **FE schema** (`frontend/src/features/offer-studio/schemas/<section>.schema.ts`) — agregar field declaración Zod. Schema FE NO se deriva auto; debe alinearse manual.
8. **Copilot: zero-touch** si solo agregás. `propose_field_updates` valida con catalog derivado, picks up auto. `next_question` algoritmo Fase 09 ranking deja entrar el field auto. Si gate / priority te interesa = setealo en Override.
9. Documentar en `docs/domains/offer/`.

### "Quiero crear nueva sección"

1. Add `SectionKey.X` enum value + entry en `SECTION_CATALOG` con `label_es`/`subtitle_es`/`help_text_es`/`icon_name`/`scope`/`kind`.
2. Decidir `scope`: OFFER_LEVEL / EDITION_LEVEL / MIXED.
3. Decidir `kind`: SINGLETON / COLLECTION (collection requiere landing + detail FE views).
4. Asignar fields al section via `OFFER_SECTION_MAP` (paths → SectionKey.X.value).
5. Update `archetype_catalog.py` per archetype: ¿qué archetypes incluyen esta sección?
6. Update `offer_type_preset_catalog.py` `base_sections` o conditional question on_yes.
7. **FE schema file** `<section-slug>.schema.ts` + register en `SECTION_REGISTRY`.
8. Arch tests + `_CATALOG_VERSION` bump.
9. Copilot: lee del catalog + FieldContract auto.

### "Quiero eliminar una sección"

Antes:
- ¿Tenants tienen data en fields de esa sección? Query `SELECT COUNT(*) FROM products WHERE <field> IS NOT NULL`.
- Si sí, **NO** eliminar — DEPRECAR (`status=DEPRECATED` en field overrides → consumers filtran auto).
- Si zero data: drop SectionKey + archetype_catalog references + preset base_sections refs + FE schema + tests.

### "Quiero cambiar descripciones (label_es / description_es / human_question_es / help_text_es)"

User dice "no se entiende" / "muy técnico" / "querés que pregunte distinto":
1. **Pregunta tenant target**: ¿qué EBT? (lenguaje varía: SAUL técnico vs LOCAL coloquial).
2. **Web search 2026 best practices** según contexto:
   - Lead magnet copy: "lead magnet copy 2026 LATAM SMB"
   - High-ticket: "high-ticket coaching offer description 2026"
   - Lead-gen B2B: "B2B service offer copy 2026 LATAM"
   - Membership: "subscription copy 2026 microempresario"
3. Apply Spanish neutro LATAM (`.claude/rules/spanish-text.md`) — sin voseo. `tú`, no `vos`.
4. Para `human_question_es`: pregunta natural conversational (Fase 09). Ej. "¿Cuál es la promesa principal de esta oferta?" (no "Promesa principal: …").
5. Edit en Override del field/section/preset.
6. Bump `_CATALOG_VERSION` si tocaste preset o section.
7. **Copilot: cambio reactive vía catalog**. Pero baseline tests (`test_offer_editable_fields_baseline.py`, `test_buyer_persona_editable_fields_baseline.py`) usan descripciones — actualizar baseline si descripcion cambia (intentional).

### "Quiero crear relaciones entre offers (upsell/downsell/lead-magnet)"

Modelo persistido:
- `Offer.upsell_product_id: UUID | None`
- `Offer.downsell_product_id: UUID | None`
- `Offer.includes_offers: list[UUID]` (bundle/pack)

Para LEAD_MAGNET → CORE relation:
- Setear `value_level=LEAD_MAGNET` en lead magnet offer.
- Setear `upsell_product_id=<lead_magnet_offer.id>` en core offer.

API: `POST /api/v1/offer/products/{id}` + payload incluye estos UUID. No hay tabla join — son foreign keys directos.

Cambios sugeridos al user:
- "¿Querés bundle (1 offer contiene N) o linked (recommendation)?"
- Bundle = `includes_offers`.
- Linked = `upsell_product_id` / `downsell_product_id`.
- Sales-agent + landing leen ambos vía Pydantic aggregate.

### "Quiero fusionar 2 offers"

Decisión PRODUCTO:
1. Identificar source-of-truth offer (la que sobrevive).
2. Migrar referencias (`upsell_product_id`, `downsell_product_id`, `includes_offers`) que apuntan a la otra.
3. Soft-delete la fusionada (`deleted_at = now()`).
4. Update `landing.offer_id` references si aplica.
5. Notificar tenant (UX banner "Tu oferta X se fusionó con Y").

NO existe API "merge offers" — operación manual via DB ad hoc o script. Si user pide repetir → considerar build feature.

### "Quiero agregar nueva conditional question / flag"

Question:
- Agrega ≥3 presets afectados antes (regla D28).
- Add a `QUESTION_REGISTRY` en `offer_type_preset_catalog.py`.
- Define `on_yes_sections` (additive only) / `on_yes_flags`.
- Register `conditional_question_ids=("new_q",)` en presets aplicables.

Flag:
- Add a `PresetFlag` enum.
- **Wire downstream consumer** (landing template branch / sales-agent prompt / analytics). Sin consumer = dead flag = arch rot.

Bump version + tests.

### "Quiero nueva variant structure"

`offer/domain/variant_structure_catalog.py` es **pure base** (zero outbound FK refs — arch test bloquea). 4 estructuras hoy: PERIOD (cohorts fechadas) / SCOPE (alcance customizable) / TIER (basic/pro/premium) / PACK (cantidades).

Agregar:
1. New enum value + metadata.
2. Update `OfferArchetype.supported_structures` mapping.
3. Update FE editor variant CRUD si la nueva structure tiene UX nueva.

## Cosas que DEBE inform al copilot

| Cambio | Copilot acción | Porqué |
|---|---|---|
| Nuevo field en Pydantic + Override | **zero-touch** | Catalog derivado de FieldContract — auto pick-up |
| Cambio `human_question_es` | **zero-touch** | `next_question` lee runtime del registry |
| Cambio `gate` / `priority` | **zero-touch** | Algoritmo lee runtime |
| Cambio `can_propose=False` | **zero-touch** | `propose_field_updates` filtra auto |
| Nuevo SectionKey | **zero-touch** | section_catalog reactive |
| Nuevo preset / question / flag | **zero-touch** + bump `_CATALOG_VERSION` | Cliente cache version-keyed |
| Drop section / field DEPRECATED | **zero-touch** | Status filter en projection auto |
| **Nuevo PresetFlag con consumer landing/sales-agent nuevo** | Add explicit branch en consumer | Flag ≠ silencioso si downstream depende |
| **Nuevo EBT** | FE mirror update obligatorio | Sin mirror, onboarding picker oculta |
| **Cambio descripción que rompe baseline tests** | Update baseline test | Intencional, debe mostrarse en commit msg |

**Resumen**: arquitectura post-Fase-09 hace que la mayoría de cambios sean **reactive auto** — copilot lee registry runtime. Solo bloqueantes manuales: nuevos PresetFlags con consumer, nuevos EBTs (FE mirror), baseline test updates.

## Limitantes arquitectónicas (no romper)

- ❌ Nunca importar otra layer cross-module excepto via `shared/links/ports/offer.py`. DDD arch test falla.
- ❌ Nunca surface `OfferArchetype` labels en wizard UX (es internal).
- ❌ Nunca duplicar metadata FE — consume hooks/catalog API. Si necesitás algo nuevo, va al `Override`.
- ❌ Nunca `lead_magnet=True` checkbox separado — derivar de `value_level == LEAD_MAGNET`.
- ❌ Nunca `_GROUP_MAP` hardcoded en FE (channel-display etc.) — consume `useFormatCatalog`/`useArchetypeCapabilities`/`useValueLevelCatalog`.
- ❌ Nunca hardcodear `business_types` en BrandIdentity. Vive en `tenant_profile` BC desde 2026-04-20.
- ❌ Nunca crear field nuevo sin entry en `OFFER_SECTION_MAP` — arch test cross-cutting `Pydantic ⊆ FieldContract` falla.
- ❌ Nunca dropear field sin DEPRECATED transition. Persisted data se orfana.
- ❌ Nunca preset con `archetype` que no existe en `ARCHETYPE_CATALOG`.
- ❌ Nunca question con on_yes que **remueve** sección — additive only (D28).
- ❌ Nunca PresetFlag sin consumer downstream (dead flag).
- ❌ Nunca editar baseline test silently — commit msg explica el motivo.

## Tests gates (correr siempre tras cambio)

```bash
cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short
cd backend && .venv/bin/pytest tests/architecture/test_offer_type_preset_catalog_completeness.py -x -q
cd backend && .venv/bin/pytest tests/modules/copilot/test_conversational_questioning.py tests/modules/copilot/test_guided_question_hint.py -x -q
cd frontend && npx vitest run src/__tests__/architecture/
```

507 BE arch + 38 FE arch baseline post-Fase-09. Sin regression.

## Cuando dudar, **preguntar** al user

Antes de codear, si:
- Cambio toca persisted data → **¿hay tenants en prod con esto?**
- Descripción → **¿qué EBT target? ¿lenguaje técnico o coloquial? ¿precio del cliente final?**
- Fusión / drop → **¿hay backward compat? ¿deprecation window?**
- Nuevo concepto cross-layer → **¿lo mapeás a algo existente?**
- Refactor cross-module → **¿lo separamos en sub-tareas?**

## Pattern conversacional (cuando skill se invoca)

1. Lee user request en lenguaje negocio.
2. Mapeá a layer(s) afectada(s) (L0..L11).
3. Confirmá con user el mapping ("Querés tocar capa X — voy a Y. ¿OK?").
4. Web search si descripción/copy.
5. Implementá siguiendo SOP arriba.
6. Run tests gates.
7. Reportá: archivos tocados + version bump + baseline updates + copilot impact.

## Docs anchor

- `docs/domains/offer/INDEX.md` (todos los docs offer)
- `docs/domains/offer/catalogs-consolidation.md` (5 axes base)
- `docs/domains/offer/offer-type-preset-catalog.md` (preset layer)
- `docs/domains/offer/variant-structure-catalog.md` (variants)
- `docs/refactors/field-contract-platform/DESIGN.md` (FieldContract platform — Fase 04-09)
- `docs/refactors/field-contract-platform/LEARNINGS.md` (descubrimientos cross-fase)
- `.claude/rules/offer-catalogs.md` (DAG rules)
- `.claude/rules/spanish-text.md` (neutro LATAM sin voseo)
- `.claude/rules/tdd-mandatory.md` (test antes impl)

## Peer skill

- `offer-type-preset-expert` — narrow scope sobre L7 preset catalog. Si user solo agrega/modifica preset → invocá ese. Si user mezcla layers (preset + field + section) → este skill maneja toda la cascada.
