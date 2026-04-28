# Handoff prompt · S6 start

> **Refinado al cierre de S5 (2026-04-28). Pin commit S5: `199bc7e9`.**

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S6 — Architectural fitness tests ratchet
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S6-fitness-tests-ratchet.md
📝 Aprendizajes previos: learnings/S0, S1, S2, S3, S4, S5.

CONTEXTO post-S5 (cerrado 2026-04-28):
- S5 cerrada: `shared/agent_observability/channels/{format,format_for_channel,intent_detector}.py` SSoT cross-agent. ChannelFormat extendido con chunk_size + typing_simulation_cpm + parse_mode (defaults None preservan back-compat copilot). Telegram MarkdownV2 escape utility (no auto-aplicado). Aliases (`instagram` → `instagram_dm`). 7 canales canónicos cross-agent (chat, whatsapp, telegram, instagram_dm, sms, voice, email). Copilot 3 archivos shim re-export para back-compat. Sales OutputManager._parse_response consume registry chunk_size via `_enforce_chunk_size` + `_split_by_cap` con boundary preference (sentence/whitespace/hard cut). Sales compose_system_prompt slot 6 (CHANNEL_FORMAT_HINT) populated via `_channel_format_hint(state)`. Arch ratchet `tests/architecture/test_no_hardcoded_channel_in_output_manager.py` sin allowlist (AST scan Compare + Dict). 3134 tests verde (incluye 113 copilot via shim).
- Branch: development limpio. Último commit S5: `199bc7e9`
- Tests: 3134 verde. ruff 0 errores (1 warning pre-existing offer_type_presets.py).
- Hooks listos S0..S5: callback handler shared, PII regex LATAM, MultiRoleLLMRouter ChatModelSpec, SPECIALIST_TO_ROLE SSoT, cache_boundary compose, channel registry shared, dual-write tablas event-sourced.

DEUDA REMANENTE para S6 (radar):
- DEFERRED-post-S6 (S5): sweep imports copilot directos a shared (output_channels, format_for_channel, channel_intent_detector). Shim cleanup + actualizar `tests/architecture/test_ddd_boundaries.py:75` allowlist.
- DEFERRED-post-S6 (S4): safety_service.py + chat.py:550 (summary) + follow_up_engine.py:83 (nudge) NO consumen `SPECIALIST_TO_ROLE` SSoT. S6 ratchet pass formaliza `LLM_ROLE_BY_SITE` expandido (NANO para summary/nudge).
- DEFERRED-post-S6 (S00): chat.py 1082 LOC overgrown, closer_studio_service.py 623 LOC, semantic_router.py 328 LOC. Stranger Fig refactor candidato.
- DEFERRED-post-S6 (S1): SalesAgentCallbackHandler duplica 6 LangChain callbacks de copilot (~250 LOC drift potencial). Lift al BaseAgentCallbackHandler Template Method.
- DEFERRED-post-S6 (S1): _tool_dedup_tracker en state es magic string sin tipo.
- DEFERRED-S6 ratchet (S1): test fixtures duplicados de SessionLocal/AuditRepository en test_node_tool_executor_dedup.py + test_domain_event_subscribers.py.
- DEFERRED-S6 ratchet (S3): _realistic_state inline ~30 LOC en test_build_specialist_system_prompt.py — promover a conftest si S7 brand_voice tests duplican.
- DEFERRED-S6 (S1): `agent_log_model.py` mencionado en docs no existe (real es `llm_log_model.py`). Cleanup nombres durante drop legacy.
- FLAGGED (S5): typing_simulation_cpm declarado pero no consumido (§3 protected CPM_SPEED).
- FLAGGED (S4): closer temp 0.4 declarado, Kimi clamp 0.6 server-side. Watchpoint conversion rate.
- FLAGGED (S1): `from __future__ import annotations` rompe LangGraph runtime introspection. Watchpoint preventivo.
- DEFERRED-pre-Jul-2026 (S4): DeepSeek alias `deepseek-chat`/`deepseek-reasoner` retiran 2026-07-24.

