# Decisiones arquitectónicas (ADR log)

Append-only. No editar entries. Si una decisión se invalida, nueva
entry marca la vieja como `superseded by ADR-NNN`.

## ADR-011 — Refactor pivote: cross-module platform

**Fecha**: 2026-04-24
**Estado**: accepted
**Reemplaza**: workspace `docs/refactors/field-contract-ssot/` Fase 04 original

**Contexto**: el refactor field-contract-ssot arrancó con scope offer-aislado.
Al abrir Fase 04 descubrimos que el problema real no es offer sino **platform**:
5 fuentes paralelas (`shared/links/ports/editable_fields`, `copilot/domain/schema_introspection`,
`copilot/domain/offer_fields::PERSISTABLE_FIELDS`, `offer/domain/field_contract`,
`offer/domain/extraction_section_map::OFFER_FIELDS_BY_FE_SECTION`) viven
parcialmente solapadas, manualmente mantenidas, con drift confirmado entre
`OFFER_EDITABLE_FIELDS` y `FIELD_CONTRACT_REGISTRY` (los nuevos pricing
LATAM, authority fields, value-stack anchor, etc. están en uno pero no
en el otro).

Continuar el refactor original con cualquiera de las opciones evaluadas
(A: 41 entries manuales, C-1: derivación offer-aislada, C-1+: derivación
con cleanup interno offer) consolida un patrón inconsistente cross-module
("frankenstein") que el copilot conversacional whatsapp/telegram
necesita unificar para escalar.

**Decisión**: pivotar el refactor. Nuevo workspace
`docs/refactors/field-contract-platform/`. Diseño cross-module en
`shared/domain/`. Migración incremental por módulo (offer Fase 04 →
brand 06 → buyer 07 → copilot unification 08 → multi-channel 09).
Sales-agent + landing + completion data-driven en Fase 05.

**Razón**:
- 17 módulos hoy + más por venir. Sin contrato único, drift compuesto
  inevitable.
- Copilot conversacional reemplaza la web a corto plazo (whatsapp/telegram).
  Necesita SSoT con `human_question_es`, `expects`, `gate`, `redo_if_changes`.
- Lifecycle de fields (agregar/agrupar/deprecar) requirement explícito.
- Consistencia es no-negociable per stakeholder.

**Alternativas rechazadas**:
- A (41 entries manuales en offer): consolida deuda que reescribimos.
- C-1+ offer-aislado: deja brand/buyer en patrón viejo. Frankenstein.
- C-2 ad hoc cross-module sin diseño previo: scope creep peligroso.
- Continuar Fase 04 frozen: agrava el problema fundamental.

**Costo**: ~5-6 sprints distribuidos vs 0.5 sprint original Fase 04.
ROI: sistema escalable a 17+ módulos + multi-channel + lifecycle.

## ADR-012 — FieldContract derivado de Pydantic + override pattern

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: dado que se acepta ADR-011, hay que decidir cómo se
construye `FieldContract`. Tres opciones evaluadas:

1. **Tuple manual** (igual que `FIELD_CONTRACT_REGISTRY` actual extendido):
   escribir 41 entries más a mano para offer + N para brand + N para
   buyer. Drift posible si Pydantic cambia.
2. **Derivación pura de Pydantic**: walker que introspecciona
   `Model.model_fields` y emite `FieldContract` automático. Cero drift
   por construcción. Pero metadata semántica (archetype_filter, gate,
   human_question_es) no es expresable en Pydantic → tiene que vivir
   en algún lado.
3. **Pydantic + decoradores**: contaminar dominio Pydantic con
   `Field(json_schema_extra={"copilot_meta": {...}})`. Acopla módulos
   a copilot.

**Decisión**: opción 2 + override pattern.

- Walker introspecciona Pydantic estructura (path, type, enum_values,
  list_item_type, is_required_structural).
- Cada módulo declara `{MODULE}_SECTION_MAP: dict[str, str]` (path → section)
  + `{MODULE}_FIELD_OVERRIDES: dict[str, FieldContractOverride]` (metadata
  semántica).
- `derive_contracts_from_pydantic(model, section_map, overrides, ignore)`
  → `tuple[FieldContract, ...]`.
- Override merge: campos no-None del override pisan derivado.

**Razón**:
- Pydantic queda limpio (SSoT estructural puro).
- Metadata semántica vive separada (fácil de iterar sin tocar dominio).
- Cero drift Pydantic ↔ contract por construcción.
- Override permite expresar lo que Pydantic no.

**Alternativas rechazadas**:
- 1: drift garantizado (lección Fase 02).
- 3: violación DDD, copilot meta contamina cada módulo.

## ADR-013 — Lifecycle de fields (status / deprecated_in / replaced_by)

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: el negocio anticipa cambios constantes en fields
(agregar / agrupar / eliminar / deprecar). Sin lifecycle, cada cambio
es breaking. Con lifecycle, deprecaciones son no-op para clientes
viejos.

**Decisión**: `FieldContract` incluye:
- `status: FieldStatus` enum (`ACTIVE`, `DEPRECATED`, `REMOVED`).
- `deprecated_in: str | None` (version string).
- `replaced_by: str | None` (path replacement field).
- `introduced_in: str | None` (version string).

