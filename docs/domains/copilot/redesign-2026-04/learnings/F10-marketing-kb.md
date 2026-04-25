# Learnings — F10 Marketing KB curado

**Fecha cierre:** 2026-04-25 · **Modelo:** Claude Opus 4.7 (1M context) · **Branch:** `development @ <ver git log -1>` (parent `a69f6c67`)

---

## Resumen 3 líneas

- F10 entrega 6 piezas: `MarketingKbStore` (Qdrant `nicolify_marketing_kb` tenant-agnóstica, dim 3072, sin filtro `tenant_id`); `chunk_markdown` breadcrumb-aware (Markdown headers → `(h1, h2, h3, h4)` tuple → embed-time prefix `# h1 > h2 > h3`); tool transversal `knowledge_search(query, domain?, methodology?)` que reemplaza `search_knowledge_base(query, scope)` con output markdown que fuerza citation; endpoints `POST /api/v1/copilot/ingest` + `GET /search` + `DELETE /{id}` retornan **HTTP 410 Gone** con `migration_hint`; admin Streamlit `/marketing-kb` con 4 tabs (overview / search QA / upload manual / reseed canónico); 31 markdown curados en `backend/data/marketing_kb/` cubriendo metodología propia + StoryBrand + Hormozi + Cialdini + AIDA + PAS + JTBD + FAB + 4U + 7 archetypes + 4 objections + 3 cookbooks + 4 funnel/pricing/email/WhatsApp playbooks; golden RAG runner en `tests/quality/golden/test_rag_retrieval.py` (8 conversaciones, stub default + `RUN_LLM_JUDGE=1` opt-in, reusa `CopilotJudge`).
- Decisión no obvia: **clean slate** sobre la collection `copilot_knowledge` legacy en lugar de migrar puntos como sugería el plan F10 §5.1. Razón: los rows existentes con scope `"help"` eran auto-resúmenes per-tenant, NO contenido marketing curado — migrarlos al KB global habría contaminado el corpus tenant-agnóstico que F10 venía a establecer. La collection vieja se queda dangling (low risk) y F-pos cleanup la dropea.
- Hooks listos para F-pos: el patrón `_PROVIDER_CONTRACT_IMPORTS` no requirió extensión (F10 no introdujo nuevos sub-ports en `CopilotProvider` Protocol); F10 sumó **1 anchor** (`COPILOT-MARKETING-KB-F10`) con cap bumped 33 → 36 (margen para 2 housekeeping anchors); ratchet `copilot → módulo` queda en **22 frozen** (`MarketingKbStore` vive enteramente en `copilot/`); `node_enter`/`node_exit` no instrumenta el `knowledge_search` aún (F-pos puede agregar — el tool corre en el ToolNode estándar y aparece en trazas como `tool_call`).

---

## Decisiones clave