ENTREGABLES S6 (mínimo):
- `tests/architecture/test_no_new_sales_agent_module_imports.py` (ratchet — KNOWN_VIOLATIONS frozen post-S6, shrinks-only).
- `tests/architecture/test_sales_agent_anchors.py` (cap — anchors de cada subpaquete sales_agent: domain/application/infrastructure/api/observability/workers).
- `tests/architecture/test_sales_agent_callback_handler_invariants.py` (best-effort: try/except + db.rollback en cada persist).
- `tests/architecture/test_pii_sanitization_coverage_sales_agent.py` (AST: cada repo `.add()` a `*_trace_event`/`*_llm_call` pasa por sanitize_payload).
- `tests/architecture/test_sales_agent_tenant_isolation.py` (cada query filter tenant_id, allowlist `model_pricing_snapshot` global).
- `tests/architecture/test_sales_agent_system_prompt_order.py` (verify exists from S3 — actualizar para slot 6 ahora populado).
- `tests/architecture/test_subagent_isolation_invariants_sales_agent.py` (sales no usa subagents pero ratchet preventivo + bloqueo `astream_events(version="v2")` sin policy_for).
- DROP entrada `agent_trace_model` + `LLMLogModel` en `02-architecture-target.md §2.Legacy` cuando dual-write window se cierre (post-S1 +4 sem). Si NO se cierra aún, FLAGGED + watchpoint.

PROTOCOLO:

1. Lee:
   - docs/domains/sales-agent/redesign-2026-04/README.md
   - 00-vision-and-objectives.md (§3 lo que NO se toca — closer_studio + buffer + output_manager.process_response + webhooks + agent_state_checkpoint)
   - 01-master-plan.md
   - 02-architecture-target.md (post-S5 actualizado)
   - 03-phase-protocol.md (10 pasos + Paso 11 code review)
   - 04-principles.md (§1 GoF + §2 anti-parche + §10 commit hygiene)
   - 05-tech-debt-log.md (entradas DEFERRED-post-S6)
   - learnings/S0, S1, S2, S3, S4, S5
   - phases/S6-fitness-tests-ratchet.md
   - audit/sales-agent-current-state.md
   - .claude/rules/architectural-fitness.md
   - .claude/rules/copilot-resilience.md (subagentes contrato — base patrón)

2. Research mandate (mínimo 3 queries):
   - `Python AST architectural fitness tests 2026 best practices`
   - `import-linter Python ratchet allowlist contract pattern`
   - `pytest fixture conftest promotion shared mock SessionLocal`
   - Lectura: `tests/architecture/test_no_new_copilot_module_imports.py`, `test_copilot_anchors.py`, `test_subagent_isolation_invariants.py`, `test_no_hardcoded_models_sales_agent.py`, `test_no_hardcoded_channel_in_output_manager.py`.

3. Documenta hallazgos en phases/S6-*.md sección "Hallazgos research".

4. TaskCreate granular.

5. TDD: tests de arquitectura SON los tests. Escribir asumiendo allowlist vacía → correr → ver violations actuales → freeze (eliminar quick wins antes si posible). Tests fail with diff → fix → tests pass → freeze allowlist con KNOWN_VIOLATIONS frozenset(). Sin pseudo-test patterns.

6. Sweeps oportunista (scope estricto):
   - Sweep imports copilot directos a shared/channels (DEFERRED-post-S6 S5). Cada hit → reemplazar import + correr tests → confirmar verde → eliminar shim copilot cuando todos consumers migraron.
   - Promover SPECIALIST_TO_ROLE a `LLM_ROLE_BY_SITE` con summary/nudge/safety. NO toca §3 (estos NO son specialists del StateGraph — son LLM calls infra/orchestrator/workers). Test arch verifica cobertura.
   - Promover fixtures duplicados a conftest (test_node_tool_executor_dedup + test_domain_event_subscribers).
   - Update `tests/architecture/test_ddd_boundaries.py:75` allowlist apuntar a `src.shared.agent_observability.channels.format`.

