# Handoff prompt · S7 start

> **Refinado al cierre de S6 (2026-04-28).**

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S7 — Brand voice integration ("Estilo Comunicacional")
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S7-brand-voice-integration.md
📝 Aprendizajes previos: learnings/S0, S1, S2, S3, S4, S5, S6.

CONTEXTO post-S6 (cerrado 2026-04-28):
- S6 cerrada: 6 arch fitness tests nuevos congelan el estado infra
  post-S0..S5 limpio. Ratchet `KNOWN_SALES_AGENT_TO_MODULE_IMPORTS` con
  4 entradas TYPE_CHECKING (brand × 1, crm × 2, offer × 1) — shrinks-only.
  ANCHOR_REGISTRY con 5 entradas, cap 25 (admite ~20 nuevos sin bumpear).
  Sweeps oportunista S4/S5 ejecutados:
    1) 11 call sites copilot migrados shim → SSoT shared
       (`src.shared.agent_observability.channels.{format,format_for_channel,intent_detector}`),
       3 shims borrados, allowlist `test_ddd_boundaries.py:75` apunta al
       SSoT real.
    2) `LLM_ROLE_BY_SITE` SSoT extendido en `domain/model_tier.py`
       cubriendo specialists + summary (NANO) + follow_up_nudge (NANO) +
       safety (FAST). `SPECIALIST_TO_ROLE` queda como sub-view back-compat.
       safety_service.py + chat.py:550 + follow_up_engine.py:83 wired.
- Branch: development limpio. Último commit S6: {HASH_TBD}.
- Tests: ~3157 verde (622 architecture + 2535 sales/copilot/admin/shared).
  Ruff 0 errores en mis files (1 RUF059 ajeno en analytics — sesión paralela).
- Hooks listos S0..S6: callback handler shared, PII regex LATAM,
  MultiRoleLLMRouter ChatModelSpec, `LLM_ROLE_BY_SITE` SSoT (specialists +
  summary + nudge + safety), cache_boundary compose con slot 4 reservado
  para lighthouse, channel registry shared con slot 6 wired.
- Subagent isolation invariants ratchet preventivo (REGISTERED_SUBAGENTS_RATCHET = ()).

DEUDA REMANENTE para S7 (radar):
- DEFERRED-post-cutover-window: drop tablas legacy
  `agent_trace_model` + `LLMLogModel` + cutover `sales_audit.py`
  (ventana dual-write 4 sem cumple 2026-05-26). NO en S7 — S6.5 dedicada.
- DEFERRED-S7: Test fixtures de subscribers + node_tool_executor
  (`_mute_trace_node_writes` + `_stub_session_local`) duplican mock
  SessionLocal en 2 tests. Promover a conftest helper si S7 brand_voice
  tests requieren mismo mock (3+ threshold).
- DEFERRED-S7 desde S5: `agent_identity.j2` duplica `## Reglas por Canal`
  con slot 6 (~100-200 tokens redundantes). S7 retira el bloque inline
  Jinja al integrar lighthouse.
- DEFERRED-S5/S7: `agent_identity` slot 4 hoy renderiza `## Catálogo de
  Ofertas` inline. S7 lo extrae a `brand_voice_summary` mirror copilot F3.
- FLAGGED (S5): typing_simulation_cpm declarado pero no consumido (§3
  protected CPM_SPEED).
- FLAGGED (S4): closer temp 0.4 declarado, Kimi clamp 0.6 server-side.
  Watchpoint conversion rate.
- FLAGGED (S1): `from __future__ import annotations` rompe LangGraph
  runtime introspection. Watchpoint preventivo (sin arch test).
- DEFERRED-pre-Jul-2026 (S4): DeepSeek alias `deepseek-chat`/`deepseek-reasoner`
  retiran 2026-07-24.

ENTREGABLES S7 (mínimo):
- VERIFICAR FIRST: nombre exacto del campo "Estilo Comunicacional" en
  Brand Studio schema. Si NO existe → ESCALAR al usuario antes de codear.
