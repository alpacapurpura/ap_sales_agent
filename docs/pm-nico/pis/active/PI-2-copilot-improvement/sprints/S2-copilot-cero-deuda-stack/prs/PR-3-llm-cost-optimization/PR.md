# PR-3-llm-cost-optimization

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-3-llm-cost-optimization |
| Sprint padre | S2-copilot-cero-deuda-stack |
| PI padre | PI-2-copilot-improvement |
| Estado | shipped (PARTIAL — wiring PR-4) |
| Tipo | infra (LLM stack swap + eval gate framework) |
| Esfuerzo | L |
| Owner PM | /pm |
| Claimed by session | 2026-04-30 sesión PI-2 S2 (módulo copilot LLM infra) |
| Cerrado | 2026-04-30 — verdict PASS PARTIAL (PM main thread post 3rd builder truncation, wiring PR-4 explícito) |

## Problema (Chris-facing — costo)

Stack LLM actual copilot consume: classifier `Kimi K2.5` (~$0.60 in / $2.50 out per 1M) + summarizer `Claude Haiku 4.5` ($1 in / $5 out). Research 2026-04-30 (`research/2026-04-30-llm-landscape-chinese-models.md`) identificó **DeepSeek V4-Flash** como ganador absoluto cost/perf para classifier + summarizer:

| Layer | Actual | DeepSeek V4-Flash | Ahorro |
|---|---|---|---|
| Classifier | Kimi K2.5 ~$0.60/$2.50 | $0.14/$0.28 | **4-9x** input/output |
| Summarizer | Haiku 4.5 $1/$5 | $0.14/$0.28 | **7-18x** input/output |

A escala 1000+ tenants, ahorro proyectado significativo. Cero deuda + escala = migración con eval gate ahora.

JTBD Chris: "Como founder pagando LLM bills crecientes con cada tenant nuevo, quiero pagar lo mínimo posible sin perder calidad copilot."

## Outcome esperado

- Classifier + summarizer copilot ejecutan **DeepSeek V4-Flash** en prod path.
- Eval gate framework ≥50 goldens per uso, threshold ≥95% calidad vs incumbente. CI runner que bloquea regresión.
- Rollback env-flag por uso (`COPILOT_CLASSIFIER_MODEL`, `COPILOT_SUMMARIZER_MODEL`) — fallback Claude Haiku 4.5 instant si SLO falla.
- Observability: `copilot_llm_call` rastrea modelo + costo per-turn pre/post (queries dashboard ad-hoc validan ahorro).
- Sales_agent voice **NO se toca** (rule `sales-agent-brand-voice.md` enforce).

Métrica: cost/turn classifier post-deploy debería caer 4-9x; summarizer 7-18x. Validation manual via `copilot_llm_call` queries 7 días post-deploy.

## Walking skeleton (mínimo viable cohesivo)

1. **Eval gate framework** (`backend/src/modules/copilot/evals/`):
   - `golden_dataset.py` — base class con loader JSON
   - `runner.py` — CLI `python -m src.modules.copilot.evals.runner --use=classifier --baseline-model=kimi-k2.5 --candidate-model=deepseek-v4-flash --threshold=0.95`
   - `scorers/` — scorers per uso (classifier exact match category; summarizer ROUGE-L + semantic similarity)
   - `goldens/classifier/*.jsonl` — 50 ejemplos (5 cat × 10 + 10 adversarial)
   - `goldens/summarizer/*.jsonl` — 50 ejemplos (5 cat × 10 + 10 adversarial)
   - Pytest gate: `tests/evals/test_classifier_eval_gate.py` + `test_summarizer_eval_gate.py` (run en CI con marker `@pytest.mark.eval_gate`)
2. **Config layer** (`backend/src/modules/copilot/infrastructure/llm/`):
   - `model_config.py` — env-flag-driven model selection con fallback chain
   - Update `tier_routing.py` o equivalente: classifier→`COPILOT_CLASSIFIER_MODEL` env (default `deepseek-v4-flash`, fallback `claude-haiku-4-5`); summarizer→`COPILOT_SUMMARIZER_MODEL` env
3. **Provider DeepSeek V4-Flash**:
   - Si stack actual usa `litellm` o equivalente, agregar provider config DeepSeek (OpenAI-compatible API).
   - Si stack actual usa providers custom, agregar `DeepSeekProvider` adapter.
   - Pricing snapshot agregado a `model_pricing_snapshot` table (rule `copilot-observability.md`).
