# Learnings — F7 Channel formatter registry

**Fecha cierre:** 2026-04-25 · **Modelo:** Claude Opus 4.7 (1M context) · **Branch:** `development @ <ver git log -1>` (parent `d8371c31`)

---

## Resumen 3 líneas

- Domain `ChannelFormat` dataclass + `CHANNEL_FORMATS` registry (7 canales: chat / whatsapp / email / sms / voice / instagram_dm / telegram) en `copilot/domain/output_channels.py`, con `register_channel(format, key=...)` extension API y `reset_registry_for_tests` para isolation. Synthesizer F5 ahora consume el registry vía `get_channel_format(...)` — el dict `_CHANNEL_HINTS` desapareció pero `SUPPORTED_OUTPUT_CHANNELS` sigue como alias re-export (`= SUPPORTED_CHANNELS`) para no romper imports F5 existentes. Tool transversal `format_for_channel(content, channel_id)` en `application/tools/format_for_channel.py` — post-procesador determinístico (regex-based markdown/emoji strip + truncate con "…") expuesto vía `@tool` LangChain en grupo `channel_format` agregado a `ALWAYS_AVAILABLE_GROUPS`.
- Decisión no obvia: el tool es **determinístico** (sin LLM call). El synthesizer ya genera prosa channel-aware leyendo `structure_hint`; el tool sirve para "agarrar este texto y dámelo limpio para WhatsApp" — pegan el contenido y reciben la versión adaptada en una sola llamada cacheable. Si quisieras reescritura semántica, el synthesizer es el camino. Esto evita un segundo LLM call innecesario y mantiene el budget de F5 (2 calls FAST por pregunta) intacto.
- Hooks listos para F8: el orden actual del system prompt es exactamente el que F8 §5.2 quiere reordenar — `lighthouse → snapshot → inspirations → workflows → tools schema`. F7 no tocó orden (no es F7 scope). F7 sí agregó `format_for_channel` a `ALWAYS_AVAILABLE_GROUPS`, ~50 tokens del prompt fijo — F8 va a querer medir cache hit antes/después con esa adición. Anchor budget bumpeado 26 → 27 con `COPILOT-CHANNEL-FORMATTER-F7`.

---

## Decisiones clave

