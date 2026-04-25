# F8 — Routing + Cost optimization (start prompt)

> Pegar el bloque entre los `---` literal a una conversación nueva de Claude Code en `/home/chris/AISALESHT`.

---

```
Estamos ejecutando la fase F8 del Copilot Redesign 2026-04 ("Claude Code de Marketing").

Objetivo único de esta fase: bajar latencia primer token + cost / conversación + subir cache hit rate del system prompt. Concretamente: (1) implementar `LLMClassifier` fallback (rule classifier sigue first-line); (2) reordenar system prompt para maximizar prompt cache hit (stable prefix first, dynamic last); (3) eliminar ReAct legacy + dual SSE (legacy + v2 → solo v2); (4) telemetry analysis 30 días post-deploy → re-tune rules; (5) admin Streamlit page `/admin/copilot/routing` con distribución tiers + cost / latency / misroute.

Antes de escribir código, leé en orden (sin saltarte ninguno):
1. docs/domains/copilot/redesign-2026-04/README.md
2. docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md  (atención §3 — lista exhaustiva de lo que NO se toca)
3. docs/domains/copilot/redesign-2026-04/01-master-plan.md
4. docs/domains/copilot/redesign-2026-04/02-architecture-target.md  (§1 model router 4 tiers)
5. docs/domains/copilot/redesign-2026-04/03-phase-protocol.md
6. docs/domains/copilot/redesign-2026-04/phases/F8-routing-cost-optim.md
7. docs/domains/copilot/redesign-2026-04/learnings/F1-provider-pattern.md
8. docs/domains/copilot/redesign-2026-04/learnings/F2-deep-agents-harness.md
9. docs/domains/copilot/redesign-2026-04/learnings/F3-brand-summary-lighthouse.md
10. docs/domains/copilot/redesign-2026-04/learnings/F4-url-contextual-scratchpad.md
11. docs/domains/copilot/redesign-2026-04/learnings/F5-ask-tenant-data.md
12. docs/domains/copilot/redesign-2026-04/learnings/F6-workflow-unification.md
13. docs/domains/copilot/redesign-2026-04/learnings/F7-channel-formatter.md  ← APRENDIZAJES F7 OBLIGATORIOS

Después seguí los 9 pasos del protocolo (03-phase-protocol.md). Énfasis especial:

- **Paso 2 — Research fresco abril 2026 (no skip).**
  - WebSearch (mínimo 3 queries del mandate F8):
    - "OpenAI prompt caching prefix strategy 2026 best practices"
    - "LangGraph cache hit rate optimization 2026"
    - "LLM classifier fallback intent detection 2026"
  - Confirmar prefix cache rules (≥1024 tokens en OpenAI vigente).
  - Patrón LLMClassifier eficiente (NANO + structured output).
  - Tessl tiles: `tessl__fastapi`, `tessl__langgraph`. Si surge tile sobre prompt caching, evaluar.

- **Foco — no scope creep.** F8 entrega cinco entregables específicos del §1. NO mezcla F9 (golden + LLM-judge) ni F10 (RAG kb). NO se tocan adapters de canales del sales_agent.

- **Paso 4 — TDD obligatorio.**
  - Tests por capa: `LLMClassifier`, system prompt order (golden snapshot del orden), ReAct deletion (smoke + telemetry), dual SSE deletion (FE/BE handshake), admin page contract.
  - Arch test invariante: `assert system_prompt order == cache_friendly_order` (define el orden esperado). Si F-pos agrega fragmento, debe insertarlo en el slot correcto.
  - Golden snapshot F1+F2+F3+F4+F5+F6+F7 verde ANTES de empezar (~872 backend tests).

- **Paso 5 — Quality gates native (NUNCA `docker exec`).**
  - **Antes de tocar cualquier cosa**: corré la baseline F0-F7 (~872 verde, ver bloque exacto en learnings F7).
  - Después de cada bloque: ruff + golden + arch.
  - Si tocás streaming/orchestrator: correr `tests/modules/copilot/test_streaming_integration.py` aislado primero (flaky heredado, F4-F7 documentaron).

- **Paso 6 — Verificar §3 intacto.**
  - SSE v2 sigue emitiendo block_start/delta/end + message_start/end.
  - Cards (proposal/clarify/preview_update/plan_card) renderean igual.
  - Multimodal blocks (TextBlock, ImageBlock, etc.) intactos.
  - Ratchet `copilot → módulo` sigue en 22 (o shrunk).

- **Paso 7 — Lecciones aprendidas: ÚTILES, no plantilla rellenada.**
  - Decisiones donde el camino no era único (cómo medir cache hit antes/después; threshold del classifier rule vs LLM; cómo limpiar el ReAct path sin romper a alguien que aún lo importe).
  - Gotchas reales: comportamiento real de `cache_creation_input_tokens` en OpenAI vs lo documentado, cualquier fragility de orchestrator descubierta al borrar ReAct.
  - Hooks listos para F9 (golden tests + LLM-judge harness).

- **Paso 8 — Generar `prompts/F9-start.md`** desde plantilla.

- **Paso 9 — Commit + push.**
  - Conventional commit: `feat(copilot-redesign-f8): routing + cost optimization`.
  - Stage por nombre (nunca `git add -A`).
  - Push a `development`.
  - Reportar 3 líneas + paths a `learnings/F8-routing.md` y `prompts/F9-start.md`.

Reglas no negociables:
- Branch único: `development`.
- Brutal honestidad. Si plan F8 no aplica por aprendizajes F7 → flagear y preguntar.
- No alucinar paths/símbolos.
- No tocar §3.
- Native dev tools.
- Spanish neutro LatAm en todo lo user-facing.
- Stage por nombre (parallel-safety).

Empezá por el Paso 1 (releer learnings F1 + F2 + F3 + F4 + F5 + F6 + F7). Reportá 3 líneas con qué entendiste antes de Paso 2.
```

