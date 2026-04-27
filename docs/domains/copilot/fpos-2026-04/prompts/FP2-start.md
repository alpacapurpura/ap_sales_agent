```markdown
Iniciar FP2 plan fpos-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión FP2

Cerrar B24-TP11: `format_for_channel` tool no se invoca cuando user pide "copy WhatsApp / email / SMS" porque Kimi K2.6 phrasing-sensitive (B11-TP6) lo descubre inconsistente. Force-bind el tool vía middleware en chat orchestrator cuando user msg matches keywords canal (whatsapp/wa/email/correo/sms/texto), con accent + case insensitive y guard contra false positives (URL mention `whatsapp.com` ≠ channel intent). H7 PASS.

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/fpos-2026-04/README.md`
2. `docs/domains/copilot/fpos-2026-04/02-fpos-plan.md`
3. `docs/domains/copilot/fpos-2026-04/04-protocol.md`
4. `docs/domains/copilot/fpos-2026-04/phases/FP2-channel-format-trigger.md`
5. `docs/domains/copilot/fpos-2026-04/results/FP1-2026-04-26.md` (aprendizajes corrida previa, especialmente §Aprendizajes para FP2)
6. `docs/domains/copilot/testing-2026-04/results/TP11-2026-04-26.md` (origen B24)
7. `docs/domains/copilot/testing-2026-04/04-protocol.md` (protocolo padre)
8. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md` + `.claude/rules/backend-ddd.md`
9. `backend/src/modules/copilot/application/orchestrator/chat.py` (`_build_dynamic_tools` + `_record_routing_decision`)
10. `backend/src/modules/copilot/application/orchestrator/tools/registry.py` (ROUTE_TOOL_MAP + `_build_route_tool_map()` post-B20-TP10)
11. `backend/src/modules/copilot/application/tools/format_for_channel.py`

## Pre-research obligatorio

Mínimo 2 web searches del Research mandate listado en `phases/FP2-channel-format-trigger.md §Research mandate`:
- `langchain force tool selection trigger keyword 2026 middleware`
- `intent classification short utterance LLM 2026 keyword vs embedding`
- `deepagents tool routing middleware before_model 2026`

Tessl tiles: `tessl__langgraph` (deepagents está sobre langgraph 0.6+).

## Setup heredado (NO rehacer — verificado en FP1)

- TP11 cerrado, B23-TP11 voseo system prompts fix vivo (commit `ed18daef`).
- **FP1 cerrado:** `MutationApplyService` + `BrandFieldApplyPort` + ProposalCard fallback + idempotency live (`ux_copilot_mutation_journal_active_natural_key` partial UNIQUE en migration 074). Sub-FP1.1/1.2/1.3 documentados pero deferred — no bloquean FP2.
- Tenant test primario: visionarias-v4 `9ba0b29a-8507-424f-a48a-896f93218a25` (tenant_profile completo, brand_summary 0, ahora con `identity.brand_name="VisionariasFP1Live"` post live e2e — limpiar si confunde escenarios).
- Sprint 0 routing: AGENT=Kimi K2.6 (no-thinking, temp 0.6) + REASONING=DeepSeek + NANO/FAST=OpenAI.
- deepagents 0.5.3.
- Span tree B15-TP8 vivo + plan_card B18-TP9 vivo + ROUTE_TOOL_MAP B20-TP10 wired.

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short
docker compose ps
.venv/bin/python -c "import deepagents; print(deepagents.__version__)"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:3000
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8000/docs

# CRÍTICO FP2 — verificar tool format_for_channel + registry vivos:
.venv/bin/python -c "from src.modules.copilot.application.tools.format_for_channel import format_for_channel; print(format_for_channel.name)"
.venv/bin/python -c "from src.modules.copilot.application.orchestrator.tools.registry import ROUTE_TOOL_MAP; print(list(ROUTE_TOOL_MAP)[:5])"
```

## Aprendizajes accionables de FP1

