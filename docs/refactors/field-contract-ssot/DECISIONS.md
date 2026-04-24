# Decisiones arquitectónicas (ADR log)

Cada decisión: fecha + contexto + decisión + razón + alternativas rechazadas.

Formato ADR minimalista. Append-only. No editar decisiones viejas — si invalidás, nueva entry marca la vieja como superseded.

---

## ADR-001 — Separación de capas estructura vs presentación

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: Offer studio schemas FE conflate `path` (estructural) + `label/hint/placeholder` (UX). Esto causó Capa A (9 paths huérfanos) y drift silencioso.

**Decisión**: Dos capas explícitas:
- Layer 1 — `FieldContract` BE-owned. Estructural: path, type, owner, required, section, archetype filter, enum values, array item.
- Layer 2 — Schemas FE-owned. UX: label, hint, placeholder, icon, formula, examples, downstream_uses, lengthHint.

**Razón**:
- Estructura originada por modelo de datos (BE). Pydantic ya es SSoT.
- Copy/UX iteración rápida (FE) — no bloquear con deploy backend.
- Validación en compile-time FE via codegen path union.
- Industria confirma patrón: Sanity/Strapi/Stripe/GitHub todos separan estructura de presentación.

**Alternativas rechazadas**:
- Todo BE (Strapi-clone): mata velocidad UX iteration. Over-engineering.
- Todo FE (status quo): drift silencioso. Bug repetible.
- JSON Schema shared package: codegen Python+TS pesado. Asimetría natural BE↔FE no calza.
- Generar Pydantic desde Zod: inversión de causalidad incorrecta.

---

## ADR-002 — `OFFER_FIELDS_BY_FE_SECTION` reemplazado por derivación

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: `OFFER_FIELDS_BY_FE_SECTION` es mapping parcial (7/21 secciones). Divergente de `Offer` domain.

**Decisión**: En Fase 04, eliminar dict. Reemplazar por util `fields_by_section(contract, section_key)` derivado puro de `FieldContract`.

**Razón**: single source. Imposible drift. Nuevo field en contract aparece auto en grouping.

**Alternativas rechazadas**: llenar el dict con los 21 slugs completos → mantener duplicación.

---

## ADR-003 — Section catalog BE como SSoT, FE consume

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: `backend/.../section_catalog.py::SECTION_CATALOG` (21 secciones + label_es + subtitle_es + help_text_es + icon_name + scope + weight + required_to_publish) duplicado por `frontend/.../section-catalog.ts::OFFER_SECTIONS` (21 secciones + label + icon + kind).

**Decisión**: BE es SSoT. FE consume endpoint catalog + mapea `icon_name` a componente Lucide via `icon-name-resolver.ts`. `kind` se mueve a BE `SectionMetadata`.

**Razón**: section ontology es estructural, no puramente UX. Affects completion weight + scope persistence.

**Alternativas rechazadas**: dejar duplicado porque "es solo display" — `label_es` diverge de `label` en cualquier momento.

---

## ADR-004 — Workspace refactor `docs/refactors/field-contract-ssot/`

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: Refactor multi-sprint, riesgo de perder contexto entre sessions Claude.

**Decisión**: Crear workspace estructurado con STATE.md atomic + protocolo RESUME/PRE_FLIGHT/POST_FLIGHT + per-fase dir. Patrón reutilizable para futuros refactors grandes.

**Razón**: crash recovery, no-drift, trazabilidad, learnings compuestos.

**Alternativas rechazadas**:
- Un solo doc largo: no survive session reset.
- Jira/GitHub issues: fuera de repo, no versionable.
- `docs/projects/`: ok pero `refactors/` más semántico.

---

## ADR-005 — Golden fixture desde Fase 00

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: user quiere asegurar base funcional no rompa durante refactor.

**Decisión**: Capturar snapshot de `a96403b5...` (DB state + rendered prompt + landing output) en Fase 00. Golden test valida paridad cada PR.

**Razón**: data-level regression catching. Automatizable.

**Alternativas rechazadas**:
- Visual regression (Playwright screenshots): overhead alto. Rechazado explícito por user.
- Solo manual check: no escalable.

---

## ADR-007 — Allowlist cap de Fase 00 arranca en 59 (no 9)

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: `PLAN.md` y `phases/00-guardrail/SPEC.md` predijeron que la
allowlist `KNOWN_UNRESOLVED_PATHS` arrancaría con 9 paths (Capa A pricing +
authority/value-stack/program narratives). El arch test corrido durante
sub-step 3 encontró **59 paths** realmente huérfanos una vez se filtran
sections `edition_level` y fields `owner: "edition"`.