4. **Wiring**:
   - `copilot/application/orchestrator/chat.py` o nodes LangGraph: classifier node usa modelo desde `model_config.get_classifier_model()`.
   - Summarizer node mismo patrón.
5. **Validation pre-merge**:
   - Eval gate CI verde: ≥95% pass DeepSeek V4-Flash vs Kimi K2.5 baseline
   - Eval gate CI verde: ≥95% pass DeepSeek V4-Flash vs Haiku 4.5 baseline
   - Latencia p99 medida en eval runner (TTFT + total) — tolerar TTFT 1.03s en classifier (no hot path con SLO <200ms — clasificación tolera)

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A — Migrar classifier + summarizer en mismo PR con eval gate framework | Cero deuda; framework reutilizable PRs futuros (specialist, embeddings); Chris paga 4-18x menos antes que después | PR L; eval gate framework non-trivial | **ELEGIDA** — alineado criterio cero deuda + escala |
| B — Solo eval gate framework PR-3, swap en S3 | Cada PR más chico | Deja ahorro 4-18x en mesa otro sprint; viola "cero deuda" si framework solo no produce valor user | descartada |
| C — Solo swap, sin eval gate | Más rápido | Sin eval gate = riesgo regresión calidad invisible; viola "build-right-once 1000+ tenants" | descartada |
| D — Migrar Kimi K2.5 → K2.6 (mismo provider) en lugar de DeepSeek | Compatibilidad provider; cache-hit $0.16 si flow caché-friendly | 5x más caro que DeepSeek V4-Flash sin ventaja calidad clara classifier; viola criterio costo | descartada |

## Validación técnica preliminar

- **Modules afectados:**
  - BE: `copilot/infrastructure/llm/` (provider config), `copilot/application/orchestrator/chat.py` o nodes LangGraph (wiring), `copilot/observability/` (pricing snapshot), `copilot/evals/` (nuevo dir).
  - **NO tocar:** `sales_agent/**` (rule brand-voice). `copilot/specialist*` (specialist es S3+).
- **Blockers conocidos:**
  - DeepSeek V4-Flash provider availability via OpenAI-compatible API (DeepSeek directo o Together/Fireworks). Architect verifica acceso + selecciona provider.
  - Pricing snapshot agregado debe ser idempotente con `IF NOT EXISTS`.
- **Tiempo estimado:** 1 ejecución architect + 1 ejecución builder con auto-loop (eval gate framework consume mayoría effort).
- **Alternativas técnicas:** GLM-5 Reasoning si DeepSeek V4-Flash falla eval gate — defer architect decide en CONTRACT.

## Decisiones diferidas (explícitas)

- **Specialist (extraction/auto-fill) → DeepSeek V4-Pro o GLM-5 Reasoning**: requiere set goldens >100 + comparación blind; defer S3.
- **Embeddings → Qwen3-Embedding-8B**: requiere re-index Qdrant ventana mantenimiento + rollback plan dedicado; defer S3 o PI dedicado.
- **Sales_agent voice swap**: defer Q3 2026 según rule `sales-agent-brand-voice.md`.

## Out of scope

- Migrar specialist (extraction/auto-fill) — S3+
- Migrar embeddings — S3+ o PI dedicado
- Tocar sales_agent voice — Q3 2026 según rule
- Cambiar tier routing logic — solo cambia model selection, no logic
- LLM-as-judge eval scoring — usar exact match + ROUGE-L simple, defer LLM-as-judge si needed

## Copilot-first checklist

