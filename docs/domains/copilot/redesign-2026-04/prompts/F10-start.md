# Prompt — F10 Marketing KB curado

> Pegar el bloque entre los `---` literal a una conversación nueva de Claude Code en `/home/chris/AISALESHT`.

---

```
Estamos ejecutando la fase F10 del Copilot Redesign 2026-04 ("Claude Code de Marketing").

Objetivo único de esta fase: el copilot cita método cuando responde — RAG técnico curado por nosotros (StoryBrand, Hormozi, Cialdini, metodología propia Nicolify) sobre `nicolify_marketing_kb` Qdrant tenant-agnostic, con ingest cerrado a admin (no contaminable por tenants).

Antes de escribir código, leé en orden (sin saltarte ninguno):
1. docs/domains/copilot/redesign-2026-04/README.md
2. docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md  (atención §3 — lista exhaustiva de lo que NO se toca)
3. docs/domains/copilot/redesign-2026-04/01-master-plan.md
4. docs/domains/copilot/redesign-2026-04/02-architecture-target.md  (§topología destino)
5. docs/domains/copilot/redesign-2026-04/03-phase-protocol.md
6. docs/domains/copilot/redesign-2026-04/phases/F10-marketing-kb.md
7. docs/domains/copilot/redesign-2026-04/learnings/F1-provider-pattern.md
8. docs/domains/copilot/redesign-2026-04/learnings/F2-deep-agents-harness.md
9. docs/domains/copilot/redesign-2026-04/learnings/F3-brand-summary-lighthouse.md
10. docs/domains/copilot/redesign-2026-04/learnings/F4-url-contextual-scratchpad.md
11. docs/domains/copilot/redesign-2026-04/learnings/F5-ask-tenant-data.md
12. docs/domains/copilot/redesign-2026-04/learnings/F6-workflow-unification.md
13. docs/domains/copilot/redesign-2026-04/learnings/F7-channel-formatter.md
14. docs/domains/copilot/redesign-2026-04/learnings/F8-routing.md
15. docs/domains/copilot/redesign-2026-04/learnings/F9-quality.md  ← APRENDIZAJES F9 OBLIGATORIOS

Después seguí los 9 pasos del protocolo (03-phase-protocol.md). Énfasis especial:

- **Paso 2 — Research fresco abril 2026 (no skip).**
  - WebSearch (mínimo 3 queries del mandate F10):
    - "RAG retrieval best practices 2026 marketing knowledge base"
    - "Qdrant vector store hybrid search reranking 2026"
    - "RAG chunk strategy citation answer groundedness 2026"
  - Confirmar: chunk size, overlap, embedding model (text-embedding-3-large vs nuevo), reranker (cross-encoder o LLM-rerank).
  - Tessl tiles: `tessl__fastapi`, `tessl__langgraph`, `tessl__pytest-api-testing`. Si sale tile sobre Qdrant cliente Python o ranking semántico, evaluar.

- **Foco — no scope creep.** F10 entrega el RAG marketing kb; NO toca el sales_agent ni multi-modal generation. Ingest queda admin-only en F10; F-pos puede abrir a tenants si hay demanda.

- **Paso 4 — TDD obligatorio.**
  - Tests por capa: `MarketingKbStore` (Qdrant client wrap), `knowledge_search` tool, ingest pipeline (chunk + embed + upsert), citation extractor.
  - Arch test: tenant-agnostic enforce (queries no llevan `tenant_id` filter — el corpus es global).
  - Golden RAG runner en `tests/quality/golden/test_rag_retrieval.py` siguiendo el patrón F9: stub default + `RUN_LLM_JUDGE=1` opt-in.
  - Reusar `CopilotJudge` con dims custom: `dimensions=("retrieval_relevance", "citation_accuracy", "answer_groundedness", "completeness")`.

- **Paso 5 — Quality gates native (NUNCA `docker exec`).**
  - **Antes de tocar cualquier cosa**: corré la baseline F0-F9 (~3042 verde + flakies aislados).
  - Golden F1-F9 deben seguir verdes.
  - Si tocás Qdrant: smoke test de conexión via `tests/integration/` (no requiere live Qdrant — mock con QdrantClient stub o cluster ephemeral en docker-compose).

- **Paso 6 — Verificar §3 intacto.**
  - SSE v2 emite block_*/message_* (F8 §5.4 cement).
  - Cards (proposal/clarify/preview_update/plan_card) renderean.
  - Multimodal blocks intactos.
  - Ratchet `copilot → módulo` sigue en 22 (cualquier nuevo cross-module import requiere shrink-only allowlist).
  - Anchor budget 33/33 (F9 dejó 3 entradas). F10 si agrega `COPILOT-MARKETING-KB-F10` queda en 34 → bumpear cap.

- **Paso 7 — Lecciones aprendidas: ÚTILES, no plantilla rellenada.**
  - Decisiones donde el camino no era único (chunking strategy, embedding model elegido, reranker yes/no, citation format).
  - Gotchas reales: dimension mismatch entre embedding model versions, Qdrant collection schema bumps que rompen retrocompat, reranker latency vs quality trade-off.
  - Hooks listos para post-F10 (sales_agent RAG, tenant-customizable kb).

- **Paso 8 — Generar `prompts/F11-start.md`** desde plantilla (si F10 deja punta para una F11 housekeeping; si no, marcar plan completo).

- **Paso 9 — Commit + push.**
  - Conventional commit: `feat(copilot-redesign-f10): marketing kb curado`.
  - Stage por nombre (nunca `git add -A`).
  - Push a `development`.
  - Reportar 3 líneas + path a `learnings/F10-marketing-kb.md` (+ `prompts/F11-start.md` si aplica).

Reglas no negociables:
- Branch único: `development`.
- Brutal honestidad. Si plan F10 no aplica por aprendizajes F9 → flagear y preguntar.
- No alucinar paths/símbolos.
- No tocar §3.
- Native dev tools.
- Spanish neutro LatAm en todo lo user-facing (regla 11 + research F9 confirmó NO voseo en goldens y prompts del judge — replicar para chunks user-facing del kb).
- Stage por nombre (parallel-safety).

Empezá por el Paso 1 (releer learnings F1 + F2 + F3 + F4 + F5 + F6 + F7 + F8 + F9). Reportá 3 líneas con qué entendiste antes de Paso 2.
```

