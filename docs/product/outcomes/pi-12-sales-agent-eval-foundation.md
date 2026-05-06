---
id: pi-12-sales-agent-eval-foundation
state: refining
title: Sales Agent — eval foundation (pass^k + voice fidelity + cost accuracy)
why_now: |
  6 agentic stories sales_agent declaradas sin pass^k tracking, sin voice fidelity
  grader runs reales, sin goldens dataset checked-in. Bloqueo: cada PR a sales_agent
  llega a producción con "puede que rompa la voz tenant" o "puede que cueste más"
  ansiedad. Necesitamos CI gate automático que bloquee regressions.
target_end: null
priority: 1
created: 2026-05-04
last_modified: 2026-05-06
migrated_from: docs/projects/active/PI-12-sales-agent-eval-foundation/
story_ids:
  # done (archived 2026-05-06):
  - sales-agent-eval-runner-foundation
  - sales-agent-litellm-canonicalization
  # refining (state=refining, awaiting spec ratification):
  - sales-agent-eval-cost-budget-cap
  - sales-agent-eval-pass-k-tracking
  - sales-agent-goldens-3-tenants-dataset
  - sales-agent-personas-instrumented-runtime
  - sales-agent-voice-fidelity-grader-runtime
  - sales-agent-voice-fidelity-ci-gate
  - sales-agent-adversarial-jailbreak-suite
success_metrics:
  - "Cada PR a modules/sales_agent/ se gradea automáticamente vs voice fidelity, no-hallucination, tool trajectory, pass^3 >= 0.5, cost <= budget"
  - "0% trials con cost_usd=0 en provider=deepseek (post fix)"
  - "Voice fidelity score >= 0.7 enforced en CI gate. Falla → PR bloqueado"
  - "12+ goldens checked-in en backend/tests/agentic_evals/sales_agent/"
tags:
  - module:sales-agent
  - type:agentic-eval-foundation
legacy_exempt: true  # WIP cap exempt — pre-paradigma v4 (2026-05-06)
---

# Sales Agent — Eval Foundation (PI-12 migrado a paradigma v4)

> **Migrated 2026-05-06** desde `docs/projects/active/PI-12-sales-agent-eval-foundation/` (paradigma legacy PI/Sprint) a paradigma v4 (Punto 4 pm-redesign). Stories ya hechas archivadas. Stories pendientes movidas a `docs/product/stories/{id}/` flat con `state=refining`.

## Vision

Cada PR a `modules/sales_agent/` se gradea automáticamente:
- Voice fidelity per tenant (rubric `voice-fidelity.md` threshold 0.7)
- No-hallucination, no-overpromise rubrics en scenarios adversarial
- Tool trajectory correcta (closer specialist sequence)
- Pass^3 >= 0.5 para promotion capability→regression
- Cost <= budget per session sin cost tracking degraded

Resultado: confianza para deployar cambios sales_agent sin "puede que rompa la voz tenant" o "puede que cueste más" ansiedad. CI gate bloquea regressions.

## Objetivos (3 — ratificados Chris 2026-05-04)

1. **Eval suite operacional** — `backend/tests/agentic_evals/sales_agent/` con runner + 12+ goldens checked-in + pass^k tracking. Métrica: 6 agentic stories sales_agent con `test_coverage.eval_suite_path != null` + `pass_k_last_run >= 0.5`.

2. **Voice fidelity grader en CI** — gate automático en `/test-backend` o pre-merge. Rubric `voice-fidelity.md` corre contra goldens runtime. Métrica: `voice_fidelity_score >= 0.7` enforced. Falla → PR bloqueado.

3. **Cost tracking accuracy** — deepseek pricing resolver provider mapping fix + budget cap por run. Métrica: 0% trials con `cost_usd=0` cuando provider=deepseek + 0 runs >$5 USD.

## Stories — estado migrado a v4

### ✅ Done (2 — archivadas a docs/archive/2026/stories/)

| Story | Done date | Capability promoción |
|---|---|---|
| `sales-agent-eval-runner-foundation` | 2026-05-06 | sales-conversational-engine (eval suite path establecido) |
| `sales-agent-litellm-canonicalization` | 2026-05-06 | sales-observability-cost-tracking (LiteLLM canonical path) |

### 🔬 Refining (7 — state=refining, requieren spec ratification)

| Story | Type | Estimate | Próximo paso |
|---|---|---|---|
| `sales-agent-eval-cost-budget-cap` | service | 1d | `/po` redacta spec |
| `sales-agent-eval-pass-k-tracking` | service | 2d | `/po` redacta spec |
| `sales-agent-goldens-3-tenants-dataset` | service | 5d | `/po` redacta spec |
| `sales-agent-personas-instrumented-runtime` | agentic | 2d | `/po` + `/ux-agentico` |
| `sales-agent-voice-fidelity-grader-runtime` | agentic | 3d | `/po` + `/ux-agentico` |
| `sales-agent-voice-fidelity-ci-gate` | service | 2d | `/po` redacta spec |
| `sales-agent-adversarial-jailbreak-suite` | agentic | 3d | `/po` + `/ux-agentico` |

**Total restante:** 18d.

## Migration note

Migrado de paradigma legacy PI/Sprint (2026-05-04 → 2026-05-06) a paradigma v4 (10 estados). Razón: cap WIP `refining ≤ 3` excedida por las 7 stories pero `legacy_exempt: true` aplica forward-only enforcement. Spec ratification pendiente story-por-story.

Original PI.md preservado en `docs/archive/2026/legacy-pis/PI-12-sales-agent-eval-foundation/PI.md` (ola 4 archive).

## Bitácora

- 2026-05-04 — `/pm` creó PI-12 paradigma legacy + 9 stories en sprints S1-S4
- 2026-05-06 — Story `sales-agent-eval-runner-foundation` shipped (state=done)
- 2026-05-06 — Story `sales-agent-litellm-canonicalization` shipped (state=done)
- 2026-05-06 — Migración a paradigma v4: outcome creado en `docs/product/outcomes/`, 7 stories pendientes movidas a `docs/product/stories/{id}/` flat con `state=refining`, 2 stories done archivadas, legacy folder eliminado