| Decisión | Razón | Alternativa descartada |
|---|---|---|
| **Clean slate sobre `copilot_knowledge` legacy.** | Plan F10 §5.1 sugería migrar el scope `"help"`, pero ese scope era auto-resúmenes per-tenant generados por `ingest_product_summary` — datos del tenant, NO material marketing curado. Migrarlos al KB global habría contaminado el corpus tenant-agnóstico desde el día uno. Y los rows del scope `"business"` ya estaban prohibidos en F10 §5.1. | Migrate completo siguiendo el plan literal. Habría reabierto el bug que F10 venía a cerrar. Documentado acá para que F-pos cleanup haga el `DROP COLLECTION copilot_knowledge` cuando se confirme cero usage. |
| **`MarketingKbStore` paralelo, no rename del legacy `CopilotKnowledgeStore`.** | El legacy sigue importado por `tools/knowledge_tools.py` (que ahora delegamos al nuevo) + admin viejo. Hacer un rename en flight habría roto el path legacy hasta que la suite corriera entera. Crear el nuevo en `infrastructure/qdrant/` (directorio nuevo) y dejar el legacy intacto en `infrastructure/knowledge/` mantiene el tree limpio + permite refactor F-pos sin urgencia. | Rename `CopilotKnowledgeStore → MarketingKbStore` in-place. Multiple archivos importadores cambiarían en el mismo commit; cualquier rollback selectivo se vuelve complicado. |
| **Embedding `text-embedding-3-large` con dim full 3072 (no Matryoshka 1536).** | Research abril 2026: 3-large es el modelo OpenAI más performante; Visionarias <50 tenants × ~600 chunks = ~30 MB en Qdrant — storage no es bottleneck. Matryoshka shrinking 1536 ahorraría storage pero con costo de retrieval quality. Mejor maximizar quality + dejar la opción de shrink en F-pos si el catálogo crece. | Matryoshka 1536. Ahorra 50% storage con costo measurable en MTEB recall. F10 no tiene volumen para justificar el trade-off. |
| **`breadcrumb` como `tuple[str, ...]`, no `str` con separador.** | Tuple permite render como prefix (`"# h1 > h2 > h3\n\n"`) en `embed_text()` y como list en payload Qdrant; un string ya unido perdería estructura para queries futuras tipo "todos los chunks bajo h1 = 'Hormozi'". Datatype distinto preserva la información para F-pos sin parsing fragil. | `breadcrumb: str = " > ".join(crumbs)`. Re-parsear con split no es difícil pero rompe la integridad para queries jerárquicas. |
| **Idempotencia via `stable_id()` derivado de `(source_doc, chunk_index, version)`.** | Reseed sin reseed-tracking-table: el chunk con el mismo `(doc, idx, ver)` tiene el mismo UUID y el upsert overwrite. Si el contenido cambia pero la posición no, se pisa solo. Para forzar nuevo id (e.g. cambio de chunking estrategia), bump del `version` en el front-matter. | Persistir reseed-history en una tabla PG. Más infra para una feature donde la idempotencia natural alcanza. |
| **Endpoints legacy → 410 Gone con `migration_hint`, NO 404 ni delete.** | Cualquier frontend tenant cacheado todavía puede tirar `POST /ingest` por días/semanas. 404 deja al user adivinando si el bug es suyo o nuestro. 410 + body explicativo da seal mensaje accionable + permite logging server-side. Borrar las rutas en lugar de marcar Gone genera 404 silencioso. | DELETE de las rutas. El 404 es la peor opción operacional. |
| **`MARKETING_KB_HINT` como prompt fragment cacheable separado, NO injectable via `ContextInjector`.** | F4 ya pasó por esa decisión: inyectar via `ContextInjector` (per-tenant/per-route) es el contrato para layers que dependen del tenant. El KB hint es **universal cross-tenant** (mismo texto para todos): perfecto candidato para slot dedicado en `compose_system_prompt` antes del lighthouse. Inyectar via ContextInjector lo habría contaminado con tenant_id semántica. | `BrandContextInjector`-style provider para el KB. Diluye el contrato. |
| **Marketing KB hint slot 3 (entre TOOLS_HINT y LIGHTHOUSE), NO slot 1.** | F8 §5.2 ordenó cacheable head: identity (universal) → tools_hint (universal). Lighthouse (per-tenant) viene después. Marketing KB hint es universal cross-tenant — natural slot 3, antes del per-tenant lighthouse. Slot 1 lo movería antes de la identity, lo cual no tiene sentido jerárquico. | Slot 1. El orden lógico Identity → Tools → KB → Lighthouse es el menos sorprendente. |
| **Sin reranker (FlashRank cross-encoder) en F10.** | Research abril 2026: reranker mejora recall@1 en ~10% pero suma 100-300ms latency + dependencia operativa (modelo en RAM). F10 corpus es chico (<1000 chunks); top-K=5 con dense cosine alcanza para baseline. F-pos puede agregar reranker si weekly RAG eval muestra `retrieval_relevance` <3.5. Hoy: budget de F10 = retrieval funcional, no reranker tunning. | Cross-encoder reranker desde F10. Latency hit + operational complexity sin baseline que justifique. El legacy `CopilotKnowledgeStore` sí tenía FlashRank pero su recall no estaba medido; copiar sin necesidad es tech debt. |
| **Sin sparse hybrid (BM25) en F10.** | Mismo argumento: corpus chico + queries en español neutro mediano-largo (donde dense embeddings ganan). Sparse hybrid pesa cuando hay términos técnicos rare-vocabulary que el embedder mapea mal. Para "grand slam offer" o "value equation", el dense ya retorna bien. | Hybrid dense + sparse desde F10. Adds complexity sin caso real que lo demande. |
| **Stub default + `RUN_LLM_JUDGE=1` opt-in para RAG goldens.** | Patrón F9 cementado. CI burns no-budget; weekly cron + manual inspection corre real LLM. La diferencia para RAG: el stub valida pipeline (tool wraps el resultado, judge plumb correctamente), real LLM valida groundedness real. CI verde ≠ retrieval bueno; weekly cron es donde se detectan regressions. | Real LLM en CI. Costo recurrente, false flakies por OpenAI updates silenciosos. |

