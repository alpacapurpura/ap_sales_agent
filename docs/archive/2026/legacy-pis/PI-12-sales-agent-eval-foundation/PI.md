---
pi_id: PI-12
theme: sales-agent-eval-foundation
started_at: 2026-05-04
target_end: 2026-06-08                            # ~5 semanas, 9 stories
status: active                                    # planning | active | wrap-up | archived
checkpoint: ./checkpoint.md
links:
  roadmap: "../../../product/roadmap.md"
  vision: "../../../product/vision.md"
  gap_report_origin: "../../../process/gap-report-2026-05-04-group-c.md"
  module: "../../../product/modules/sales-agent.md"
---

# PI-12 — Sales Agent Eval Foundation

> **Origen:** gap-report-2026-05-04-group-c.md flag CRÍTICO. `backend/tests/agentic_evals/sales_agent/` no existe.
> 6 agentic stories sales_agent declaradas en `product/stories/sales-agent/` sin pass^k tracking, sin voice fidelity grader runs reales, sin goldens dataset checked-in.

## Vision

Al final de PI-12, **cada PR que toca `modules/sales_agent/` se gradea automáticamente** contra:
- Voice fidelity per tenant (rubric `voice-fidelity.md` threshold 0.7)
- No-hallucination, no-overpromise rubrics en scenarios adversarial
- Tool trajectory correcta (closer specialist sequence)
- Pass^3 >= 0.5 para promotion capability→regression
- Cost <= budget per session sin cost tracking degraded

Resultado: confianza para deployar cambios sales_agent sin "puede que rompa la voz tenant" o "puede que cueste más" ansiedad. CI gate bloquea regressions.

## Objetivos (3) — RATIFICADOS Chris 2026-05-04

1. **Eval suite operacional** — `backend/tests/agentic_evals/sales_agent/` con runner + 12+ goldens checked-in + pass^k tracking. Métrica: 6 agentic stories sales_agent con `test_coverage.eval_suite_path != null` + `pass_k_last_run >= 0.5`.

2. **Voice fidelity grader en CI** — gate automático en `/test-backend` o pre-merge. Rubric `voice-fidelity.md` corre contra goldens runtime. Métrica: `voice_fidelity_score >= 0.7` enforced. Falla → PR bloqueado.

3. **Cost tracking accuracy** — deepseek pricing resolver provider mapping fix + budget cap por run. Métrica: 0% trials con `cost_usd=0` cuando provider=deepseek + 0 runs >$5 USD.

## Stories ratificadas (9) — final scope

> Decomposition ratificada Chris 2026-05-04. Cada story <5d. Cost-fix movido a S1 (quick win + reporting confiable desde día 1). Budget cap agregado a S1 (defensa preventiva contra runaway en S2/S4).

| # | Story | Type | Sprint | Estimate | Owner pool |
|---|---|---|---|---|---|
| 1 | `sales-agent-eval-runner-foundation` | service | S1 | 3d | claude-opus (eval infra) |
| 2 | `sales-agent-eval-pass-k-tracking` | service | S1 | 2d | claude-opus |
| 3 | `sales-agent-eval-cost-budget-cap` | service | S1 | 1d | claude-opus |
| 4 | `sales-agent-cost-tracking-deepseek-fix` | service | S1 | 2d | qwen-opencode (BE non-agentic patch) |
| 5 | `sales-agent-goldens-3-tenants-dataset` | service | S2 | 5d | agent-helper (extract candidates) + Chris (curate final 12) |
| 6 | `sales-agent-personas-instrumented-runtime` | agentic | S2 | 2d | claude-opus |
| 7 | `sales-agent-voice-fidelity-grader-runtime` | agentic | S3 | 3d | claude-opus |
| 8 | `sales-agent-voice-fidelity-ci-gate` | service | S3 | 2d | claude-opus |
| 9 | `sales-agent-adversarial-jailbreak-suite` | agentic | S4 | 3d | claude-opus |

**Total estimado:** 23d (~5 semanas con buffer).

## Sprints