- Tabla `brand_voice_summary` (mirror `brand_summary` copilot F3) — idempotente
  Alembic raw SQL `IF NOT EXISTS`.
- ARQ task `regenerate_brand_voice_summary` + subscriber a
  `BrandVoiceUpdatedEvent`.
- `_agent_identity_lighthouse(state)` builder en
  `application/prompts/compose.py` que reemplaza el render Jinja inline
  de slot 4 con lectura de `brand_voice_summary` lighthouse.
- Port `shared/links/ports/brand.py::get_brand_voice_summary(tenant_id)`
  para que sales_agent NO importe directo de `brand.infrastructure`.
  Esto SHRINKS el ratchet: la entrada
  `sales_agent -> brand | application/services/style_anchor_retriever.py`
  potencialmente queda obsoleta si style anchors también migran al port.
- Anchor `SALES-AGENT-BRAND-VOICE-S7` en compose.py + ANCHOR_REGISTRY.
- Goldens nuevos: tenant fixture formal vs casual con voseo (override
  documentado per `.claude/rules/spanish-text.md` §2 — voseo permitido
  SOLO si tenant lo configuró en Brand Studio).
- Re-correr scan voseo post-integration.
- Tests:
  - test_brand_voice_summary_regen (hash short-circuit)
  - test_lighthouse_in_slot_4
  - test_brand_voice_differentiation (tenant A vs B mismo input → outputs distintos)
  - test_voseo_respected_per_tenant (excepción documentada en `.claude/rules/spanish-text.md` §2)
  - test_brand_voice_summary_cache_invalidation (BrandVoiceUpdatedEvent → ARQ regen)
  - test_no_pii_in_brand_voice_summary (extender `test_pii_sanitization_coverage_sales_agent.py`).

PROTOCOLO:

1. Lee:
   - docs/domains/sales-agent/redesign-2026-04/README.md
   - 00-vision-and-objectives.md (§3 lo que NO se toca — closer_studio +
     buffer + output_manager.process_response + webhooks +
     agent_state_checkpoint + follow_up_engine cadence)
   - 01-master-plan.md
   - 02-architecture-target.md (§3.6 brand voice lighthouse + §3.4
     compose slot 4)
   - 03-phase-protocol.md (10 pasos + Paso 11 code review)
   - 04-principles.md (§1.3 cohesión: brand_voice vive en brand/, no
     sales_agent/ + §2 anti-parche + §10 commit hygiene)
   - 05-tech-debt-log.md (entradas DEFERRED-S7)
   - learnings/S0, S1, S2, S3, S4, S5, S6
   - phases/S7-brand-voice-integration.md
   - audit/sales-agent-current-state.md
   - .claude/rules/architectural-fitness.md
   - .claude/rules/spanish-text.md (§2 voseo override per tenant)

2. Research mandate (mínimo 3 queries):
   - `brand voice prompt engineering style transfer LLM 2026 best practices`
   - `prompt cache invariance per-tenant cacheable prefix lighthouse pattern`
   - `LLM do don't list constraint vs system prompt instruction 2026`
   - Lectura: `src/modules/copilot/observability/lighthouses/brand_summary.py` +
     F3 implementation + skill `brand-expert`.

3. **Verificación crítica antes de codear**: leer
   `src/modules/brand/domain/identity.py` (o equivalente) +
   `frontend/src/features/brand-studio/schemas/identity.schema.ts` para
   confirmar el nombre exacto del campo "Estilo Comunicacional". Si no
   existe campo equivalente → **ESCALAR al usuario**: puede requerir una
   fase pre-S7 de Brand Studio para crear el campo. NO inventar campo
   sin confirmación. Anti-parche §2 04-principles.md.

4. Documenta hallazgos research en phases/S7-*.md sección "Hallazgos research".

5. TaskCreate granular.

6. TDD: tests RED → GREEN → REFACTOR. Tests por capa antes de implementar.

7. Migración: idempotente raw SQL `IF NOT EXISTS`. Verificar en clone
   DB antes de prod (`pg_dump -s | psql -d migration_test` pattern).

