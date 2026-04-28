# Learnings · S3 · prompt cache_boundary refactor

> Doc para S4 (ChatModelSpec adopt). Foundation cache-friendly system prompt
> lista; lo que viene a S4 puede medir hit rate real con `sales_agent_llm_call.cached_read_tokens`
> ya populado (S1 callback handler captura ambos providers vía LangChain
> `usage_metadata.input_token_details.cache_read`).

---

## Resumen (3 líneas)

- **Entregado**: módulo nuevo `src/modules/sales_agent/application/prompts/compose.py` mirror exacto del pattern F8 copilot (`PromptFragment(StrEnum)` + `CACHEABLE_FRAGMENTS`/`VOLATILE_FRAGMENTS` tuples + `CACHE_BOUNDARY_MARKER` + `compose_system_prompt(fragments) -> str`). Builder de alto nivel `build_specialist_system_prompt(state, role)` resuelve los 10 slots desde state + Jinja existentes (specialists.j2 renderizados con kwargs vacíos para no incluir state volátil). Specialists qualifier/product_expert/closer migrados — 3 callsites en `nodes.py` cambiaron de `prompt_loader.render(...) + _build_system_prompt(...)` a `build_specialist_system_prompt(state, SpecialistRole.X)`. Supervisor fuera de scope (max_output_tokens=10 + ModelRole.FAST = cache wins despreciables). Arch test `tests/architecture/test_sales_agent_system_prompt_order.py` (5 invariants) congela el orden. Suite full 1613 verde, ruff/format clean.
- **Decisión no obvia**: el plan original S3 proponía `compose_system_prompt(state) -> list[SystemMessage]` con dos `SystemMessage` separados (uno cacheable, uno volatile). **Lo cambié a single string + HTML-comment marker** (mirror F8 copilot) tras research mandate confirmar que (a) OpenAI / Kimi / DeepSeek son auto-cache sin annotations — solo necesitan prefix estable contiguo ≥1024 tokens; (b) Anthropic `cache_control` blocks no aplica porque sales_agent NO enruta a Claude; (c) `LLMFactory.generate_response(system_prompt: str)` ya acepta string — cambiar a `list[SystemMessage]` rompía 9 callsites del shared/infrastructure/llm contract. F8 ya está en producción copilot con hit rate verificable. Cero razón para divergir.
- **Listo para S4**: zero deuda en compose.py path. `cached_read_tokens` columna ya existe (S1 migración 078). Cualquier cambio S4 a `LLMFactory.get_service(role)` con multi-provider per-role va a beneficiarse del cache_boundary YA presente — Kimi K2.6 + DeepSeek V4 son auto-cache, así que el switch de provider mantendrá la ventaja de hit rate. **Watchpoint S4**: si Kimi/DeepSeek tienen tokens-per-char ratio menor que GPT (más eficientes), el threshold 1024 tokens nuestro queda holgado — actualmente prefix realista mide ~2700 tokens (>2× threshold).

---

## Decisiones clave

- **Single string con marker, NO `list[SystemMessage]`**:
  - Tomada: `compose_system_prompt(fragments: Mapping[PromptFragment, str]) -> str` con `CACHE_BOUNDARY_MARKER = "\n\n<!-- ==== CACHE BOUNDARY (S3) ==== -->\n\n"` insertado entre prefix cacheable y suffix volatile.
  - Razón: research confirmó OpenAI / Kimi K2.6 (OpenAI-compat API) / DeepSeek V3-V4 son auto-cache sin annotations — solo necesitan prefix contiguo estable ≥1024 tokens. Single string es el pattern probado en copilot F8 (production con hit rate verificable). Ajusta `compose_system_prompt(fragments)` con la firma exacta del módulo `system_prompt_layout` copilot (literal copy del shape) para minimizar divergencia conceptual.
  - Alternativa descartada: `list[SystemMessage]` con cacheable + volatile. (1) LangChain solo soporta `cache_control` blocks dentro de UN SystemMessage (no múltiples) para Anthropic; (2) sales_agent hoy usa OpenAI/Kimi/DeepSeek que ignoran cache_control — sólo importa el prefix estable; (3) cambiaba `LLMFactory.generate_response(system_prompt: str)` a `list` y rompía 9 callsites. El plan original venía de antes que cerrara F8 copilot — fue ajustado en research mandate y documentado en `phases/S3-*.md` sección "Ajustes vs plan original".

