# Prompt — Architect kickoff

> **Prerequisito:** ejecutar `prompts/00-context-prep.md` primero (Haiku produce CONTEXT-BRIEF.md). Architect lee el brief — NO re-lee 30-50k de docs.
>
> Spawn `nicolify-architect` (Opus 4.7[1M]) vía Agent tool con `model: "opus"`.

## Spawn pattern

```
Agent({
  description: "Architect PR-{n}",
  subagent_type: "nicolify-architect",
  model: "opus",
  prompt: <BLOQUE FIJO + BLOQUE VARIABLE abajo>
})
```

**Cache prefix discipline:** estructura del prompt en dos partes — BLOQUE FIJO byte-idéntico entre invocaciones (cacheable) + BLOQUE VARIABLE específico por PR (no cached). Si arquitect re-spawnea para refinar, mantener BLOQUE FIJO IDÉNTICO.

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
- CONTRACT debe ser ÚNICO consumido en paralelo por builders distintos según surface (negocio → nicolify-backend Sonnet; copilot/sales_agent → nicolify-agentic Opus; FE → nicolify-frontend Sonnet).
- SQLA 2.0 async + Pydantic v2 + structlog. Migrations idempotentes (raw SQL IF NOT EXISTS).
- Cada query con tenant_id filter (incl. get_by_id). response_model obligatorio en cada endpoint.
- Si detectás gap funcional en PR.md → flag en § 16 Open questions for PM y NO inventes solución.

Surface ownership (declara mapping en CONTRACT § 0):
- modules/copilot/, modules/sales_agent/ → nicolify-agentic + nicolify-agentic-auditor (skills: copilot-expert / sales-agent-expert + tessl__langgraph)
- modules/{brand,offer,landing,assets,analytics,advertising,social_media,scheduling,connections,iam,crm,core,shared}/ → nicolify-backend + nicolify-backend-auditor
- frontend/src/** → nicolify-frontend + nicolify-frontend-auditor

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
  · Next.js: https://nextjs.org/docs
- WebSearch: interpolar {current_year} de Step 0
- mcp__tessl__query_library_docs si tile existe (mcp__tessl__outdated antes si dudas de staleness)
- Cita en § 15 Research Notes: URL + accessed {YYYY-MM-DD desde Step 0}

Skills domain a invocar antes de diseñar (uno por surface tocada):
- copilot/sales_agent → copilot-expert / sales-agent-expert + tessl__langgraph + tessl__graceful-degradation
- brand → brand-expert
- offer/preset → offer-expert / offer-type-preset-expert
- analytics → metrics-expert
- backend infra → backend-expert
- FE → frontend-expert

Output: CONTRACT.md siguiendo template del agent definition (§ 0-§ 16). § 0 Context Summary debe declarar:
- Architect run on: {today YYYY-MM-DD}
- Surface → builder → auditor mapping (PM lo usa para spawn correcto)
- CONTEXT-BRIEF source: ¿usaste § 7 + § 8 de Haiku context-builder?
- Skills consulted con decisiones tomadas

Última línea de tu respuesta MUST ser:
<!-- @pm: CONTRACT.md ready. Surface mapping declared in § 0. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-{n} architect done" para review. -->

Reportar a Chris brief < 200 palabras: qué decidiste + open questions + EXTEND-vs-NEW decision si aplica.

[BLOQUE VARIABLE — específico de este PR]

PR folder: docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S1-foundation-telegram-bot/prs/PR-1-telegram-bot-foundation
Modules touched: copilot (primary, agentic surface), shared (reuse `agent_observability/channels/format.py::escape_markdown_v2`), core (add `COPILOT_TELEGRAM_BOT_TOKEN` env var to Settings), frontend (new `app/(main)/[tenantId]/(dashboard)/settings/copilot/telegram/`)
Surface scope: cross-stack (agentic + frontend) — NO toca módulos negocio. NO toca `modules/connections/` (D-PI5-005 separación física)

Lectura obligatoria (en orden):
1. {pr_folder}/CONTEXT-BRIEF.md (Haiku Pre-flight) — lee § 7 + § 8 ANTES de cualquier diseño
2. {pr_folder}/PR.md — problema + solución elegida + scope + decisiones diferidas
3. /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/decisions.md — D-PI5-001..031 (especialmente D-PI5-005 separación física, D-PI5-006..009 memory diferida S2, D-PI5-019..022 magic link, D-PI5-023..025 tool subset, D-PI5-026..031 escalabilidad+seguridad)
4. /home/chris/AISALESHT/docs/pm-nico/research/2026-04-30-telegram-bot-copilot-patterns.md — 7 secciones research + paths código referencia §"Código Nicolify de referencia"

Paths código referencia (READ para diseñar EXTEND vs NEW):
- backend/src/modules/connections/api/telegram.py (referencia webhook pattern sales_agent — NO modificar)
- backend/src/modules/connections/infrastructure/channels/telegram.py (referencia adapter pattern sales_agent — NO modificar)
- backend/src/modules/copilot/application/orchestrator/system_prompt_layout.py (cache boundary pattern)
- backend/src/modules/copilot/application/tools/registry.py (extender con `ToolGroupMeta.available_channels`)
- backend/src/modules/copilot/infrastructure/models/conversation_model.py (EXTEND con cols `channel_type` + `channel_chat_id`)
- backend/src/modules/copilot/infrastructure/prompts/sanitizer.py (reuso `sanitize_payload` antes persistir)
- backend/src/shared/agent_observability/channels/format.py (reuso `escape_markdown_v2`)
- backend/src/shared/links/ports/conversational_channel.py (port existente — verificar si fits el bot adapter)

Decisiones críticas que CONTRACT debe formalizar:
- Schema cols nuevas `copilot_conversations.channel_type` + `channel_chat_id` (migration idempotente)
- Schema tablas nuevas `copilot_channel_links` + `copilot_link_tokens` (research §2 §4 schemas)
- Endpoint `/api/v1/copilot/telegram/webhook` (POST, non-blocking) — request/response Pydantic v2
- Endpoint `/api/v1/copilot/telegram/link-tokens` (POST, autenticado) — genera token + deep_link_url
- Endpoint `/api/v1/copilot/telegram/link-status` (GET, autenticado) — polling FE
- ARQ worker `copilot_telegram_turns` queue + job signature
- Cross-module port: NINGUNO (cero acoplamiento copilot↔sales_agent en este PR; HITL es S3)
- Arch fitness tests específicos (research §7 + PR.md "Arch fitness")

Open questions to flag § 16 (NO inventes):
- Si `connections/infrastructure/channels/telegram.py` ya tiene helper que justifica EXTEND vs NEW por reuso shared
- Si `shared/links/ports/conversational_channel.py` cubre el contract bot adapter o si necesita extension/wrapper

Output: {pr_folder}/CONTRACT.md + {pr_folder}/UI-SPEC.md (este último spawnea `ux-flow-architect` skill paralelo desde tu sesión architect, no separado)
```

## Cómo usar

1. PM ya pre-llenó BLOQUE VARIABLE con paths reales PR-1.
2. Chris spawn vía Agent tool con `subagent_type: "nicolify-architect"` + `model: "opus"`, pasando todo el body del prompt.
3. Architect Step 0 captura date dinámicamente — PM no pasa fecha.
4. Architect retorna brief en chat + escribe CONTRACT.md + spawnea ux-flow-architect skill para UI-SPEC.md.