---

## Hooks específicos para F8 (de aprendizajes F7)

### Aprendizajes F7 que F8 debe asumir

- **`format_for_channel` agregado a `ALWAYS_AVAILABLE_GROUPS`** (~50 tokens al prompt fijo). F8 mide cache hit rate antes/después de su reorden. Si target ≥60% no se alcanza, F8 puede:
  - Lazy-bind `channel_format` por keyword detection (`whatsapp|email|sms|formato` en último user message).
  - O moverlo a route subset (sales, growth-studio, settings).
- **System prompt order actual** (heredado F2/F3/F4):
  ```
  lighthouse F3 → snapshot/behavior/guided/studio (volátiles per-turn) →
  inspirations F4 (state-aware, semi-volátil) → deep-agent suffix F2
  ```
  F8 §5.2 quiere reordenar a:
  ```
  static instructions → tools schema → lighthouse → editable catalog →
  active providers → /* fin prefix cacheable */ → studio snapshot →
  workflow state → inspirations → conversation messages
  ```
  El bloque static + tools schema + lighthouse debe sumar ≥1024 tokens (umbral OpenAI prefix cache).
- **Test flaky heredado `test_streaming_integration`** (heredado F0+) confirmado standalone PASS. F8 que toque ReAct legacy / dual SSE / orchestrator: correr **aislado primero** y luego después de cada bloque.
- **Test flaky heredado `test_editable_fields_ssot::test_no_cross_domain_duplicates`** sigue activo. Si F8 toca editable_fields (poco probable), aislar.
- **Anchor budget en 27/27**. F8 que agregue `[COPILOT-LLM-CLASSIFIER-F8]` o similar debe bumpear `assert len(ANCHOR_REGISTRY) <= 28+` en `tests/architecture/test_copilot_anchors.py:88`.
- **`SUPPORTED_OUTPUT_CHANNELS` en synthesizer es alias re-export** (`= SUPPORTED_CHANNELS` desde domain). F8 NO debe romper el alias — si refactoriza synthesizer, mantener el `SUPPORTED_OUTPUT_CHANNELS` export para no cascadear cambios en F5 callers.
- **Workflow.metadata `default_output_channel`** (F6 hook) sigue sin consumer. Si F8 toca el orchestrator chat (porque cuts ReAct), oportunidad de wirear: `wf.metadata.get("default_output_channel", "chat")` antes del synthesizer.

