# TP7 — Marketing KB RAG (F10 + F11.5)

**F# que valida:** F10 (`MarketingKbStore` + `nicolify_marketing_kb` collection + `knowledge_search` tool + 31 docs curados) + F11.5 (`weekly_copilot_rag_eval` cron).
**Tiempo estimado:** 1-2 hs.
**Pre-req hard:** TP0 + Qdrant collection seedeada (`nicolify_marketing_kb` con ≥31 docs).

---

## Misión

Confirmar que:

1. Los 8 RAG goldens (F10) recuperan correctamente del KB curado real (no stub).
2. `knowledge_search` tool emite output con methodology label citable.
3. Citation_accuracy + answer_groundedness ≥4.0 (judge multi-dim).
4. Latencia search ≤500ms p50.
5. Cross-tenant: misma query → mismos resultados (KB es tenant-agnóstico).
6. Manual run de `weekly_copilot_rag_eval` produce row en `copilot_workflow_metric._rag_eval`.
7. Admin `/marketing-kb` muestra stats + permite search QA.

---

## Research mandate

Queries:

- `"qdrant collection size optimization 2026 dense vector"` — confirmar 31 docs no requiere reranker.
- `"contextual chunking RAG retrieval recall 2026 benchmarks"` — validar breadcrumb-prefix sigue siendo effective.
- `"text-embedding-3-large openai 2026 pricing dimension"` — confirmar 3072 dim sigue siendo el default + costos embedding.

---

## Scenarios

### S7.1 — Re-correr 8 RAG goldens contra KB real

Run el test runner F10/F11.5 EN MODO REAL (no stub):

```bash
cd backend && RUN_LLM_JUDGE=1 .venv/bin/pytest tests/quality/golden/test_rag_retrieval.py -v -o addopts=""
```

**Pass:** 8/8 con `passes_threshold=True` + `retrieval_recall=1.0` (chunk expected aparece top-5).

### S7.2 — Recall por golden con KB real (no stub)

Bypassing `_StubStore`, usar `MarketingKbStore` real:

```python
from src.modules.copilot.infrastructure.qdrant.marketing_kb_store import MarketingKbStore
store = MarketingKbStore()
for golden in RAG_GOLDENS:
    chunks = store.search(golden.question, limit=5)
    sources = [c.get('source_doc') for c in chunks]
    recall = 1.0 if golden.expected_source_doc in sources else 0.0
    print(f"{golden.id}: recall={recall} sources={sources}")
```

**Pass:** ≥7/8 con recall=1.0 (1 falso negativo aceptable bajo dense-only retrieval). Si <7/8 → considerar reranker.

### S7.3 — Latencia search per golden

10 queries variadas. Medir:

```sql
SELECT name, AVG(duration_ms), PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms)
FROM copilot_trace_event
WHERE event_type='tool_call' AND name='knowledge_search'
GROUP BY name;
```

**Pass:** p50 ≤500ms, p95 ≤1500ms.

### S7.4 — Cross-tenant determinism

Mismo query desde 2 tenants distintos:
```
Tenant A: "explícame StoryBrand"
Tenant B: "explícame StoryBrand"
```

**Pass:** mismos chunks devueltos (KB es global). Confirmar via `chunk.id` en ambos traces.

### S7.5 — Citation accuracy via judge

Para los 8 RAG goldens, capturar respuesta sintetizada por copilot (no excerpt esperado, respuesta REAL del agent en producción modo). Correr CopilotJudge con dim `citation_accuracy`:

```python
judge = CopilotJudge(dimensions=("citation_accuracy",))
```

**Pass:** avg ≥4.0/5.

### S7.6 — Manual run weekly_copilot_rag_eval

```bash
docker exec visionarias_brain_dev .venv/bin/python -c "
from src.shared.workers.copilot_rag_eval import run_weekly_rag_eval
from src.core.database import SessionLocal
db = SessionLocal()
n = run_weekly_rag_eval(db)
print(f'rows written: {n}')
"
```

```sql
SELECT period_start, judge_avg_score, jsonb_pretty(extra_metadata) FROM copilot_workflow_metric
WHERE workflow_id='_rag_eval' ORDER BY period_start DESC LIMIT 1;
```

**Pass:** 1 row con extra_metadata complete (golden_count, retrieval_recall_avg, kb_citations, judge_dimensions, per_golden_recall).

### S7.7 — Admin `/marketing-kb` smoke

Browser to `http://localhost:8502/marketing-kb`:
- Tab "Overview" muestra stats (≥31 chunks).
- Tab "Search QA" permite tipear query y devolver chunks.
- Tab "Upload manual" disponible (sin testear upload real, solo render).
- Tab "Reseed canónico" disponible.

**Pass:** 4 tabs render sin 500.

### S7.8 — Conversación e2e con citation visible

Browser flow:
- Conv nueva, prompt: `"explícame StoryBrand para mi marca"`.
- Esperar respuesta.
- Verificar respuesta menciona "StoryBrand" + alguna pista de citation (no requiere FE renderer especial, solo que el LLM lo cite en el body).

**Pass:** "StoryBrand" en respuesta + reference al método ("según StoryBrand…").

---

## Tools / queries

- DeepEval + RAG dimensions (TP7 reusa F10 goldens runner).
- Chrome DevTools MCP para S7.7 + S7.8.
- Direct call a `MarketingKbStore.search` para S7.2.

---

## Targets

| Métrica | Target | Hard fail |
|---|---|---|
| RAG goldens pass | 8/8 | <7/8 |
| Recall avg | ≥0.875 (7/8) | <0.75 |
| Search latencia p50 | ≤500ms | >2000ms |
| Citation accuracy avg | ≥4.0 | <3.5 |
| Cross-tenant determinism | OK | divergencia |
| weekly_rag_eval row OK | 1 row con metadata complete | 0 rows o metadata incomplete |
| Admin /marketing-kb 4 tabs | OK | 1+ tabs 500 |

---

## Failure playbook

| Síntoma | Investigar | Root cause | Fix |
|---|---|---|---|
| Recall <0.75 | corpus no seedeado | `marketing_kb_store.stats()` count | `python scripts/seed_nicolify_marketing_kb.py` |
| Cross-tenant divergence | `tenant_id` filter accidental | `MarketingKbStore.search` code review | confirmar arch test `test_store_module_does_not_reference_tenant_id` |
| Search latencia >2s | embedding API slow | OpenAI status + medir `embed_query` | considerar batching o cache embeddings |
| Citation no aparece en respuesta | output prompt no insiste | system_prompt MARKETING_KB_HINT | refinar fragment |
| weekly_rag_eval 0 rows | sentinel tenant_id check | `workflow_metric.tenant_id NOT NULL` | F11.5 implementó UUID(int=0) — verificar |

---

## Lo que necesito de Chris

- [ ] Confirmar Qdrant collection `nicolify_marketing_kb` poblada (`docker exec visionarias_qdrant curl http://localhost:6333/collections/nicolify_marketing_kb`).
- [ ] OpenAI key con quota para embeddings (text-embedding-3-large).
- [ ] Confirmar admin Streamlit corriendo (`docker ps | grep admin`).