| Decisión | Razón | Alternativa descartada |
|---|---|---|
| **Tool `format_for_channel` es post-procesador determinístico (sin LLM).** | El synthesizer F5 ya genera prosa channel-aware con `structure_hint` en su prompt. El tool transversal cumple un caso distinto: "dame este texto pegado listo para WA / SMS". Si fuera LLM-based duplicaría costo y agregaría latencia inaceptable para un tool que el LLM puede llamar 2-3 veces por turn. Regex strip + truncate es O(n) y tests determinísticos. | Wrapper LLM con `structure_hint` que reescriba el texto. Habría sido el doble de calls del synthesizer y latencia añadida; el caso real "limpiá esto para WA" no necesita reescritura, solo strip + truncate. |
| **Registry mutable global (`CHANNEL_FORMATS`) con `register_channel(format)` + `reset_registry_for_tests`.** | Plan F7 §5.4 explícito: "Providers can register new channels via `register_channel(format)`". Mutación global con guards (rechaza id vacío, rechaza duplicate spec, valida key=fmt.id) + fixture autouse en tests evita state-leak. F4 ya documentó que provider scan corre side-effects en module-load — `register_channel` desde `provider/__init__.py` encaja en ese patrón. | Registry inmutable + factory builder (`build_registry(extra_channels=...)`) instanciado por el orchestrator. Habría requerido propagar el registry como parámetro a synthesizer + tool + cualquier consumer futuro — mucha plumbing para una mutación que ya tiene guards y vive en domain. |
| **`SUPPORTED_OUTPUT_CHANNELS = SUPPORTED_CHANNELS` (alias re-export en synthesizer.py)**, no inline `frozenset(_CHANNEL_HINTS.keys())`. | F5 callers (`test_supported_output_channels_includes_chat_and_whatsapp`) importan `SUPPORTED_OUTPUT_CHANNELS` desde el módulo synthesizer. Romper ese símbolo cascada en tests externos. Alias = SSoT único + back-compat en una línea. | Renombrar a `SUPPORTED_CHANNELS` y obligar refactor de imports F5 + golden snapshot churn. Suma ruido al diff sin valor — el alias está sub-100-bytes y documentado. |
| **`output_channels.py` agregado a `_PROVIDER_CONTRACT_IMPORTS` ahora**, antes de tener consumer real provider. | Mirror del patrón F6: cuando un provider eventualmente importe `from src.modules.copilot.domain.output_channels import ChannelFormat, register_channel`, el ratchet `copilot → módulo` no debe explotar. Sumar la entrada en F7 evita que F-pos descubra el problema cuando ya tiene 4 archivos en flight. La "deuda" es 1 línea + comentario explícito del por qué. | Esperar al primer provider real (F-pos) para sumar. Funciona pero introduce un PR rojo cuando ese provider llegue, con coordinación cross-fase innecesaria. |
| **Tool en `_BASE_TOOL_GROUPS["channel_format"]` + `ALWAYS_AVAILABLE_GROUPS`**. | Q&A F5 ya agregó `data_query` a `ALWAYS_AVAILABLE_GROUPS` con el mismo argumento: el user puede pedirlo en cualquier ruta ("dame esto para whatsapp"). Inconsistencia sería tener uno disponible cross-route y el otro no. ~50 tokens extra en el prompt fijo, F8 va a medir el impacto. | Solo en routes específicas (sales, growth-studio). Restringía el caso de uso natural — el user pega texto en cualquier studio y lo quiere "para WA". |
| **Registry NO usa `Mapping` immutable + post-init validation (Pydantic).** Dataclass frozen plain. | El dataclass es un value object: 7 campos + frozen. Pydantic `BaseModel` agregaría dependencia y serialización inútil acá. Validation real vive en `register_channel` que sí valida key + dup + id. La validación en arch test (`test_channel_formatter_compliance.py`) es la red de seguridad cuando alguien edita el módulo. | Pydantic v2 BaseModel con `@field_validator` para max_chars > 0 y label_es non-empty. El cost: serialization machinery innecesaria + cada provider import-time paga el cost. Para 7 records read-only, overkill. |
| **Ningún arch test que valide "every channel registered es consumido en algún lado".** | Sería falso positivo: `voice` y `instagram_dm` por ejemplo nadie los consume aún en producción (el output_channel param en `ask_tenant_data` lo recibe del FE, y el FE no tiene selector aún en F7 — el plan §5.5 es deferido). Forzar "consume or remove" cortaría la extensión hacia futuro. | Test que recorra repo buscando `output_channel="X"` para cada X. Falla apenas alguno se add antes de que la primera llamada lo use. |
| **UI selector composer (`§5.5` plan) NO se entrega en F7.** | El prompt usuario fue explícito: "F7 entrega UNA cosa: ChannelFormat registry + format_for_channel tool consumer + reemplazo del _CHANNEL_HINTS dict". UI selector + badge "Formato: WhatsApp" en cards = work FE no trivial (composer state, persist preference, render flag). Mejor en sprint UX dedicado o cuando un caso real lo demande — el LLM ya sabe usar el tool sin selector. | Implementar selector + badge ahora. Habría duplicado el sprint y cruzado scope con F8 (latency tuning). |

---

## Sorpresas / gotchas (críticos, no triviales)

- **Ruff `B017` "Do not assert blind exception"** dispara con `pytest.raises(Exception)` aunque uses `# noqa: BLE001`. La pista: `BLE001` es para uso/captura, `B017` es el anti-blind-assert dedicado. Fix: usar tuple concreta `pytest.raises((AttributeError, TypeError))`. Cualquier test futuro que verifique frozen dataclass mutation: usar la tuple explícita, no `Exception`.

- **`langchain_core.tools.tool` decorator + tool groups validados por `id()`**: el tool decorator wrapea la función dentro de un objeto `BaseTool` con `name=function.__name__`. Si en un futuro un provider importa `format_for_channel` desde otro path (e.g. shim de re-export) y lo agrega a su `tool_groups()`, `_register_tool_groups` rechaza por `id()` distinto aunque el `name` sea idéntico. Solución: providers que extiendan grupos transversales **importan el mismo objeto** desde el path canónico (`copilot.application.tools.format_for_channel`). F4 lo aprendió; F7 lo aplicó.

- **`__all__` ordering rule (RUF022)**: ruff exige isort-style alphabetic sort en `__all__`. Sorprendió en mi primer commit de domain — había orderado por categoría conceptual. Aplicar `--fix` lo resuelve, pero recordá: sorted `__all__` es invariant del repo, no estilo personal.

- **Frontend ALWAYS_AVAILABLE_GROUPS expansion = golden snapshot rebuild obligatorio.** El snapshot `route_tool_selection.json` lista los tool names ordenados alfabéticamente por route. Agregar UN tool transversal mete una línea en CADA ruta → diff "+13 lines, 13 routes" lo cual es señal correcta (no un bug). F-pos que toque `ALWAYS_AVAILABLE_GROUPS` debe `UPDATE_GOLDEN=1` y revisar visualmente que el diff sea "+1 línea por route" (si aparece en menos rutas o desordena, algo más rompió).

