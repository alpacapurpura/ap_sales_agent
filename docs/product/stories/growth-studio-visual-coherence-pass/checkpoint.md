---
story_id: growth-studio-visual-coherence-pass
outcome: growth-copilot-layout-unification
state: parked
phase: PM_DRAFT
last_artifact: checkpoint.md
last_modified: 2026-05-06T22:54:54Z
next_action: "Esperar shipping de stories 1 (sidebar-copilot-decoupling) + 2 (growth-architectural-parity). Si post-shipping queda inconsistencia visual detectable cross-studio → unparkear → /po-ux refina. Probable que NO se ejecute (Chris 2026-05-06: 'visualmente si se ve bien')."
ratified_by_chris: false
spawned_at: 2026-05-06T22:54:54Z
spawned_by: /po (sesión refining outcome unification 2026-05-06)
parallel_safe: true
blocked_reason: "Depende de stories 1+2 shipped + audit visual posterior que detecte gap real. Mantenida parked para no inflar WIP refining."
audit_iterations: 0
hotfix_metadata:
  repro_verified: false
  repro_command: null
  diagnosis_validates_handoff: null
---

# Story scope (placeholder condicional)

**Tipo:** ui-story (UI polish post-shipping de las otras 2 stories)
**Skill spec:** `/po-ux` (si se desparkea)
**Module primario:** `analytics` (FE: `frontend/src/features/growth-studio/`)

## Cuándo se ejecuta esta story

SOLO si después del shipping de:
- `app-shell-sidebar-copilot-decoupling` (story 1)
- `growth-studio-architectural-parity` (story 2)

…queda detectable inconsistencia visual cross-studio (cards/spacing/
typography/interaction) que requiera pasada explícita de polish.

Probable que NO se ejecute. Chris (2026-05-06):
> "visualmente si se ve bien y lo que no es negociable es la vista del
>  bowtie de los botones del panel con metricas, eso esta bien"

## Trigger para desparkear

Trigger explícito de Chris o auditor post-shipping:
- "Veo que tal componente growth se siente distinto a brand"
- Audit visual cross-studio falla (axe-core o screenshot diff threshold)

Si trigger ocurre → `/pm` cambia state `parked` → `refining` y pasa a
`/po-ux` para refinement.

## Bitácora

- 2026-05-06 22:54 — `/po` (sesión refining unification) creó folder + checkpoint.md (state=parked). Story conservada como placeholder para audit trail del outcome.

## Notas

- `state: parked` (no `refining`) intencional — evita ocupar slot WIP refining (cap ≤ 3)
- Si las primeras 2 stories ship sin gap visual → esta story se transitiona a `dropped` con `superseded_reason: "no visual gap detected post-stories 1+2 shipping"`
