# Handoff prompt · S11 start

> **Refinado al cierre de S10. Refactor riesgoso — goldens eval loop son el safety net.**

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S11 — Shared base lift + orchestrator decomposition (Stranger Fig)
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S11-shared-lift-orchestrator-decomp.md
📝 Aprendizajes previos: learnings/S0..S10.

CONTEXTO:
- S0..S10 cerrados.
- Eval loop S10 activo (judge multi-rubric + goldens semanal). ESTOS
  son el safety net del refactor — diff goldens pre/post-refactor debe
  ser 0 turn outputs.
- Arch tests S6 + S6.5 vigilan: ratchet imports, anchors, callback handler
  invariants, PII coverage, tenant isolation, subagent isolation, channel
  registry, model tier, system prompt order, no legacy reads, no
  __future__ annotations.
- callback handler hoy: SalesAgentCallbackHandler 575 LOC duplica 6
  callbacks de copilot ObservabilityCallbackHandler ~580 LOC. 250 LOC
  drift potencial.
- Files overgrown:
  - chat.py 1082 LOC (ConversationPipeline + IdentityResolver +
    AuditEmitter mezclados)
  - closer_studio_service.py 623 LOC (8+ responsabilidades)
  - semantic_router.py 328 LOC (routes hardcoded)

ENTREGABLES S11 (en 2 sub-sprints):

Sub-sprint A (5 días) — Shared base lift:
- BaseAgentCallbackHandler concreto: 6 on_* callbacks + helpers
  (_extract_usage, _from_openai_token_usage, _extract_provider_and_model,
  _apply_sanitization, _resolve_pricing) en la base shared.
- Subclases sólo overrides de _persist_*_row + _agent_specific().
- SalesAgentCallbackHandler < 200 LOC. ObservabilityCallbackHandler < 200 LOC.
- Tests existentes 113 copilot + sales callback verde sin cambio.
- Arch test test_sales_agent_callback_handler_invariants extendido para
  validar el base + subclass.
- COORDINACIÓN: copilot retrofit en mismo sprint (sales lift requiere
  ambos handlers heredando del base). Si copilot no listo → bloquear
  sub-sprint A hasta confirmación.

Sub-sprint B (7 días) — Orchestrator decomposition (Stranger Fig):
- AuditEmitter (extraer event publish + audit log de chat.py).
- IdentityResolver (extraer lead identity resolution de chat.py).
- ConversationPipeline (extraer parsing + state machine + dispatch).
- ChatOrchestrator < 400 LOC, thin facade compone los 3.
- closer_studio_service.py split: ConversationQueryService +
  ConversationCommandService + KpiService.
- semantic_router.py registry-based: domain/semantic_routes.py + strategy
  + tenant overrides separados.
- §3 protected NO se toca: closer_studio.py API + ws.py + buffer_service.smart_debounce
  + output_manager.process_response + enrollment + agent_state_checkpoint
  schema + webhook adapters + follow_up_engine cadence.
- Goldens del eval loop S10 diff = 0 turn outputs pre/post-refactor.

PROTOCOLO:

1. Lee: README + 00 (§3 — CRÍTICO no tocar) + 01 + 02 + 03 + 04 (§1.3
   cohesión + §1.4 acoplamiento) + 05 + learnings/S0..S10 +
   audit/sales-agent-current-state.md §8 cohesion heatmap +
   phases/S11-* + .claude/rules/architectural-fitness.md.

2. Research mandate:
   - "Stranger Fig pattern Python service decomposition tests preserve behavior 2026"
   - "LangChain BaseCallbackHandler Template Method multi-agent inheritance 2026"
   - "pytest snapshot testing golden output Python 2026 best practices"

3. Pre-flight check obligatorio:
   - Eval loop S10 corriendo + goldens estables (últimas 2 sem semanal sin diffs).
   - Confirmar coordinación con copilot redesign team para retrofit.
   - Si copilot no listo → bloquear sub-sprint A.

4. TaskCreate granular por sub-sprint.

5. TDD:
   Sub-sprint A:
   - Capture goldens pre-lift.
   - RED: tests del shared base con stubs.
   - Lift helpers en orden (más bajo riesgo primero).
   - Lift 6 callbacks. Sales + copilot heredan.
   - GREEN. Goldens diff = 0.

   Sub-sprint B:
   - Capture goldens pre-decomposition.
   - Extraer una clase por commit (AuditEmitter → IdentityResolver →
     ConversationPipeline → reduce ChatOrchestrator).
   - Cada commit revertible solo. Goldens diff = 0 tras cada commit.
   - Si diff > 0 → revertir + investigar.
   - Idem para closer_studio_service split + semantic_router refactor.

6. Quality gates:
   - cd backend && .venv/bin/ruff check src/ tests/ --no-cache
   - cd backend && .venv/bin/pytest tests/architecture/ -x -q
   - cd backend && .venv/bin/pytest tests/modules/sales_agent/
     tests/modules/copilot/ tests/admin/ tests/shared/ -x -q
   - Cobertura sales_agent ≥ 70% post-decomposition.
   - Goldens eval loop diff = 0.

7. Verificación funcional:
   - Closer Studio inbox + pipeline + frozen renderea normal.
   - WS /closer-studio emite eventos.
   - Webhooks Telegram/WhatsApp/IG procesan.
   - Smart debounce + OutputManager intactos (§3).
   - Follow-up engine cadence intacto (§3).

8. Tech debt log: FIXED entries (con commit hash):
   - [MEDIUM] SalesAgentCallbackHandler duplica 6 LangChain callbacks (S1)
   - [MEDIUM] chat.py orchestrator overgrown 1082 LOC (S00)
   - [MEDIUM] closer_studio_service.py 8+ responsabilidades (S00)
   - [MEDIUM] semantic_router.py routes hardcoded 328 LOC (S00)
   - [LOW] _tool_dedup_tracker en state es magic string (S1)
   - [LOW] Lazy imports brand + offer en sales_agent services (S00) — si
     decomposition los formaliza vía port.
   - [LOW] Subscribers crean SessionLocal() per-event (S1) — opportunity
     post-decomposition.
   - [LOW] knowledge_builder.py factory amplio (S00)

9. learnings/S11-*.md + prompts/S12-start.md refinado.

10. README estado fase ✅ S11.

11. Commit: `feat(sales-agent-redesign-s11): shared base lift + orchestrator decomposition (Stranger Fig)`

PRINCIPIOS:
- Goldens son la VERDAD. Diff > 0 → revertir.
- §3 protected intacto. Smoke check al cierre.
- Cada commit revertible solo (no commits parciales).
- Coordinación con copilot retrofit antes de sub-sprint A.
- Stranger Fig: extraer una clase por vez, NO refactor masivo.
- Stage por nombre.
- Spanish neutro LATAM.

Empieza con paso 1.
```
