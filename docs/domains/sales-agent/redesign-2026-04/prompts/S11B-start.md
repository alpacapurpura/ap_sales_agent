# Handoff prompt · S11B start

> Pega esto al iniciar conversación nueva (sesión 2 de S11). Sub-sprint
> A cerrado en commit `8cc9ea2c`. Sub-sprint B = orchestrator
> decomposition Strangler Fig.

---

```
Continuamos redesign sales_agent — Sub-sprint B (orchestrator decomposition).

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Sub-fase: S11B — Strangler Fig orchestrator decomposition
📂 Doc fase: docs/domains/sales-agent/redesign-2026-04/phases/S11-shared-lift-orchestrator-decomp.md
   (sección "Diseño · Stranger Fig orchestrator" + "Plan TDD")
📝 Aprendizajes Sub-sprint A: docs/domains/sales-agent/redesign-2026-04/learnings/S11A-shared-base-lift.md

CONTEXTO:
- S11A cerrado en commit `8cc9ea2c`. BaseAgentCallbackHandler shared
  absorbe 8 callbacks LangChain + Template Method skeleton. Sales
  subclass 85 LOC, copilot subclass 83 LOC. 3270 tests verde.
- Snapshot framework determinístico activo en
  `tests/shared/agent_observability/test_callback_handler_snapshot.py` +
  `tests/snapshots/callback_handler/{sales,copilot}_handler_baseline.json`.
  Reusable para Sub-sprint B (extender para process_chat_flow).
- Pre-flight S11 (en S11A) decidió: snapshot determinístico de pipeline
  outputs en lugar de goldens LLM — porque S10 cerró 2026-04-28 sin
  histórico semanal. Sub-sprint B continúa con esa lógica: snapshot
  byte-equal pre/post-decomposition por commit.
- Files a descomponer:
  - `chat.py` 1140 LOC → < 400 LOC.
  - `closer_studio_service.py` 624 LOC → split Query/Command/Kpi.
  - `semantic_router.py` 329 LOC → registry-based + tenant overrides.
- §3 protected NO se toca: closer_studio.py API + ws.py +
  buffer_service.smart_debounce + output_manager.process_response +
  enrollment + agent_state_checkpoint schema + webhook adapters +
  follow_up_engine cadence.

ENTREGABLES Sub-sprint B (~7 días):

Orden de extracción Strangler Fig (data flow inverso, menos riesgo
primero):

1. AuditEmitter — extraer event publish + audit log de chat.py.
2. IdentityResolver — extraer lead identity resolution (_resolve_customer,
   _enrich_instagram_profile, _resolve_lead, _process_customer_lifecycle).
3. ConversationPipeline — extraer parsing + state machine + dispatch
   (_build_initial_state, _prepare_messages_and_intent,
   _invoke_agent_with_typing, _save_checkpoint, _deliver_response).
4. ChatOrchestrator reducido — thin facade compone los 3.

Y en paralelo (commits independientes):

5. closer_studio_service split:
   - ConversationQueryService: list_conversations, get_conversation_detail,
     list_frozen + display/avatar/lifecycle helpers.
   - ConversationCommandService: stop_ai, resume_ai, send_message,
     reactivate, diagnose + _log_system_event + _generate_recommendation.
   - KpiService: get_kpis.
   - Helper compartido `_get_checkpoint` → repo común.
6. semantic_router refactor:
   - domain/semantic_routes.py: SYSTEM_ROUTES const.
   - application/services/semantic_router.py: clase singleton sin
     hardcoded routes.
   - application/services/tenant_route_overlay.py: register_tenant_routes.

PROTOCOLO:

1. Lee: README + 00 (§3 — CRÍTICO no tocar) + 01 + 02 + 03 + 04 (§1.3
   cohesión + §1.4 acoplamiento) + 05 + learnings/S11A + S11 phase doc
   sección "Stranger Fig orchestrator" + .claude/rules/architectural-fitness.md.

2. Research mandate (re-confirma 2026):
   - "Strangler Fig pattern Python service decomposition tests preserve
     behavior 2026"
   - "Python dataclass kw_only inheritance ordering 2026" (si aparece
     hack en lift S11A — sales `lead_id: UUID = None # type: ignore`).
   - "FastAPI service split Repository pattern Query Command separation
     2026" (para closer_studio_service).