---

## Sorpresas / gotchas (críticos, no triviales)

- **Plan F10 §5.1 vs realidad: tenant data en KB legacy NO debía migrarse.** El plan literal decía "migrate puntos del scope `help`", pero ese scope era auto-resúmenes per-tenant (Brand+Offer+Connections summary), NO marketing curado. Detecté esto leyendo `knowledge_ingestion.py::ingest_product_summary` antes de implementar. F-pos que vuelva sobre el plan original literal sin verificar realidad va a contaminar el KB global. **Lección:** plan F10 fue escrito sin auditoría exhaustiva del estado legacy; F-pos debe validar realidad antes de implementar plan literal.

- **`docstring` con `tenant_id` en `MarketingKbStore` rompió el primer arch test.** El test `test_store_module_does_not_reference_tenant_id` usaba `"tenant_id" not in text` como string-match — pero la docstring del módulo explica precisamente que NO usa `tenant_id`, así que la palabra aparece en docstrings. Solución: AST-based scan que strippea docstrings antes de buscar identifiers + string constants. Cualquier futuro arch test "no mention X" debe usar AST, no string match.

- **Ruff `TC003`/`TC002` en runtime imports.** `from collections.abc import Iterable` + uso solo en type annotations (con `from __future__ import annotations`) → ruff exige moverlo a `if TYPE_CHECKING`. Pasó con `Iterable` en `marketing_kb_store.py` y `contextual_chunker.py`. Aplica a CUALQUIER import que solo aparezca como anotación. Mover a TYPE_CHECKING o agregar usage runtime.

- **`FAST001` rechaza `response_model=` redundante con return type annotation.** Al cerrar los endpoints `/ingest`/`/search`/`/{id}` con `-> GoneResponse`, el `response_model=GoneResponse` se vuelve redundante y ruff lo flagea. Pero el arch test `test_api_contracts` enforces `response_model= OR has_return_type` — return type cubre el contrato PII. **Lección:** NUEVOS endpoints deben usar return type annotation, NO `response_model=` (es duplicación que ruff bloquea).

- **`E501` del `# noqa: ARG001 — kept for parity` rebasó 120 cols.** Comentarios largos en signature + noqa multiplican largo. Solución: parameter `_ = document_id` dentro del body (consume el var, evita ARG001) en lugar de noqa. Patrón replicable cuando un FastAPI handler retiene un path param que NO usa.

- **`golden snapshots` con tool name viejo (`search_knowledge_base`) explotaron al renombrar.** El snapshot `tests/modules/copilot/golden/snapshots/route_tool_selection.json` tenía 13 ocurrencias del nombre viejo. `UPDATE_GOLDEN=1 pytest test_baseline_route_tools.py` regenera. Cualquier fase que rename un tool DEBE update goldens en el mismo commit; el flag `UPDATE_GOLDEN=1` es la herramienta canónica documentada en F6 learnings.

