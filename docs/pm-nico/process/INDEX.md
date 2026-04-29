# Proceso PM-Nico

> Cómo trabajamos PIs, sprints, PRs, handoffs. Owner: `/pm`. Append-only learnings.

## Mapa

| Archivo | Propósito |
|---|---|
| [sprint-template.md](sprint-template.md) | Template `sprint.md` por sprint (objetivo + plan + learnings + handoff) |
| [pr-template.md](pr-template.md) | Template `PR-N-{slug}.md` por PR (problema + solución + checklist + agentes) |
| [handoff-template.md](handoff-template.md) | Template entre sprints / entre PR-PM y agente builder |
| [agent-routing-matrix.md](agent-routing-matrix.md) | Qué agente/skill cargar según tipo de trabajo |
| [process-learnings.md](process-learnings.md) | Append-only. Learnings sesión-a-sesión. PM mejora con cada PI. |

## Estructura PI

```
pis/PI-N-{theme}/
  PI.md                ← visión + sprint plan + decisiones macro
  decisions.md         ← ADR append-only
  retro.md             ← cierre PI
  sprints/
    S0-foundation/     ← un folder por sprint
      sprint.md        ← desde sprint-template.md
      learnings.md     ← append durante sprint, congela al cerrar
      handoff.md       ← lo que sprint siguiente necesita
      prs/
        PR-0-research-migration.md
        PR-1-outbox-global.md
        PR-2-idempotency.md
    S1-domain-repos/
      sprint.md
      prs/
    ...
```

## Reglas

1. **Cada sprint tiene su `sprint.md`.** Self-contained: alguien debe poder cargar solo ese folder y entender qué hacer.
2. **Cada PR tiene su `PR-N-{slug}.md`.** Define problema, solución, agentes/skills a cargar, copilot-first, decisiones diferidas.
3. **Aprendizaje sprint-by-sprint.** Cierre sprint = `learnings.md` congelado + `handoff.md` para siguiente.
4. **Handoff explícito.** PM declara qué agentes/skills cargar para próximo sprint, qué decisiones quedaron, qué surface (APIs/types) cambió.
5. **PM agnóstico al builder.** PM no escribe código. Solo decide quién lo escribe (`agent-routing-matrix.md`).

## Anchor

- Inicio sprint nuevo → copy `sprint-template.md` → llenar.
- Cierre sprint → `learnings.md` congela + `handoff.md` empaqueta para siguiente.
- Cualquier mejora al proceso descubierta → `process-learnings.md`.
- PM update SKILL.md cuando learnings consolidados se vuelven regla.