**Desglose**:
| Origen | Paths | Fase que cierra |
|---|---|---|
| Pricing LATAM (SPEC original) | 3 | Fase 01 |
| Authority / Value-stack / Program narratives (SPEC original) | 6 | Fase 02 |
| SubscriptionDetails (renames `billing_cycle→frequency`, `content_update_freq` + 5 nuevos) | 7 | Fase 02 |
| ServiceDetails (3 nuevos) | 3 | Fase 02 |
| ProductDetails (5 nuevos) | 5 | Fase 02 |
| PLATFORM archetype sin modelar en BE | 14 | Fase 02 |
| Cross-module federados (assets, social-proof, scheduling, knowledge) | 21 | Fase 05 |

**Decisión**: Ratchet arranca en 59 (valor actual). Test pasa hoy; cada
fase subsiguiente baja el cap. Nunca subir sin ADR + PR que avance el plan.

**Razón**:
- El SPEC underestimó porque se basó en Capa A/B teórica sin auditar
  `OFFER_SCHEMA_REGISTRY` entero.
- Cerrar la brecha en Fase 00 inflaría la fase (implicaría migración de
  SubscriptionDetails/ServiceDetails/ProductDetails + nuevo archetype
  PLATFORM). Eso es Fase 02.
- Preservar el espíritu del ratchet (shrink-only) es más importante que el
  valor inicial.

**Alternativas rechazadas**:
- Limitar cap a 9 → test RED hoy, imposible mergear Fase 00.
- Eliminar el test → elimina el mecanismo guardrail, contradice el objetivo
  de la fase.
- Excluir paths cross-module y platform-details de la auditoría → oculta
  la deuda en vez de cuantificarla.

---

## ADR-006 — Tech debt arreglada en la misma fase

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: user preferencia: no posponer deuda descubierta.

**Decisión**: Tech debt encontrada durante fase **relacionada al scope** se arregla en PR de la fase (o PR vecina). Tangencial va a TODO.md + `docs/mejoras-proceso/to-do.md`.

**Razón**: compounding debt es el problema original (Capa A = deuda aplazada).

**Alternativas rechazadas**: "fix forward" tangenciales — crean scope creep y mergeadas en batch tardías.

---

## ADR-008 — Pricing extraction corre como wave W2 concurrente dedicada

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: Fase 01 agrega 3 fields pricing (`tax_included`,
`installments_available`, `accepted_payment_providers`). El orchestrator
actual corre 3 waves (W1 promise+strategy · W2 psychology+value_stack+closing
· W3 details). Hay que decidir dónde colocar la extracción pricing.

Alternativas evaluadas:

1. **Ampliar `_extract_closing`** para incluir pricing. Contra: mezcla
   responsabilidades (closing = garantías/urgencia, pricing = impuestos y
   cuotas). Prompt closing ya tiene 7 campos, agregar 2 más afloja el
   "senior marketing consultant" framing.
2. **Nueva wave W4** exclusiva. Contra: overhead LLM innecesario (4ta
   round-trip secuencial), rompe latencia objetivo.
3. **Agregar pricing concurrente en W2**. ✓ Elegida.

**Decisión**: pricing es extractor independiente (`_extract_pricing`
+ template `offer_extract_pricing.j2` + `PricingWaveOutput`) que corre
en paralelo dentro de W2 junto a psychology / value_stack / closing.
W2 pasa de 3 sections a 4.

**Razón**:
- Mantiene responsabilidad aislada (prompt pricing vive solo).
- Sin overhead secuencial (W2 ya paraleliza con asyncio.gather).
- Schema-output por wave se preserva (`PricingWaveOutput` adicional).
- `_merge_and_save` ya itera `results` uniformemente.

**Alternativas rechazadas**: ampliar closing (mezcla), nueva W4 (latencia).

**Nota**: `accepted_payment_providers` NO se extrae (lo configura el
usuario en Conexiones). Prompt pricing solo emite `tax_included` +
`installments_available`.

---

## ADR-009 — `accepted_payment_providers` persiste como `list[str]` (no enum)

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: `PaymentProvider` enum vive en
`src/modules/sales_agent/domain/enrollment.py::PaymentProvider`
(stripe/mercadopago/culqi/manual). Offer-domain necesita referenciarlo
para el nuevo campo `accepted_payment_providers`. Un import directo
cross-module viola DDD (INVARIANT 15, `.claude/rules/backend-ddd.md`:
"Module A no importa de B's domain").

Alternativas evaluadas:

1. **Import directo** `from sales_agent.domain.enrollment import PaymentProvider`.
   Contra: viola DDD, arch test `test_no_new_cross_module_imports`
   entra en allowlist.
2. **Duplicar enum en offer/domain/enums.py**. Contra: dos SSoT drift
   garantizado (exactamente el problema que el refactor combate).
3. **Mover enum a `shared/domain/payment.py`** + offer importa, enrollment
   importa. ✓ Correcto a largo plazo.
4. **`list[str]` en domain/DTO con validación runtime opcional contra
   catálogo en `shared/domain/`** para Fase 01. ✓ Elegida (para Fase 01).

