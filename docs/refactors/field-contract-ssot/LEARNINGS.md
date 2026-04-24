# Aprendizajes acumulados

Append-only. Cada fase suma entries. Cross-cutting arriba. Per-fase abajo.

---

## Cross-cutting (aplica a todo Nicolify)

- **Pydantic default `extra="ignore"` es silent data loss trap.** `BaseEntity` config en `shared/domain/base_entity.py` no declara `extra=`. Post-refactor considerar `forbid` con arch test que permite solo legacy via migration `metadata_info`.

- **Schemas FE sin enforcement de paths contra BE domain = drift garantizado.** Capa A (9 paths huérfanos) fue consecuencia predecible. Arch test desde Fase 0 lo impide a futuro.

- **`OFFER_FIELDS_BY_FE_SECTION` es mapeo parcial que nadie tiene incentivo a completar.** Dict paralelo al FE schema. Solución de fondo = derivación de contrato, no completar lista manual.

- **Section catalog ya existe BE** (`section_catalog.py`) con metadata rica (label_es, subtitle_es, help_text_es, icon_name, scope, weight). FE no lo consume. Duplicación legacy.

- **Brand-studio tiene mismo patrón** que offer-studio (schemas FE + section-catalog.ts). Cualquier mejora en offer debe plantear replica en brand.

- **Polling cap hardcoded 120s** rompió offer extraction >2min. Fixed in `e8dd4bd5`. Lección: safety caps arbitrarios son frágiles ante cambios BE. Poll hasta terminal con cap alto + backoff escalonado.

- **Scripts standalone que tocan SA deben importar `model_registry` primero.** Sin eso, al primer query SA intenta resolver nombres de relaciones string (`LeadModel`, etc.) y falla porque el módulo no fue importado. Patrón: `from src.shared.infrastructure import model_registry  # noqa: F401` arriba de cualquier `db.execute`.

- **Allowlists de arch tests deben medirse, no estimarse.** Fase 00 SPEC predijo 9 paths y la realidad fue 59. Lección: antes de fijar un cap en ADR, corré el test contra el repo y contá. Sub-estimar lleva a red CI o a ADR reactivos.

- **Fixtures golden de BE que necesitan DB corren dentro del container, no en WSL native.** Docker publica en Windows host, WSL2 no llega por `localhost`. Patrón documentado en `docs/refactors/field-contract-ssot/fixtures/offer_a96403b5_baseline.md`.

---

## Fase 00 — Guardrail

**Status**: done (2026-04-24)

### Pre-fase expectations
- Arch test simple (AST parse + JSON compare). 2-3h realista.
- Allowlist inicial 9 paths.
- Golden fixture captura limitada a lo verificable hoy (Wave 1 completada, Wave 2/3 dudoso por bug polling ya fixed).

### Descubrimientos
- Allowlist real arrancó en **59**, no 9. Audit completo de
  `OFFER_SCHEMA_REGISTRY` con filtro `scope !== "edition_level"` + `owner !== "edition"`
  surfacó brecha mayor de lo previsto. Se documenta en ADR-007.
- `SubscriptionDetails` sufre rename drift: FE usa `billing_frequency` /
  `content_update_frequency`, BE declara `billing_cycle` / `content_update_freq`.
  Arreglable en Fase 02 (rename BE para alinear con terminología neutra).
- PLATFORM archetype (14 paths en `platform-details.schema.ts`) no tiene
  contraparte `PlatformDetails` en BE. Fase 02 debe introducir la 6ta entry
  en `ARCHETYPE_TO_DETAILS_MAPPING`.
- Cross-module federado (21 paths en `assets`, `testimonials`, `portfolio`,
  `knowledge`, `scheduling`, `gallery`, `faq`, `location.venues`) exige
  que el resolver Fase 05 consulte múltiples JSONs BE, no solo `Offer`.
- `LandingService.generate_landing_for_offer` persiste — replicamos el
  resolver puro (`_resolve_content` + SQL) en `scripts/capture_offer_a96403b5_baseline.py`
  para snapshot dry-run.
- Postgres bind sale por 127.0.0.1:5432 desde Windows, pero WSL2 no rutea
  al bridge Docker; scripts que necesitan DB local tienen que correr dentro
  de `visionarias_brain_dev` y copiar el output con `docker cp`.
- `from src.shared.infrastructure import model_registry` debe preceder
  cualquier consulta SA en scripts standalone para evitar
  `InvalidRequestError: expression 'LeadModel' failed to locate a name`.

### Decisiones nuevas
- ADR-007 — allowlist cap Fase 00 = 59, shrink-only desde ahí.