Workflow:
1. Marcar `status=DEPRECATED` con `deprecated_in` + `replaced_by`.
2. Consumers filtran por `status == ACTIVE` para nuevo render. Old
   consumers ven el field hasta sprint deprecation window.
3. FE schemas se actualizan en sprint dedicado para no renderizar.
4. Una vez no hay rendering ni reads → ratchet `status=REMOVED` →
   drop del Pydantic + migration.

Versions usan format `YYYY-MM-DD-fase-NN-block-X`.

**Razón**: zero breaking changes durante deprecaciones. Lifecycle
visible y auditable. Coordinación FE-BE explícita.

**Alternativas rechazadas**:
- Sin lifecycle (drop directo): rompe clientes en producción.
- `deprecated: bool` simple: pierde contexto sobre cuándo y por qué.

## ADR-014 — Copilot meta sobre FieldContract

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: el copilot conversacional whatsapp/telegram necesita
preguntar naturalmente. Hoy esa metadata vive en prompts hardcoded
por módulo. Sin un anchor estructural, agregar un field implica tocar
cada prompt.

**Decisión**: `FieldContract` incluye:
- `can_propose: bool` (¿el copilot puede escribir este field?).
- `human_question_es: str | None` (pregunta natural en español neutro).
- `expects: str | None` (hint type/format para el LLM).
- `gate: str | None` (path precondición; "archetype debe estar set").
- `redo_if_changes: tuple[str, ...] | None` (paths cuyo cambio invalida
  esta respuesta).

Consumido por:
- Sistema prompt enumeration del copilot (Fase 08).
- `next_question(module, state)` algorithm (Fase 09).
- `propose_field_updates` validator (filtra por `can_propose=True`).

**Razón**: agregar un field al contract → aparece auto en flujos
conversacionales sin tocar prompts. Lifecycle preserves backward-compat.

**Alternativas rechazadas**:
- Mantener prompts hardcoded por módulo: scope creep cada vez que
  agregamos field.
- Dictar en `notes`: confunde audiences (notes para devs, human_question_es
  para usuario final).

## ADR-015 — Multi-channel projection desde el mismo contract

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: el sistema debe servir form-runtime web + chat conversacional
(whatsapp/telegram) + email + voz a futuro, sin duplicar lógica de
"qué fields preguntar".

**Decisión**: el `FieldContract` con `human_question_es` + `gate` +
`priority` es channel-agnostic. Cada canal lo proyecta:

- **Web (form-runtime)**: schema FE consume codegen `OfferFieldPath` y
  renderiza form. Si schema declara `label` custom, usa eso. Si no,
  fallback a `human_question_es` (Fase 09).
- **Chat (whatsapp/telegram)**: orchestrator selecciona next field por
  `(priority, gate satisfied, missing value)`. Emite `human_question_es`.
  Parsea respuesta con `expects` como hint LLM.
- **Email**: idem chat con plantilla email.
- **Voz**: idem chat con TTS.

**Razón**: un solo source of truth para flujos de captura. Agregar canal
nuevo = nuevo adapter, mismo algoritmo.

**Alternativas rechazadas**:
- Prompts hardcoded por canal: scope creep multiplicativo.
- LLM decide todo en runtime sin guidance: imprecisión + drift.

## ADR-016 — Workspace nuevo en `docs/refactors/field-contract-platform/`

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: el refactor anterior (field-contract-ssot) cerró 3 fases.
El pivote (ADR-011) cambia scope cross-module. Mantener el workspace
viejo confunde por el nombre.

**Decisión**: nuevo workspace. Workspace viejo queda como histórico
(Fases 00-03 cerradas). En su `STATE.md` se agrega redirect a este.

**Razón**:
- Naming refleja realidad nueva.
- Estructura phases/ se reinicia (numeración 04-09).
- Historia de Fases 00-03 preservada en su lugar original.

## ADR-017 — Pre-investigación obligatoria por fase

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: la lección dura del refactor anterior fue cerrar Fase 02
sin notar 41 fields gap por falta de inventario completo. La métrica
de cierre (allowlist shrink) era proxy débil.

**Decisión**: cada fase tiene `phases/{NN-name}/PRE_INVESTIGATION.md`
con preguntas obligatorias que **deben responderse** antes del primer
Write/Edit. Ejemplos:
- "¿Qué archivos del módulo target consumen registries paralelos?"
- "¿Cobertura completa del Pydantic vs scope de la fase?"
- "¿Qué tests existentes cubren el área? ¿Cuáles necesito escribir?"
- "¿Qué dependencies cross-module se invocan?"
- "¿Qué endpoints / artifacts FE consumen lo que voy a tocar?"

Si una pregunta no se puede responder con confianza, **se investiga
hasta poder** — no se asume, no se procede.

**Razón**: prevenir el blind spot del refactor anterior. El costo de
2 horas extras por fase es trivial vs el costo de descubrir gap a
mitad y replantearlo todo.

**Alternativas rechazadas**:
- Confiar en SPEC + LEARNINGS: la lección dice que no alcanza.
- Métrica de cierre estricta: ya tenemos arch tests, no ayudan a
  detectar el problema fuera de su scope.
