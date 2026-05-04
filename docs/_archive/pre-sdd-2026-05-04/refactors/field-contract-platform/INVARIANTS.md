# Invariantes — reglas inviolables

Violación de cualquiera = PR rechazado + revert inmediato. Aplica a
todas las fases del refactor field-contract-platform.

## 1. SSoT no negociable

Un solo `FieldContract` cross-module en `shared/domain/`. Cero registries
paralelos nuevos. Si un consumer necesita metadata adicional, va al
`FieldContract` (o al override del módulo). Cualquier `set[str]` o
`tuple[FieldSpec]` paralelo descubierto en el camino se elimina o se
deriva — nunca se deja coexistir.

## 2. Additive antes de subtractive

Agregar capa nueva. Vieja vive. Migrar consumers. Borrar vieja solo
cuando todos migrados + paridad probada.

## 3. Un concepto por commit

No mezclar "promover FieldContract + migrar offer + drop registries
paralelos" en un commit. Tres+ commits separados, cada uno revertible.

## 4. UX byte-identical durante migración

El usuario no debe percibir nada. Cualquier endpoint, cualquier
schema FE, cualquier output del copilot, cualquier render del
sales-agent o landing — el JSON / texto / HTML emitido debe ser
**idéntico** al pre-refactor para offers existentes sin data nueva.

Forma de verificar: golden snapshot tests por consumer.

## 5. Arch tests verde cada commit

Baseline tests capturado antes de fase. Post-commit, mismo o mayor.
Nunca menor. Cada gate nuevo agrega protección — no quita.

## 6. Pydantic ⊆ FieldContract per módulo migrado

Cobertura total. Si Pydantic `Offer.model_fields` tiene field X,
`FieldContract` registry para offer tiene entry para X (excepto
ignored_paths del sistema). Arch test enforces.

## 7. Consumer derivation ⊆ FieldContract

Cualquier consumer (editable_fields catalog, PERSISTABLE_FIELDS,
extraction grouping, sales-agent prompt, landing builder) debe
derivarse. Arch test verifica que `consumer_paths ⊆ FieldContract paths`.

## 8. Lifecycle respetado

Field con `status=DEPRECATED` no se borra del Pydantic ni del registry
hasta su `status=REMOVED`. Consumers leen `status` para decidir
incluir/no. FE schemas filtran deprecated en sprint dedicado al deprecate,
no en el commit que marca deprecate.

## 9. Sin cambios al UX schema FE durante refactor

Schemas `frontend/src/features/{module}/schemas/*.schema.ts` no se
tocan en la migración a `FieldContract`. Solo cuando consumers FE
necesiten consumir nueva metadata (Fase 09 multi-channel) se evalúa
modificar schemas.

## 10. Brand/buyer/copilot intactos hasta su fase

En Fase 04 solo offer migra. Brand `copilot_editable_fields.py` sigue
manual. Buyer idem. Copilot sigue consumiendo `editable_fields` port
y `schema_introspection` sin cambios. Si algo de su comportamiento
cambia → bug en Fase 04, revert.

## 11. Pre-investigación obligatoria antes de cada fase

Cada fase tiene `phases/{NN}/PRE_INVESTIGATION.md` con preguntas que
deben responderse antes del primer Write/Edit. Si la respuesta no
está clara, **se investiga** — no se asume. Razón: el refactor anterior
(field-contract-ssot Fase 02) cerró sin notar 41 fields gap por falta
de inventario completo.

## 12. STATE.md actualizado post-commit material

Nunca dejar STATE.md mintiendo. Si rompe esto, rompe recovery.

## 13. Parallel session awareness

- Git `add` por nombre. Nunca `-A`, `-u`, `.`.
- Stage solo files esta sesión modificó.
- Archivos ajenos en working tree → no tocarlos.
- `.claude/scheduled_tasks.lock` nunca tocar.

## 14. Spanish neutro LATAM (sin voseo)

Todo `human_question_es` y `notes` user-facing en español neutro LATAM.
Ver `.claude/rules/spanish-text.md`.

## 15. TDD obligatorio

Test primero (regression / acceptance / contract), implementación después.
Cada arch gate nuevo escrito como test antes de que detecte algo real.

## 16. Tech debt descubierto → arreglado en la misma fase

Si durante una fase aparece deuda técnica relacionada al scope, la
arreglás en la misma fase (o PR vecina dentro de la fase). Si es
tangencial: entry a `docs/mejoras-proceso/to-do.md` + nota en
`LEARNINGS.md`. **Nunca** posponer al final del refactor.

## 17. Override pattern para metadata semántica

Cualquier metadata que Pydantic no puede expresar (archetype_filter,
human_question_es, gate, etc.) va al `FieldContractOverride` del
módulo. Nunca decoradores Pydantic ni metadata en `Field()` json_schema_extra
para esto — mantiene Pydantic limpio para ser SSoT estructural puro.

## 18. No reentrar a fase cerrada

Una vez una fase cierra (LEARNINGS escrito, STATE bumped, próxima fase
abierta) **no se reabre**. Si algo descubierto requiere fix:
- Si afecta solo a la fase activa → fix en fase activa.
- Si afecta producción → bugfix commit fuera del refactor.
- Si requiere replanteo arquitectónico → ADR nueva + fase nueva.

## 19. Pensar antes de actuar

Cada fase: 5-10 min leer DESIGN + INVARIANTS + LEARNINGS acumulados +
PRE_INVESTIGATION antes de tocar código. Pensar en trade-offs antes
del primer Write.

## 20. No desviar objetivo

PLAN.md frozen. Oportunidades tentadoras fuera scope → TODO.md, NO commit.
