---
id: pi-11-backend-quality-guardrails
state: building
title: Backend quality guardrails — anti-default-flip + test integrity
why_now: |
  Failed /pase-produccion 2026-05-04 detectó 25 BE failures + 2 FE failures
  + polluter no identificable post 3h investigación. Causa raíz: default flip
  USE_OUTBOX_PATTERN_* sin auditar tests path viejo. Sin guardrails, cada
  futuro deploy replica un % de este costo (~500k tokens, ~3h sesión).
target_end: null
priority: 1
created: 2026-05-04
last_modified: 2026-05-05
migrated_from: docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/
story_ids: []
success_metrics:
  - "0 BE failures, 0 FE failures con pytest+vitest sin flags especiales"
  - "Polluter snapshot test fixed at source (sin band-aid @flaky permanente)"
  - "Singletons class-level documentados + reseteados (autouse fixture exhaustivo)"
  - "Tests legacy EventBus mocks 100% migrados a adapter_bus / outbox table inspection"
  - "Arch fitness test_no_legacy_eventbus_mock_when_outbox_on bloqueador"
tags:
  - type:hardening
  - type:transversal
  - blocking:deploy
---

# Backend quality guardrails

PI hardening transversal: restaurar CI verde permanentemente + prevenir
recurrencia de la causa raíz arquitectural detectada en failed
`/pase-produccion` 2026-05-04 (default flip USE_OUTBOX_PATTERN_* sin auditar
tests path viejo).

## Migration note
This outcome was migrated from legacy paradigm (`docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/`)
on 2026-05-05 as part of Wave 2 PM redesign. Full original content archived at
`docs/archive/2026/legacy-pis/PI-11-backend-quality-guardrails/`.

Estado en migración:
- S1 PR-1 (fix-broken-tests-and-arch-snapshots): shipped (RESULT.md)
- S1 PR-3 (anti-default-flip-enforcement): shipped (RESULT.md, commit `463ecc87`)
- S1 PR-4 (update-agents-skills-default-flip-audit): shipped (RESULT.md,
  commits `4b832e34` + `7553ae80` + `a33061e1` + `1539ee81`)
- S1 PR-2 (coverage-p0-modules): partial — commit `6a352df2 test(pi-11): add
  P0 coverage tests for crm + scheduling` mergeado pero sin RESULT.md formal.
  Pendiente cierre formal sprint.
- S2 (coverage P1 + shared contracts): no iniciado.

## Original content summary

Outcome esperado (post-S1):
| Outcome | Métrica |
|---|---|
| 0 BE/FE failures | pytest/vitest sin flags especiales |
| Polluter snapshot test fixed at source | Sin band-aid @flaky final |
| Singletons class-level reseteados | Autouse fixture exhaustivo en conftest.py |
| Tests legacy EventBus migrados | 100% a adapter_bus o outbox table inspection |
| Snapshot helpers outbox-aware | Captura domain_events real |
| Arch fitness bloqueador | test_no_legacy_eventbus_mock_when_outbox_on.py |

Decisiones cardinales (per archived PI):
- D1: Outbox `USE_OUTBOX_PATTERN_*` queda True permanente (escala 1000 clientes)
- D2: Tests migran a `adapter_bus` mock o outbox table probe (path nuevo es prod path)
- D3: `LegacyEventBus.publish` runtime warning + deprecation gradual
- D4: Polluter hunt sin band-aid @pytest.mark.flaky final
- D5-D7: Architect Opus 1 ejecución cubre PR-1+PR-3; PR-4 = PM directo

Defense-in-depth 7 layers cementados (per S1 learnings PR-4):
1. PM PR.md template "Default flips audited"
2. Architect CONTRACT.md § 9.5 Tests audit obligatorio
3. Builder Step 0.5 grep + migration strategy + run both values
4. Auditor Cat 12 (backend) / Cat 14 (agentic)
5. Arch fitness test bloqueador
6. TDD rule sección Default flag flips
7. Runtime DeprecationWarning

Pendiente: cierre formal S1 (PR-2 RESULT.md + handoff S2). Eventual S2
coverage P1 (sales_agent/copilot ≥80%) + shared/links/ports tests.