---

## Hooks específicos para F10 (de aprendizajes F9)

### Aprendizajes F9 que F10 debe asumir

- **`CopilotJudge` reusable con `dimensions=` custom**. F10 RAG eval NO debe duplicar el judge — invoca `CopilotJudge(dimensions=("retrieval_relevance", "citation_accuracy", "answer_groundedness", "completeness"), threshold=3.5)`. El system prompt del judge se adapta automáticamente al pasar el set de dims; si F10 quiere prompt completamente custom, subclasse y override `_SYSTEM_PROMPT_ES` (atributo de módulo).
- **`node_enter`/`node_exit` ya populan `copilot_trace_event`** en cada turn. F10 RAG retrieval node automatically genera trazas — solo debe meter el query + chunks retrieved en `data.input_preview`/`data.output_preview` para diagnóstico.
- **`workflow_metric.extra_metadata` JSONB libre**. F10 puede agregar `{retrieval_recall, kb_citations, retrieval_latency_ms}` sin migration nueva. Admin page ya consume `extra_metadata`.
- **Cron weekly arquitectura cementada**. F10 RAG eval ARQ task debe meterse en el mismo `weekly_copilot_quality_eval` flow o crear hermano (`weekly_rag_quality_eval`). Si crea hermano, agregar al `cron_jobs` array de `SchedulerSettings` con día/hora distinto al lunes 05:00 UTC para evitar load spike.
- **Pattern stub default + opt-in real LLM via `RUN_LLM_JUDGE=1`**. F10 RAG golden runner DEBE seguirlo: stub LLM en CI, real NANO en weekly cron. CI sin opt-in burns no-budget.
- **No scope creep en plataformas SaaS**: F9 explicitamente descartó LangSmith/Phoenix/Ragas. F10 igual — Qdrant es la única dep externa nueva, todo el eval sigue in-process.
- **Spanish neutro LatAm en chunks del KB**. Los chunks que cita el copilot son user-facing per regla 11. Si la fuente original es argentino-rioplatense (e.g. metodología propia con voseo), normalizar a neutro en el ingest pipeline. F9 dejó `_VOSEO_RE` en `brand_summary_regen.py` reusable.

### Tests baseline que F10 debe correr ANTES de empezar