- **Test `test_system_prompt_layout.py` (NO test_system_prompt_order.py — son DOS tests distintos).** F10 actualizó solo `test_system_prompt_order.py` (arch test fitness) inicialmente; el otro test unit `test_system_prompt_layout.py::TestFragmentOrderInvariants::test_cacheable_fragments_match_f8_plan` también necesitaba el bump. Hay un duplicate-snapshot anti-pattern aquí: dos lugares que ranchean el orden del prompt. F-pos puede consolidar si surge.

- **Embedder lazy resolve abre Qdrant client real cuando `MarketingKbStore()` sin args.** El test `test_tool_decorator_invocable` originalmente invocaba el `@tool` decorator con args reales — el `_resolve_store(None)` construía `MarketingKbStore()` y eventualmente abría conexión Qdrant. Pasó por casualidad (el `try/except` en `knowledge_search_impl` atrapó el error y devolvió "No pude consultar"). Solución defensiva: el test ahora monkey-patcha `MarketingKbStore` con factory que retorna stub. **Patrón replicable:** cualquier test E2E del tool wrapper debe stub el store, NO depender del `try/except` para esconder dependencia de red.

- **Test flaky heredado `test_streaming_integration` y `test_editable_fields_ssot` siguen activos.** F10 NO tocó streaming ni editable_fields. Heredado F0-F9. Pattern: standalone PASS, dentro de la suite full FAIL por order-dep con pytest-randomly. Operativa: correr aislado.

- **Anchor budget: bumpé 33 → 36 (no 34).** F9 cerró con 33/33 cap. F10 agrega 1 (`COPILOT-MARKETING-KB-F10`) → mínimo 34. Subí el cap a 36 para dar margen a F-pos housekeeping (2 anchors más posibles para post-mortems del redesign). No hay urgencia en mantener cap apretado.

---

## Recomendaciones accionables para F-pos / housekeeping

1. **Antes de cualquier housekeeping:** correr la suite F0-F10 (~3112 verde, sin contar flakies aislados):
   ```bash
   cd backend && .venv/bin/pytest \
     tests/modules/copilot/ tests/architecture/ tests/admin/ \
     tests/modules/brand/ tests/modules/offer/ tests/modules/crm/ \
     tests/shared/ tests/quality/ tests/scripts/ tests/api/ \
     -q -o addopts="" --timeout=120 \
     --ignore=tests/modules/copilot/test_streaming_integration.py \
     --ignore=tests/architecture/test_editable_fields_ssot.py
   ```
   Flakies aislados (heredados):
   ```bash
   cd backend && .venv/bin/pytest \
     tests/modules/copilot/test_streaming_integration.py \
     tests/architecture/test_editable_fields_ssot.py \
     -q -o addopts=""
   ```

2. **Drop collection `copilot_knowledge` legacy.** Una vez confirmado que ningún path productivo lee de ella (grep producción + admin trazas), F-pos puede correr `qdrant.delete_collection("copilot_knowledge")`. Documentar en commit.

3. **Borrar `infrastructure/knowledge/vector_store.py` + `application/services/knowledge_ingestion.py` legacy.** Hoy quedan en el árbol pero solo `knowledge_tools.py` los reexportaba; F10 ya redirigió `KNOWLEDGE_TOOLS` al nuevo `knowledge_search`. Verificar grep y borrar. Reduce confusión.

4. **Reranker opcional (cross-encoder).** Si weekly RAG eval (`RUN_LLM_JUDGE=1`) muestra `retrieval_relevance` <3.5 con corpus poblado, agregar `flashrank` cross-encoder en `MarketingKbStore.search` post-dense. Patrón: top-K=15 dense → rerank top-5. Latency +100-300ms aceptable si quality se materializa.

5. **Sparse hybrid (BM25) opcional.** Si analytics muestra queries con vocabulario raro/técnico en inglés mezclado con español neutro, considerar sparse via `fastembed.SparseTextEmbedding`. Hoy F10 está dense-only; agregar requiere bumpear el collection schema (vector_config con dense + sparse named vectors).

