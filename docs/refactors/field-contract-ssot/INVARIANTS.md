# Invariantes — reglas inviolables

Violación de cualquiera = PR rechazado + revert inmediato.

## 1. Additive-only antes de subtractive

Agregar capa nueva. Vieja vive. Migrar consumers. Borrar vieja solo cuando todos migrados + paridad probada.

## 2. Un concepto por commit

No mezclar: "add FieldContract + migrate pricing + drop legacy map" en un commit. Tres commits.

## 3. Offer `a96403b5...` funcional siempre

Cada fase cierra con verificación manual + test golden:
- Editor renderiza igual (o mejor: muestra nuevo campo)
- Sales-agent prompt renderea (additive only, nunca perdidos)
- Landing genera (additive only)
- Persistencia PATCH → GET round-trip igual (o mejor)

## 4. Arch tests green cada commit

`/test-all` baseline captured ANTES de arrancar fase. Post-fase, mismo o más tests green. Nunca menos.

## 5. Migrations idempotentes

`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. Probada en clone DB antes de prod. Rollback path documentado.

## 6. Golden fixture nunca pierde info

Fixture puede sumar keys (refactor additivo) pero nunca perder. Test arch enforces.

## 7. Sales-agent prompt render — additive only

Nuevo campo seteado = aparece. Campo vacío = no aparece. Jamás cambia el render de un offer sin fields nuevos.

## 8. Landing output — additive only

Misma regla. Si el offer no tenía data nueva, landing output byte-identical.

## 9. Schemas FE no inventan paths (desde Fase 0)

Arch test valida. Allowlist temporal = deuda documentada. Allowlist shrink-only.

## 10. Rollback = `git revert <hash>`

Cada PR debe ser revertible atómico. Si revert deja sistema roto = PR mal hecho, rehacer.

## 11. No borrar `OFFER_FIELDS_BY_FE_SECTION` hasta Fase 04

Coexiste con `FieldContract` hasta Fase 03 cierre. Protección a extraction worker + tests downstream.

## 12. STATE.md actualizado post-commit material

Nunca dejar STATE.md mintiendo. Si rompe esto rompe recovery.

## 13. Parallel session awareness

- Git `add` por nombre. Nunca `-A`, `-u`, `.`.
- Stage solo files esta sesión modificó.
- Antes de commitear: `git status --short` — si hay archivos ajenos, no tocarlos.
- `.claude/scheduled_tasks.lock` nunca tocar (runtime Claude).

## 14. Spanish neutro LATAM (sin voseo)

Todo user-facing: textos nuevos en neutro. Ver `.claude/rules/spanish-text.md`.

## 15. No romper `backend/tests/architecture/test_*.py`

Specialmente:
- `test_fastapi_app_has_redirect_slashes_disabled`
- `test_no_new_cross_module_imports`
- `test_extraction_contract`
- `test_offer_type_preset_catalog_completeness`
- `test_master_data` (currency)

## 16. No romper `frontend/src/__tests__/architecture/test_*.ts`

Especialmente:
- `test-no-catalog-duplicates`
- `test-studio-sections-lazy-loading`
- `test-component-naming` / file-naming / folder-naming
- `test-no-default-exports`
- `test-fe-schema-paths-resolve` (introducido Fase 0)

## 17. TDD obligatorio

Test primero (regression / acceptance / contract), implementación después. Ver `.claude/rules/tdd-mandatory.md`.

## 18. Tech debt descubierto → arreglado en la misma fase

No posponer al final. Deuda compound. Entry en `docs/mejoras-proceso/to-do.md` como backup.

## 19. Pensar antes de actuar

Cada fase: 5-10 min leer SPEC + INVARIANTS + LEARNINGS acumulados + knowledge específico antes de tocar código. Pensar en trade-offs antes del primer Write. Ver [protocol/PRE_FLIGHT.md](protocol/PRE_FLIGHT.md).

## 20. No desviar objetivo

PLAN.md frozen. Oportunidades tentadoras fuera scope → TODO.md entry, NO PR.
