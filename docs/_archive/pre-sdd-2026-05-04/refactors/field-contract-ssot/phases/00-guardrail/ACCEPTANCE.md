# Fase 00 — Acceptance checklist

Mergeable cuando **todos** green.

## Golden fixture

- [ ] `backend/tests/modules/offer/fixtures/offer_a96403b5_baseline.json` existe
- [ ] `backend/tests/modules/offer/test_offer_a96403b5_baseline.py` existe y pasa
- [ ] Test captura: DB state + rendered prompt + landing output
- [ ] Docs regeneración en `docs/refactors/field-contract-ssot/fixtures/offer_a96403b5_baseline.md`

## Backend paths generator

- [ ] `backend/scripts/generate_offer_field_paths.py` existe
- [ ] Script produce `backend/tests/architecture/fixtures/offer_field_paths.json` determinista
- [ ] JSON committeado (no sólo en `.gitignore`)
- [ ] Instrucción regeneración en header script
- [ ] Script corre native (.venv), no Docker

## FE arch test paths-resolve

- [ ] `frontend/src/__tests__/architecture/test-fe-schema-paths-resolve.test.ts` existe
- [ ] Test green con allowlist + paths BE actuales
- [ ] Allowlist tiene 9 entries + comentario razón cada una
- [ ] Test falla si se agrega path nuevo FE sin match BE + sin allowlist
- [ ] Shrink-only ratchet: allowlist size ≤ 9
- [ ] Mensaje de error claro para dev futuro

## Test counts baseline vs post

- [ ] Backend tests: post ≥ baseline (additive: +1 nuevo test golden)
- [ ] Frontend tests: post ≥ baseline (additive: +1 nuevo arch test)
- [ ] Arch tests ambos: 100% green
- [ ] TSC: 0 errors
- [ ] ESLint: 0 errors (warnings pre-existentes OK)
- [ ] Ruff: 0 errors

## Manual verification offer real

- [ ] Editor `offer-studio/a96403b5.../editor/pricing` carga sin error
- [ ] Editor `.../editor/promise` carga sin error
- [ ] Extraction URL test: pill sube 40→65→85→100 (fix polling previo)
- [ ] Sales-agent prompt render diff (antes/después del commit): additive only

## Workspace

- [ ] `STATE.md` actualizado (`active_phase: 01-...`, `sub_step: 0/N`, `last_green_commit: {hash}`)
- [ ] `LEARNINGS.md` cross-cutting actualizado con learnings fase
- [ ] `phases/00-guardrail/STATUS.md` = `done`, commits listados
- [ ] `phases/00-guardrail/LEARNINGS.md` completo
- [ ] `phases/01-field-contract-pilot-pricing/STATUS.md` = `ready-to-start`
- [ ] `docs/mejoras-proceso/to-do.md` entry nueva

## Git hygiene

- [ ] Cada commit conventional (`type(scope): desc`)
- [ ] Cada commit atómico (un concepto)
- [ ] Stage por nombre explícito (no `-A`/`-u`/`.`)
- [ ] `.claude/scheduled_tasks.lock` NO tocado
- [ ] Working tree limpio al cierre

## Handoff

- [ ] Prompt de continuación entregado a Chris con detalles exactos (fase siguiente + last_green_commit)
