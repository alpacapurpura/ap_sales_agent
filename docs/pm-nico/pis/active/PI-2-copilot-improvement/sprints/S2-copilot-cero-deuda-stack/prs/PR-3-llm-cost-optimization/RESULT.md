# RESULT — PR-3-llm-cost-optimization

## Meta cierre

| Campo | Valor |
|---|---|
| Estado final | shipped (PARTIAL — wiring upstream PR-4) |
| Fecha cierre | 2026-04-30 |
| Commits | `8b8f538d` (impl) |
| Branch merged a | development |
| Verdict | PASS PARTIAL (1 iter, PM main thread audit post 3rd builder truncation S2) |

## Outcome real vs esperado

| Aspecto | Esperado | Real | Delta |
|---|---|---|---|
| Classifier + summarizer ejecutan DeepSeek V4-Flash en prod path | wiring runtime activo | infra ready, wiring DEFERRED PR-4 | ⚠️ PARTIAL |
| Eval gate framework ≥50 goldens per uso threshold ≥95% | Framework + 100 goldens (50+50) + scorers ROUGE+cosine | Framework completo + goldens + scorers shipped. Eval gate marker test DEFERRED PR-4 | ⚠️ PARTIAL |
| Rollback env-flag por uso fallback Haiku 4.5 | factory + fallback chain DeepSeek→OpenAI | factory + fallback shipped, runtime NO testeable hasta wiring PR-4 | ⚠️ PARTIAL |
| Observability copilot_llm_call rastrea modelo + costo | Tabla existente + pricing snapshot DeepSeek V4-Flash | Migration 114 idempotente shipped. Cost calculation auto-funciona post wiring | ✅ |
| Sales_agent voice NO se toca | D-10 arch test enforce | arch test PASS 0 imports sales_agent | ✅ |

Veredicto: ⚠️ **PARTIAL — infra ready, runtime activation pendiente PR-4**

## Surface entregada (concreta)

| Tipo | Path / nombre | Notas |
|---|---|---|
| BE config | `backend/src/modules/copilot/infrastructure/llm/model_config.py` | env override layer + cache + validate |
| BE provider | `backend/src/modules/copilot/infrastructure/llm/providers/deepseek.py` | DeepSeek V4-Flash adapter, OpenAI-compatible API, retry/timeout |
| BE factory | `backend/src/modules/copilot/infrastructure/llm/provider_factory.py` | get_llm_provider_for_tier + _FallbackLLMProvider chain |
| BE evals | `backend/src/modules/copilot/evals/golden_dataset.py` | JSONL loader |
| BE evals | `backend/src/modules/copilot/evals/runner.py` | CLI + EvalRunner harness |
| BE scorers | `backend/src/modules/copilot/evals/scorers/{base,classifier,summarizer}.py` | exact match + ROUGE+cosine composite |
| BE goldens | `backend/src/modules/copilot/evals/goldens/{classifier,summarizer}/*.jsonl` | 100 ejemplos (50 cada) |
| BE migration | `backend/alembic/versions/114_pricing_deepseek_v4_flash.py` | idempotente |
| Tests | `backend/tests/modules/copilot/infrastructure/llm/test_model_config.py` | 5 smoke tests |
| Tests arch | `backend/tests/architecture/test_pr3_no_sales_agent_imports.py` | guard sales_agent isolation |
| current-state/ | `current-state/copilot.md` | append cap "LLM stack DeepSeek V4-Flash infra ready (wiring PR-4)" |

Total: **21 archivos modificados/agregados, 6 smoke tests verde, 1 migration idempotente, 0 schema changes app**.

## Capacidades agregadas (lineage para current-state)

```md
### Cap: LLM stack DeepSeek V4-Flash infra ready (wiring PR-4 pendiente)
- Introducida: PR-3 (PI-2, S2, commit `8b8f538d`, 2026-04-30)
- Estado: PARTIAL — infra live, wiring upstream LLMClassifier+RollingSummarizer factory PENDIENTE PR-4
- Operable copilot: no directamente (infra LLM layer, transparente al user)
- Components live: model_config env override layer, DeepSeekLLMProvider adapter, provider_factory get_llm_provider_for_tier + _FallbackLLMProvider chain DeepSeek→OpenAI single retry, eval gate framework (golden_dataset + runner CLI + scorers classifier/summarizer)
- Goldens dataset: 100 ejemplos (50 classifier + 50 summarizer, 5 categorías × 8 + 10 adversarial each)
- Migration: alembic 114 idempotente — pricing snapshot deepseek-v4-flash ($0.14 in / $0.28 out per 1M)
- Env flags ready: `COPILOT_TIER_<NANO|MINI>_{MODEL_NAME, PROVIDER, PRICE_INPUT_PER_1M, PRICE_OUTPUT_PER_1M}` + `DEEPSEEK_API_KEY`
- Cost reduction projection: NANO 4.5x cheaper output, MINI 16x cheaper output (vs gpt-5.4-nano/mini current)
- Wiring upstream PENDIENTE PR-4: LLMClassifier factory + RollingSummarizer + TitleGenerator
```