7. Implementación step-by-step:
   - Crear cada arch fitness test con `KNOWN_VIOLATIONS = frozenset()` (sin allowlist) → correr → si falla, decidir: (a) fixear violation real, (b) si requiere refactor cross-fase mayor, agregar allowlist con razón documentada en docstring. Preferencia (a).
   - Anchors test list los archivos canónicos por capa (domain/application/infrastructure/api/observability/workers). Cada archivo nuevo en sales_agent debe matchear un patrón.
   - Best-effort test verifica que cada `_persist_llm_call_row` / `_persist_trace_event_row` está envuelto en try/except con `db.rollback()` + structlog warning.
   - Tenant isolation test: AST scan de cada SQLA query (`select(Model).where(...)`) en sales_agent — verificar `Model.tenant_id ==` aparece. Allowlist solo para `model_pricing_snapshot` (global reference data).
   - Subagent isolation: aunque sales no usa subagents hoy, ratchet preventivo + arch test bloquea `astream_events(version="v2")` callsites sin `policy_for`.

8. Quality gates nativos:
   - `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`
   - `cd backend && .venv/bin/ruff format --check src/ tests/`
   - `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`
   - `cd backend && .venv/bin/pytest tests/modules/sales_agent/ tests/admin/ tests/shared/ tests/modules/copilot/ -x -q --tb=short` (mantener 3134+ tests verde post-cleanup imports + sweeps).
   - `make arch-test` global pasa.

9. Verificación funcional:
   - 1 conversación dev sales_agent en canal Telegram. Output sale correcto, slot 6 prefix cacheable populated, OutputManager chunks no exceden 1024 (whatsapp) si lead pide WhatsApp.
   - §3 NO roto: closer_studio.py + ws.py + buffer_service.smart_debounce + output_manager.process_response + enrollment + agent_state_checkpoint + webhook adapters + follow_up_engine cadence intactos.
   - Cache hit rate sales_agent_llm_call.cached_read_tokens segundo turn ≥60% mantenido.

10. Tech debt log:
    - FIXED entries para cualquier sweep oportunista (shim cleanup, LLM_ROLE_BY_SITE expansion, conftest promotion).
    - Nuevos DEFERRED entries si emergen invariantes que requieren refactor cross-fase.

11. Code review final (Paso 11):
    - Callers no rotos: cada arch test que add allowlist documenta razón en docstring.
    - Cohesión: cada test_*.py archivo verifica UN invariant. No tests que mezclan.
    - Acoplamiento: arch tests NO importan src.modules.sales_agent.* en runtime — usan AST parse.
    - Simplify pass: arch tests que duplican lógica común promover a `tests/architecture/_helpers.py`.

12. Cierre:
    - learnings/S6-*.md (denso, accionable).
    - prompts/S7-start.md refinado con context fresco.
    - README estado fase ✅.
    - Mark FIXED entradas DEFERRED-post-S6 que se resolvieron en sweeps.

13. Commit: `feat(sales-agent-redesign-s6): architectural fitness tests ratchet + sweep cleanup`

PRINCIPIOS:
- TDD: arch tests SON los tests. Sin allowlist hasta probar shrink.
- Anti-parche: violation → fixear root cause. Si requiere refactor cross-fase mayor → DEFERRED + razón documentada en docstring del allowlist.
- Best-effort: arch tests NO deben romper tests al mover archivos. AST parse stable cross-refactor.
- Tenant isolation: arch test verifica cada SQLA query filter tenant_id.
- Stage por nombre en commits (otra sesión activa en development — coordinar via comentarios commits).
- Spanish neutro LATAM en cualquier user-facing copy de los tests (descripciones + assertion messages).
- §3 protected: NO tocar closer_studio + buffer + output_manager.process_response + enrollment + agent_state_checkpoint + webhooks + follow_up_engine cadence.

Empieza con paso 1.
```