6. **Re-evaluar `brand_relevance_score` para chunks del KB.** F4 dejó `brand_relevance_score` en `copilot_inspiration` para URLs externos. Aplicar misma idea a chunks del KB curado (qué tan bien matchea con la marca específica del tenant) habilitaría priorizar chunks "más cercanos" al tenant en cada query. Hook: agregar `brand_relevance_score: NUMERIC(3,2)` al payload Qdrant + scoring offline (ARQ task) que se dispara cuando `BrandSummaryRegen` actualiza el resumen.

7. **`ContextualChunker` con LLM-generated context summary.** Anthropic Contextual Retrieval propone un step adicional: para cada chunk, llamar LLM FAST para generar un summary corto del chunk en context del documento. Tunable; F10 NO lo implementó (cost de seed jumps de 10 calls embed → 10 calls embed + 10 calls FAST). F-pos puede agregar como flag `--with-context-summary` en el seeder.

8. **Drop legacy admin module/page si confirmado dead.** `src/admin/modules/knowledge.py` + `src/admin/pages/knowledge.py` ya borrados en F10. Si algún script externo o doc menciona `/admin/knowledge`, redirige a `/admin/marketing-kb`.

9. **Si F-pos introduce nuevo `[COPILOT-*]` anchor**, cabe en cap 36 (F10 dejó 34/36). Más de 2 nuevos requiere bump explícito.

10. **Wire `build_default_router` al orchestrator chat (heredado F8/F9).** Sigue pendiente: el factory está expuesto pero `chat.py::stream_chat` no llama `router.select()`. Sin esto, `copilot_routing_log` queda vacío. F10 NO lo cerró (fuera de scope). Probable F-pos próximo.

11. **Real-LLM RAG eval primer run.** El weekly cron `weekly_copilot_quality_eval` de F9 corre lunes 05:00 UTC sobre los goldens de conversaciones. F10 NO agregó un weekly cron específico para RAG goldens. Si quieres telemetría real de retrieval quality cada lunes, F-pos puede agregar `weekly_rag_eval` task ARQ siguiendo el mismo patrón pero llamando `tests/quality/golden/test_rag_retrieval.py` con `RUN_LLM_JUDGE=1`.

---

## Riesgos abiertos

- **Cost del seed inicial.** 31 docs × ~5-10 chunks × 1 embedding call = ~150-300 OpenAI calls al primer seed. Idempotente, así que reseed no recobra. Pero si F-pos agrega corpus 10x (300+ docs), considerar batch embedding y resume capability concreta (no solo idempotencia). Hoy: el seeder NO tiene checkpoint si crashea midway.

- **Provider scan import side-effects.** `MarketingKbStore` está bien (lazy `_get_client()`), pero `knowledge_search.py` import-time crea `MarketingKbStore()` en `_resolve_store(None)` solo si se invoca el tool. Si futura fase agrega un provider que importa `knowledge_search` y construye el store en module-load, vuelve el bug F4. Patrón: providers/admins que necesiten el store deben construirlo en `__call__` time (function-level), nunca module-level.

- **Sin `chunk_relevance_score` ni `brand_relevance_score` en payload.** El KB es uniforme — todos los chunks pesan igual al ranking. Si un tenant pregunta "cómo armo mi grand slam offer" y el corpus tiene 5 chunks Hormozi de calidad similar, top-K=5 los devuelve todos sin priorizar el más on-brand. F-pos puede agregar offline scoring.

- **Compresión semántica del KB hint en cache prefix.** El hint del system prompt agrega ~150 tokens al cacheable prefix universal. Si F-pos suma más prompt fragments cacheable cross-tenant, el prefix puede crecer arriba de 4KB y degradar latency mínimamente. Hoy es saludable.

- **Spanish neutro en chunks NO está enforced por arch test.** Los 31 docs los escribí en neutro a mano. Si futuro contributor agrega `objection_pricing_v2.md` con voseo argentino, no hay test que lo bloquee. F-pos housekeeping: agregar test `test_marketing_kb_chunks_no_voseo` que aplique `_VOSEO_RE` (heredado F3 brand_summary) sobre cada `.md` de `data/marketing_kb/`.

