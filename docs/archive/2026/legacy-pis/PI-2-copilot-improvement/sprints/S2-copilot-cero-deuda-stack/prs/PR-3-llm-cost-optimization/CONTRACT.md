# PR-3-llm-cost-optimization — CONTRACT

> Architect-empowered (PM main thread escribe — architect agent truncó). ZERO open questions. Builders ejecutan sin volver a PM excepto findings escalate scope.

## Meta

| Campo | Valor |
|---|---|
| Fecha | 2026-04-30 |
| Owner | nicolify-architect (PM main thread takeover post agent truncation) |
| Trigger | Research `docs/pm-nico/research/2026-04-30-llm-landscape-chinese-models.md` veredicto migración parcial agresiva |

## Discovery code real (verificado pre-CONTRACT)

| Componente | Path | Estado |
|---|---|---|
| Tier→Model SSoT | `backend/src/modules/copilot/domain/model_tier.py` | 4 tiers: NANO=`gpt-5.4-nano` ($0.20/$1.25), MINI=`gpt-5.4-mini` ($0.75/$4.50), REASONING=`o4-mini` ($1.10/$4.40), HEAVY=`o3` ($2.00/$8.00) |
| Routing policy | `backend/src/modules/copilot/domain/routing_policy.py` | rules → tier mapping |
| Model router | `backend/src/modules/copilot/application/router/model_router.py` | itera classifiers |
| LLM classifier | `backend/src/modules/copilot/application/router/classifiers/llm_classifier.py` | usa `llm.invoke(messages)` sync (LangChain ChatModel injected) — **NO LLMProvider abstraction** |
| Summarizer | `backend/src/modules/copilot/application/memory/rolling_summarizer.py` | usa `LLMProvider.complete(tier=ModelTier.NANO, ...)` async |
| Title generator | `backend/src/modules/copilot/application/memory/title_generator.py` | usa `LLMProvider` mismo patrón |
| LLMProvider port | `backend/src/modules/copilot/domain/ports.py` | Protocol |
| Implementación LLMProvider | NO encontrada en `src/` (probablemente en infra layer factory wired en main.py o DI container) | verificar builder al implementar |

**Veredicto research aplicado a stack real:**
- NANO `gpt-5.4-nano` ($0.20/$1.25) → DeepSeek V4-Flash ($0.14/$0.28) → **30% cheaper input, 4.5x cheaper output**
- MINI `gpt-5.4-mini` ($0.75/$4.50) → DeepSeek V4-Flash ($0.14/$0.28) → **5x cheaper input, 16x cheaper output**
- REASONING `o4-mini` ($1.10/$4.40) → mantener (defer S3 — eval gate calidad reasoning crítico)
- HEAVY `o3` ($2.00/$8.00) → mantener (defer S3 — eval gate calidad agentic crítico)

PR-3 scope: NANO + MINI tiers swap. Classifier (NANO) + Summarizer (NANO) + cualquier otro consumer NANO/MINI son hot paths de PR-3.

## Decisions (D-1..D-15, justificadas)

### D-1: Override TIER_METADATA via env-flag config layer (NO modificar enum)
**Veredicto:** Add new module `backend/src/modules/copilot/infrastructure/llm/model_config.py` con función `get_tier_metadata(tier: ModelTier) -> TierMetadata` que:
- Lee env flag `COPILOT_TIER_<TIER>_MODEL_NAME` (e.g., `COPILOT_TIER_NANO_MODEL_NAME`)
- Si env override presente → retorna TierMetadata override (model_name + pricing override)
- Else → fallback a `TIER_METADATA[tier]` static (preserva default OpenAI)
- Cached en module-level dict (lazy init, idempotente)

**Razón:** cero riesgo modificar enum SSoT. Env override = rollback instant. Cero refactor downstream consumers que importan `TIER_METADATA[ModelTier.NANO]` direct (pueden migrar individualmente al getter).

**Trade-off:** dos paths (TIER_METADATA static + getter) coexisten transitoriamente. Cero deuda futura: post eval-gate-PASS S3+, getter es default + TIER_METADATA queda como fallback config.

**Alternativa descartada:** mutate TIER_METADATA at import time → riesgo testing, mocking complicado.