- **Test flaky heredado `test_editable_fields_ssot::test_no_cross_domain_duplicates`** sigue activo desde F3. F4/F5/F6 lo confirmaron. F7 también: standalone PASS, dentro de `pytest -x -q` full FAIL por order-dep con pytest-randomly. F8 que toque `editable_fields` registry: correr aislado primero. Si llega a otra fase la operativa, considerar deuda en `docs/mejoras-proceso/to-do.md` para fix permanente.

- **Test flaky heredado `test_streaming_integration`** (heredado F0+) — confirmado standalone PASS (26/26). F8 va a tocar streaming (deletion ReAct legacy + dual SSE). **F8 debe correr `tests/modules/copilot/test_streaming_integration.py` aislado primero** y luego después de cada bloque que toque orchestrator.

- **`get_channel_format(channel_id: str | None)` con `None` no rompe** (acepta el caso) pero el type hint `str` en el `@tool` decorator de LangChain construye el JSON schema con `"type": "string"`. Si el LLM le pasa `null`, LangChain rechaza pre-tool-call. Ese no es un problema F7 (el tool obliga `channel_id: str`), pero `format_for_channel_impl` sí acepta `None` y devuelve chat fallback — útil para callers internos (synthesizer) sin pasar por el `@tool` wrapper. Patrón replicable: API pública strict, función impl tolerante.

---

## Recomendaciones accionables para F8

1. **Antes de empezar:** correr la suite F0-F7 baseline (~872 verde, sin contar streaming + flaky aislados):
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

2. **F8 §5.2 reordering del system prompt = golden snapshot churn esperado.** El orden actual de fragmentos viene de F2/F3/F4: `lighthouse → snapshot → behavior → guided → studio → inspirations → deep-agent suffix`. F8 quiere mover `tools schema` al inicio (post-cache prefix). Verificar `tests/modules/copilot/test_brand_lighthouse_in_system_prompt.py` y golden cuando lo hagas.

3. **`format_for_channel` en `ALWAYS_AVAILABLE_GROUPS` agrega ~50 tokens al prompt fijo per turn.** F8 que quiera optimizar tokens transversales puede:
   - (a) Lazy-bind por keyword detection (regex `whatsapp|email|sms|formato` en último user message);
   - (b) Mover a route map subset (sales, growth-studio, settings) pero romper el caso transversal;
   - (c) Aceptar el costo si cache hit rate alcanza target ≥60% (más simple).
   Mediar antes de elegir. Hook de medición disponible vía OpenAI usage `cache_creation_input_tokens` vs `cache_read_input_tokens`.

4. **Tier NANO para intent classifier (F5 hint):** F5 dejó documentado "cuando F8 introduzca `ModelRole.NANO`, cambiar la línea `intent_classifier.py:126` de `ModelRole.FAST` a `NANO`". F7 no agregó ningún consumer NANO, ese hook sigue válido y único.

5. **NO agregar canales custom solo para "completar la lista"**. El registry tiene 7 baseline. Mañana se podrá agregar `discord` / `slack` / `messenger` solo si hay un workflow real que lo emita. La regla del plan F7 §5.4 es: providers registran via `register_channel`, no se agregan al baseline. Test arch `test_baseline_covers_canonical_channels` valida los 7, no más.

6. **Si F8 introduce nuevos `[COPILOT-*]` anchors**, bumpear `assert len(ANCHOR_REGISTRY) <= 28` (o más) en `tests/architecture/test_copilot_anchors.py:88`. F7 dejó 27/27 con `COPILOT-CHANNEL-FORMATTER-F7`.

7. **Test `tests/architecture/test_copilot_provider_compliance.py`** sigue verde sin tocar. F7 no introdujo sub-port nuevo en `CopilotProvider` Protocol — el `register_channel` es función global, no método de provider. Si F8 introduce uno (poco probable), recordar el gotcha F5: actualizar `_StubProvider` en `tests/modules/copilot/domain/test_provider_ports.py` o `test_root_provider_protocol` falla silente.

---

## Riesgos abiertos

- **`output_channel` parameter en F-pos workflows.** Plan F6 §metadata permite que un Workflow declare `metadata={"default_output_channel": "whatsapp"}`. F7 no implementó ningún consumer del default — la integración natural sería en el orchestrator cutover de F-pos. Cuando llegue: `wf.metadata.get("default_output_channel", "chat")` antes de invocar synthesizer.

- **`format_for_channel` markdown strip es regex-based, no AST.** Casos edge: `**bold ** unbalanced` deja el primer `**` literal en output. Para producción Nicolify-grade no es bloqueante (input es prosa LLM, no Markdown adversarial), pero F-pos UX que quiera "preview real" puede swap a `markdown-it-py` AST stripper. Hoy: regex es suficiente y el output queda correcto en el 99% de casos.