3. Pre-flight check:
   - Branch `development` limpio + último commit es S11A
     (`feat(sales-agent-redesign-s11a): ...`).
   - Verificar que snapshot framework Sub-sprint A está activo:
     `pytest tests/shared/agent_observability/test_callback_handler_snapshot.py -q`
     debe pasar.
   - Capturar snapshot pipeline pre-decomposition ANTES del primer
     refactor — sin esto el Strangler Fig es ciego.

4. TaskCreate granular por extracción.

5. TDD por commit:
   - Capturar snapshot pipeline (si no existe).
   - RED: tests de la nueva clase con stubs.
   - Implementar la extracción manteniendo legacy path en chat.py
     (delega a la nueva clase).
   - GREEN.
   - Snapshot diff = 0. Si > 0 → revertir + investigar.
   - Commit.

6. Quality gates por commit:
   - cd backend && .venv/bin/ruff check src/ tests/ --no-cache
   - cd backend && .venv/bin/pytest tests/architecture/ -x -q
   - cd backend && .venv/bin/pytest tests/modules/sales_agent/
     tests/modules/copilot/ tests/admin/ tests/shared/ -x -q
   - Snapshot byte-equal con baseline.

7. Verificación funcional al cierre:
   - Closer Studio inbox + pipeline + frozen renderea normal.
   - WS /closer-studio emite eventos.
   - Webhooks Telegram/WhatsApp/IG procesan.
   - Smart debounce + OutputManager intactos (§3).
   - Follow-up engine cadence intacto (§3).

8. Tech debt log: FIXED entries (con commit hash):
   - [MEDIUM] chat.py orchestrator overgrown 1140 LOC (S00) → FIXED en S11B.
   - [MEDIUM] closer_studio_service.py 8+ responsabilidades (S00) → FIXED.
   - [MEDIUM] semantic_router.py routes hardcoded 329 LOC (S00) → FIXED.
   - [LOW] _tool_dedup_tracker en state es magic string (S1) → FIXED si
     ConversationPipeline lo touch.
   - [LOW] Lazy imports brand + offer en sales_agent services (S00) →
     FIXED si IdentityResolver / ConversationPipeline formalizan vía
     port en shared/links/.
   - [LOW] Subscribers crean SessionLocal() per-event (S1) → FIXED si
     event_bus reshape es parte de la decomposition; si no, dejar
     DEFERRED-S12.
   - [LOW] knowledge_builder.py factory amplio (S00) → FIXED si
     IdentityResolver lo simplifica; si no, dejar DEFERRED-S12.

9. learnings/S11B-orchestrator-decomp.md (denso, accionable, sin filler).

10. README estado fase: S11A ✅ + S11B ✅ → S11 ✅ (sub-fases combinan
    en cierre del plan).

11. prompts/S12-start.md: actualizar con commit hash final S11B + hooks
    Sub-sprint B + tech debt residual (si quedó algo).

12. Commit conventional + push (solo archivos sesión, NUNCA
    git add -A): `feat(sales-agent-redesign-s11b): orchestrator
    decomposition Strangler Fig (chat.py + closer_studio_service +
    semantic_router)`. Múltiples commits durante el proceso (uno por
    extracción), commit final consolida.

PRINCIPIOS:
- Snapshot pipeline byte-equal es la VERDAD. Diff > 0 → revertir.
- §3 protected intacto. Smoke check al cierre.
- Cada commit revertible solo (no commits parciales).
- Strangler Fig: extraer una clase por vez, NO refactor masivo.
- Stage por nombre. NUNCA git add -A.
- Spanish neutro LATAM en user-facing.
- Native-first dev (NUNCA docker exec lint/tests/type-check).
- response_model= en todos los endpoints.

CONTEXTO ESPERADO AL ARRANCAR:
- Branch: development limpio (último commit S11A).
- Hooks listos: BaseAgentCallbackHandler + Template Method skeleton +
  snapshot framework determinístico (ver learnings/S11A § "Hooks listos").
- Tech debt en radar: 6 entries DEFERRED-S11B en 05-tech-debt-log.md
  (líneas 37-42).
- Coordinación: ninguna externa — solo developer + Claude.

Empieza con paso 1.
```