### D-2: NEW DeepSeek V4-Flash provider adapter (OpenAI-compatible API)
**Veredicto:** crear `backend/src/modules/copilot/infrastructure/llm/providers/deepseek.py` con clase `DeepSeekLLMProvider` que implementa `LLMProvider` Protocol. Usa OpenAI Python client con `base_url="https://api.deepseek.com/v1"` + `api_key=settings.DEEPSEEK_API_KEY`.

**Razón:** DeepSeek expone OpenAI-compatible API directo (Together/Fireworks adicional layer no necesaria para clase Pro production usage). Provider directo = lower latency + mismo SDK.

**Trade-off:** Vendor lock-in DeepSeek directo. Mitigación: adapter pattern significa swap futuro a Fireworks/Together = un solo archivo nuevo.

### D-3: Eval gate framework — package layout
**Veredicto:**
```
backend/src/modules/copilot/evals/
├── __init__.py
├── golden_dataset.py       # JSONL loader + pydantic schema
├── runner.py               # CLI + harness
├── scorers/
│   ├── __init__.py
│   ├── base.py             # Protocol Scorer
│   ├── classifier.py       # exact match category scorer
│   └── summarizer.py       # ROUGE-L + cosine similarity scorer
└── goldens/
    ├── classifier/
    │   ├── nano_routing.jsonl       # 50 ejemplos
    │   └── adversarial.jsonl        # 10 ejemplos (subset of 50)
    └── summarizer/
        ├── conversation_compress.jsonl  # 50 ejemplos
        └── adversarial.jsonl            # 10 ejemplos (subset of 50)

backend/tests/evals/
├── test_classifier_eval_gate.py    # marker @eval_gate
└── test_summarizer_eval_gate.py    # marker @eval_gate
```

**Razón:** evals package separado de application/infrastructure (cross-cutting). Goldens versionados en repo (small text files OK <100KB total).

### D-4: Goldens dataset — schema + cobertura
**Veredicto JSONL schema:**
```python
# Classifier golden:
{"id": "cls-001", "input_route": "/brand-studio", "input_user_msg": "Hola", "input_mode": "chat", "input_available_tool_count": 12, "expected_tier": "nano", "category": "greeting", "notes": "..."}

# Summarizer golden:
{"id": "sum-001", "previous_summary": "...", "displaced_messages": [{"role": "user", "content": "..."}, ...], "max_chars": 400, "reference_summary": "...", "category": "casual_chat", "notes": "..."}
```

**Cobertura classifier 50:**
- Categoría `greeting` × 8 (NANO)
- Categoría `simple_edit` × 8 (MINI)
- Categoría `analysis` × 8 (REASONING)
- Categoría `audit_full` × 8 (HEAVY)
- Categoría `clarify_short` × 8 (NANO)
- Adversarial × 10 (boundary cases entre tiers)

**Cobertura summarizer 50:**
- Categoría `casual_chat` × 8
- Categoría `extraction_intent` × 8
- Categoría `tool_invocation` × 8
- Categoría `multi_module_decision` × 8
- Categoría `objection_handling` × 8
- Adversarial × 10 (long conversations + ambiguous)

### D-5: Scoring functions
**Classifier scorer:**
- Exact match: `predicted_tier == expected_tier` → 1.0 else 0.0
- Aggregate score = mean across N goldens
- Threshold pass: ≥0.95

**Summarizer scorer:**
- ROUGE-L F-score reference vs predicted (rouge_score lib)
- Cosine similarity sentence embeddings (sentence-transformers MiniLM lib si available, else word-overlap fallback)
- Composite score = 0.6 × rouge_l + 0.4 × cosine
- Aggregate = mean across N goldens
- Threshold pass: ≥0.85 (summarizer tolera más variabilidad — output natural-language, no categórico)