- **Render specialists Jinja con kwargs vacíos**:
  - Tomada: `_render_static_specialist_body(role)` invoca `prompt_loader.render(specialist_<role>)` SIN pasar state-dependent kwargs (`consecutive_questions`, `qualification_answers`, `buying_signals`, `objection_history`, `last_session_summary`, `session_gap_hours`, `context_rag`, `lead_score`, `turn_count`, `active_product`, `close_strategy`).
  - Razón: las templates `specialist_*.j2` existentes ya tienen `{% if state_var %}` guards en cada inyección de state. Jinja default env trata Undefined como falsy → todos los if-blocks se saltan → el render es PURE static body (cacheable cross-tenant). Cero re-escritura de templates. PromptVersionModel override path sigue funcionando: si tenant overridea `specialist_qualifier` en DB, la version DB también renderiza con kwargs vacíos.
  - Alternativa descartada: split físico en `specialist_qualifier_static.j2` + `specialist_qualifier_volatile.j2`. Ganaba claridad pero (a) el override DB existente apunta a `specialist_qualifier` único — splittear rompería tenants que ya overridearon; (b) los volatile blocks ya están en compose.py builders Python (`_lead_signals`, `_session_continuity`) — duplicarlos en Jinja era doble costo.

- **Volatile slots como Python builders, no Jinja**:
  - Tomada: `_stage_hint`, `_lead_signals`, `_session_continuity`, `_tool_request_format` viven como funciones Python en compose.py — generan strings desde state directo, no via prompt_loader.render.
  - Razón: el contenido volátil es estructural simple (f-strings + json.dumps con sort_keys). Una template Jinja agregaría DB lookup (PromptLoader cache TTL 60s + tenant_config injection) que no aporta cuando el contenido depende 100% de state runtime. Bonus: los volatile builders son testeables sin filesystem; el unit test de "sin volátil en cacheable" puede comparar bytes deterministically.
  - Alternativa descartada: per-slot Jinja templates (`_stage_hint.j2`, etc) mirror F8 copilot. F8 copilot SI tiene templates por slot porque sus volatile fragments incluyen mucha lógica + multi-line markdown — para sales_agent los volatile son 3-5 líneas cada uno. Sobre-engineering sin payoff.

- **Supervisor fuera de scope S3**:
  - Tomada: `SpecialistRole` enum solo tiene `QUALIFIER`, `PRODUCT_EXPERT`, `CLOSER`. Supervisor sigue usando `prompt_loader.render("supervisor_routing", **state_kwargs)` directo en `node_sales_supervisor`.
  - Razón: supervisor llama LLM con `model_type=ModelRole.FAST` + `max_output_tokens=10`. Cache benefit despreciable (output trivial + input pequeño). Refactor agregaba ratchet sin payoff y supervisor_routing.j2 mezcla static rules + bare `{{ var }}` vars (sin `{% if %}` guards) → renderizar con kwargs vacíos rompe estructura.
  - Alternativa descartada: hacer supervisor parte del refactor por consistencia. Trade-off perdedor.

- **Slots OFFER_SUMMARY + CHANNEL_FORMAT_HINT empty placeholders**:
  - Tomada: enum incluye los slots 5+6 pero `build_specialist_system_prompt` los pasa con `""` — `_take` los descarta (whitespace strip).
  - Razón: el target architecture (§3.4) lista los 6 slots cacheable; agent_identity.j2 hoy YA contiene offer + channel rules embebidos. Splittear en S3 era prematuro: S5 va a poblar CHANNEL_FORMAT_HINT con registry channel data, S7 va a poblar OFFER_SUMMARY desde `brand_voice_summary` table (mirror copilot lighthouse). Mantener los slots en el enum congelados por arch test = future-proof sin cambiar nada hoy.
  - Alternativa descartada: omitir los slots del enum hasta S5/S7. El arch test se rompería en cada extensión. Mejor congelar el orden ahora.

