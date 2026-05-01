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

PR folder: docs/pm-nico/pis/active/PI-{X}-{theme}/sprints/S{N}-*/prs/PR-{n}-{slug}
Modules touched: {list — e.g., "copilot, brand"}
Surface scope: {agentic | business | frontend | cross-stack}

Lectura obligatoria (en orden):
1. {pr_folder}/CONTEXT-BRIEF.md (Haiku Pre-flight) — lee § 7 + § 8 ANTES de cualquier diseño
2. {pr_folder}/PR.md — problema + solución elegida + scope
3. CLAUDE.md — project constraints (solo si CONTEXT-BRIEF.md no está disponible)
4. Paths adicionales según PR: {ej: docs/etl/extraction-contract.md si analytics; docs/domains/sales_agent/ si sales_agent}

Output: {pr_folder}/CONTRACT.md
```

## Cómo usar

1. Reemplazar `{X}`, `{theme}`, `{N}`, `{n}`, `{slug}`, `{módulo}`, `{current_year}` (lo captura Step 0 del agent), con valores reales del PR. PM pre-llena BLOQUE VARIABLE.
2. Spawn vía Agent tool con `model: "opus"` o copy-paste a nueva sesión Opus.
3. Architect Step 0 captura date dinámicamente — PM no necesita pasar fecha.