| Sprint | Slug | Target weeks | Stories | Outcome |
|---|---|---|---|---|
| S1 | eval-runner | 1-2 | 4 (~8d) | Runner pytest + pass^k + budget cap operacional + cost tracking accurate |
| S2 | goldens-personas | 3 | 2 (~7d) | 12 goldens × 3 tenants checked-in + 5 personas instrumentadas en CI |
| S3 | voice-fidelity-gate | 4 | 2 (~5d) | Voice fidelity grader runtime + CI gate enforced |
| S4 | adversarial | 5 | 1 (~3d) | Adversarial scenarios (jailbreak/injection/overpromise) instrumentados |

## Stakeholders

- **Product owner:** Chris
- **Discovery:** /pm + Chris (rubrics tuning, golden curation)
- **Implementation:**
  - Eval infra → claude-opus (Opus 4.7 obligatorio para agentic-stories)
  - Pricing fix → qwen-opencode (BE non-agentic, simple patch)
  - Goldens curation → agent-helper extract + Chris ratifica
- **Audit:** /auditor → spawna `auditor-agentic` (eval), `auditor-backend` (pricing fix)

## Riesgos

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Goldens dataset curation lenta (requiere data real tenants) | high | Híbrido: agent extrae candidatos via `sales_agent_session` reales + `sanitize_payload`, Chris elige 12 finales. Story 5 explícita. |
| Voice fidelity grader nondeterministic (LLM judge) | high | Calibrate vs experto humano cada 50 goldens. Threshold 0.7 NO 1.0. Documentar variance esperada. |
| Cost p95 eval suite alta (12 goldens × 3 trials × 5 personas = 180 LLM calls/run) | medium | Story 3 budget cap $5/run hard guard. Run nightly, no en cada PR. Cache prefix slot 1-5 reuse → costo bajo. |
| Deepseek pricing fix breaks otra cosa | medium | Test con `pricing_snapshot` table snapshots. Verificar 5 modelos provider mappings post-fix. |
| Multi-instancia conflict (otra session toca sales_agent) | medium | M1 protocol — sólo 1 sesión activa en sales_agent durante PI-12. checkpoint.md `parallel_safe: false`. |

## Constraints técnicos

- Eval runner se integra con pytest (no nuevo framework standalone)
- Personas y rubrics existentes (`docs/specs/{personas,rubrics}/`) — NO crear nuevos sin justificar
- Goldens checked-in en `backend/tests/agentic_evals/sales_agent/goldens/` (YAML)
- Voice fidelity threshold env var `SALES_AGENT_VOICE_FIDELITY_THRESHOLD=0.7` ya declarada (Decision 30)
- Budget cap env var `SALES_AGENT_EVAL_BUDGET_CAP_USD=5.0` (Story 3)
- BudgetGuard SA pool wiring respetado en eval (no consume budget tenant real, usa mock budget)
- Trial policy default: trials=3, pass^3 >= 0.5, cost_cap_per_trial=$0.50

## Out of scope (explícito)

- Copilot eval suite (es PI-13, gap report HIGH separado)
- GA4 property picker FE (es story aislada, no PI completo)
- Watch channel renewal alert (es ticket S menor, no agentic eval)
- Adversarial copilot Telegram (PI-13)
- Goldens dataset >5 tenants (scope inicial 3, expand en PI futuro si grader saturate)
- Per-tenant voice fidelity threshold (scope global env var; per-tenant tuning queda futuro)

## Cierre del PI

Criterios:
- [ ] 9 stories audit-passed + merged
- [ ] 6 stories existentes sales-agent en `product/stories/sales-agent/*.yaml` actualizadas con `test_coverage.eval_suite_path` real
- [ ] Capability `sales-conversational-engine` y `sales-outbound-orchestrator` con `eval_suite_status: instrumented`
- [ ] `module sales-agent.md` frontmatter `agentic_eval_suite_path: backend/tests/agentic_evals/sales_agent/` (no null)
- [ ] CI gate enforced (verificable: 1 PR sintético con voice drift > 0.7 → bloqueado)
- [ ] `process/learnings.md` entry con decisiones cardinales (threshold tuning, golden curation strategy, budget cap rationale)
- [ ] Métricas objetivo alcanzadas (pass^3 >= 0.5, cost_usd=0 trials = 0%, runs > $5 USD = 0)
- [ ] Mover folder a `archive/`

## Próximo paso

`/pm` creó scope ratificado + 4 sprints + 9 `00-story.md`. Chris arranca `/po` por Sprint 1 story 1 (`sales-agent-eval-runner-foundation`) para expandir a `01-spec.md` Gherkin.
