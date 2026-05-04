---
pi_id: PI-12
theme: sales-agent-eval-foundation
started_at: 2026-05-04
target_end: 2026-06-08                            # ~5 semanas, 8 stories
status: planning                                  # planning | active | wrap-up | archived
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

## Objetivos (3)

1. **Eval suite operacional** — `backend/tests/agentic_evals/sales_agent/` con runner + 12+ goldens checked-in + pass^k tracking. Métrica: 6 agentic stories sales_agent con `test_coverage.eval_suite_path != null` + `pass_k_last_run >= 0.5`.

2. **Voice fidelity grader en CI** — gate automático en `/test-backend` o pre-merge. Rubric `voice-fidelity.md` corre contra goldens runtime. Métrica: `voice_fidelity_score >= 0.7` enforced. Falla → PR bloqueado.

3. **Cost tracking accuracy** — deepseek pricing resolver provider mapping fix. Métrica: 0% trials con `cost_usd=0` cuando provider=deepseek.

## Stories propuestas (8)

> Decomposition pendiente ratificación Chris. Cada story <5d.

| Story | Type | Sprint | Estimate | Owner |
|---|---|---|---|---|
| `sales-agent-eval-runner-foundation` | service | S1 | 3d | claude-opus (eval infra + python) |
| `sales-agent-eval-pass-k-tracking` | service | S1 | 2d | claude-opus |
| `sales-agent-goldens-3-tenants-dataset` | service | S2 | 5d | claude-opus + Chris (curate goldens) |
| `sales-agent-personas-instrumented-runtime` | agentic | S2 | 2d | claude-opus |
| `sales-agent-voice-fidelity-grader-runtime` | agentic | S3 | 3d | claude-opus |
| `sales-agent-voice-fidelity-ci-gate` | service | S3 | 2d | claude-opus |
| `sales-agent-adversarial-jailbreak-suite` | agentic | S4 | 3d | claude-opus |
| `sales-agent-cost-tracking-deepseek-fix` | service | S4 | 2d | qwen-opencode (BE non-agentic patch) |

**Total estimado:** 22d (~5 semanas con buffer).

## Sprints

| Sprint | Slug | Target weeks | Stories | Outcome |
|---|---|---|---|---|
| S1 | eval-runner | 1 | 2 | Runner pytest + pass^k computation operacional |
| S2 | goldens-personas | 2-3 | 2 | 12 goldens × 3 tenants checked-in + personas en CI |
| S3 | voice-fidelity-gate | 4 | 2 | Voice fidelity rubric runtime + CI gate enforced |
| S4 | adversarial-cost-fix | 5 | 2 | Adversarial scenarios + deepseek pricing fix |

## Stakeholders

- **Product owner:** Chris
- **Discovery:** /pm + Chris (rubrics tuning, golden curation)
- **Implementation:**
  - Eval infra → claude-opus (Opus 4.7 obligatorio para agentic-stories)
  - Pricing fix → qwen-opencode (BE non-agentic, simple patch)
- **Audit:** /auditor → spawna `auditor-agentic` (eval), `auditor-backend` (pricing fix)

## Riesgos

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Goldens dataset curation lenta (requiere data real tenants) | high | Chris cura 3 tenants representativos. Anonymize PII via `sanitize_payload`. |
| Voice fidelity grader nondeterministic (LLM judge) | high | Calibrate vs experto humano cada 50 goldens. Threshold 0.7 NO 1.0. Documentar variance esperada. |
| Cost p95 eval suite alta (3 trials × 12 goldens = 36 LLM calls/run) | medium | Run nightly, no en cada PR. Cache prefix slot 1-5 reuse → costo bajo. Budget cap $5/run. |
| Deepseek pricing fix breaks otra cosa | medium | Test con `pricing_snapshot` table snapshots. Verificar 5 modelos provider mappings post-fix. |
| Multi-instancia conflict (otra session toca sales_agent) | medium | M1 protocol — sólo 1 sesión activa en sales_agent durante PI-12. checkpoint.md `parallel_safe: false`. |

## Constraints técnicos

- Eval runner se integra con pytest (no nuevo framework standalone)
- Personas y rubrics existentes (`docs/specs/{personas,rubrics}/`) — NO crear nuevos sin justificar
- Goldens checked-in en `backend/tests/agentic_evals/sales_agent/goldens/` (JSON o YAML)
- Voice fidelity threshold env var `SALES_AGENT_VOICE_FIDELITY_THRESHOLD=0.7` ya declarada (Decision 30)
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
- [ ] 8 stories audit-passed + merged
- [ ] 6 stories existentes sales-agent en `product/stories/sales-agent/*.yaml` actualizadas con `test_coverage.eval_suite_path` real
- [ ] Capability `sales-conversational-engine` y `sales-outbound-orchestrator` con `eval_suite_status: instrumented`
- [ ] `module sales-agent.md` frontmatter `agentic_eval_suite_path: backend/tests/agentic_evals/sales_agent/` (no null)
- [ ] CI gate enforced (verificable: 1 PR sintético con voice drift > 0.7 → bloqueado)
- [ ] `process/learnings.md` entry con decisiones cardinales (threshold tuning, golden curation strategy)
- [ ] Métricas objetivo alcanzadas (pass^3 >= 0.5, cost_usd=0 trials = 0%)
- [ ] Mover folder a `archive/`

## Próximo paso

`/pm` propone scope. **Chris ratifica:**
- ¿Aprobás los 3 objetivos?
- ¿Aprobás decomposition en 8 stories / 4 sprints?
- ¿Algún ajuste de scope (out-of-scope move o agregar)?
- ¿Querés priorizar diferente (ej. cost-fix primero porque es S, 2d)?

Una vez ratificado → /pm crea `00-story.md` por cada story → hand off /po story-by-story.