### D-6: Env flags + fallback chain
| Env flag | Default | Notes |
|---|---|---|
| `COPILOT_TIER_NANO_MODEL_NAME` | (unset → fallback `gpt-5.4-nano`) | post eval gate PASS: set `deepseek-v4-flash` |
| `COPILOT_TIER_NANO_PRICE_INPUT_PER_1M` | (unset → fallback static $0.20) | set `0.14` |
| `COPILOT_TIER_NANO_PRICE_OUTPUT_PER_1M` | (unset → fallback static $1.25) | set `0.28` |
| `COPILOT_TIER_NANO_CONTEXT_WINDOW_TOKENS` | (unset → fallback static 1_000_000) | set `1000000` |
| `COPILOT_TIER_NANO_PROVIDER` | (unset → fallback `openai`) | set `deepseek` — used by DI factory para selecionar provider |
| `COPILOT_TIER_MINI_MODEL_NAME` | (unset → fallback `gpt-5.4-mini`) | post eval gate PASS: set `deepseek-v4-flash` |
| `COPILOT_TIER_MINI_PROVIDER` | (unset → `openai`) | set `deepseek` |
| Same set for MINI pricing | ... | same pattern |
| `DEEPSEEK_API_KEY` | required if `*_PROVIDER=deepseek` | runtime ValueError if missing |

**Fallback chain runtime:**
- Provider factory: `get_llm_provider_for_tier(tier) -> LLMProvider`
  - Reads `COPILOT_TIER_<TIER>_PROVIDER` env
  - If `deepseek` → returns `DeepSeekLLMProvider` instance
  - Else → returns `OpenAILLMProvider` instance (existing)
- Si DeepSeek API call raise (timeout, 5xx, 429) → single retry → si retry falla → log + fallback a OpenAI provider for same tier (ONE TIME per call, no recursive)

### D-7: Wire summarizer + title_generator (via LLMProvider injection — NO code change required)
**Veredicto:** `RollingSummarizer` y `TitleGenerator` reciben `LLMProvider` injected. PR-3 cambio = factory que inyecta provider correcto según `COPILOT_TIER_NANO_PROVIDER` env. Componentes consumers SIN cambios.

**Razón:** clean abstraction port already existe. Cero deuda introduced.

### D-8: Wire classifier (LLMClassifier — usa `llm.invoke()` sync)
**Veredicto:** `LLMClassifier` recibe `llm` injected (LangChain ChatModel). PR-3 modifica el factory que construye este `llm` para que cuando `COPILOT_TIER_NANO_PROVIDER=deepseek`, el ChatModel sea `langchain_openai.ChatOpenAI(base_url=DeepSeek API, api_key=DEEPSEEK_API_KEY, model=COPILOT_TIER_NANO_MODEL_NAME)`. LangChain soporta OpenAI-compatible endpoints sin cambio interface.

**Razón:** mismo patrón factory. LLMClassifier sin cambios — solo el factory upstream.

### D-9: Migration `model_pricing_snapshot` add DeepSeek V4-Flash
**Veredicto:** migration alembic `XXX_pricing_deepseek_v4_flash.py` con raw SQL idempotente:
```python
op.execute("""
    INSERT INTO model_pricing_snapshot (model_id, provider, price_input_per_1m, price_output_per_1m, price_cached_input_per_1m, context_window_tokens, supports_caching, is_reasoning, snapshot_date)
    VALUES ('deepseek-v4-flash', 'deepseek', 0.14, 0.28, NULL, 1000000, FALSE, FALSE, CURRENT_DATE)
    ON CONFLICT (model_id, snapshot_date) DO NOTHING
""")
```

**Razón:** tabla `model_pricing_snapshot` ya existe (rule `copilot-observability.md`). PR-3 solo añade row nueva. Idempotente.

### D-10: NO TOCAR sales_agent (verificación arch test)
**Veredicto:** PR-3 NO importa nada de `src.modules.sales_agent.*`. Verificación arch test agregada: `test_pr3_no_sales_agent_imports.py` que falla si encuentra import. Sales_agent tiene su propia ruta cost optimization (rule `sales-agent-brand-voice.md` + voice fidelity grader pendiente Q3 2026).

### D-11: NO TOCAR specialist (REASONING + HEAVY tiers) — defer S3
**Veredicto:** PR-3 modifica solo NANO + MINI tier behavior. REASONING (o4-mini) + HEAVY (o3) intactos. Eval gate calidad agentic crítico requiere set goldens >100 + comparación blind = scope S3.