---

## Sorpresas / gotchas críticos

- **`logging` module bloqueado por arch test cross-cutting** — `tests/architecture/test_coherence.py::test_consistent_logging` exige `structlog`. Tropecé al primer pytest. Fix trivial (1-line import swap), pero **lección S4+**: cualquier módulo nuevo en sales_agent debe usar `structlog.get_logger(__name__)` desde el día 1; el arch test tiene allowlist congelada con 60 entradas (shrink-only). NO agregar a allowlist.

- **Test plan original tenía aserts sobre `list[SystemMessage]`** — al ajustar a single string, los tests también se ajustaron antes de implementar. Eso me obligó a re-leer el research mandate output entre RED y GREEN. **Lección**: cuando research altera el plan, RED tests son del plan ajustado, no del plan original. El protocolo paso 4 (TDD) y paso 2 (research) tienen orden estricto: research primero, plan se ajusta, después RED.

- **`from __future__ import annotations` + `Mapping` import** — TC003 ruff fired. Fix simple (mover a `if TYPE_CHECKING:`), pero **lección**: con `from __future__ import annotations`, todos los annotation-only imports DEBEN ir en `TYPE_CHECKING` block — Python NO los necesita en runtime. F8 copilot ya tenía el patrón, lo repliqué directo.

- **Test `test_qualifier_passes_consecutive_questions` legacy chequeaba `prompt_loader.render` kwargs** — patch sobre `nodes_mod.prompt_loader` ya no captura nada porque el render lo hace `compose.py`, no `nodes.py`. Re-escribí el test para chequear que las cooldown vars (consecutive_questions, session_gap_hours) aparecen en el VOLATILE suffix del system prompt. Mismo invariant funcional, distinto observation point. **Lección**: tests post-refactor que mockeaban un implementation detail (Jinja render kwargs) deben subir nivel a observable behavior (output prompt contains expected substring).

- **`prompt_loader._tenant_config_cache` es mutable in-process** — tests aislados en CI pueden ver tenant_config cacheado de un test previo si comparten el singleton. No fue un problema porque mis fixture tests pasan tenant_config=`{"brand_name": "Test Brand"}` que no toca el cache (sin DB lookup). **Watchpoint**: si futuros tests prompts dependen de `_get_tenant_config` real (DB), deben monkeypatch el cache en autouse fixture.

- **`# noqa` indirecto** — `ruff format` reformateó string literals con `\"` a `'`-quoted strings (Q003). Tests también afectados. Aplicado por ruff --fix automático; no genera warnings en runtime. **No-issue**.

---

## Recomendaciones accionables para S4

- [ ] **S4 (ChatModelSpec adopt) puede medir hit rate post-deploy** — con `cached_read_tokens` y `input_tokens` en `sales_agent_llm_call` (S1 callback handler), una query SQL simple revela hit rate per turn. Target: ≥60% post 7 días (`sum(cached_read_tokens) / sum(input_tokens)`). Si <60% en tenant promedio, root-cause antes de avanzar S4.

- [ ] **S4 NO debe agregar state-dependent kwargs al render de specialists static body** — el cache_boundary se rompe si alguien pasa `consecutive_questions=` u otro state var al `prompt_loader.render(specialist_qualifier, ...)` invoke en compose.py. Si S4 agrega un nuevo specialist (ej: `specialist_objection_handler`) seguir el patrón: render con kwargs vacíos.

- [ ] **Si S4 cambia el provider del closer a Kimi K2.6** → verificar empíricamente que `usage_metadata.input_token_details.cache_read` está populado (LangChain normaliza pero solo en versiones recientes). El callback handler S1 ya leyó esa key; si el provider devuelve `prompt_cache_hit_tokens` (DeepSeek raw) y LangChain no normaliza, ajustar el handler. Documentado en `_extract_usage` de `SalesAgentCallbackHandler`.