### Deuda técnica encontrada
- Rename `billing_cycle` → `billing_frequency` + `content_update_freq` →
  `content_update_frequency` en `SubscriptionDetails` (incluye migration
  + update repositorio). Programado Fase 02.
- Modelar `PlatformDetails` en `offer/domain/details.py` + 6ta entry de
  `ARCHETYPE_TO_DETAILS_MAPPING`. Programado Fase 02.
- Extender resolver de `test-fe-schema-paths-resolve` a paths federados
  (assets/social-proof/scheduling/knowledge) en Fase 05.
- Item-level (itemSchema.fields[].path) validation no enforzado — solo
  se excluyen de top-level. Fase 01+ debe extender la resolución a tipos
  `PricingStructure`/`ObjectionItem`/`DeliverableItem`/etc.

---

## Fase 01 — FieldContract pilot (pricing)

**Status**: done (2026-04-24)

### Pre-fase expectations
- 3 fields LATAM quedan persistidos + extraídos por LLM.
- Allowlist shrink 59 → 56.
- Golden fixture round-trip con 3 fields nuevos.
- Sales-agent prompt additive only.

### Descubrimientos

- **`PaymentProvider` enum vive en `sales_agent.domain.enrollment`**, no en
  `offer.domain`. Importarlo cross-module viola DDD. Decisión (ADR-009):
  persist `accepted_payment_providers: list[str]` en Fase 01. Mover el enum
  a `shared/domain/payment.py` queda como tech debt Fase 02.
- **Landing content builders consumen `pricing` JSONB legacy**
  (`pricing.pay_in_full`) y NO los fields top-level del Offer. Alinear al
  FieldContract queda para Fase 05 (downstream unify). En Fase 01 la
  Invariante 8 (landing byte-identical con offer sin data nueva) se
  preserva porque el nuevo dato es opt-in.
- **Prompt extraction wave design:** wave dedicada para pricing (W2)
  gana sobre extender closing. Razón en ADR-008 — closing ya tiene 7
  campos y mezclar impuestos/cuotas aflojaba el framing "consultor de
  cierre". Paralelismo W2 absorbe la llamada sin overhead secuencial.
- **`accepted_payment_providers` no se extrae por LLM** (Fase 01).
  UI-configurado via Conexiones. Prompt lo deja null por default y sólo
  lo completa si la página lista providers explícitos (`stripe`,
  `mercadopago`, `culqi`, `manual`). Cualquier otro nombre (PayPal,
  PagSeguro) queda null.
- **`exclude_none=True` en `capture_offer_a96403b5_baseline.py`** hace que
  baseline golden no persista las 2 fields null (`tax_included`,
  `installments_available`). Solo `accepted_payment_providers: []`
  aparece (default factory produce lista vacía, no None). INVARIANT 6
  preservada: additive only, nada se pierde.
- **Codegen TS dual output** (JSON + TS) evita drift FE↔BE: el mismo
  script de introspección Pydantic emite `offer_field_paths.json` (arch
  test BE/FE) y `offer-field-paths.ts` con `OfferFieldPath` literal
  union (typecheck FE). Patrón reutilizable para Fase 02+ secciones.
- **`__generated__/` rompía arch test `test-folder-naming`** (kebab-case
  expected) y `check-file/folder-naming-convention` ESLint. Fix: sumar
  `__generated__` a `EXEMPT_PREFIXES` (consistente con `__tests__` /
  `__mocks__`) + relax eslint block bajo `**/__generated__/**`.
- **`test_extraction_orchestrator_per_wave_save.py` requiere AsyncMock
  para cada extractor nuevo**. Agregar extractor sin actualizar fixture
  rompe el test con `TypeError: asyncio.Future required`. Patrón de
  regression: cada vez que se suma wave/section hay que tocar fixture.

### Decisiones nuevas
- ADR-008 — pricing extraction = wave W2 concurrente dedicada.
- ADR-009 — `accepted_payment_providers` como `list[str]` (no enum) para
  evitar import cross-module offer ↔ sales_agent.

### Deuda técnica encontrada
- Mover `PaymentProvider` enum a `shared/domain/payment.py` para que
  offer y sales_agent lo consuman desde una SSoT. Evaluar en Fase 02.
- Landing content builders consumen `pricing` JSONB legacy — alinear al
  FieldContract queda para Fase 05.
- `src/modules/offer/api/offer_type_presets.py:28` tiene `# noqa`
  directive con formato inválido (detectado por ruff warning). No toca
  scope Fase 01; backlog.