### D-12: Performance budget
- **Classifier endpoint p99 <300ms**: TTFT DeepSeek V4-Flash 1.03s + clasificación tolera relax vs <200ms hot path. Acepta si TTFT real-prod < spec. Si rompe → fallback a OpenAI gpt-5.4-nano via env flag.
- **Summarizer p99 <500ms**: compression task tolera latencia. 1M context elimina chunking overhead.

### D-13: Rollback plan instant
1. Identifico regresión (latency SLO breach OR calidad eval failure post-deploy):
   - Latency: queries `copilot_llm_call WHERE model_id='deepseek-v4-flash' GROUP BY HISTOGRAM(duration_ms)`
   - Calidad: re-run eval gates contra dataset post-deploy actual
2. Rollback: `unset COPILOT_TIER_NANO_PROVIDER COPILOT_TIER_NANO_MODEL_NAME COPILOT_TIER_MINI_PROVIDER COPILOT_TIER_MINI_MODEL_NAME` en env prod (un solo deploy revert config)
3. Validation: queries `copilot_llm_call.model_id = 'gpt-5.4-nano'` reanudado

**Razón:** env-flag-driven = no code revert needed. Operational rollback < 5 min.

### D-14: Observability — leveraged existing
**Veredicto:** `copilot_llm_call` table ya rastrea `model_id` per call (rule `copilot-observability.md`). Cost calculation per-turn via `model_pricing_snapshot` join. PR-3 NO requiere schema change observability.

**Validación post-deploy queries (ad-hoc — no dashboard nuevo PR-3):**
- Cost reduction: `SELECT model_id, SUM(input_tokens * price_input_per_1m / 1e6 + output_tokens * price_output_per_1m / 1e6) AS cost_usd FROM copilot_llm_call JOIN model_pricing_snapshot USING (model_id) WHERE created_at > NOW() - INTERVAL '7 days' GROUP BY model_id`
- Latency comparison: `SELECT model_id, percentile_cont(0.99) WITHIN GROUP (ORDER BY duration_ms) FROM copilot_llm_call WHERE created_at > NOW() - INTERVAL '7 days' GROUP BY model_id`

### D-15: Anchor + ratchets
**Veredicto:**
- Anchor cap actual 36/37 — bumpear si necesario nuevo anchor `[COPILOT-LLM-PROVIDER-ABSTRACTION]` o `[COPILOT-EVAL-GATE-FRAMEWORK]` (decidí: SOLO crear si referencia cross-file >3, sino comment inline)
- Ratchet `copilot→módulo` 22 frozen — PR-3 NO importa cross-module nada (solo internal copilot + core/config + alembic)

## Surface esperada (lista cerrada)

