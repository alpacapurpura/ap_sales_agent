# Prompt — Architect kickoff PR-1-cascade-bugs-recovery

> **Prerequisito:** `prompts/00-context-prep.md` ejecutado (CONTEXT-BRIEF.md ready). Architect lee el brief — NO re-lee 30-50k de docs.
>
> Spawn `nicolify-architect` (Opus 4.7[1M]) vía Agent tool con `model: "opus"`.

## Spawn pattern

```
Agent({
  description: "Architect PR-1 cascade-bugs-recovery",
  subagent_type: "nicolify-architect",
  model: "opus",
  prompt: <BLOQUE FIJO + BLOQUE VARIABLE abajo>
})
```

## Prompt body

```
[BLOQUE FIJO — cacheable, byte-idéntico entre invocaciones]

Sos `nicolify-architect` (Opus 4.7[1M]). Trabajo: producir CONTRACT.md full-stack para el PR especificado.

Step 0 OBLIGATORIO antes de cualquier acción:
  date -u +%Y-%m-%d   # captura today
  date -u +%Y         # captura {current_year} para WebSearch

NUNCA hardcodees fechas en CONTRACT.md. Usa la fecha capturada en Step 0 para:
- WebSearch queries: "LiteLLM proxy docker-compose mount config production {current_year}" (interpolación)
- § Research Notes: cita "accessed {YYYY-MM-DD}" desde Step 0
- Disclosure de cutoff: "Opus 4.7 cutoff Jan 2026; live researched on {today}"

Reglas duras:
- NO escribas código de implementación. Solo schemas + interfaces + decisiones arquitectónicas + grep evidence.
- CONTRACT debe ser ÚNICO consumido en paralelo por builders distintos según surface (negocio → nicolify-backend Sonnet; copilot/sales_agent → nicolify-agentic Opus; FE → nicolify-frontend Sonnet).
- SQLA 2.0 async + Pydantic v2 + structlog. Migrations idempotentes (raw SQL IF NOT EXISTS).
- Cada query con tenant_id filter (incl. get_by_id). response_model obligatorio en cada endpoint.
- Si detectás gap funcional en PR.md → flag en § 16 Open questions for PM y NO inventes solución.

Surface ownership (declara mapping en CONTRACT § 0):
- modules/copilot/, modules/sales_agent/ → nicolify-agentic + nicolify-agentic-auditor (skills: copilot-expert / sales-agent-expert + tessl__langgraph)
- modules/{brand,offer,landing,assets,analytics,advertising,social_media,scheduling,connections,iam,crm,core,shared}/ → nicolify-backend + nicolify-backend-auditor
- frontend/src/** → nicolify-frontend + nicolify-frontend-auditor
- infra (docker-compose.yml, config/litellm/) → ad-hoc PM-coordinated fix (NO builder estándar — propone surface owner explicito en § 0)

NO-NEW-LAYER rule (origen PR-3 PI-2 audit failure):
1. Lee CONTEXT-BRIEF.md § 7 (existing systems detected) + § 8 (EXTEND-vs-NEW recommendations)
2. Si § 7 reporta sistema con ≥80% overlap → diseña EXTEND, NO NEW
3. Si § 11 Faithfulness flag scan-incomplete → re-corre los greps tú mismo (Path B en agent definition)
4. Cita § 7 evidencia en CONTRACT § Existing Systems Audit
5. Auditor FAIL si detecta layer paralelo cuando había sistema 80%+ disponible

Step 0.4 Cross-session overlap check (REGLA M7 parallel-sessions):
- Sesiones paralelas activas: PI-3 (discovery), PI-4-brand-evolutive-maintenance/S1-cleanup-buyer-persona (active, brand module), PI-5-copilot-multicanal-telegram/S2 (sales_agent + copilot wiring)
- PI-4 toca brand module → posible overlap con Bug #7 (brand_data_adapter)
- Si CONTEXT-BRIEF § 6 lista archivos shared con PI-4 → flag en § 16 Open questions for PM con paths exactos. PM coordina con sesión PI-4 antes builder spawn.

State-of-the-art research (DATE-AWARE):
- WebFetch canonical URLs (nunca obsoletas):
  · LiteLLM docs: https://docs.litellm.ai/docs/proxy/quick_start
  · Docker compose mount syntax: https://docs.docker.com/compose/compose-file/
  · FastAPI: https://fastapi.tiangolo.com/
  · Pydantic v2 ↔ SQLA conversion: https://docs.pydantic.dev/latest/concepts/models/
- WebSearch: interpolar {current_year} de Step 0
- mcp__tessl__query_library_docs si tile existe (mcp__tessl__outdated antes si dudas de staleness)
- Cita en § 15 Research Notes: URL + accessed {YYYY-MM-DD desde Step 0}

Skills domain a invocar antes de diseñar:
- backend-expert (brand surface backend)
- brand-expert (PersonalityProfile schema + adapter pattern)
- sales-agent-expert (consume `knowledge_builder.build_identity` — verifica downstream impact)
- tessl__graceful-degradation (LLM resilience post-fix recommendation)

Output: CONTRACT.md siguiendo template del agent definition (§ 0-§ 16). § 0 Context Summary debe declarar:
- Architect run on: {today YYYY-MM-DD}
- Surface → builder → auditor mapping (PM lo usa para spawn correcto)
- CONTEXT-BRIEF source: ¿usaste § 7 + § 8 de Haiku context-builder?
- Skills consulted con decisiones tomadas
- Scope decision: 1 PR cohesivo cross-surface vs split en 2 paralelos (BE brand + infra litellm) — justificá con razones
- Order of execution recommendation: Bug #9 first (sin LLM no smoke verify Bug #7) o Bug #7 first (test unit independiente del LLM stack)

Última línea de tu respuesta MUST ser:
<!-- @pm: CONTRACT.md ready. Surface mapping declared in § 0. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-1 architect done" para review. -->

Reportar a Chris brief < 200 palabras: qué decidiste + open questions + scope decision (single PR vs split) + EXTEND-vs-NEW decision si aplica.

[BLOQUE VARIABLE — específico de este PR]

PR folder: docs/pm-nico/pis/active/PI-7-app-stability-restore/sprints/S1-cascade-bugs-fix/prs/PR-1-cascade-bugs-recovery
Modules touched: brand (módulo backend negocio) + infra (docker-compose / litellm config)
Surface scope: cross-surface (business + infra) — single PR cohesivo (architect puede dictaminar split)

Bugs en scope:
- Bug #7: backend/src/modules/brand/application/services/brand_data_adapter.py:46 — `PersonalityProfileModel.model_dump` AttributeError (SQLA ORM tratado como Pydantic)
- Bug #9: visionarias_litellm container exited (127) — docker mount /app/config.yaml conflict (file vs directory)

Smoke target post-fix: Chris manda "hola" al visionarias_bot Telegram → bot responde greeting voice-tenant Visionarias (no error fallback).
Tenant test: 6347e21e-8112-4aa1-80d3-6adaa73bf6f9 (visionarias).
Lead test Telegram: cb711aea-e0a5-42c0-b276-7a63570207bd (chalreme).

Lectura obligatoria (en orden):
1. {pr_folder}/CONTEXT-BRIEF.md (Haiku Pre-flight) — lee § 7 + § 8 ANTES de cualquier diseño
2. {pr_folder}/PR.md — problema + bugs detallados + walking skeleton
3. CLAUDE.md — project constraints (solo si CONTEXT-BRIEF.md no está disponible)
4. .claude/rules/anti-duplication.md — verificar inventario shared abstractions
5. backend/src/modules/brand/application/services/brand_data_adapter.py:1-100 — leer file completo para context Bug #7
6. backend/src/modules/sales_agent/application/services/knowledge_builder.py — caller upstream de get_brand_knowledge
7. docker-compose.yml o equivalente — buscar service `litellm` y mount `config.yaml`
8. config/litellm.config.yaml — leer estructura actual (si existe)

Output: {pr_folder}/CONTRACT.md
```

## Cómo usar

1. Spawn vía Agent tool con `model: "opus"` o copy-paste a nueva sesión Opus.
2. Architect Step 0 captura date dinámicamente — PM no necesita pasar fecha.
3. Si Opus paused mid-task → SendMessage con agentId previo, NO re-spawn fresh ni fallback PM.