- ESLint error prettier preexistente en `OfferShellLayout.test.tsx:115`
  — fuera de scope Fase 01, no tocado por ninguno de los commits A-J.

---

## Fase 02 — Migrate remaining sections

**Status**: done (2026-04-24)

### Pre-fase expectations

- Allowlist shrink 56 → 21 (35 paths cerrados distribuidos en 7 bloques
  semánticos).
- 21 restantes quedan para Fase 05 (cross-module federated).
- PlatformDetails declarado con 6ta entry ARCHETYPE_TO_DETAILS_MAPPING.
- Una migración idempotente por bloque con DB column; sin migración
  para fields en JSONB `specific_details`.

### Descubrimientos

- **Pattern confirmado**: migration+domain+model+repo+DTO+FieldContract+
  regen-codegen+allowlist-shrink en commit único por bloque semántico
  escala bien hasta 7-bloque ambitious. Fase 01 lo probó con pricing;
  Fase 02 lo replicó en 6 bloques adicionales sin abandonar la
  invariante atómica.

- **JSONB rename es casi gratuito**: migration 065 renombró
  `billing_cycle→billing_frequency` y `content_update_freq→
  content_update_frequency` con dos UPDATE filtrados por presencia de
  la clave vieja + ausencia de la nueva. Idempotente en una query.
  Downside: referencias a los nombres viejos viven fuera del dominio
  (prompt j2, draft de herramienta copilot, assert de test). La
  grep-check pre-commit los barrió todos sin falsos positivos.

- **ADR-010 surgió al abrir Block G**: introducir
  `OfferArchetype.PLATFORM` cascadeaba en `ARCHETYPE_CATALOG`,
  `format_catalog`, `offer_type_preset_catalog`, wizard flows — todo
  material de producto, no de refactor. La solución composable
  (`Offer.platform_details: PlatformDetails | None`) con columna JSONB
  dedicada preserva SSoT estructural sin tocar el sistema de archetypes.
  Reversible: si en una fase futura PLATFORM sí merece archetype
  propio, la promoción es mecánica porque los 14 paths ya viven en BE.

- **Codegen extiende a composables**: `generate_offer_field_paths.py`
  ahora walk explícitamente `PlatformDetails.model_fields` además de
  `ARCHETYPE_TO_DETAILS_MAPPING.values()`. Patrón reutilizable — si
  futuras fases introducen otro composable top-level, se agrega una
  línea.

- **FE schema migration a paths anidados es mecánica**: los 14 paths
  `X` → `platform_details.X` son un find-and-replace sin semántica
  nueva. El FE no conoce de "composable vs polymorphic" — solo sigue
  la lista canónica emitida por el codegen.

- **Block F (ProductDetails) y Block E (ServiceDetails) son baratos**:
  al ser JSONB no hay migración, no hay repo mapping, no hay ProductModel
  edit. La nueva persistencia sale sola via `specific_details.model_dump()`.
  Por bloque: 5 líneas en `details.py` + N entries en `field_contract.py`
  + regen codegen + shrink allowlist. <5 min cada uno.

### Decisiones nuevas

- ADR-010 — `PlatformDetails` composable, no 6ta entry en
  `ARCHETYPE_TO_DETAILS_MAPPING`. Desvío documentado del SPEC original
  de Fase 02 para mantener scope refactor sin invadir producto.

### Deuda técnica encontrada

- **Extraction prompts no actualizados para nuevos campos**: authority
  block, value-stack anchor/positioning, program narratives, service
  scope, product shipping no tienen entradas en los prompts j2
  correspondientes. LLM no los extraerá (quedarán null por default).
  No bloquea: campos están disponibles manualmente en UI + sales-agent
  render additive. Programado Fase 05 cuando se unifique el sales-agent
  + landing data-driven.

- **Platform extraction opcional**: prompts j2 no contemplan
  `platform_details.*`. SaaS-flavored offers requieren llenado manual
  hasta que Fase 05 unifique el downstream. UI lo permite.

- **Pre-existing lint noise en `scripts/`**: 418 errores ruff en
  scripts/ no relacionados al refactor (mayormente `PTH100`/`I001`
  en scripts antiguos). Ignorado; ruff check del módulo offer está
  limpio. Entry en `docs/mejoras-proceso/to-do.md` sugerido.

- **Fase 01 flagged**: `# noqa` inválido en
  `src/modules/offer/api/offer_type_presets.py:28` — warning ruff
  persiste en todas las corridas. Backlog.