### Tests baseline que F8 debe correr ANTES de empezar

```bash
cd backend && .venv/bin/pytest \
  tests/modules/copilot/golden/ \
  tests/architecture/ \
  tests/modules/copilot/test_workflow_dataclass.py \
  tests/modules/copilot/test_workflow_engine.py \
  tests/modules/copilot/test_workflow_registry.py \
  tests/modules/copilot/test_workflow_state_persistence.py \
  tests/modules/copilot/test_deep_agent_harness.py \
  tests/modules/copilot/test_plan_card_emission.py \
  tests/modules/copilot/test_pinned_memory_repository.py \
  tests/modules/copilot/test_inspiration_repository.py \
  tests/modules/copilot/test_inspirations_layer.py \
  tests/modules/copilot/test_data_access_port.py \
  tests/modules/copilot/test_conversation_data_access_provider.py \
  tests/modules/copilot/test_ask_tenant_data_intent_classifier.py \
  tests/modules/copilot/test_ask_tenant_data_synthesizer.py \
  tests/modules/copilot/test_ask_tenant_data_executor.py \
  tests/modules/copilot/test_ask_tenant_data_query_builder.py \
  tests/modules/copilot/test_ask_tenant_data_state_check.py \
  tests/modules/copilot/test_ask_tenant_data_integration.py \
  tests/modules/copilot/test_ask_tenant_data_date_parser.py \
  tests/modules/copilot/test_data_query_cache.py \
  tests/modules/copilot/test_conversation_repository_count_window.py \
  tests/modules/copilot/domain/test_provider_ports.py \
  tests/modules/copilot/test_output_channel_format.py \
  tests/modules/copilot/test_format_for_channel_tool.py \
  tests/modules/offer/test_offer_repository_search.py \
  tests/modules/offer/test_offer_data_access_provider.py \
  tests/modules/crm/test_lead_repository_count_inbound.py \
  tests/modules/crm/test_crm_data_access_provider.py \
  tests/modules/brand/test_brand_summary_repository.py \
  tests/modules/brand/test_brand_section_updated_event.py \
  tests/modules/brand/test_brand_context_injector.py \
  tests/shared/workers/test_brand_summary_regen.py \
  tests/shared/application/test_brand_summary_event_handlers.py \
  tests/modules/copilot/test_brand_lighthouse_in_system_prompt.py \
  tests/modules/copilot/test_fetch_url_tool.py \
  tests/modules/copilot/test_pin_to_memory_tool.py \
  tests/modules/copilot/test_trafilatura_client.py \
  tests/modules/copilot/test_url_inspiration_analyzer.py \
  -q -o addopts="" --timeout=60
```

Debe ser ~872 verde (F0-F7 acumulado). El flaky heredado `test_streaming_integration` y `test_editable_fields_ssot::test_no_cross_domain_duplicates` se corren **aislados** post-cambios — NO bloqueantes para F8 directamente, PERO bloquearán cualquier merge si el cambio F8 los empeora.

### Archivos clave que F8 modifica (a priori)