8. Implementación step-by-step:
   - Crear `brand_voice_summary` table + repo (en `brand/`).
   - Port `shared/links/ports/brand.py::get_brand_voice_summary`.
   - ARQ task `regenerate_brand_voice_summary` con hash short-circuit
     (mirror copilot F3 invariance).
   - Subscriber `BrandVoiceUpdatedEvent` → trigger ARQ task.
   - `_agent_identity_lighthouse(state)` builder en compose.py slot 4.
   - Retire `## Reglas por Canal` del template Jinja `agent_identity.j2`
     (S5 DEFERRED-S7 ahora se cierra — slot 6 ya es SSoT del channel hint).
   - Update `ANCHOR_REGISTRY` con `SALES-AGENT-BRAND-VOICE-S7`.

9. Quality gates nativos:
   - `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`
   - `cd backend && .venv/bin/ruff format --check src/ tests/`
   - `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`
   - `cd backend && .venv/bin/pytest tests/modules/sales_agent/ tests/admin/ tests/shared/ tests/modules/copilot/ tests/modules/brand/ -x -q --tb=short -m "not verify and not integration"`
   - `make arch-test` global pasa.
   - Migration apply idempotente en clone DB.

10. Verificación funcional:
    - 1 conversación dev sales_agent en canal Telegram para tenant A
      con `Estilo Comunicacional` formal vs tenant B con casual + voseo.
      Output del agente debe sonar distinto (cualitativo).
    - §3 NO roto: closer_studio + ws + buffer + output_manager.process_response
      + enrollment + agent_state_checkpoint + webhooks + follow_up_engine
      cadence intactos.
    - Cache hit rate sales_agent_llm_call.cached_read_tokens segundo turn
      ≥ 60% mantenido (slot 4 ahora con voz lighthouse cacheable per-tenant).
    - Reconciliation worker S1 sigue corriendo durante ventana dual-write
      (la cierre 2026-05-26 es FUERA de S7).

11. Tech debt log:
    - FIXED entries para `agent_identity.j2` (retire `## Reglas por Canal` + `## Catálogo de Ofertas`).
    - FIXED entry para test fixtures conftest si S7 introduce 3er test
      con SessionLocal mock.
    - Nuevos DEFERRED si emergen.

12. Code review final (Paso 11):
    - Callers no rotos: cada nuevo símbolo (brand_voice_summary table,
      port, ARQ task, lighthouse builder) con grep de consumers.
    - Cohesión: brand_voice_summary en brand/, no sales_agent/. Sales
      consume via port shared/links/.
    - Acoplamiento: NO importar `brand.infrastructure` desde sales —
      arch test ratchet S6 falla.
    - Simplify pass sobre files modificados.
    - Spanish neutro: scan voseo + override per tenant respetado.

13. Cierre:
    - learnings/S7-*.md (denso, accionable).
    - prompts/S8-start.md refinado con context fresco.
    - README estado fase ✅.
    - Mark FIXED entradas DEFERRED-S7.

14. Commit: `feat(sales-agent-redesign-s7): brand voice lighthouse integration ("Estilo Comunicacional")`

PRINCIPIOS:
- SSoT: brand_voice vive en brand/, NO en sales_agent/. Sales consume via port.
- TDD: tests RED → GREEN. Sin shortcut.
- Anti-parche: campo "Estilo Comunicacional" no existe → ESCALAR.
- Cohesión: cada subpaquete UNA responsabilidad.
- Tenant isolation: brand_voice_summary filter tenant_id.
- Cache hit rate: slot 4 lighthouse render estable per-tenant cross-turn.
- Stage por nombre en commits (otra sesión activa en development —
  coordinar via comentarios commits).
- Spanish neutro LATAM en cualquier user-facing copy. Excepción: voseo
  per tenant si lo configuró en Brand Studio (.claude/rules/spanish-text.md §2).
- §3 protected: NO tocar closer_studio + buffer + output_manager.process_response +
  enrollment + agent_state_checkpoint + webhooks + follow_up_engine cadence.

Empieza con paso 1.
```