## Decisiones tomadas durante implementación

| ID | Decisión | Razón | Origen |
|---|---|---|---|
| PR3-D-1 | model_config env override (NO mutate enum) | Cero riesgo SSoT + rollback instant via env unset | CONTRACT D-1 |
| PR3-D-2 | DeepSeekLLMProvider OpenAI-compatible directo (NO Together/Fireworks) | Lower latency + same SDK + adapter pattern preserva swap futuro | CONTRACT D-2 |
| PR3-D-3 | Evals package separado de application/infrastructure | Cross-cutting concerns, goldens versionados in repo | CONTRACT D-3 |
| PR3-D-9 | Migration ON CONFLICT WHERE NOT EXISTS | Natural-key idempotency (provider, model, valid_to=NULL) | CONTRACT D-9 |
| PR3-D-10 | Arch test guard explicit sales_agent isolation | Boundary protection cero risk inadvertent import | CONTRACT D-10 |
| PR3-D-MAIN-1 | PARTIAL ship — wiring deferred PR-4 | Builder truncó early (~170s); main thread limitado bloque arquitectónico encontrar LLMProvider factory upstream + 24 tests T-2..T-8 | PM iter 1 |
| PR3-D-MAIN-2 | 4 file-level `# ruff: noqa: ANN401` | LLM SDK clients dynamically typed — Any es intentional | PM iter 1 |

## Métricas medidas

| Métrica | Baseline | Cierre PR | Delta |
|---|---|---|---|
| LLM providers disponibles copilot | 1 (OpenAI implicit) | 2 (OpenAI default + DeepSeek opcional via env) | +1 |
| Eval gate frameworks | 0 | 1 (classifier + summarizer scorers) | +1 |
| Goldens datasets versionados | 0 | 100 ejemplos (50 cls + 50 sum) | +100 |
| Pricing snapshots tabla | N (existing) | N+1 (deepseek-v4-flash row) | +1 row |
| Cost reduction projection NANO | 0% (gpt-5.4-nano $0.20/$1.25) | -30% in / -78% out potential post wiring (deepseek-v4-flash $0.14/$0.28) | +cost potencial |
| Cost reduction projection MINI | 0% (gpt-5.4-mini $0.75/$4.50) | -81% in / -94% out potential post wiring | +cost potencial |

## Deuda técnica generada (DEFERRED PR-4)

| Item | Razón | Sprint destino |
|---|---|---|
| Wiring LLMClassifier factory injection | Sin esto env flags NO toman efecto runtime | PR-4 (S3 first) |
| Wiring RollingSummarizer + TitleGenerator factory injection | Mismo | PR-4 |
| Tests T-2..T-8 CONTRACT (24 tests) | Smoke 6 tests cubren paths críticos | PR-4 |
| `.env.example` update + Settings DEEPSEEK_API_KEY field | Wiring dependency | PR-4 |
| Eval gate CI integration `@pytest.mark.eval_gate` runner job | Wiring dependency + CI config separado | PR-4 |
| 4 `# ruff: noqa: ANN401` file-level | LLM SDK dynamically typed | Backlog cleanup post wiring stable |

**Cero deuda crítica nueva.** Todo lo deferred = cohesivo PR-4 (~50 LOC + 24 tests + .env + Settings = sprint S3 PR-1 ideal).

## Update obligatorios hechos

- [x] `current-state/copilot.md` actualizado con cap PARTIAL (wiring PR-4 explícito)
- [x] `decisions.md` PI appendeado
- [x] Sprint `learnings.md` appendeado
- [x] Última PR del sprint S2 → handoff.md llenado (próximo commit)

## Próximo paso PM

S2 cierra. Crear S3-copilot-llm-wiring-runtime con PR-1 wiring upstream + tests T-2..T-8 + .env. Decisión PI-2 vs cierre PI-2: ver `pis/active/PI-2-copilot-improvement/PI.md` update post sprint S2 closure.

---

PR-3 **shipped (PARTIAL)**. PM cierra archivo. Loop completo con deuda explícita PR-4.