- [x] ¿Operable conversacional desde copilot? — **no** (infra LLM, transparente al user)
- [x] ¿Qué tools nuevos requiere? — ninguno
- [x] ¿Cards/UI nueva? — no
- [x] Si NO copilot → razón documentada — infra layer, mejora cost/escala sin cambiar user surface

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` + `copilot-expert` + `sales-agent-expert` (verify NO touch) | `prompts/01-architect-start.md` | `CONTRACT.md` (provider config, eval gate API, rollback plan, scoring functions) |
| Implementation | `nicolify-backend` + `copilot-expert` | `prompts/02-builder-start.md` | `IMPL-LOG.md` + tests + commit |
| Audit | `nicolify-backend-auditor` (auto-spawn) | `prompts/03-auditor-start.md` | `REVIEW.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/copilot.md` lineage |

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| BE config | `copilot/infrastructure/llm/model_config.py` | nuevo |
| BE provider | `copilot/infrastructure/llm/providers/deepseek.py` | nuevo (si custom adapter) |
| BE orchestrator | `copilot/application/orchestrator/chat.py` o nodes | wire model_config |
| BE evals | `copilot/evals/{golden_dataset.py, runner.py, scorers/, goldens/}` | nuevo (framework completo) |
| BE migration | `alembic/versions/{XXX}_pricing_deepseek_v4_flash.py` | idempotente — agregar pricing snapshot DeepSeek V4-Flash a `model_pricing_snapshot` |
| Tests | `tests/evals/test_classifier_eval_gate.py` + `test_summarizer_eval_gate.py` | nuevos (CI gate marker `eval_gate`) |
| Env | `.env.example` | append `COPILOT_CLASSIFIER_MODEL`, `COPILOT_SUMMARIZER_MODEL`, `COPILOT_CLASSIFIER_FALLBACK`, `COPILOT_SUMMARIZER_FALLBACK`, `DEEPSEEK_API_KEY` |
| current-state/ | `current-state/copilot.md` | append cap "LLM stack DeepSeek V4-Flash classifier+summarizer + eval gate framework" |

## Tests requeridos (TDD)

- `tests/modules/copilot/infrastructure/llm/test_model_config.py`: env flag default + override + fallback chain
- `tests/modules/copilot/infrastructure/llm/test_deepseek_provider.py`: happy path + retry + timeout
- `tests/modules/copilot/evals/test_runner.py`: runner CLI parses args + executes scorers + aggregates score + exit code 0/1 según threshold
- `tests/modules/copilot/evals/scorers/test_classifier_scorer.py`: exact match category
- `tests/modules/copilot/evals/scorers/test_summarizer_scorer.py`: ROUGE-L + semantic similarity threshold
- `tests/evals/test_classifier_eval_gate.py` (CI marker `eval_gate`): DeepSeek V4-Flash ≥95% vs Kimi K2.5 baseline en 50 goldens
- `tests/evals/test_summarizer_eval_gate.py` (CI marker `eval_gate`): DeepSeek V4-Flash ≥95% vs Haiku 4.5 baseline en 50 goldens
- `tests/modules/copilot/test_chat_orchestrator_model_swap.py`: classifier node usa modelo correcto según env
- arch test: NO import sales_agent desde nuevos archivos copilot/llm

## Aceptación

- [ ] Tests verdes (incluido eval gate marker)
- [ ] Lint/type check verdes
- [ ] `IMPL-LOG.md` completo
- [ ] `REVIEW.md` PASS
- [ ] `RESULT.md` escrito por PM
- [ ] `current-state/copilot.md` actualizado con lineage
- [ ] Decisiones registradas en `decisions.md` PI-2
- [ ] Migration `model_pricing_snapshot` aplicada idempotente
- [ ] Verificación manual: dev up + invocar classifier → log `copilot_llm_call.model_id = "deepseek-v4-flash"` + cost reduction visible
- [ ] Verificación rollback: env flag `COPILOT_CLASSIFIER_MODEL=claude-haiku-4-5` → uso Haiku confirmado

## Riesgos

| Riesgo | Mitigación |
|---|---|
| DeepSeek V4-Flash falla eval gate vs incumbente (calidad <95%) | Eval gate CI bloquea merge; fallback Kimi K2.5 actual mantenido. Architect propone GLM-5 Flash si DeepSeek falla. |
| TTFT 1.03s rompe SLO classifier hot path <200ms | Architect verifica TTFT en infra real; si rompe, defer a paths donde TTFT no crítico (classifier asíncrono pre-warm) o fallback Haiku |
| Provider DeepSeek API outage | Fallback automático env flag a Claude Haiku 4.5 (instant rollback) |
| Goldens insuficientes / sesgo | 50 mínimo + cobertura: 5 categorías × 10 + 10 adversarial. Architect propone goldens en CONTRACT. |
| Cost snapshot mal calculado | Pricing snapshot table tracking + manual verify primer turno post-deploy |
| Builder toca sales_agent por error | Prompt explicit "NO TOUCH sales_agent" + arch test gate |
| Sesión paralela PI-1 modifica `copilot/orchestrator/` | Regla M8: leer + extend; PI-1 NO toca orchestrator (módulo distinto campaigns) |
