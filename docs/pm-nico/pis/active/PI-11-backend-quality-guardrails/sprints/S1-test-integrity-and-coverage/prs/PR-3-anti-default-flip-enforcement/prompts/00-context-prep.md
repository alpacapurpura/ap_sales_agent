# Prompt — Context Prep PR-3 (Haiku)

## Spawn pattern

```
Agent({
  description: "Pre-flight PR-3 anti-default-flip",
  subagent_type: "nicolify-context-builder",
  model: "haiku",
  prompt: <bloque abajo>
})
```

## Prompt body

```
Sos `nicolify-context-builder` (Haiku). Producí CONTEXT-BRIEF.md para PR-3.

<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-3-anti-default-flip-enforcement
<modules>: shared (domain_events), tests/architecture
<phase>: architect (compartido PR-1)

Lectura obligatoria:
1. {pr_folder}/PR.md
2. .claude/rules/anti-duplication.md (estructura inspiración)
3. backend/tests/architecture/ (patrón existing arch fitness)
4. backend/src/shared/domain_events/legacy_event_bus.py (path real validar)
5. backend/src/shared/domain_events/outbox/application/event_bus_adapter.py
6. backend/src/core/config.py (flags USE_OUTBOX_PATTERN_*)

Output: {pr_folder}/CONTEXT-BRIEF.md siguiendo formato 10 secciones (PR summary, contract decisions, current-state, rules, diff, gates, IMPL highlights, faithfulness gaps, raw paths consultados).

Última línea:
<!-- @pm: CONTEXT-BRIEF.md PR-3 ready. -->
```
