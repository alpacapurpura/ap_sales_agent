# S2-shared-observability — Sprint plan

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S2-shared-observability |
| PI padre | PI-1.1-pi1-post-mortem |
| Inicio | 2026-05-01 |
| Estado | discovery (architect spawning) |

## Objetivo

Cementar `BaseObservabilityContext` shared abstraction lift + Bug #8 FXResolver fix, eliminando mirror duplication anti-pattern detectado en PR-1 hotfix. Primer test del 5-layer anti-duplication enforcement (rules + template + builder gate + auditor Cat 13 + skills warning).

## PRs en sprint

| PR | Scope | Estado |
|---|---|---|
| PR-2-shared-agent-observability | Lift turn_envelope a `shared/agent_observability/recording/` + FXResolver.default() factory + dual concrete subclass copilot/sales_agent + Bug #8 fix + real persistence test sales_agent | discovery → architect spawn |

## Criterio éxito

- ✅ `sales_agent_trace_event` rows > 0 post-Telegram message smoke
- ✅ `copilot_trace_event` count growth normal post-refactor (no regression)
- ✅ Cero `FXResolver()` no-arg instances en codebase (grep test enforced)
- ✅ Cero mirror `turn_envelope.py` per-module
- ✅ CONTRACT.md producido por architect Opus con grep evidence completa
- ✅ REVIEW-agentic.md verdict PASS Cat 13 mirror detection
- ✅ Anti-duplication 5-layer enforcement validated functioning (no slip)

## Hipótesis testeo

H1: anti-duplication rule + 5-layer enforcement previene mirror duplication recurrence.
- Test: builder spawneado debe ejecutar Step 0 grep gate, encontrar copilot turn_envelope existing, NO crear mirror, escalate PM o ejecutar LIFT-TO-SHARED.

H2: shared base + concrete subclass es estructura right-sized para growth (commercial_director PI-6, ManyChat WA, IG DM agentes futuros).
- Test: subclass new agent post-PR-2 debe ser <50 LOC.

## Riesgos sprint

| Riesgo | Mitigación |
|---|---|
| Architect Opus paused mid-CONTRACT (cap caché) | Re-spawn fresh per "Opus paused → resume Opus" rule. CONTRACT en disco preservado |
| Cross-session collision PI-5 PR-2 (copilot WIP) | Architect Step 0.4 verifica overlap. Si overlap → blocker note. Sino → proceed |
| Real DB persistence test flakiness | Marker `pytest -m verify` + skip default si DB no available |
| Refactor copilot envelope rompe 4260 traces existing | Regression test `test_envelope_inheritance.py` antes merge |

## Próximos pasos

1. Spawn `nicolify-architect` Opus con `prompts/01-architect-start.md`
2. Architect produce CONTRACT.md
3. PM revisa CONTRACT.md, valida coordination con PI-5 PR-2
4. Spawn `nicolify-agentic` builder con `prompts/02-builder-agentic.md` (template + Step 0 grep gate)
5. Builder auto-spawnea auditor agentic
6. PM cierra PR + RESULT.md + current-state lineage

## Cross-references

- PR-1 RESULT.md (origen este sprint): `../S1-stabilization/prs/PR-1-pi1-bugs-hotfix/RESULT.md`
- Anti-duplication rule: `.claude/rules/anti-duplication.md`
- Process learning: `docs/pm-nico/process/process-learnings.md` § 2026-05-01
