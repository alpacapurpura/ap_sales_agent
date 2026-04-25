# F7 — start prompt

> Copiar el bloque entre los `---` literal en una conversación nueva de Claude Code en `/home/chris/AISALESHT`.

---

```
Estamos ejecutando la fase F7 del Copilot Redesign 2026-04 ("Claude Code de Marketing").

Objetivo único de esta fase: registry declarativo `OutputChannelFormat[chat|whatsapp|email|sms|voice|instagram_dm|telegram]` con specs por canal (max chars, emoji, line breaks, markdown allowed, structure hint), consumido por el `synthesizer` de F5 y por el general chat para producir output canal-aware copia-pegable.

Antes de escribir código, leé en orden (sin saltarte ninguno):
1. docs/domains/copilot/redesign-2026-04/README.md
2. docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md  (atención §3 — lista exhaustiva de lo que NO se toca)
3. docs/domains/copilot/redesign-2026-04/01-master-plan.md
4. docs/domains/copilot/redesign-2026-04/02-architecture-target.md  (§7 channel formatter registry)
5. docs/domains/copilot/redesign-2026-04/03-phase-protocol.md
6. docs/domains/copilot/redesign-2026-04/phases/F7-channel-formatter.md
7. docs/domains/copilot/redesign-2026-04/learnings/F1-provider-pattern.md
8. docs/domains/copilot/redesign-2026-04/learnings/F2-deep-agents-harness.md
9. docs/domains/copilot/redesign-2026-04/learnings/F3-brand-summary-lighthouse.md
10. docs/domains/copilot/redesign-2026-04/learnings/F4-url-contextual-scratchpad.md
11. docs/domains/copilot/redesign-2026-04/learnings/F5-ask-tenant-data.md
12. docs/domains/copilot/redesign-2026-04/learnings/F6-workflow-unification.md  ← APRENDIZAJES F6 OBLIGATORIOS

Después seguí los 9 pasos del protocolo (03-phase-protocol.md). Énfasis especial:

- **Paso 2 — Research fresco abril 2026 (no skip).**
  - WebSearch (mínimo 3 queries del mandate F7):
    - "WhatsApp Business API message limits formatting 2026"
    - "email formatting plain text vs HTML LLM generated 2026"
    - "SMS character limit segmentation 2026 best practices"
  - Confirmar specs por canal (max_chars, markdown rules, line break style).
  - Tessl tiles: `tessl__fastapi`. Si surge tile WhatsApp/messaging relevante, evaluar.

- **Foco — no scope creep.** F7 entrega UNA cosa: `ChannelFormat` registry + `format_for_channel` tool consumer + reemplazo del `_CHANNEL_HINTS` dict del F5 synthesizer. NO se mezcla F8 (routing) ni se tocan adapters de canales (sales_agent canales hands-off — §3).

- **Paso 4 — TDD obligatorio.**
  - Test por capa: `ChannelFormat` dataclass + `CHANNEL_FORMATS` registry + `register_channel(format)` extension + integración con `synthesize_answer` (F5).
  - Arch test invariante: cada `ChannelFormat` tiene `id` + `label_es` + `max_chars` + `markdown_allowed` poblados; sin canales con id duplicado.
  - Golden snapshot F1+F2+F3+F4+F5+F6 verde ANTES de empezar.

- **Paso 5 — Quality gates native (NUNCA `docker exec`).**
  - **Antes de tocar cualquier cosa**: corré la baseline F0-F6 (~821 verde, ver bloque exacto en learnings F6).
  - Después de cada bloque: ruff + golden + arch.
  - Si tocás synthesizer o ask_tenant_data tests: correr aislado primero.

- **Paso 6 — Verificar §3 intacto.**
  - SSE v2 sigue emitiendo block_start/delta/end + message_start/end.
  - Cards (proposal/clarify/preview_update/plan_card) renderean igual.
  - Multimodal blocks (TextBlock, ImageBlock, etc.) intactos.
  - Ratchet `copilot → módulo` sigue en 22 (o shrunk).

- **Paso 7 — Lecciones aprendidas: ÚTILES, no plantilla rellenada.**
  - Decisiones donde el camino no era único (registry domain en copilot/ vs en provider; cómo manejar canales custom de providers; cómo coexistir con F5 synthesizer existente).
  - Gotchas reales: spec ambiguity por canal (WA permite *bold*?, email plain vs HTML?), que apareció en la ejecución.
  - Hooks listos para F8 (routing puede usar canal hint para tier selection: WA/SMS short → MINI; email long → REASONING).

- **Paso 8 — Generar `prompts/F8-start.md`** desde plantilla.

- **Paso 9 — Commit + push.**
  - Conventional commit: `feat(copilot-redesign-f7): channel formatter registry + synthesizer integration`.
  - Stage por nombre (nunca `git add -A`).
  - Push a `development`.
  - Reportar 3 líneas + paths a `learnings/F7-channel-formatter.md` y `prompts/F8-start.md`.

Reglas no negociables:
- Branch único: `development`.
- Brutal honestidad. Si plan F7 no aplica por aprendizajes F6 → flagear y preguntar.
- No alucinar paths/símbolos.
- No tocar §3.
- Native dev tools.
- Spanish neutro LatAm en todo lo user-facing.
- Stage por nombre (parallel-safety).

Empezá por el Paso 1 (releer learnings F1 + F2 + F3 + F4 + F5 + F6). Reportá 3 líneas con qué entendiste antes de Paso 2.
```

---

## Hooks específicos para F7 (de aprendizajes F6)

### Aprendizajes F6 que F7 debe asumir