- **Reranker optional gotcha.** El legacy `CopilotKnowledgeStore` tenía FlashRank pero F10 NO lo migró al nuevo store (decisión consciente: F10 no medir baseline reranker). Si F-pos agrega reranker, el módulo `flashrank` ya está instalado (heredado del legacy) — no requiere `pip install`.

- **Goldens RAG son 8, NO 20.** F9 estableció 20 conversaciones; F10 entregó 8 RAG goldens cubriendo las 7 metodologías core. Sufficient para baseline + permite ruido bajo. Si producción muestra muchos casos edge, expandir a 15-20 sin reescribir infra.

- **`text-embedding-3-large` puede ser deprecated/replaced.** OpenAI puede lanzar 4-large en próximos 6-12 meses. Cuando ocurra, swap requiere: bump `MARKETING_KB_VECTOR_SIZE`, drop+recreate collection, reseed. La idempotencia del seeder ayuda; pero los embeddings viejos quedan inutilizables. Documentar en runbook el procedimiento.

---

## Hooks listos para próximas fases

- `backend/src/modules/copilot/infrastructure/qdrant/marketing_kb_store.py::MarketingKbStore` — wrapper Qdrant lazy. Constructor inject (`client=`, `embedder=`) para tests; lazy en producción. F-pos que necesite búsquedas por otro filtro (`tags`, `language`) extiende `search()` agregando otro `FieldCondition` opcional + el arch test queda igual.

- `backend/src/modules/copilot/application/services/contextual_chunker.py::chunk_markdown` — pure function. F-pos puede llamar con custom `chunk_tokens` / `overlap_tokens` si encuentra que el default 512/100 produce chunks fragmentados.

- `backend/src/modules/copilot/application/tools/knowledge_search.py::knowledge_search_impl` — pure function (sin `@tool` wrapper). Reusable desde código no-LLM (e.g. admin Streamlit, scripts) sin pasar por la signature LangChain.

- `backend/scripts/seed_nicolify_marketing_kb.py::seed(dry_run=, only=, store=)` — runner reusable. F-pos puede llamarlo desde admin Streamlit u otro script (e.g. CI cron post-merge a `data/marketing_kb/`).

- `backend/data/marketing_kb/*.md` — corpus versionado en repo. Agregar nuevo `.md` con front-matter válido + correr seeder lo carga. Si Chris agrega contenido raw, basta `git add` + `python scripts/seed_nicolify_marketing_kb.py --only nuevo.md`.

- `tests/quality/golden/test_rag_retrieval.py::GOLDENS` — frozenset de golden conversations. Agregar `RagGolden(...)` row + auto-corre. Real LLM via `RUN_LLM_JUDGE=1` en weekly cron F-pos.

- `src/admin/modules/marketing_kb.py::render_marketing_kb_page` — admin Streamlit con 4 tabs. F-pos puede agregar tab "Top retrieved chunks" leyendo `copilot_trace_event.data->>'tool_call'` filtrado a `name='knowledge_search'`.

- `src/admin/modules/capability_catalog.py` — actualizado con tab "🚀 Redesign 2026-04" enumerando F0-F10. Documentación viva del plan.

- `_MARKETING_KB_HINT_ES` constant en `graph.py` — el texto del prompt fragment es hard-coded. Para A/B testing de redacción, F-pos puede mover a Jinja template + hot-reload sin tocar `compose_system_prompt`.

- `KbChunk.embed_text()` — separación `payload.content` (lo que devuelve la query) vs `embed_text()` (lo que se vectoriza). F-pos que quiera embeddings con/sin breadcrumb (e.g. para A/B test de retrieval quality) puede swap el método sin cambiar el payload.

---

## Fuentes research útiles