- **Golden fixture no regenerada**: baseline `a96403b5...` es
  PROGRAMA → los nuevos fields del Block D (MEMBRESIA) no aplican; los
  otros bloques son additive y el fixture usa `exclude_none=True`, por
  lo que el hash queda idéntico sin data nueva. Si Fase 03 requiere
  roundtrip fixture regeneración, documentar ahí.

---

## Fase 03 — Section catalog dedup

**Status**: done (2026-04-24)

### Pre-fase expectations

- Extender `SectionMetadata` con `kind` (singleton/collection).
- FE hook `useSectionCatalog()` ya existía — sumar helpers + migrar
  consumers.
- Brand-studio mirror refactor: new BE catalog (no existía), new FE
  hook.
- Nuevo arch test anti-drift previene regresión del hardcoded array.

### Descubrimientos

- **Offer-studio catalog ya servía via `/archetypes/catalog`** (Sprint 6
  Phase A.5). El hook `useArchetypeCatalog` + `useSectionCatalog` ya
  existían — Fase 03 solo sumó `kind` al DTO y helpers de resolución.
  Ahorro de scope significativo vs la expectativa inicial (crear todo
  el hook).

- **Brand-studio sí requirió BE catalog desde cero**. Nuevo módulo
  `brand/domain/section_catalog.py` con 14 entries + nuevo endpoint
  `/api/v1/brand/sections/catalog` + arch test `completeness`. Patrón
  copiado de offer-studio con menos metadata (no scope/weight/help_text
  porque brand no filtra por archetype).

- **`buildCrumbs` migrado a "pure function + injected resolver"**. En
  lugar de tragarse el hook dentro de la función pura, se acepta un
  `resolveSectionLabel: (slug) => string` como parámetro. El hook vive
  en el componente y se pasa por `useMemo`. Consecuencia: tests ya no
  necesitan mockear React hooks — stub resolver directo. Aplicable a
  cualquier pure function que necesite el catálogo.

- **Icon resolver per-feature**. Brand-studio tiene su propio
  `lib/icon-name-resolver.ts` con 14 íconos. No se promovió a shared lib
  para respetar FE boundary rules (no cross-feature imports). Si un 3er
  studio necesita el mismo resolver, ahí promover. DRY < boundary.

- **Tests que mockean `useSectionsForArchetype` con `[]` rompieron al
  quitar el OFFER_SECTIONS fallback**. NavRail previamente renderizaba
  los 21 sections cuando el mock devolvía []. Post-refactor, [] →
  renderiza []. Fix: mock `useSectionsForArchetype` con al menos el
  `PROMISE_META` object que los tests específicamente asserten. Leve
  churn vale la simplificación: ahora NavRail es más coherente (archetype
  sections + catalog fallback únicamente).

- **ExtractionSummaryCard tests ganaron 2 mocks** (offer + brand
  resolvers) porque el card es cross-studio. Mock identity resolver
  `(slug) => slug` es suficiente para asserts de estructura.

- **Catalog endpoint versioning evita stale cache**. `_CATALOG_VERSION`
  bump cada vez que cambia la metadata — React Query revalida por cache
  key; clientes reciben copia fresca post-deploy.

- **Arch test anti-drift es 1 regex + 1 walk**. ~50 líneas TS que
  previenen que alguien re-hardcodee un array. Muy barato comparado con
  el costo de descubrir el drift en prod.

### Decisiones nuevas

Ninguna ADR nueva. ADR-010 (Fase 02) sigue vigente sin contradicciones
en Fase 03.

### Deuda técnica encontrada

- **Offer-studio y brand-studio tienen dos icon-name-resolvers con
  overlap** (Users, Fingerprint, Target, Scale, ScrollText, Sparkles
  compartidos). Mini-DRY violation. Promover a `src/lib/` cuando 3er
  studio aparezca o el overlap crezca.

- **Settings feature también tiene su propio section-catalog.ts**
  hardcoded (`SettingsNavRail`, `SettingsBreadcrumb`, `section-page-map.test.ts`).
  Fuera del scope del refactor field-contract-ssot (settings no pertenece
  al contract), pero si el patrón "BE-owned section catalog" se vuelve
  convención, migrar settings también. Backlog en
  `docs/mejoras-proceso/to-do.md`.

- **Pre-existing `# noqa` inválido** en
  `src/modules/offer/api/offer_type_presets.py:28` sigue vigente —
  detectado desde Fase 01. Warning ruff persiste.

---

## Fase 04 — Drop OFFER_FIELDS_BY_FE_SECTION

**Status**: pending

---

## Fase 05 — Downstream unify

**Status**: pending