- **`SUPPORTED_OUTPUT_CHANNELS = frozenset({"chat", "whatsapp", "email", "sms"})`** ya existe en `application/tools/ask_tenant_data/synthesizer.py` (F5 hook). F7 reemplaza el `_CHANNEL_HINTS` dict adyacente con el registry real `CHANNEL_FORMATS`. La signature `synthesize_answer(..., output_channel: str)` está congelada — F7 NO la cambia.
- **`output_channel: str` parámetro viaja end-to-end al synthesizer** desde el tool `ask_tenant_data`. F7 puede agregar default `output_channel="chat"` a más tools transversales si conviene, pero el contrato existente queda.
- **`Workflow.metadata` field es `Mapping[str, Any]` libre**. F7 puede usarlo para que un Workflow declare `metadata={"default_output_channel": "whatsapp"}` cuando aplique, sin tocar el schema. Lectura es responsabilidad del orchestrator (F-pos).
- **Anchor budget en 26/26**. F7 que agregue `[COPILOT-CHANNEL-FORMATTER-F7]` debe bumpear `assert len(ANCHOR_REGISTRY) <= 27` en `tests/architecture/test_copilot_anchors.py:87`.
- **Provider scan import side-effects (F4)**: si F7 hace que providers expongan `channel_provider()` con custom channels, el sub-port nuevo expande `CopilotProvider` Protocol y rompe `_StubProvider` en `tests/modules/copilot/domain/test_provider_ports.py` igual que F5. Actualizar stub en el mismo commit.
- **Si `output_channels.py` es parte del provider contract** (providers importan `ChannelFormat`/`register_channel` desde `copilot.domain.output_channels`), agregar `src.modules.copilot.domain.output_channels` a `_PROVIDER_CONTRACT_IMPORTS` en `test_ddd_boundaries.py:60` (mirror del patrón F1 + F6).

### Tests baseline que F7 debe correr ANTES de empezar

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

Debe ser ~821 verde (F0-F6 acumulado). Los flaky heredados (`test_streaming_integration` y `test_editable_fields_ssot::test_no_cross_domain_duplicates`) se corren **aislados** post-cambios — NO bloqueantes para F7.

### Archivos clave que F7 modifica (a priori)

- `backend/src/modules/copilot/domain/output_channels.py` — nuevo, registry + dataclass.
- `backend/src/modules/copilot/application/tools/ask_tenant_data/synthesizer.py` — reemplaza `_CHANNEL_HINTS` con consumer del registry.
- `backend/src/modules/copilot/application/tools/format_for_channel.py` — nuevo, tool transversal opcional.
- `tests/architecture/test_channel_formatter_compliance.py` — nuevo, fitness tests del registry.
- `tests/modules/copilot/test_output_channel_format.py` — nuevo, dataclass + registry.
- `tests/architecture/test_copilot_anchors.py` — bump 26 → 27 si agrega anchor.

### Riesgos que vigilar en F7

- **`_CHANNEL_HINTS` reemplazo**: el F5 synthesizer ya consume el dict para inyectar prompt hints al LLM. Si F7 cambia la shape (e.g. de `dict[str, str]` a `ChannelFormat` con `.structure_hint`), el synthesizer test `test_ask_tenant_data_synthesizer.py` rompe. Hacer el reemplazo backward-compatible: ChannelFormat tiene `.structure_hint: str` y synthesizer lee eso (no la dataclass entera).
- **Markdown-allowed por canal**: WhatsApp Business API soporta `*bold*` `_italic_` `~strike~` y triple-backtick code blocks, pero NO links markdown `[text](url)` (debe ser texto plano + URL inline). Email permite full markdown si client renderiza HTML. SMS NO permite nada (160 chars by default, segmenta en multi-part). Cada spec verificada en research mandate.
- **Max chars truncation**: synthesizer hoy NO trunca (genera prosa libre). F7 debe decidir: ¿truncar agresivo en synthesizer vs dejar al cliente FE? Recomendación: synthesizer respeta `max_chars` del format y trunca con `…` final si excede; format con `max_chars=None` significa sin límite.
- **Custom channels via providers**: plan F7 §5 menciona `register_channel(format)` para providers que registren canales propios. Si F7 lo implementa, considerar que `discover_providers()` ya itera modules — extender con un nuevo sub-port `ChannelProvider` o añadir `register_channel` global mutable (el segundo es más simple pero introduce state global).
- **Test flaky `test_streaming_integration`** heredado F0/F1/F2/F3/F4/F5/F6. Si F7 toca synthesizer (probable — es el consumer del registry), correr aislado primero.

### Hooks F6 disponibles para F7

- `backend/src/modules/copilot/domain/workflow.py::Workflow` — `metadata: Mapping[str, Any]` field libre. F7 puede leer `wf.metadata.get("default_output_channel")` cuando haga el integration en orchestrator (F-pos). NO necesita cambiar schema.
- `backend/src/modules/copilot/application/tools/ask_tenant_data/synthesizer.py` — `output_channel: str` parameter ya wired. F7 reemplaza el `_CHANNEL_HINTS` dict adyacente con un import desde `domain/output_channels.py::CHANNEL_FORMATS`.
- `tests/architecture/test_workflow_compliance.py` — pattern de fitness test para registry-based features. F7 puede copiar la estructura para `test_channel_formatter_compliance.py`.
- `tests/architecture/test_ddd_boundaries.py::_PROVIDER_CONTRACT_IMPORTS` — F6 agregó `copilot.domain.workflow`. Patrón replicable si F7 hace `output_channels.py` provider contract.
- F-pos cutover de F6 (workflows live runtime) puede usar `ChannelFormat` para hidratar output del workflow synthesis — sinergia natural sin coordinación tight.
