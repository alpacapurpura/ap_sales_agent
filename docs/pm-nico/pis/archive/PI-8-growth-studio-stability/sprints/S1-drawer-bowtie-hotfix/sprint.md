# Sprint S1-drawer-bowtie-hotfix

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S1-drawer-bowtie-hotfix |
| PI padre | PI-8-growth-studio-stability |
| Inicio | 2026-05-01 |
| Estado | active |
| Owner PM | /pm |

## Objetivo

3 fixes layout localizados Growth Studio para resolver solapamiento drawer/copilot + bowtie offset + viewport edge cases. **Sin tocar componentes visuales ni reescribir lógica.**

## PRs plan

| PR | Scope | Estado |
|---|---|---|
| PR-1-drawer-bowtie-fixes | z-index ladder + bowtie offset + viewport edges + tests regresión | ready |

## Criterio éxito sprint

- PR-1 shipped PASS auditor
- Chris smoke navegación Growth Studio en mobile + desktop sin solapamientos visuales
- 4-tier loading + currency + multi-stage navigation sin regresión
- Arch fitness ratchet `useCopilotOffset` adoption

## Riesgos sprint

| Riesgo | Mitigación |
|---|---|
| Fixes esconden 4to bug latente | Chris smoke profundo + chrome-devtools-verify post-fix |
| Brand/Offer Studios afectados por z-index bump | Grep consumers `DetailPanel` + smoke regresión Brand/Offer |
| Tests regresión visual flaky | Snapshot testing con tolerancia threshold + dom diff (no pixel-perfect) |

## Aceptación sprint

- [ ] PR-1 shipped (verdict PASS)
- [ ] Smoke Chris-mediated 5 stages × mobile + desktop = 10 caminos verificados
- [ ] Tests regresión viewport breakpoints verdes
- [ ] Arch fitness `useCopilotOffset` ratchet shrink-only verde
- [ ] learnings.md append + handoff.md hacia PI-9 redactado