- [Document Chunking for RAG: 9 Strategies Tested (LLM Practical Experience Hub, oct 2025)](https://langcopilot.com/posts/2025-10-11-document-chunking-for-rag-practical-guide) — confirmó semantic chunking + recursive como mejor combo para KB técnica. Validó la decisión de usar `MarkdownHeaderTextSplitter` + `RecursiveCharacterTextSplitter` en cascada.
- [RAG Chunking Strategies: 2026 Benchmark Guide (Premai)](https://blog.premai.io/rag-chunking-strategies-the-2026-benchmark-guide/) — confirmó 256-512 tokens + 10-20% overlap como sweet spot baseline; +contextual retrieval como upgrade obvio. Decidió 512/100.
- [Hybrid Search Revamped — Building with Qdrant's Query API](https://qdrant.tech/articles/hybrid-search/) — confirmó que Qdrant 1.7+ tiene Query API unificada para dense + sparse + RRF + reranking. F10 dense-only por scope; el upgrade path está documentado para F-pos.
- [RAG Triad — TruLens](https://www.trulens.org/getting_started/core_concepts/rag_triad/) — confirmó que las dimensiones canónicas son context_relevance, groundedness, answer_relevance. Adapté a 4 dims F10 (`retrieval_relevance`, `citation_accuracy`, `answer_groundedness`, `completeness`) que siguen el RAG triad pero más explícitas para dashboard.
- [text-embedding-3-large — OpenAI API docs](https://platform.openai.com/docs/models/text-embedding-3-large) — confirmó 3072 dim default + Matryoshka shrinking + costo. Validó la elección dim full.

Tessl tiles consultados: `tessl__fastapi`, `tessl__langgraph`, `tessl__pytest-api-testing`. No instalé tile nuevo — Qdrant + RAG patterns no tienen tile en el registry; cubrimos con docs oficiales + research abril 2026.

---

## Cierre del plan Redesign 2026-04

F10 cierra el plan completo (F0-F10). El copilot ahora es:

- **Plug-in friendly** (F1 provider pattern + discovery).
- **Memoria viva** (F2 deep-agent harness + write_todos plan_card; F3 brand_summary lighthouse cacheable; F4 inspirations + pin_to_memory).
- **Q&A natural sobre datos propios** (F5 ask_tenant_data deterministic pipeline, 2 LLM calls FAST).
- **URL contextual persistente** (F4 fetch_url + scratchpad).
- **Workflows unificados** (F6 declarative + engine + dual-read fallback).
- **Channel-aware output** (F7 ChannelFormat registry + format_for_channel determinístico).
- **Routing/cost optimizado** (F8 LLMClassifier NANO + cache-friendly system prompt + SSE v2 only).
- **Quality observability** (F9 CopilotJudge + goldens + ARQ weekly + node trace + admin /copilot-quality).
- **RAG curado autoritario** (F10 nicolify_marketing_kb + knowledge_search + 31 docs + breadcrumb-aware contextual chunking + golden RAG runner).

**Anchor count final:** 16 anchors del redesign (F1-F10) sobre cap 36. Margen para 2 housekeeping anchors post-mortem.

**Ratchet `copilot → módulo`:** 22 frozen desde F1. F-pos cleanup de `offer_section_tools.py` + `crm_tools.py` puede shrunk a ~15 cuando esos tools migren a sus providers respectivos.

**Próximos pasos sugeridos (NO bloqueantes):**

1. F-pos cutover: wire `build_default_router` al chat orchestrator + cleanup `procedure_state` legacy + drop `copilot_knowledge` collection.
2. F-pos housekeeping: fix flakies heredados (`test_streaming_integration`, `test_editable_fields_ssot`).
3. F-pos UX: composer FE con selector "Formato salida" para `format_for_channel`; FE renderer para `inspiration_saved` card; tooltip de citation en respuestas RAG.
4. F-pos quality: real-LLM weekly RAG eval cron (`weekly_rag_eval` ARQ task siguiendo F9 pattern).
5. F-pos data: scoring offline `brand_relevance_score` para chunks del KB cuando brand_summary cambie.

El plan completo está documentado y entrega valor user-visible end-to-end.