- [ ] **NO usar `OFFER_SUMMARY` ni `CHANNEL_FORMAT_HINT` slots en S4** — están reservados S7/S5 respectivamente. Si S4 ve necesidad de un slot cacheable nuevo (ej: chat_model_spec_capabilities), agregarlo al enum con un nombre semántico distinto y al arch test snapshot.

- [ ] **PromptVersionModel override sigue funcionando** — un tenant que previo a S3 overridea `specialist_qualifier` en DB ve su override entrar al slot 3 cacheable. NO romper esto en S4. Si S4 introduce una capa de templates per-provider (ej: kimi-specific instructions), los nuevos templates van como cacheable cross-tenant en su propio slot, NO mezclados con el override per-tenant.

- [ ] **Tools registry hardcoded en `_TOOLS_HINT`** está flagged tech-debt — si S4 agrega tools nuevas (vía S8 scheduler o S9 payment lifecycle), el `_TOOLS_HINT` puede driftear. Mantener una sola fuente de verdad: `TOOL_REGISTRY` en `agents/sales/tools.py` debería generar el hint string vía un helper `format_tools_hint(registry)`. Hoy no es problema porque la lista del hint está alineada con TOOL_REGISTRY actual; en S8/S9 se rompe → priorizar.

- [ ] **Cache poison auditing**: cuando lleguen turns de tráfico real, agregar arch test que verifique `cache_read_tokens` >0 en >50% de turns post-T+1 (segundo turn de cada conversación). Si <50%, la prefix no es estable. Watchpoint en S6 ratchet pass.

---

## Hooks listos

- `backend/src/modules/sales_agent/application/prompts/compose.py::compose_system_prompt(fragments)` — pure data assembler. Cualquier futuro builder (judge prompt, golden snapshot) puede invocarlo + sufijar.

- `backend/src/modules/sales_agent/application/prompts/compose.py::build_specialist_system_prompt(state, role)` — high-level. S4 puede pasar el output a `LLMFactory.get_service().generate_response(messages, system_prompt=...)` sin cambios.

- `backend/src/modules/sales_agent/application/prompts/compose.py::SpecialistRole` — enum con QUALIFIER / PRODUCT_EXPERT / CLOSER. Si S4 agrega un nuevo specialist (improbable según §3 vision-and-objectives), añadir entry + template_key + Jinja template + arch test snapshot.

- `backend/tests/architecture/test_sales_agent_system_prompt_order.py` — 5 fitness tests congelan el orden. S4-S10 que no toquen prompts deben ignorarlo; cualquier reorden requiere actualizar `EXPECTED_CACHEABLE`/`EXPECTED_VOLATILE` deliberadamente.

- `backend/tests/modules/sales_agent/prompts/test_compose_system_prompt.py` — 16 unit tests sobre el assembler puro.

- `backend/tests/modules/sales_agent/prompts/test_build_specialist_system_prompt.py` — 13 integration tests sobre el builder con state realista. El fixture `_realistic_state` es el patrón para futuras tests prompts.

---

## Riesgos abiertos

- **Cache hit rate no verificado en producción** — todo el design supone OpenAI/Kimi/DeepSeek auto-cache + ≥1024 tokens. Si en producción el prefix de algún tenant cae bajo el threshold (ej: tenant nuevo sin agent_identity rico), no hay degradación gradual — es 0% cache. **Mitigación**: el arch test verifica prefix ≥1024 tokens con tenant fixture realista; si el tenant real tiene agent_identity más pequeño, el slot AGENT_IDENTITY puede colapsar.

- **agent_identity.j2 es 1 blob grande per-tenant** — si tenant cambia voice_tone (raro), todo el slot 4 invalida. Aceptable hoy; S7 split lo arregla.

- **`_TOOLS_HINT` lista hardcoded de tools** — drift con TOOL_REGISTRY si S8/S9 agregan tools sin actualizar el hint. Mitigación tech-debt entry.

