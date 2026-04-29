# PR-{N}-{slug}

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-N-{slug} |
| Sprint padre | S{N}-{slug} |
| PI padre | PI-X-{theme} |
| Estado | discovery \| ready \| in-progress \| review \| shipped |
| Tipo | infra \| feature \| bug \| refactor \| research |
| Esfuerzo | XS \| S \| M \| L |
| Owner PM | /pm |
| Claimed by session | — (cuando in-progress, anotar fecha + módulo trabajo paralelo si aplica) |

## Problema (user-facing)

{1-2 líneas. JTBD si aplica.}

## Outcome esperado

{Qué cambia para el user. Métrica si medible.}

## Walking skeleton (mínimo viable cohesivo)

{Lo más chico que entrega valor cohesivo. Aprovechar Opus 4.7[1M] = scope amplio cuando es cohesivo. NO splittear por miedo al contexto.}

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A | ... | ... | ELEGIDA |
| B | ... | ... | descartada porque... |

## Validación técnica preliminar (Technical Sanity Check)

> PM spawned `Explore` o `nicolify-architect` (read-only) durante discovery. Brief sintético abajo. CONTRACT formal lo escribe architect en su fase.

- Modules afectados: ...
- Blockers conocidos: ...
- Tiempo estimado: ...
- Alternativas técnicas: ...

(skip si scope XS/S sin riesgo arquitectónico)

## Decisiones diferidas (explícitas)

- {Qué NO se resuelve hoy y cuándo se aborda.}

## Out of scope

- ...

## Copilot-first checklist

- [ ] ¿Operable conversacional desde copilot? (default Sí)
- [ ] ¿Qué tools nuevos requiere? (lista)
- [ ] ¿Cards/UI nueva? (lista)
- [ ] Si NO copilot → razón documentada

## Agentes / skills recomendados

(Ver `process/agent-routing-matrix.md`)

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` | `prompts/01-architect-start.md` | `CONTRACT.md` |
| UX (opcional) | `ux-flow-architect` | (PM crea ad-hoc si aplica) | `UI-SPEC.md` + `mockups/` |
| Implementation | `nicolify-{backend\|frontend\|agentic}` | `prompts/02-builder-start.md` | code + tests + `IMPL-LOG.md` |
| Audit | `nicolify-{backend\|frontend}-auditor` | `prompts/03-auditor-start.md` | `REVIEW.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/{m}.md` update |

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| Tabla DB | ... | nueva / alter |
| API endpoint | ... | nuevo / modificado |
| Domain type | ... | nuevo / modificado |
| FE component | ... | nuevo / modificado |
| current-state/ | `current-state/{módulo}.md` | append capability con lineage |

## Tests requeridos (TDD)

- `tests/.../test_*.py` — qué cubre

## Aceptación

- [ ] Tests verdes
- [ ] Lint/type check verdes
- [ ] `IMPL-LOG.md` completo
- [ ] `REVIEW.md` sin findings críticos
- [ ] `RESULT.md` escrito por PM
- [ ] `current-state/{módulo}.md` actualizado con capability lineage
- [ ] Decisiones registradas en `decisions.md` PI

## Riesgos

| Riesgo | Mitigación |
|---|---|
| ... | ... |
