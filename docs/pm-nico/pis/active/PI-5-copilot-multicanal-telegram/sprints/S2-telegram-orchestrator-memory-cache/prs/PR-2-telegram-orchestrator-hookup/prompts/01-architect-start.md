# Prompt — Architect kickoff

> **Prerequisito:** ejecutar `prompts/00-context-prep.md` primero (Haiku produce CONTEXT-BRIEF.md). Architect lee el brief — NO re-lee 30-50k de docs.
>
> Spawn `nicolify-architect` (Opus 4.7[1M]) vía Agent tool con `model: "opus"`.

## Spawn pattern

```
Agent({
  description: "Architect PR-2 telegram-orchestrator-hookup",
  subagent_type: "nicolify-architect",
  model: "opus",
  prompt: <BLOQUE FIJO + BLOQUE VARIABLE abajo>
})
```

**Cache prefix discipline:** estructura del prompt en dos partes — BLOQUE FIJO byte-idéntico entre invocaciones (cacheable) + BLOQUE VARIABLE específico por PR (no cached).

## Prompt body

```
[BLOQUE FIJO — cacheable, byte-idéntico entre invocaciones]

Sos `nicolify-architect` (Opus 4.7[1M]). Trabajo: producir CONTRACT.md full-stack para el PR especificado.

Step 0 OBLIGATORIO antes de cualquier acción:
  date -u +%Y-%m-%d   # captura today
  date -u +%Y         # captura {current_year} para WebSearch

NUNCA hardcodees fechas en CONTRACT.md. Usa la fecha capturada en Step 0 para:
- WebSearch queries: "LangGraph supervisor production {current_year}" (interpolación)
- § Research Notes: cita "accessed {YYYY-MM-DD}" desde Step 0
- Disclosure de cutoff cuando aplica: "Opus 4.7 cutoff Jan 2026; live researched on {today}"

Reglas duras:
- NO escribas código de implementación. Solo schemas + interfaces + decisiones arquitectónicas.
- CONTRACT debe ser ÚNICO consumido por builder según surface. Para PR-2 single surface = nicolify-agentic Opus.
- SQLA 2.0 async + Pydantic v2 + structlog. Migrations idempotentes (raw SQL IF NOT EXISTS) — PR-2 NO requiere migration nueva (cols ya en PR-1).
- Cada query con tenant_id filter (incl. get_by_id). response_model obligatorio en cada endpoint.
- Si detectás gap funcional en PR.md → flag en § 16 Open questions for PM y NO inventes solución.

Surface ownership (declara mapping en CONTRACT § 0):
- modules/copilot/, modules/sales_agent/ → nicolify-agentic + nicolify-agentic-auditor (skills: copilot-expert / sales-agent-expert + tessl__langgraph)
- modules/{brand,offer,landing,assets,analytics,advertising,social_media,scheduling,connections,iam,crm,core,shared}/ → nicolify-backend + nicolify-backend-auditor
- frontend/src/** → nicolify-frontend + nicolify-frontend-auditor

PR-2 mapping específico:
- Single surface: AGENTIC (modules/copilot/) → nicolify-agentic (Opus) builder + nicolify-agentic-auditor (Opus)
- Cero backend negocio surface
- Cero frontend surface

NO-NEW-LAYER rule (origen PR-3 PI-2 audit failure):
1. Lee CONTEXT-BRIEF.md § 7 (existing systems detected) + § 8 (EXTEND-vs-NEW recommendations)
2. Si § 7 reporta sistema con ≥80% overlap → diseña EXTEND, NO NEW
3. Si § 11 Faithfulness flag scan-incomplete → re-corre los greps tú mismo (Path B en agent definition)
4. Cita § 7 evidencia en CONTRACT § Existing Systems Audit
5. Auditor FAIL si detecta layer paralelo cuando había sistema 80%+ disponible

State-of-the-art research (DATE-AWARE):
- WebFetch canonical URLs (nunca obsoletas):
  · LangGraph: https://docs.langchain.com/oss/python/langgraph/workflows-agents
  · deepagents: https://docs.langchain.com/oss/python/deepagents/overview
  · Anthropic prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
  · FastAPI: https://fastapi.tiangolo.com/
- WebSearch: interpolar {current_year} de Step 0
- mcp__tessl__query_library_docs si tile existe (mcp__tessl__outdated antes si dudas de staleness)
- Cita en § 15 Research Notes: URL + accessed {YYYY-MM-DD desde Step 0}

Skills domain a invocar antes de diseñar (single surface PR-2 = agentic):
- copilot/sales_agent → copilot-expert + tessl__langgraph + tessl__graceful-degradation

Output: CONTRACT.md siguiendo template del agent definition (§ 0-§ 16). § 0 Context Summary debe declarar:
- Architect run on: {today YYYY-MM-DD}
- Surface → builder → auditor mapping (PM lo usa para spawn correcto)
- CONTEXT-BRIEF source: ¿usaste § 7 + § 8 de Haiku context-builder?
- Skills consulted con decisiones tomadas

Última línea de tu respuesta MUST ser:
<!-- @pm: CONTRACT.md ready. Surface mapping declared in § 0 (agentic-only). Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-2 architect done" para review. -->

Reportar a Chris brief < 200 palabras: qué decidiste + open questions + EXTEND-vs-NEW decisions críticas (memory builder + cache fragment + orchestrator entrypoint).

[BLOQUE VARIABLE — específico de este PR]

PR folder: docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S2-telegram-orchestrator-memory-cache/prs/PR-2-telegram-orchestrator-hookup
Modules touched: copilot (single surface — application/memory + application/orchestrator + application/tools + infrastructure/workers + infrastructure/repositories), shared (READ ONLY reuse `agent_observability/channels/format.py::escape_markdown_v2`)
Surface scope: AGENTIC SINGLE — NO toca módulos negocio. NO toca frontend. NO toca DB schema (cols ya añadidas PR-1). NO toca migration.

Lectura obligatoria (en orden):
1. {pr_folder}/CONTEXT-BRIEF.md (Haiku Pre-flight) — lee § 7 + § 8 ANTES de cualquier diseño
2. {pr_folder}/PR.md — problema + solución elegida + scope + decisiones diferidas + Existing systems audit checklist
3. /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/decisions.md — D-PI5-006..D-PI5-009 (memory + cache fragment), D-PI5-023..D-PI5-025 (tool subset SSoT), D-PI5-IMPL-001..006 (PR-1 implementation decisions)
4. /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S1-foundation-telegram-bot/handoff.md — surface live PR-1 + plan macro S2
5. /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S1-foundation-telegram-bot/prs/PR-1-telegram-bot-foundation/RESULT.md — capability live + deuda técnica que S2 absorbe (orchestrator hookup placeholder, memory config faltante, cache fragment faltante)
6. /home/chris/AISALESHT/docs/pm-nico/research/2026-04-30-telegram-bot-copilot-patterns.md — §1 Conversation Memory Pattern + §6 Escalabilidad

Paths código referencia (READ para diseñar EXTEND vs NEW — TODO debe ser EXTEND, NO NEW):
- backend/src/modules/copilot/application/memory/context_window_builder.py (EXTEND con param `channel`)
- backend/src/modules/copilot/application/memory/rolling_summarizer.py (EXTEND con param `channel` si summary length distinto)
- backend/src/modules/copilot/domain/context_window.py (EXTEND con `TELEGRAM_CONTEXT_WINDOW_CONFIG` constant)
- backend/src/modules/copilot/application/orchestrator/system_prompt_layout.py (EXTEND `CACHEABLE_FRAGMENTS` con `TELEGRAM_CHANNEL_CONTEXT` condicional `context.channel == 'telegram'`)
- backend/src/modules/copilot/application/tools/registry.py (verificar `get_tools_for_context(channel='telegram')` ya soportado PR-1; orchestrator pasa correctly)
- backend/src/modules/copilot/application/orchestrator/{orchestrator entrypoint}.py (EXTEND aceptar `channel` param + propagar a memory + tool registry + format adapter)
- backend/src/modules/copilot/infrastructure/workers/telegram_worker.py (REPLACE placeholder reply con orchestrator real call)
- backend/src/modules/copilot/infrastructure/repositories/conversation_repository.py (EXTEND con `get_or_create_by_channel`)
- backend/src/modules/copilot/infrastructure/channels/telegram_bot.py (READ ONLY — bot adapter ya live PR-1)
- backend/src/modules/copilot/application/services/telegram_link_service.py (READ ONLY — linking ya live PR-1)
- backend/src/shared/agent_observability/channels/format.py::escape_markdown_v2 (READ ONLY — reuso)

Decisiones críticas que CONTRACT debe formalizar:
- `TELEGRAM_CONTEXT_WINDOW_CONFIG` constant (D-PI5-006 valores exactos)
- Inyección de config por canal en `ContextWindowBuilder` + `RollingSummarizer` — signature change vs lookup interno (preservar backward compat default 'web')
- `TELEGRAM_CHANNEL_CONTEXT` cacheable fragment design (qué contenido pones que sume ≥1024 tokens estables byte-idénticos — evitar timestamps/tenant_name interpolado mid-block que rompe cache)
- Tool registry filter runtime: cómo el orchestrator entrypoint pasa `channel='telegram'` a `get_tools_for_context()`
- Format adapter post-orchestrator: `format_for_channel(channel='telegram', parse_mode='MarkdownV2')` — si función existe reuso, si no diseñar interface delgada que internamente llame `escape_markdown_v2`
- Conversation lookup `get_or_create_by_channel(tenant_id, user_id, channel_type, channel_chat_id)` — concurrencia (UNIQUE constraint + ON CONFLICT vs SELECT FOR UPDATE)
- Orchestrator entrypoint signature: ¿acepta `channel` param hoy? Si no → cambio backward compat con default 'web'
- Test integration mock pattern: cómo mockear ARQ enqueue + worker + Telegram Bot API + orchestrator dependencies sin DB real
- Arch fitness sample compute: tenant minimal fixture + threshold 1024 con margin

Open questions to flag § 16 (NO inventes):
- Si `format_for_channel(channel, parse_mode)` ya existe vs hay que diseñarla (PR-1 puede haber introducido helper relacionado en `copilot/application/tools/telegram_redirect.py` o similar)
- Si orchestrator entrypoint actual acepta `channel` o requiere signature change
- Si `RollingSummarizer.SUMMARY_MAX_CHARS` está hardcoded vs configurable (D-PI5-006 quiere 600 telegram vs 400 web)

Output: {pr_folder}/CONTRACT.md — NO UI-SPEC.md (cero cambios FE PR-2).
```

## Cómo usar

1. PM ya pre-llenó BLOQUE VARIABLE con paths reales PR-2.
2. Chris spawn vía Agent tool con `subagent_type: "nicolify-architect"` + `model: "opus"`, pasando todo el body del prompt.
3. Architect Step 0 captura date dinámicamente — PM no pasa fecha.
4. Architect retorna brief en chat + escribe CONTRACT.md. NO spawnea ux-flow-architect (cero cambios FE PR-2).