### Files NUEVOS
| Path | Líneas estimadas | Notas |
|---|---|---|
| `backend/src/modules/copilot/infrastructure/llm/__init__.py` | 5 | package init |
| `backend/src/modules/copilot/infrastructure/llm/model_config.py` | ~80 | env override layer |
| `backend/src/modules/copilot/infrastructure/llm/providers/__init__.py` | 5 | |
| `backend/src/modules/copilot/infrastructure/llm/providers/deepseek.py` | ~150 | LLMProvider impl |
| `backend/src/modules/copilot/infrastructure/llm/provider_factory.py` | ~60 | factory get_llm_provider_for_tier + fallback chain |
| `backend/src/modules/copilot/evals/__init__.py` | 5 | |
| `backend/src/modules/copilot/evals/golden_dataset.py` | ~80 | JSONL loader + Pydantic schema |
| `backend/src/modules/copilot/evals/runner.py` | ~120 | CLI + harness |
| `backend/src/modules/copilot/evals/scorers/__init__.py` | 5 | |
| `backend/src/modules/copilot/evals/scorers/base.py` | ~30 | Protocol |
| `backend/src/modules/copilot/evals/scorers/classifier.py` | ~50 | exact match |
| `backend/src/modules/copilot/evals/scorers/summarizer.py` | ~70 | ROUGE-L + cosine |
| `backend/src/modules/copilot/evals/goldens/classifier/nano_routing.jsonl` | 50 lines | 50 ejemplos |
| `backend/src/modules/copilot/evals/goldens/classifier/adversarial.jsonl` | 10 lines | subset adversarial |
| `backend/src/modules/copilot/evals/goldens/summarizer/conversation_compress.jsonl` | 50 lines | 50 ejemplos |
| `backend/src/modules/copilot/evals/goldens/summarizer/adversarial.jsonl` | 10 lines | adversarial |
| `backend/alembic/versions/<timestamp>_pricing_deepseek_v4_flash.py` | ~25 | migration idempotente |
| `backend/tests/modules/copilot/infrastructure/llm/test_model_config.py` | ~120 | env override + fallback + missing API key |
| `backend/tests/modules/copilot/infrastructure/llm/test_deepseek_provider.py` | ~150 | happy + retry + timeout + auth fail + 429 |
| `backend/tests/modules/copilot/infrastructure/llm/test_provider_factory.py` | ~80 | factory + fallback chain |
| `backend/tests/modules/copilot/evals/test_runner.py` | ~100 | CLI parses args + executes scorers + exit code |
| `backend/tests/modules/copilot/evals/scorers/test_classifier_scorer.py` | ~50 | exact match |
| `backend/tests/modules/copilot/evals/scorers/test_summarizer_scorer.py` | ~70 | ROUGE-L + cosine |
| `backend/tests/evals/test_classifier_eval_gate.py` | ~50 | marker @eval_gate, threshold ≥0.95 |
| `backend/tests/evals/test_summarizer_eval_gate.py` | ~50 | marker @eval_gate, threshold ≥0.85 |
| `backend/tests/architecture/test_pr3_no_sales_agent_imports.py` | ~30 | guard arch test |

### Files MODIFICADOS
| Path | Cambio |
|---|---|
| `backend/.env.example` | append `COPILOT_TIER_NANO_PROVIDER=`, `COPILOT_TIER_MINI_PROVIDER=`, `DEEPSEEK_API_KEY=`, `COPILOT_TIER_NANO_MODEL_NAME=`, `COPILOT_TIER_NANO_PRICE_INPUT_PER_1M=`, `COPILOT_TIER_NANO_PRICE_OUTPUT_PER_1M=`, etc. (with comments explicando defaults) |
| `backend/src/core/config.py` (settings) | add Settings field `DEEPSEEK_API_KEY: str | None = None` + `COPILOT_TIER_<...>` overrides |
| LLMProvider factory upstream (path TBD durante implementación) | add provider routing por tier |

### Files NO TOCAR
- `backend/src/modules/copilot/domain/model_tier.py` (D-1 — env override, NO mutate enum)
- `backend/src/modules/copilot/application/router/classifiers/llm_classifier.py` (D-8 — solo el factory upstream cambia, no la clase)
- `backend/src/modules/copilot/application/memory/rolling_summarizer.py` (D-7 — solo factory injection cambia)
- `backend/src/modules/copilot/application/memory/title_generator.py` (D-7 — mismo)
- `backend/src/modules/sales_agent/**` (D-10 — ZERO touch)

## Tests obligatorios (lista cerrada — RED→GREEN TDD)

| # | Test file | Tests | Foco |
|---|---|---|---|
| T-1 | `test_model_config.py` | 5 | env unset → static fallback; env override → returns override TierMetadata; partial override (model_name set, pricing not) → mix; cached idempotent; missing required env (DEEPSEEK_API_KEY when provider=deepseek) → ValueError |
| T-2 | `test_deepseek_provider.py` | 6 | happy stream complete; non-stream complete; 429 retry; 5xx retry then fail; timeout fallback signal; auth 401 → raise immediately |
| T-3 | `test_provider_factory.py` | 4 | provider=openai → OpenAILLMProvider; provider=deepseek → DeepSeekLLMProvider; deepseek raise → fallback openai (single retry); fallback exhausted → raise |
| T-4 | `test_runner.py` (evals) | 5 | CLI parses --use, --baseline, --candidate, --threshold; runs scorer per golden; aggregates score; exit 0 if pass, 1 if fail; output JSON report |
| T-5 | `test_classifier_scorer.py` | 3 | exact match 1.0; mismatch 0.0; aggregate mean correct |
| T-6 | `test_summarizer_scorer.py` | 3 | high ROUGE-L → score >0.8; low ROUGE-L → score <0.5; cosine + rouge composite weight 0.6/0.4 |
| T-7 | `test_classifier_eval_gate.py` | 1 | marker @eval_gate — runs runner CLI sub-process, asserts exit 0 (≥0.95 threshold) |
| T-8 | `test_summarizer_eval_gate.py` | 1 | marker @eval_gate — same pattern, threshold ≥0.85 |
| T-9 | `test_pr3_no_sales_agent_imports.py` | 1 | grep src/modules/copilot/{infrastructure/llm,evals}/ no import sales_agent |

