# PR-{N}-{slug}

> Template. Copy a `sprints/S{N}-*/prs/PR-N-{slug}.md`.

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

## Problema (user-facing)

{1-2 líneas. JTBD si aplica.}

## Outcome esperado

{Qué cambia para el user. Métrica si medible.}

## Walking skeleton (mínimo viable)

{Lo más chico que entrega valor. No agregar features.}

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A | ... | ... | ELEGIDA |
| B | ... | ... | descartada porque... |

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

| Fase | Agente/skill | Entregable esperado |
|---|---|---|
| Pre-design | `nicolify-architect` | CONTRACT.md |
| Implementation | `nicolify-backend` | code + tests |
| UX | `ux-flow-architect` | FLOW-SPEC.md (si aplica) |
| Audit | `nicolify-backend-auditor` | REVIEW.md |

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| Tabla DB | ... | nueva / alter |
| API endpoint | ... | nuevo / modificado |
| Domain type | ... | nuevo / modificado |
| FE component | ... | nuevo / modificado |

## Tests requeridos (TDD)

- `tests/.../test_*.py` — qué cubre

## Aceptación

- [ ] Tests verdes
- [ ] Lint/type check verdes
- [ ] Docs `current-state/{module}.md` actualizado
- [ ] Decisiones registradas en `decisions.md` PI
- [ ] Handoff a sprint siguiente actualizado (si aplica)

## Riesgos

| Riesgo | Mitigación |
|---|---|
| ... | ... |
