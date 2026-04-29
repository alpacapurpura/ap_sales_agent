# Proceso PM-Nico

> Cómo trabajamos PIs, sprints, PRs, handoffs. Owner: `/pm`. Append-only learnings.

## Mapa

| Archivo | Propósito |
|---|---|
| [sprint-template.md](sprint-template.md) | Template `sprint.md` por sprint (objetivo + plan PRs + criterio éxito) |
| [pr-folder-template/](pr-folder-template/) | Template **carpeta entera** por PR (PR + CONTRACT + UI-SPEC + prompts/* + IMPL-LOG + REVIEW + RESULT) |
| [handoff-template.md](handoff-template.md) | Template entre sprints (decisiones + surface + agentes recomendados) |
| [agent-routing-matrix.md](agent-routing-matrix.md) | Qué agente/skill cargar según tipo de trabajo |
| [parallel-sessions-protocol.md](parallel-sessions-protocol.md) | Reglas M1-M6 sesiones paralelas (KISS, sin worktrees) |
| [process-learnings.md](process-learnings.md) | Append-only. Learnings sesión-a-sesión. PM mejora con cada PI |

## Estructura PI

```
pis/active/PI-{N}-{theme}/
├── PI.md                ← visión + sprint plan + decisiones macro
├── decisions.md         ← ADR append-only
├── retro.md             ← cierre PI (luego folder se mueve a archive/)
└── sprints/
    └── S{N}-{slug}/     ← un folder por sprint
        ├── sprint.md
        ├── learnings.md
        ├── handoff.md
        └── prs/
            └── PR-{n}-{slug}/   ← carpeta auto-contenida (template pr-folder-template/)
                ├── PR.md, CONTRACT.md, UI-SPEC.md, IMPL-LOG.md, REVIEW.md, RESULT.md
                ├── prompts/01-04-*.md
                └── phases/         ← opcional, solo PRs amplios
```

## Lifecycle PI

```
Discovery → active/PI-N/ ← PM trabaja acá
   ↓ (PI cierra: retro.md escrito)
archive/PI-N/ ← read-only, fuente histórica
   ↓
roadmap.md "Done" linkea a archive/PI-N/
```

## Reglas

1. **Cada sprint tiene su `sprint.md`.** Self-contained: alguien debe poder cargar solo ese folder y entender qué hacer.
2. **Cada PR es CARPETA**, no archivo. Template `pr-folder-template/`. Sub-archivos por rol.
3. **Aprendizaje sprint-by-sprint.** Cierre sprint = `learnings.md` congelado + `handoff.md` para siguiente.
4. **Handoff explícito.** PM declara qué agentes/skills cargar para próximo sprint, qué decisiones quedaron, qué surface (APIs/types) cambió.
5. **PM agnóstico al builder.** PM no escribe código. Solo decide quién lo escribe (`agent-routing-matrix.md`) y produce prompts pre-cocidos.
6. **Protocolo `@pm`.** Cada agente builder/UX/auditor termina su última respuesta con comment `<!-- @pm: ... -->` indicando próximo paso.
7. **Sesiones paralelas → `parallel-sessions-protocol.md`** (M1-M6).
8. **Sprint sizing Opus 4.7[1M]:** target 1-3 PRs amplios cohesivos. Cada PR ≈ 3 ejecuciones (architect + builder + auditor).

## Anchor

- Inicio sprint nuevo → copy `sprint-template.md` → llenar.
- Inicio PR nuevo → `cp -r pr-folder-template/` → editar `PR.md` + `prompts/*`.
- Cierre sprint → `learnings.md` congela + `handoff.md` empaqueta para siguiente.
- Cierre PI → `retro.md` + mover folder a `pis/archive/`.
- Cualquier mejora al proceso descubierta → `process-learnings.md`.
- PM update SKILL.md cuando learnings consolidados se vuelven regla.