**Total: ~29 tests new**, todos verde antes commit.

## Coordinación PR-1 + PR-2

- PR-3 NO toca `copilot/api/suggestions*` (PR-1 territory)
- PR-3 NO toca `copilot/application/suggestions/`, `copilot/application/tools/offer_section_tools.py`, `shared/links/ports/{brand,sales_agent}.py` (PR-2 territory)
- PR-3 NO toca `frontend/` (cero FE work)
- Cero overlap filesystem. Mergeable cualquier orden.

## Performance budget

- **Classifier**: p99 inferencia <2s end-to-end (TTFT 1.03s DeepSeek V4-Flash + token gen 200ms). ChatComposer NO bloquea UX (classifier es async pre-routing decision).
- **Summarizer**: p99 <3s (rolling summary corre async out-of-band — NO bloquea response user-facing).
- **Eval gate runner**: completes 50 goldens en <5min (parallelizable async client calls).

## Rollback plan instant
- Env flag swap: `unset COPILOT_TIER_<NANO|MINI>_PROVIDER` + restart pods → instant revert
- Validation: `SELECT DISTINCT model_id FROM copilot_llm_call WHERE created_at > NOW() - INTERVAL '5 minutes'` debe retornar solo `gpt-5.4-*` post rollback

## Out of scope CONTRACT
- Specialist (REASONING + HEAVY tiers) → S3+
- Embeddings → S3 o PI dedicado (Qwen3-Embedding-8B re-index Qdrant ventana mantenimiento)
- Sales_agent voice → Q3 2026
- LLM-as-judge eval scoring → defer si exact match + ROUGE no alcanza
- Dashboard observability nuevo → ad-hoc queries OK PR-3
- Goldens dataset >50 each → 50 mínimo cumple criterio cero deuda; expandir si métricas adopción justifican

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| DeepSeek V4-Flash falla eval gate calidad (<95% classifier or <85% summarizer) | Eval gate CI bloquea merge. Architect alternativa: GLM-5 Reasoning (96 MMLU, 99 HumanEval) — pero costo $1/$2.08 vs DeepSeek $0.14/$0.28 → solo si DeepSeek falla calidad gate |
| TTFT 1.03s rompe SLO classifier hot path | Architect verifica TTFT real-prod first; si rompe, set fallback Claude Haiku 4.5 vía env (mantener actual gpt-5.4-nano TTFT mejor) |
| DeepSeek API outage prod | Fallback chain automatic factory layer (D-6) → OpenAI provider single retry |
| Goldens dataset insuficientes/sesgo | 50 mínimo + categorías cobertura explícitas D-4 + adversarial 10 each. Architect agrega goldens como tests RED first ANTES código provider — verifica eval funciona ANTES migración |
| Cost snapshot mal calculado pricing | Pricing snapshot table tracking + manual verify primer turno post-deploy via query D-14 |

---

**ZERO open questions.** Builder ejecuta TDD RED→GREEN siguiendo D-1..D-15 + tests obligatorios T-1..T-9. ESCALATE PM si encuentra:
- LLMProvider factory NO existe en path esperado (verificar `find backend/src -name "*.py" | xargs grep "OpenAILLMProvider\|class.*Provider.*LLMProvider"`)
- Settings layer no permite override env-flag dinámico (probable Pydantic Settings funciona OK)
- Eval gate corre >10min en CI (probable async parallelism resuelve)

<!-- @pm: CONTRACT.md ready (architect-empowered, PM main thread takeover post agent truncation, 15 decisions). -->
