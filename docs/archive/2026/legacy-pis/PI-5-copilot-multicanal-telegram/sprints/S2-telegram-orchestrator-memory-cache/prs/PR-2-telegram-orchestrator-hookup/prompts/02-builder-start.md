# Prompt — Builder kickoff (auto-audit loop)

> **Prerequisitos:** `prompts/00-context-prep.md` ejecutado (CONTEXT-BRIEF.md ready) + `prompts/01-architect-start.md` ejecutado (CONTRACT.md ready).
>
> PR-2 = single surface AGENTIC → builder único `nicolify-agentic` (Opus). NO paralelización (cero FE, cero backend negocio).
>
> Builder spawnea auditor automáticamente al terminar — Chris recibe código YA AUDITADO Y CORREGIDO.

## Spawn pattern

```
Agent({
  description: "Build PR-2 telegram-orchestrator-hookup agentic",
  subagent_type: "nicolify-agentic",
  model: "opus",
  prompt: <BLOQUE FIJO + BLOQUE VARIABLE abajo>
})
```

**Cache prefix discipline:** BLOQUE FIJO byte-idéntico entre fix-loop iters → cache hit en iter 2-3.

## Prompt body

```
[BLOQUE FIJO — cacheable, byte-idéntico entre fix-loop iters]

Sos `nicolify-agentic`. Trabajo: implementar PR completo siguiendo CONTRACT.md + auto-spawn gate-runner + auditor + fix loop hasta PASS.

Step 0 OBLIGATORIO:
  date -u +%Y-%m-%d   # captura today
NUNCA hardcodees fechas. Cita "accessed {YYYY-MM-DD}" desde Step 0 en IMPL-LOG.md § State-of-the-art validation si validás patterns live.

Lectura obligatoria (en orden):
1. {pr_folder}/CONTEXT-BRIEF.md — pre-flight Haiku (lee § 7 + § 8 SI tu builder modificará subsystem; cita en IMPL-LOG)
2. {pr_folder}/CONTRACT.md — schemas + interfaces + decisiones (SSoT pre-implementación)
3. {pr_folder}/PR.md — problema + scope (si CONTEXT-BRIEF está incompleto)
4. CLAUDE.md (root) — sección "Git Workflow — INVIOLABLE"

Skills obligatorios (invoca via Skill tool ANTES de tocar código):
- copilot-expert (memory + orchestrator + tool registry + cache fragments deep knowledge)
- tessl__langgraph (state machine patterns si orchestrator usa LangGraph)
- tessl__graceful-degradation (timeout/fallback si orchestrator dependencies fallan)

Restricciones DURAS:
- Tocás SOLO archivos de tu surface según CONTRACT § 0 mapping. Lista paths permitidos derivada del CONTRACT — para PR-2: modules/copilot/{application/memory,application/orchestrator,application/tools,infrastructure/workers,infrastructure/repositories,domain/context_window}/, shared/agent_observability/channels/format.py READ ONLY.
- nicolify-agentic NO toca modules/{brand,offer,landing,assets,analytics,advertising,social_media,scheduling,connections,iam,crm}/ (escalate nicolify-backend).
- nicolify-agentic NO toca frontend/ (cero cambios FE PR-2).
- NO tocás archivos de otros PRs activos (regla M7). git status ajenos → DEJAR INTACTOS.
- PROHIBIDO: git pull, git fetch && merge, git push --force, git revert, git reset --hard, git add .|-A|-u, git commit --no-verify, branches/worktrees.
- Push falla non-fast-forward → STOP, reportar Chris. NO git pull para resolver.

Workflow Phase 1 — IMPLEMENT:
1. TDD strict: tests RED ANTES implementación. Capa por capa (domain → application → infrastructure).
2. Implementar cada sub-deliverable del CONTRACT secuencialmente:
   a. `TELEGRAM_CONTEXT_WINDOW_CONFIG` constant en domain/application memory
   b. EXTEND `ContextWindowBuilder` + `RollingSummarizer` con param `channel` (default 'web' backward compat)
   c. EXTEND `system_prompt_layout.py` con `TELEGRAM_CHANNEL_CONTEXT` cacheable fragment ≥1024 tokens (condicional `context.channel == 'telegram'`)
   d. EXTEND orchestrator entrypoint con `channel` param + propagación a memory builder + tool registry + format adapter
   e. EXTEND `CopilotConversationRepository` con `get_or_create_by_channel`
   f. REPLACE placeholder reply en `telegram_worker.py` con `await invoke_copilot_orchestrator(channel='telegram', ...)` + format adapter + bot.send_message
   g. Tests: integration end-to-end (3 cases) + memory config inyección + tool filter runtime + arch fitness cache prefix
3. NO migration nueva (cols ya en PR-1). Si descubrís que falta col → STOP, escalate PM (no inventes migration).
4. Quality gates locales NATIVE (sin docker exec):
   - cd backend && .venv/bin/{ruff|pytest|mypy}
5. Si bloqueado arquitectónicamente → STOP, append a IMPL-LOG.md, devolver control a PM (NO inventar solución).
6. Llenar IMPL-LOG.md completo (sub-deliverables, EXTEND-vs-NEW resoluciones por subsistema, skills consultadas, tests añadidos, gates pasados, commits, State-of-the-art validation accessed dates).
7. Stage por nombre + conventional commit + push origin development.

Workflow Phase 2 — AUTO-GATE-RUN + AUTO-AUDIT (obligatorio):

Phase 2.1 — Spawn gate-runner Haiku:
8. Agent({
     description: "Run /test-backend gates iter-1",
     subagent_type: "nicolify-gate-runner",
     model: "haiku",
     prompt: "<pr_folder>: {abs path}; <command>: test-backend; <iter>: 1"
   })
9. Esperá gate-output.json. Si overall.any_fail = true → fix scope findings, re-stage + re-commit + re-spawn gate-runner. NO sigas a Phase 2.2 hasta gates green.

Phase 2.2 — Spawn auditor Opus:
10. Agent({
      description: "Audit PR-2 agentic",
      subagent_type: "nicolify-agentic-auditor",
      model: "opus",
      prompt: "<pr_folder>: {abs path}; iter: 1"
    })
11. Esperá REVIEW-agentic.md output. Lee verdict.
12. Si verdict = PASS → terminás. Última línea respuesta:
    <!-- @pm: implementación + gate-runner + auditoría done (verdict PASS). PR-2 listo para /pm "PR-2 cerrar" -->
13. Si verdict = WARN o FAIL → entra Phase 3.

Workflow Phase 3 — AUTO-FIX LOOP (max 3 iteraciones):
14. Lee findings file:line del REVIEW-agentic.md. Filtrá findings que tocan paths de TU surface (regla M7).
15. Para cada finding FAIL/WARN dentro scope:
    - Si finding == drift CONTRACT vs código → STOP fix, NO inventes solución. Append IMPL-LOG bloqueador "Drift CONTRACT — escalate PM". Devuelve control con verdict actual + nota.
    - Si finding == missing test/typo/hardcoded value/refactor menor → fixá.
    - Si finding == arquitectónico (cambia design CONTRACT) → STOP, escalate PM.
    - Si finding == NO-NEW-LAYER violation → STOP, escalate PM (auditor detectó duplicado vs sistema existente — decisión contractual).
16. Quality gates locales re-run NATIVE.
17. Stage por nombre + conventional commit `fix(copilot): address auditor findings iter-{N}` + push.
18. Re-spawn gate-runner Haiku (Phase 2.1) — produce gate-output.iter-{N}.json (preserva el anterior).
19. Re-spawn auditor Opus (Phase 2.2). Iter ++.
20. Si iter == 3 y verdict aún ≠ PASS → STOP. Append IMPL-LOG "Max iterations reached, escalate PM". Última línea:
    <!-- @pm: implementación done, auditoría WARN/FAIL tras 3 iter. Findings pendientes: {lista}. Escalate /pm "PR-2 fix-loop maxed" -->

Outputs:
- Code + tests en codebase (committed + pushed)
- IMPL-LOG.md completo (Skills consulted, EXTEND-vs-NEW decisions por subsistema, Auto-fix iterations si entró Phase 3, State-of-the-art validation accessed dates)
- gate-output.json final + gate-output.iter-N.json preserved si hubo iteraciones
- REVIEW-agentic.md final (output último auditor run)
- Commits conventional: feat(copilot): ..., fix(copilot): address auditor findings iter-N, test(copilot): ...

Reportar a Chris brief < 300 palabras: qué se implementó + tests verdes + iteraciones gate-runner + iteraciones audit + verdict final + bloqueadores escalados a PM (si los hay).

[BLOQUE VARIABLE — específico de este PR]

Surface a implementar: AGENTIC SINGLE (modules/copilot/) — NO cross-stack, NO cross-scope, NO paralelización.
PR folder: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S2-telegram-orchestrator-memory-cache/prs/PR-2-telegram-orchestrator-hookup
Modules touched (agentic builder único): copilot/application/memory/, copilot/application/orchestrator/, copilot/application/tools/ (verificación), copilot/infrastructure/workers/telegram_worker.py, copilot/infrastructure/repositories/, copilot/domain/context_window.py (si aplica).
READ ONLY (no modificar): backend/src/shared/agent_observability/channels/format.py::escape_markdown_v2 (reuso).
Iter actual: 1

PR-2 specific reminders:
- D-PI5-006 valores `TELEGRAM_CONTEXT_WINDOW_CONFIG`: RAW_WINDOW_TOKENS=3000, RAW_WINDOW_MAX_MESSAGES=15, RAW_WINDOW_MIN_MESSAGES=4, SUMMARY_MAX_CHARS=600, SUMMARY_TARGET_TOKENS=200, NUDGE_AFTER_TOTAL_TOKENS=12000, NUDGE_HARD_LIMIT_TOKENS=20000, NUDGE_AFTER_MESSAGE_COUNT=20.
- D-PI5-007: reusar `CopilotConversationModel` con cols `channel_type`+`channel_chat_id` (ya live PR-1).
- D-PI5-008: NO vector retrieval Qdrant en MVP. NO añadir embedding code.
- D-PI5-009: `TELEGRAM_CHANNEL_CONTEXT` fragment ≥1024 tokens cacheable. Contenido byte-idéntico entre invocaciones (NO timestamps, NO tenant_name interpolado mid-block, NO conversation_id — esos rompen cache).
- D-PI5-024 tool subset SSoT ya implementado PR-1 (`ToolGroupMeta.available_channels`). Builder verifica que orchestrator pasa `channel='telegram'` a `get_tools_for_context()` correctly.
- D-PI5-IMPL-001..006 PR-1: contexto histórico decisiones implementación foundation.
- HITL escalation (D-PI5-010..014) = OUT OF SCOPE PR-2, S3 PR-3.
- Push notifs proactivas = OUT OF SCOPE PR-2, S4 PR-4.
- Migration 114 fix pre-existing = OUT OF SCOPE (separate ticket).
- Test integration mock pattern: usar `pytest-asyncio` + `unittest.mock.AsyncMock` para `bot.send_message`, `arq.connections.create_pool`, orchestrator deps. NO real DB connection en tests integration (usar `pytest` async fixtures con `AsyncSession` factory rolled-back).
- Arch fitness sample compute: fixture tenant minimal sin studio_snapshot/form_data + cuenta tokens via `tiktoken` o equivalente ya disponible en codebase. Threshold ≥1024 con margin (target ≥1100 para safety).
- Backward compat: cualquier signature change en `ContextWindowBuilder` / `RollingSummarizer` / orchestrator entrypoint debe usar default `channel='web'` para preservar call sites web pre-existentes. Tests baseline web pre-existing pass sin cambios.
```

## Auto-loop fail-safe

- Max 3 iter fix → escalate PM. Evita bucles infinitos sobre findings irresolvibles arquitectónicamente.
- Findings drift CONTRACT → STOP iter 1 → escalate PM (decisión contractual, no fix-by-builder).
- Findings cross-PR → ignorar + nota IMPL-LOG (regla M7).
- Findings NO-NEW-LAYER violation → STOP, escalate PM.
- Push falla non-fast-forward → STOP cualquier fase → escalate Chris. NO git pull.

## Cache prefix discipline (ahorro tokens en iter 2-3)

El BLOQUE FIJO arriba es cacheable — entre iter 1 y iter 2 (fix-loop), el prefix se mantiene byte-idéntico → 80%+ del input cached → ~10% del costo en iter 2 y 3.

NO inyectes timestamps, hashes, conversation_id, tenant_name dentro del BLOQUE FIJO. Solo el BLOQUE VARIABLE puede tener `iter actual: {N}`.