- **Emoji regex obsolescencia.** Las ranges Unicode en `format_for_channel.py::_EMOJI_RE` cubren Unicode 15.1 (abril 2026 baseline). Cada release nueva (15.2, 16.0) agrega code points que se filtrarían. No bloqueante pero F-housekeeping puede swap a la lib `emoji` 2.x si alguna fase identifica emojis modernos sin strip.

- **UI selector deferred (plan F7 §5.5).** El composer no expone "Formato salida" picker; el LLM tiene que inferir el canal del último user message ("dame esto para whatsapp"). Funciona en práctica pero un selector visible cierra la UX. Cuando se decida: agregar a `frontend/src/features/copilot/components/Composer/...` un dropdown bind a un `output_channel` state + persist en URL/localStorage. Backend ya lo recibe por `output_channel` param en el body del request.

- **Cache hit rate del system prompt no medido.** Heredado F3/F4/F5/F6. F7 sumó ~50 tokens (`format_for_channel` description) — F8 va a medir baseline + post-reorder. Si cache rate ya está debajo de 30%, el reorder F8 §5.2 es prioridad. Si está cerca de 60%, los 50 tokens nuevos no mueven la aguja.

---

## Hooks listos para próximas fases

- `backend/src/modules/copilot/domain/output_channels.py::ChannelFormat` + `CHANNEL_FORMATS` + `register_channel` — F-pos provider que quiera meter canal custom (e.g. `discord`) hace `from copilot.domain.output_channels import ChannelFormat, register_channel` desde su `copilot_provider/__init__.py` y llama `register_channel(...)`. El arch test `test_ddd_boundaries.py::_PROVIDER_CONTRACT_IMPORTS` ya whitelist el path.

- `backend/src/modules/copilot/application/tools/format_for_channel.py::format_for_channel_impl` — función pura sync, idempotente. Cualquier fase que necesite "limpiar texto para canal X" sin pasar por el LLM o por la wrapper `@tool` puede llamar directo: `format_for_channel_impl(content=..., channel_id=...)`. Sin DB, sin red, sin LLM.

- `backend/src/modules/copilot/application/tools/format_for_channel.py::_strip_markdown` — regex pipeline reutilizable si F-pos agrega "exportar respuesta como text-only" o similar.

- `backend/src/modules/copilot/application/tools/ask_tenant_data/synthesizer.py::SUPPORTED_OUTPUT_CHANNELS` — alias re-export de `SUPPORTED_CHANNELS`. F-pos NO debe importar el alias si está creando código nuevo: usar `SUPPORTED_CHANNELS` desde el domain directo.

- `backend/tests/architecture/test_channel_formatter_compliance.py` — 7 fitness tests (covers canonical, key/id parity, populated fields, bool flags, sms invariants, whatsapp invariants). F-pos que extienda registry: actualizar `CANONICAL_CHANNEL_IDS` solo si agrega canal **al baseline** (no si registra desde provider).

- `backend/src/modules/copilot/application/tools/registry.py::_BASE_TOOL_GROUPS["channel_format"]` + `ALWAYS_AVAILABLE_GROUPS` con `channel_format` — F-pos puede mover el grupo a route subset si la medición F8 lo justifica.

- `tests/architecture/test_ddd_boundaries.py::_PROVIDER_CONTRACT_IMPORTS` ahora incluye `copilot.domain.output_channels`. Patrón replicable cuando F-pos agregue otro domain shared con providers.

---

## Fuentes research útiles

- [WhatsApp Business Platform messaging limits](https://developers.facebook.com/docs/whatsapp/messaging-limits/) — confirmó text messages 4096 chars + templates 1024; markdown subset es propietario (*bold*/_italic_/~strike~), NO standard markdown. Decidió `markdown_allowed=False` para WhatsApp.
- [Twilio "How long can a message be?"](https://www.twilio.com/docs/glossary/what-sms-character-limit) — confirmó GSM-7 single 160 / multi-part 153, UCS-2 single 70 / multi-part 67. Decisión `max_chars=160` + emoji_allowed=False para mantener GSM-7.
- [HTML vs Plain Text Email Deliverability 2026](https://www.mailforge.ai/blog/html-vs-plain-text-best-format-for-deliverability) — confirmó plain text > HTML para cold outreach + 60:40 text:image ratio. Decisión email `markdown_allowed=True` (el client renderiza si quiere) pero structure_hint enfatiza "texto plano" para evitar spam triggers.

Tessl tiles consultados: ninguno específico para channel formatters. `tessl__fastapi` y `tessl__pytest-api-testing` ya cubren el stack base; F7 no introdujo lib externa nueva, no instalé tile nuevo.