1. F1 ratchet `test_no_new_copilot_module_imports` se viola fácil con direct repo import. Cualquier middleware nuevo que necesite acceso a otros modules debe ir via port en `shared/links/ports/`. Adapter en `{domain}/application/services/`.
2. `MutationApplyService` registry pattern (`register_apply_handler`) replicable si FP2 necesita per-channel formatter dispatcher. Patrón: `_HANDLERS: dict[str, ChannelFormatter]` + `register_channel_formatter(channel, fn)`. Wiring en `copilot/application/services/__init__.py`.
3. **TDD inline + live curl + SQL probe = ciclo de 25 min replicable.** RED test antes código, GREEN al cerrar capa, live re-validation con `copilot_trace_event WHERE name='format_for_channel'` SQL probe es más barato que Chrome DevTools E2E. Aplicar mismo flow FP2.

## Anomalías heredadas FP1

- **Sub-FP1.1 (DEFERRED):** offer + buyer_persona handlers requieren `entity_id` extension. Brand domain solo en FP1. FP2 no lo destraba.
- **Sub-FP1.2 (DEFERRED):** verificar SSE proposal emit incluye `message_id` consistente — si no, FP2 (que toca chat.py) puede dejar la verificación lista.
- **Sub-FP1.3 (HEREDADO TP4):** 3 tests pre-existentes flaky (`test_conversation_count_question`, `test_lead_count_question_returns_number`, `test_route_tool_selection_matches_baseline`). NO bloquean FP2.

## Reglas non-negotiables

1. Acceptance criteria mandatorio (no scenarios+5 ejes — eso es TP).
2. TDD obligatorio: test RED → fix → GREEN.
3. Root cause obligatorio. NO `# noqa`, NO `pytest.skip`, NO mock-tape-error.
4. Before/After evidence en results — sin SQL probe / trace event / curl output, AC no se cierra.
5. Spanish neutro LatAm (regla 11) en cualquier user-facing tocado (incluye output `format_for_channel`).
6. Native-first WSL — lint/tests/eval native, NUNCA `docker exec` para lint/tests/type-check.
7. Stage por nombre commits (parallel-safety).
8. Tenant isolation en cualquier nuevo middleware (regla `tenant-isolation.md`).
9. F1 ratchet — NO direct cross-module imports desde copilot. Port pattern obligatorio si necesitás otro module.

## Output esperado al cerrar FP2

1. `docs/domains/copilot/fpos-2026-04/results/FP2-{YYYY-MM-DD}.md` con:
   - Pre-research insights
   - AC1-AC7 checklist con before/after evidence (curl + trace event SQL probe)
   - Tests added (count + paths)
   - Sub-bugs descubiertos (si los hubo)
   - Métricas: latency overhead middleware (objetivo <50ms p50)
   - **§Aprendizajes para FP3** (1-3 bullets accionables)
   - **§Handoff FP3** referencia a `prompts/FP3-start.md`
2. Si `phases/FP2-channel-format-trigger.md` cambió → commit incluido.
3. **Generar `prompts/FP3-start.md`** (template canónico §Anexo A del `04-protocol.md`).
4. Commits conventional + push origin/development:
   - `feat(copilot-fpos2): channel intent middleware + force-bind format_for_channel (B24)`
   - Tests + docs en su commit propio si crece mucho.
5. Reporte al user: 3 líneas resumen + score H7 mejora + paths a results/.

## Anti-patrones (no caer)

- Reportar AC sin evidence concreta (sin SQL probe / sin trace event / sin curl).
- Hardcodear keywords en tool registry sin tests.
- Cerrar FP2 con sub-bug abierto sin TDD.
- Spawnear sub-agentes para AC paralelos (FP necesita context completo + fix iteration).
- Embedding similarity para channel detection — overengineering. Regex normalizada (lowercase + accent strip) es suficiente per pre-research insights.
- Llenar reporte con info no accionable.

## Si te trabás

- Middleware no se gatilla → SQL probe `copilot_trace_event WHERE event_type='node_enter' AND name LIKE '%route%'` ver el orden.
- False positive `whatsapp.com` URL → guard regex con boundary + URL detection antes del keyword match.
- Bridge tool no se incluye en bound set → revisar `_build_dynamic_tools` order: middleware DEBE correr ANTES del tools.bind.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2. Recién después tocás tools.
```