**Decisión**: Para Fase 01, `accepted_payment_providers: list[str] = []`
en `Offer` + `OfferPricingUpdate`. Validación runtime queda opcional.
En Fase 02+ se evalúa mover el enum a `shared/domain/payment.py`.

**Razón**:
- Scope Fase 01 es pricing pilot, no cross-module refactor.
- Alternativa 3 (mover enum) toca sales_agent + offer + shared + migrations
  de referencias — scope creep que compromete fase atómica.
- `list[str]` permite que el FE picker emita los providers válidos del
  tenant (ya filtra por Connections). Validación BE puede sumarse cuando
  el catálogo migra a shared.

**Alternativas rechazadas**:
- Alt 1: viola DDD.
- Alt 2: drift SSoT.
- Alt 3 ahora: scope creep Fase 01.

**Tech debt entry**: TODO.md — "Mover `PaymentProvider` enum a
`shared/domain/payment.py` y consumir desde offer + sales_agent". Programado
evaluación al arrancar Fase 02.

---

## ADR-010 — `PlatformDetails` composable, no 6ta entry de ARCHETYPE_TO_DETAILS_MAPPING

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: Fase 02 Block G cierra 14 paths `platform_*` del schema FE
que estaban huérfanos. El SPEC de la fase planteaba originalmente introducir
`OfferArchetype.PLATFORM` como 6ta entrada polimórfica en
`ARCHETYPE_TO_DETAILS_MAPPING`. Una auditoría rápida demostró que ese camino
cascadeaba en todo el sistema de archetypes:

- `ARCHETYPE_CATALOG` (nueva entry completa: sections tuple, wizard copy,
  `default_variant_structure`, `supported_variant_structures`,
  examples, icon).
- `format_catalog.py` (`suitable_for: dict[EBT, float]` per archetype).
- `offer_type_preset_catalog.py` (nuevos presets PLATFORM o reubicación
  de presets que hoy usan `_base_membresia()` con `SK.PLATFORM_DETAILS`).
- `archetype_catalog.py::sections` para `MEMBRESIA` — perdería acceso a
  `SK.PLATFORM_DETAILS` si queda exclusivo de PLATFORM, rompiendo los
  ~8 presets SaaS-membership actuales.
- Wizard UI (archetype picker) + edition / variant mechanics + dashboards
  por tipo.

Esa inflación de scope rompía la regla de "un concepto por commit"
(INVARIANT 2) y obligaba a decisiones de producto (¿cómo se posiciona
PLATFORM frente a MEMBRESIA SaaS?) ajenas al objetivo del refactor.

**Decisión**: Introducir `PlatformDetails` como **campo composable** de
primer nivel en `Offer` (`platform_details: PlatformDetails | None`),
persistido en una columna JSONB dedicada (`products.platform_details`,
migration 066). NO se agrega `OfferArchetype.PLATFORM` ni 6ta entry en
`ARCHETYPE_TO_DETAILS_MAPPING`. El codegen se extiende explícitamente
para walk `PlatformDetails.model_fields` y emitir `platform_details.X`
paths.

Los paths FE del schema `platform-details.schema.ts` se renombran de
`X` (top-level huérfano) a `platform_details.X`. `SK.PLATFORM_DETAILS`
sigue apareciendo en el rail de la sección para presets MEMBRESIA
SaaS-flavored via `offer_type_preset_catalog.py` existente.

**Razón**:
- PlatformDetails es ortogonal al archetype — cualquier oferta puede
  declarar metadata SaaS (features, integrations, compliance) sin
  cambiar su archetype primario.
- Evita cascade a catálogos, wizards, presets.
- Mantiene SSoT estructural (los 14 paths ahora tienen origen canónico
  en BE via `PlatformDetails`).
- Reversible: si en una fase futura surge `OfferArchetype.PLATFORM` por
  razones de producto, `PlatformDetails` se puede promover a 6ta entry
  polimórfica sin repetir el refactor (los paths ya existen).

**Alternativas rechazadas**:
1. Promover a `OfferArchetype.PLATFORM` ahora — scope creep de producto,
   rompe INVARIANT 2, toca presets y wizards.
2. Extender `SubscriptionDetails` con 14 campos extra — bloat (8+14
   fields), rompe responsabilidad (billing vs software), excluye a
   archetypes no-MEMBRESIA de declarar platform metadata.
3. Hoist los 14 campos flat en `Offer` — polución de la raíz (14
   campos SaaS-only en todas las ofertas), FE mantenible porque
   los paths quedan como estaban, pero BE sucio.

**Contrato codegen**: `scripts/generate_offer_field_paths.py` ahora
también walk `PlatformDetails.model_fields` → emite
`platform_details.{field}`. Pattern reutilizable si futuras fases
agregan otro composable (BrandGlossaryDetails, ComplianceDetails, etc.).
