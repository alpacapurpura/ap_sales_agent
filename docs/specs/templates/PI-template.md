# PI.md — Template (Project Increment)

> Owner: `/pm`. Vive en `docs/projects/active/PI-N-{theme}/PI.md`.
> Cuando cierra → mover a `docs/projects/archive/`.

---
pi_id: PI-N
theme: SLUG-CORTO
started_at: 2026-05-04
target_end: 2026-06-15
status: planning                                 # planning | active | wrap-up | archived
checkpoint: ./checkpoint.md
links:
  roadmap: "../../../product/roadmap.md"
  vision: "../../../product/vision.md"
---

## Vision para este PI

[1 párrafo: qué cambiará para el usuario al final de este PI. North-star.]

## Objetivos (3 max)

1. **Objetivo 1** — outcome medible. Métrica objetivo + baseline.
2. **Objetivo 2** — ...
3. **Objetivo 3** — ...

## Stories planeadas

| Story ID | Type | Module | Sprint | Status |
|---|---|---|---|---|
| `copilot-brand-audit` | agentic | copilot | S1 | planned |
| `brand-completeness-score` | service | brand | S1 | planned |
| `copilot-brand-audit-button` | ui | copilot | S2 | planned |

## Sprints

| Sprint | Slug | Target weeks | Stories planeadas | Estado |
|---|---|---|---|---|
| S1 | foundation | 1-2 | 2 | planning |
| S2 | ui-integration | 3 | 1 | not-started |
| S3 | rollout | 4-5 | 0 | not-started |

## Decisions log

Ver `decisions.md`.

## Riesgos

| Riesgo | Severidad | Mitigación |
|---|---|---|
| LLM cost spike por agentic-stories | high | Cap por session + tier pricing + cost grader en eval |
| Migration de schema durante uso prod | medium | Feature flag + rollout chunked |

## Stakeholders

- **Product owner:** Chris
- **Discovery / opportunities:** /pm + Chris
- **Implementation:** Claude Code (Opus + Sonnet) + opencode/qwen
- **Audit:** /auditor (Opus)

## Cierre del PI

Criterios de cierre:
- [ ] Todas las stories `live` o explícitamente movidas a próximo PI
- [ ] Capabilities afectadas con status correcto
- [ ] `product/modules/*.md` reflejan realidad post-PI
- [ ] Métricas objetivo alcanzadas (o documentado por qué no)
- [ ] Retrospective en `decisions.md`
- [ ] Mover folder a `archive/`