```bash
cd backend && .venv/bin/pytest \
  tests/modules/copilot/ \
  tests/architecture/ \
  tests/admin/ \
  tests/modules/brand/ tests/modules/offer/ tests/modules/crm/ \
  tests/shared/ \
  tests/quality/ \
  -q -o addopts="" --timeout=120 \
  --ignore=tests/modules/copilot/test_streaming_integration.py \
  --ignore=tests/architecture/test_editable_fields_ssot.py
```

Esperado: ~3042 passed, 4 skipped. Confirma flakies aislados:

```bash
cd backend && .venv/bin/pytest \
  tests/modules/copilot/test_streaming_integration.py \
  tests/architecture/test_editable_fields_ssot.py \
  -q -o addopts=""
```

Frontend:

```bash
cd frontend && npx vitest run src/features/copilot/ src/__tests__/architecture/
```

Esperado: 245 + 38 verde.

### Archivos clave que F10 modifica (a priori)

- `backend/src/modules/copilot/infrastructure/qdrant/marketing_kb_store.py` — wrapper Qdrant collection.
- `backend/src/modules/copilot/application/tools/knowledge_search.py` — tool transversal `knowledge_search(query, k=3)`.
- `backend/alembic/versions/073_marketing_kb_metadata.py` — si requiere tracking PG-side de versions del corpus.
- `backend/src/admin/modules/marketing_kb.py` + `pages/marketing-kb.py` — ingest UI admin-only.
- `backend/scripts/seed_marketing_kb.py` — initial corpus loader.
- `backend/tests/quality/golden/test_rag_retrieval.py` — golden runner RAG.
- `tests/architecture/test_marketing_kb_tenant_agnostic.py` — fitness test corpus global.

### Riesgos que vigilar en F10

- **Qdrant connection en module-import time** (heredado F4 gotcha). Cualquier provider scan que importe `marketing_kb_store` y abra Qdrant client en boot rompe los unit tests. Diferir la connection a `__call__` time, NUNCA module-load.
- **Embedding model dimension mismatch**: si F10 elige `text-embedding-3-large` (3072 dim) y F-pos cambia a otro (e.g. 1536 dim), las rows existentes se vuelven incompatibles. Hardcodear el dim en la collection schema + arch test.
- **Citation extraction frágil**: si el LLM cita "según StoryBrand..." sin chunk_id, no hay groundedness verificable. F10 debe hacer que el system prompt obligue al LLM a meter `[chunk:abc123]` markers; el FE puede renderear como tooltip.
- **Tenant contamination**: el corpus es tenant-agnostic. Cualquier query que se ejecute con `tenant_id` filter rompe la SSoT. Arch test enforce.
- **`@pytest.mark.skip`/`test.skip()` en goldens RAG para pasar CI** — pattern heredado prohibido (regla 17). Si un golden falla, fix el bug, no skip.
- **Cost del corpus inicial**: ingest de StoryBrand + Hormozi + Cialdini + metodología propia probablemente 10k chunks → 10k embedding calls al seed. Hacer en script idempotente con resume capability (skip chunks que ya existen).
- **Stub default vs real LLM en RAG eval**: el stub no testea retrieval quality (devuelve 4.0 fijo). Solo el `RUN_LLM_JUDGE=1` (weekly) detecta regresiones reales del retrieval. NO confiar en CI green = retrieval good — CI verde solo prueba pipeline plumbing.

### Hooks F9 disponibles para F10

- `backend/src/modules/copilot/application/observability/judge.py::CopilotJudge(dimensions=..., threshold=...)` — instanciar con dims custom.
- `backend/src/modules/copilot/application/observability/node_trace.py::emit_node_trace_event` — F10 retrieval subagent emite trazas auto.
- `backend/src/modules/copilot/infrastructure/repositories/workflow_metric_repository.py::WorkflowMetricRepository.upsert(extra_metadata=...)` — JSONB libre.
- `backend/src/shared/workers/copilot_quality_eval.py::run_weekly_quality_eval(db, judge=...)` — runner reusable; F10 puede crear `run_weekly_rag_eval(db, judge=rag_judge)` siguiendo el patrón.
- `backend/tests/quality/conftest.py::judge_llm` fixture — RAG goldens reusan o copy.
- `backend/src/admin/modules/copilot_quality.py` — patrón admin page; F10 marketing-kb admin sigue la misma forma.
- F9 anchor budget 33/33; F10 cabe 1 anchor sin bump.