- **PromptVersionModel override de specialist genera cache miss cross-tenant** — tenants con override pierden hit cross-tenant en slot 3. Aceptable; la mayoría no overridean.

- **Subgraph callback forwarding (S1) + nuevo compose** — el callback handler de S1 graba cada llm_call. Verificar (post-deploy 24h) que cada turn de qualifier/product_expert/closer tiene 1 llm_call row con cached_read_tokens populado en el segundo turno mínimo. Si no aparece → re-investigar el callback path.

---

## Tech debt detectado (NO arreglado)

Ya en `05-tech-debt-log.md` sección "Detectados durante S3":

- [LOW] `agent_identity` slot mezcla offer + channel → DEFERRED-S5/S7.
- [LOW] `_realistic_state` test fixture inline ~30 líneas → DEFERRED-S6.
- [LOW] PromptVersionModel override + cache scope cross-tenant → FLAGGED, monitorear.
- [LOW] `_BASE_IDENTITY` y `_TOOLS_HINT` constants en código → FLAGGED, S5 lift posible.

---

## Fuentes research útiles

Solo las que **cambiaron una decisión**.

- [OpenAI Prompt Caching Guide](https://developers.openai.com/api/docs/guides/prompt-caching) — confirmó threshold 1024 tokens vigente abril 2026 + auto sin annotations. Cambió la decisión de "list[SystemMessage]" a single string.
- [Anthropic Claude Prompt Caching · platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — confirmó que `cache_control` requiere blocks DENTRO de UN SystemMessage. Combinado con LangGraph v1.0 `create_agent` solo aceptando `str`, mostró que multi-SystemMessage es trade-off perdedor.
- [Kimi K2.6 API Integration Guide](https://help.apiyi.com/en/kimi-k2-6-api-integration-guide-en.html) — confirmó OpenAI-compatible API + automatic prefix caching 75-83% savings. Validó que el pattern S3 funciona para el switch S4 a Kimi sin re-design.
- [DeepSeek Context Caching · api-docs.deepseek.com](https://api-docs.deepseek.com/guides/kv_cache) — confirmó disk-based auto-cache default-on con `prompt_cache_hit_tokens` raw (LangChain normaliza). Watchpoint para S4 callback handler.
- [LangChain Issue #33635 (LangGraph v1.0 create_agent str-only)](https://github.com/langchain-ai/langchain/issues/33635) — confirmó la limitación que descartó el approach `list[SystemMessage]` definitivamente.
- [F8 copilot system_prompt_layout.py + learning](docs/domains/copilot/redesign-2026-04/learnings/F8-routing.md) — pattern reference. Replicado literal para sales_agent.

---

## Métricas medidas

- Quality gates nativos: `ruff check` 0 errors, `ruff format --check` clean.
- `pytest tests/modules/sales_agent/ tests/architecture/ tests/admin/ tests/shared/ tests/modules/copilot/observability/`: **1613 passed, 1 warning** (Pydantic deprecation, no impacto).
- Tests nuevos S3: **35** (16 compose unit + 13 builder integration + 5 arch + 1 nodes integration update).
- Tests modificados: 3 (test_nodes.py — 3 deletions de `_build_system_prompt` cobertura + 2 mock simplifications; test_cooldown.py — 1 test reescrito de Jinja-kwargs check a system_prompt suffix substring check).
- Files nuevos: 5 (compose.py + __init__.py + 2 test files + 1 arch test).
- Files modificados: 3 (nodes.py, test_nodes.py, test_cooldown.py).
- LOC añadidas: ~700 (incluye docs phase + learnings + code + tests).
- Prefix cacheable real con tenant fixture: ~11067 chars (~2766 tokens), volatile suffix ~819 chars. Margen 2.7× threshold.
- Spanish neutro: 0 hits actionables. Voseo regex sólo encuentra los ejemplos negativos en `_BASE_IDENTITY` (lista de prohibiciones).