- `backend/src/modules/copilot/application/router/classifiers/llm_classifier.py` — nuevo, NANO structured output.
- `backend/src/modules/copilot/application/router/model_router.py` — wire LLMClassifier fallback.
- `backend/src/modules/copilot/application/orchestrator/graph.py::build_system_prompt` — reorden de fragmentos.
- `backend/src/modules/copilot/application/orchestrator/chat.py` — eliminar ReAct path, eliminar `_select_graph` flag, eliminar dual SSE emit.
- `backend/src/modules/copilot/domain/model_tier.py` — confirmar 4 tiers (NANO/MINI/REASONING/HEAVY) presentes; agregar NANO si no.
- `backend/src/admin/pages/routing.py` + `backend/src/admin/modules/routing.py` — admin page nueva.
- `tests/architecture/test_system_prompt_order.py` — nuevo, fitness test del orden cacheable.
- `tests/architecture/test_copilot_anchors.py` — bump 27 → 28+ si agrega anchor.

### Riesgos que vigilar en F8

- **`build_system_prompt` ya tiene ~10 fragmentos volátiles** (snapshot, behavior, guided, studio, lighthouse, inspirations, deep-agent suffix, format_for_channel implícito en tools). El reorden sin medición previa puede empeorar cache hit. **Antes** de reordenar: instrumentar `cache_creation_input_tokens` vs `cache_read_input_tokens` y capturar baseline 24h en prod (o synthetic load) — sin ese baseline F8 está adivinando.

- **Eliminar ReAct legacy = posible breaking change para fallback paths.** F2 introdujo flag `COPILOT_DEEP_AGENT_V2` con default off; F4/F5/F6 lo encendieron en sus envs. Si prod aún corre con flag off, deletion rompe sin aviso. F8 debe verificar `Settings.COPILOT_DEEP_AGENT_V2` está True (default o env) en TODOS los envs antes de borrar el path. Sentry alertas + canary deploy primero.

- **Dual SSE deletion riesgo FE.** El frontend `frontend/src/features/copilot/...` debe estar 100% migrado a SSE v2. F8 verifica grep en FE por `text_chunk` o handlers legacy antes de borrar el emit BE. Si quedan callers FE que no chequean v2 first, romperán silente al deploy.

- **Admin page Streamlit** (plan §5.5) requiere registro en `PAGE_SPECS` (`backend/src/admin/app.py`) + smoke test (`backend/tests/admin/test_admin_smoke.py`). El conftest `tests/admin/conftest.py` mockea DB/Qdrant; cualquier nuevo repo que la admin page use debe agregarse al mock o el render headless cuelga.

- **NANO tier costo real bajo pero latencia variable.** OpenAI gpt-4o-mini-realtime es NANO equivalente; latencia p99 puede subir cuando carga sube. F8 debe medir p50/p95/p99 separado y no asumir que NANO es free-lunch. Si NANO no cumple <300ms p95, fallback a FAST con structured output.

- **Cache prefix threshold OpenAI ≥1024 tokens** (April 2026 vigente per docs). Si el reorden deja el prefix cacheable en ~900 tokens, no hay cache. Validar después de reordenar.

### Hooks F7 disponibles para F8

- `backend/src/modules/copilot/domain/output_channels.py::CHANNEL_FORMATS` — registry shared. F8 si necesita info del canal en routing (e.g. "WA + SMS short → MINI tier", "email long → REASONING tier") puede leer `get_channel_format(output_channel).max_chars` para decidir tier. Patrón natural sin ampliar el port.
- `backend/src/modules/copilot/application/tools/format_for_channel.py::format_for_channel_impl` — sync, sin LLM. F8 puede usarlo en el admin page para mostrar "preview channel-aware" sin hacer un round-trip a OpenAI.
- `backend/src/modules/copilot/application/tools/registry.py::ALWAYS_AVAILABLE_GROUPS` — F8 puede mover `channel_format` de "always" a "subset routes" si el budget de tokens del prompt fijo aprieta. Marcar la decisión en learnings F8 con métrica antes/después.
- F-pos cutover de F6 sigue pendiente (workflows live runtime). Si F8 toca el orchestrator chat para borrar ReAct, oportunidad de meter `WorkflowEngine.step` en el path nuevo. NO obligatorio para F8 — pero documentar si se hace.
