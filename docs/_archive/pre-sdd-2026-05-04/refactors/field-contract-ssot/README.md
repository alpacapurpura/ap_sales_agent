# Field Contract SSoT — Refactor Workspace

Crash-recoverable workspace for multi-sprint architectural refactor.

## Objetivo final

Separar **contrato estructural** (qué fields existen, tipos, paths, validación dura, secciones) del **UX presentation** (labels, hints, placeholders, copy) para offer-studio y brand-studio.

**Estado deseado al cerrar fase 5:**

- `FieldContract` BE es SSoT estructural. Endpoint `/api/v1/offer/field-contract` versionado.
- Schemas FE solo contienen UX presentation. `path` tipo-validado contra contrato BE.
- `SectionCatalog` BE es SSoT de secciones (label, icon_name, help_text, scope, weight). FE consume, no duplica.
- `OFFER_FIELDS_BY_FE_SECTION` eliminado (derivado de `FieldContract`).
- Sales-agent prompt + landing builder + completion service + extraction todos consumen `FieldContract`.
- Arch tests impiden drift: todo path FE debe resolver a contract BE.

## Por qué existe este workspace

Refactor grande que:
- Toca 5+ sprints
- No puede romper base funcional actual
- Debe sobrevivir crashes de sesión Claude (cualquier session retoma)
- No puede desviarse del plan frozen
- Debe capitalizar learnings fase-a-fase

## Mapa de archivos

| Archivo | Rol |
|---|---|
| [STATE.md](STATE.md) | **Estado actual atomic.** Leer primero al retomar. |
| [PLAN.md](PLAN.md) | 5 fases frozen. No cambia sin motivo fuerte. |
| [INVARIANTS.md](INVARIANTS.md) | Reglas inviolables. |
| [DECISIONS.md](DECISIONS.md) | ADR log. |
| [LEARNINGS.md](LEARNINGS.md) | Aprendizajes acumulados. |
| [TODO.md](TODO.md) | Próximas acciones + blockers. |
| [protocol/RESUME.md](protocol/RESUME.md) | **Cómo retomar.** |
| [protocol/PRE_FLIGHT.md](protocol/PRE_FLIGHT.md) | Checks antes de fase. |
| [protocol/POST_FLIGHT.md](protocol/POST_FLIGHT.md) | Checks al cerrar fase. |
| [protocol/CRASH_RECOVERY.md](protocol/CRASH_RECOVERY.md) | Qué hacer si rompe. |
| phases/{nn}-{name}/ | Una por fase. SPEC + ACCEPTANCE + STATUS + LEARNINGS. |
| fixtures/ | Golden snapshots offer real (`a96403b5...`). |

## Quick start

**Al retomar**: [protocol/RESUME.md](protocol/RESUME.md).
**Arrancar nueva fase**: [protocol/PRE_FLIGHT.md](protocol/PRE_FLIGHT.md).
**Cerrar fase**: [protocol/POST_FLIGHT.md](protocol/POST_FLIGHT.md).
**Si rompe**: [protocol/CRASH_RECOVERY.md](protocol/CRASH_RECOVERY.md).

## Tenant + offer de referencia

Toda verificación de no-regresión usa:
- `tenant_id`: `1fd1562b-2101-410a-870c-dc2f7e27b355`
- `offer_id`: `a96403b5-c1db-4b31-97aa-cb18d08ad9f9`
- `archetype`: programa · `preset_id`: coach_bootcamp · `value_level`: transformacion

Golden snapshot: [fixtures/offer_a96403b5_baseline.md](fixtures/offer_a96403b5_baseline.md).
