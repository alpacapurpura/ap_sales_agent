# PR-0 — Saneamiento: Migrar research legacy a SSoT pm-nico

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-0-research-migration |
| Sprint padre | S0-foundation |
| PI padre | PI-1-campaigns-module |
| Estado | shipped (2026-04-29) |
| Tipo | research / docs |
| Esfuerzo | S |
| Owner PM | /pm |

## Problema

Research legacy en `docs/pm/campaigns/` (5 carpetas + FOUNDATION.md + MASTER_TODO 13 fases) es input rico pero no es SSoT formal. Antes de escribir código S0.1+, alinearlo con `docs/pm-nico/` para que builders carguen contexto desde un único lugar.

## Outcome esperado

Cualquier agente builder puede leer **solamente** `docs/pm-nico/` y entender estado, oportunidades, plan, decisiones del módulo campaigns. `docs/pm/campaigns/` queda como input histórico, no canónico.

## Walking skeleton

PM solo. Sin builders. Sin código. Solo docs.

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A — Migrar todo verbatim | preserva 100% | duplica info, nadie lo lee | descartada |
| B — Synthesis comprimida + 6 opportunities + current-state update | navegable, caveman style, perserva trazabilidad linkeando legacy | requiere cuts editoriales | **ELEGIDA** |
| C — Borrar legacy y solo dejar PI.md | máxima compresión | pierde contexto histórico de research | descartada |

## Decisiones diferidas

- ¿Cuándo borrar `docs/pm/campaigns/`? Después de S0 completo (todo migrado y validado en uso). Decisión PI cierre.

## Out of scope PR-0

- No tocar código.
- No reescribir FOUNDATION.md (queda como input legacy hasta S0 cierre).
- No abrir PR-1 outbox (sigue después).

## Copilot-first checklist

- [x] N/A — PR de docs PM, no expone capacidad nueva.

## Agentes / skills recomendados

| Fase | Agente/skill | Entregable esperado |
|---|---|---|
| Migración | PM solo | files |

(Sin builders. Es trabajo de PM puro.)

## Surface impactada

| Tipo | Path | Cambio |
|---|---|---|
| Doc | `docs/pm-nico/opportunities/outbound-conversational.md` | nuevo |
| Doc | `docs/pm-nico/opportunities/source-aware-treatment.md` | nuevo |
| Doc | `docs/pm-nico/opportunities/email-drip-mailerlite.md` | nuevo |
| Doc | `docs/pm-nico/opportunities/event-campaign-orchestration.md` | nuevo |
| Doc | `docs/pm-nico/opportunities/retargeting-meta-ads.md` | nuevo |
| Doc | `docs/pm-nico/opportunities/tiktok-dm-automation.md` | nuevo |
| Doc | `docs/pm-nico/research/2026-04-29-campaigns-foundation-synthesis.md` | nuevo |
| Doc | `docs/pm-nico/current-state/campaigns.md` | update |
| Doc | `docs/pm-nico/roadmap.md` | update (PI-2/PI-3 placeholders) |
| Doc | `docs/pm-nico/INDEX.md` | update (link opportunities/) |

## Tests requeridos

N/A — docs only.

## Aceptación

- [x] 6 opportunities/{slug}.md creados con caveman style consistente
- [x] research/2026-04-29-campaigns-foundation-synthesis.md creado (síntesis comprimida)
- [x] current-state/campaigns.md actualizado con input completo
- [x] roadmap.md actualizado con PI-2/PI-3 placeholders en Next/Later
- [x] INDEX.md menciona opportunities/ como subfolder
- [x] Sin orfandad: cada opportunity vive en opportunities/, cada research en research/

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Compresión pierde matiz | Linkea archivo legacy original en cada opportunity para fallback |
| `docs/pm/campaigns/` queda inconsistente con pm-nico → drift | Sprint 0 cierre: decisión sobre archivar/borrar legacy |
