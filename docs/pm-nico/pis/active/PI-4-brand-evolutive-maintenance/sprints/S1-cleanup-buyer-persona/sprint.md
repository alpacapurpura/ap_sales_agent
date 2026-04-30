# Sprint S1 — Cleanup Buyer Persona

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S1-cleanup-buyer-persona |
| PI padre | PI-4-brand-evolutive-maintenance |
| Estado | in-progress |
| Inicio | 2026-04-29 |
| Cierre estimado | 2026-05-03 |
| Cierre real | — |
| Owner PM | /pm |

## Objetivo (1 línea)

Eliminar fields `objections` + `preferred_channels` de `buyer_personas` (BD + BE + FE + copilot extraction) sin romper invariantes ni contratos cross-módulo.

## Pre-handoff (input desde sprint anterior)

- N/A (primer sprint del PI). Input directo: feedback Chris + Explore brief 2026-04-29 (mapeo surface).

## Plan PRs (folders)

| PR | Folder | Descripción | Agentes/skills | Esfuerzo | Estado |
|---|---|---|---|---|---|
| PR-1 | `prs/PR-1-drop-buyer-persona-fields/` | Drop `objections` + `preferred_channels` de buyer_persona stack completo (BD + BE + FE + copilot) | `nicolify-architect` → `nicolify-backend` + `nicolify-frontend` (paralelo, cross-stack) → `nicolify-backend-auditor` + `nicolify-frontend-auditor` + skill `brand-expert` | M | ready |

## Criterio éxito sprint

- [ ] Migration DROP COLUMN x2 idempotente aplicada
- [ ] Backend: model + entity + DTOs + repository + arch tests verdes sin referencias a fields eliminados
- [ ] Frontend: schema + types + components + tests verdes sin referencias
- [ ] Copilot: persister + field_paths_hint + extraction template j2 + field-contract overrides limpios
- [ ] `current-state/brand.md` actualizado con lineage cleanup
- [ ] `RESULT.md` escrito (loop cerrado)
- [ ] /test-all PASS

## Out of scope

| Item | Razón | Sprint destino |
|---|---|---|
| Refactor sub-schema buyer_persona (re-orden secciones, fusión campos restantes) | Scope creep — sprint S2 si Chris trae feedback adicional | S2 (rolling) |
| Backfill audit datos prod (¿hay rows con objections/preferred_channels llenos?) | Decidir en architect phase: data-loss-acceptable o backup script | dentro PR-1 |
| Wire copilot↔telegram | Distinto módulo (PI-2-copilot-improvement) | PI-2 |

## Decisiones a tomar durante sprint

| Fecha | Decisión | PR |
|---|---|---|
| (architect) | ¿Backup data prod antes DROP o aceptar pérdida? | PR-1 |
| (architect) | ¿1 migration con 2 ALTER TABLE o 2 migrations separadas? | PR-1 |

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| Offer module tiene `objections` propio — confusión rename/grep | Architect lee Explore brief: `offer.objections` NO se toca, solo `buyer_personas.objections` | architect |
| Migration falla en prod por data en columns | Test con clone DB antes (regla `backend-migrations.md`) | builder |
| Frontend tests fixtures con `objections: []` rotos | Builder actualiza fixtures + remueve assertions specific | FE builder |
| Copilot extraction template j2 cambio breaks cache prefix | Verify slot ordering preservada (regla cache prefix) | copilot-expert |

## Cierre

Al cerrar:
1. Llenar `learnings.md` (qué funcionó, sorpresas en surface map).
2. Llenar `handoff.md` (¿hay nuevo sprint S2 con feedback adicional o el track espera nuevos items?).
3. Marcar sprint `done`.
4. Verificar `prs/PR-1-*/RESULT.md` escrito.
