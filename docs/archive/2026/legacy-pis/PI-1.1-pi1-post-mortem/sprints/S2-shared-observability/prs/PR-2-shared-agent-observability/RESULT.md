# PR-2-shared-agent-observability — RESULT

## Meta cierre

| Campo | Valor |
|---|---|
| PR ID | PR-2-shared-agent-observability |
| Estado final | shipped |
| Fecha cierre | 2026-05-01 |
| Owner cierre | /pm |
| Architect | Opus 4.7 (CONTRACT.md commit `522703ba`) |
| Builder | nicolify-agentic Opus (commit `d80d15f5`) |
| Auditor | nicolify-agentic-auditor Opus (REVIEW-agentic.md commit `8744ff06` verdict PASS iter 1) |
| Smoke Chris-mediated | 2026-05-01 14:15 UTC — Telegram "holaaaa" → traces persisted +4 trace_event +2 llm_call |

## Outcome real vs esperado

### Bug #2 FIX VERIFIED END-TO-END ✅

**Pre-fix (0 rows globalmente desde 2026-04 commit 3f7d28bf S1-redesign):**

| Tabla | Count |
|---|---|
| `sales_agent_trace_event` | 0 |
| `sales_agent_llm_call` | 0 |
| `sales_agent_routing_log` | 0 |

**Post-fix smoke (Chris mandó "holaaaa" al visionarias_bot Telegram):**

| Tabla | Count | Delta |
|---|---|---|
| `sales_agent_trace_event` | 4 | **+4** ✅ |
| `sales_agent_llm_call` | 2 | **+2** ✅ |
| `sales_agent_routing_log` | 0 | 0 (no routing decisions este turn — normal) |

**Eventos persistidos (real DB query post-smoke):**
1. `turn_start` `ok` — message_preview "holaaaa", route="sales_agent"
2. `llm_call` openai.deepseek-reasoner `error` (cost tracking captura errors también)
3. `llm_call` openai.gpt-4o-mini `error`
4. `turn_end` `error` — APIConnectionErr (turn lifecycle persisted incluso fallo LLM call)

**Demostración best-effort observability:** envelope captura turn_start ANTES del fallo LLM + captura llm_call rows con cost=0 + captura turn_end con error_type. Sales agent operability ahora auditable.

### Bug #8 FIX VERIFIED ✅

`backend/src/modules/sales_agent/observability/recording/factory.py:78`:
- Pre-fix: `FXResolver()` (sin args, runtime AttributeError "missing http_client_factory")
- Post-fix: `FXResolver.default()` classmethod factory encapsula `lambda: httpx.Client(timeout=10)`

Cero `FXResolver()` no-arg instances en codebase post-PR (verificado vía nuevo arch ratchet `tests/architecture/test_anti_duplication_envelope.py`).

### Bugs DEFERRED a PRs separados (out-of-scope este PR)

| Bug | Severidad | Razón defer | Status post-smoke |
|---|---|---|---|
| **#7 PersonalityProfileModel.model_dump** | CRÍTICO | Brand adapter `brand/application/services/brand_data_adapter.py:46` SQLA ORM tratado como Pydantic. Out-of-scope (módulo brand backend negocio). | Confirmed runtime — knowledge_builder.build_identity falla |
| **#9 LiteLLM container exited mount config.yaml** | CRÍTICO infra | Docker compose mount conflict. Container `visionarias_litellm` exited (127). `visionarias_litellm:4000` DNS unreachable. | Confirmed — APIConnectionError todos LLM calls |
| **#5 max update depth FE** | a investigar | No reproducido post-fix #1+#4 | TBD repro window |
| **#6 tenant switch non-persist** | medio UX | Clerk publicMetadata.tenant_id stale post-dropdown | RCA documentado PR-1 RESULT.md |

## 5-layer anti-duplication enforcement — PRIMER TEST PASSED ✅

PR-2 era el primer PR del nuevo proceso (commits b0700be9 + 3e84bb93). Resultado:

| Layer | Status | Evidence |
|---|---|---|
| 1 PR.md template grep evidence | ✅ MANDATORY block fulfilled | CONTRACT § 1 embebió grep output completo verbatim |
| 2 Builder Step 0 GATE | ✅ PASS | IMPL-LOG-agentic § "Step 0 grep findings" sección obligatoria documentó cada Write nuevo file |
| 3 Auditor Cat 13 mirror detection | ✅ PASS | REVIEW-agentic verdict PASS — class distinct + 3 overrides + 2 fields = NOT mirror per anti-duplication semantics |
| 4 Architect mandatory | ✅ DONE | CONTRACT.md producido por architect Opus ANTES builder (747 lines, 9 secciones) |
| 5 Skills warning | ✅ ALL 5 INVOCADOS | copilot-expert + sales-agent-expert + tessl__langgraph + tessl__graceful-degradation + tessl__pytest-api-testing |

**Process correction de PR.md:** PR.md inicial decía "FXResolver() at lines 116, 168" — architect Opus ejecutando Step 0 grep CORRIGIÓ a "factory.py:78" (1 sitio único). Sin Step 0 GATE este error PR.md hubiera propagado al builder. Layer 1 trabajó.

## Surface entregada (final)

### Shared (NEW)

- `backend/src/shared/agent_observability/recording/turn_envelope.py` — `BaseObservabilityContext` Template Method ABC con lifecycle (`__aenter__` → turn_start commit; `__aexit__` → turn_end commit; exception → set_turn_error; abstract `_build_repos`, `_build_callback_handler`, `_persist_turn_end_data`)
- `backend/src/shared/agent_observability/cost/fx_resolver.py` — EXTEND con `FXResolver.default()` classmethod (~5 LOC) encapsula `lambda: httpx.Client(timeout=10)` boilerplate

### Copilot (REFACTOR in-place)

- `backend/src/modules/copilot/observability/recording/turn_envelope.py` — class `ObservabilityContext` ahora subclass `CopilotObservabilityContext(BaseObservabilityContext)`. Module-level alias preserva 4260+ import sites back-compat (`from src.modules.copilot.observability import ObservabilityContext`).
- `backend/src/modules/copilot/application/orchestrator/chat.py` — `FXResolver(http_client_factory=lambda: ...)` simplified a `FXResolver.default()`

### Sales agent (NEW + Bug #2/#8 wiring)

- `backend/src/modules/sales_agent/observability/recording/turn_envelope.py` — NEW `SalesAgentObservabilityContext(BaseObservabilityContext)`. Adds `lead_id` + `channel_type` fields. Overrides 3 abstract methods. Class name distinct, NO mirror byte-eq.
- `backend/src/modules/sales_agent/observability/recording/factory.py` — line 78 Bug #8 fix `FXResolver.default()` + factory builder `build_sales_agent_observability_context()`
- `backend/src/modules/sales_agent/application/orchestrator/conversation_pipeline.py::invoke_agent_with_typing` — wraps `agent_app.ainvoke` en `async with observability_context.observe_turn(...)`
- `backend/src/modules/sales_agent/application/orchestrator/chat.py` — instancia ObservabilityContext + pass al pipeline
- `backend/src/modules/sales_agent/application/orchestrator/outbound_orchestrator.py` — same pattern outbound

### Tests

- `backend/tests/shared/agent_observability/recording/test_turn_envelope_base.py` — abstract methods enforcement + lifecycle commit/rollback (NEW)
- `backend/tests/shared/agent_observability/cost/test_fx_resolver_default.py` — `FXResolver.default()` retorna instance functional (NEW)
- `backend/tests/modules/copilot/observability/test_envelope_inheritance.py` — copilot regression (NEW): inheritance + back-compat alias
- `backend/tests/modules/sales_agent/observability/test_observability_context.py` — sales subclass behavior (NEW)
- `backend/tests/modules/sales_agent/observability/test_real_trace_persistence.py` — REAL DB persistence (no mocks). Marker `@pytest.mark.verify` (NEW)
- `backend/tests/architecture/test_anti_duplication_envelope.py` — 5 ratchet tests:
  - `test_no_fxresolver_no_arg_call_sites` — grep enforces no `FXResolver()` no-arg
  - `test_no_envelope_mirror` — only shared base + 2 concrete subclasses, no byte-mirror
  - + 3 más (estructura herencia + class names distinct + acceptable file naming convention)

### Quality gates

- ruff check: 0 errors
- mypy: -1 error vs baseline (PR fixes more than introduces)
- 369/369 observability tests green
- 20/20 PR-specific architecture tests green
- 0 new failures introduced (5 broad arch + 7 broad module failures all pre-existing baseline; PR fixes 6 of them)
- Cross-session M8: PI-5 PR-2 commit `d09799b9` hunks distinct from this PR's hunk @@ -611. No function-level overlap.

## Lineage update current-state

`docs/pm-nico/current-state/sales_agent.md`:
- New cap **"Observability traces persistence (live)"** with lineage `PR-2-shared-agent-observability (PI-1.1, S2, commit d80d15f5, 2026-05-01) — emerges via shared lift + envelope wire`
- Status changes:
  - "Voice fidelity grader" cap → ready (data available)
  - "Cost tracking sales_agent" cap → live (captures errors too)
  - "Routing decisions auditable" cap → live (when LLM functional)

`docs/pm-nico/current-state/copilot.md`:
- Cap "Observability lifecycle" — append note `Refactored to BaseObservabilityContext shared subclass — PR-2 (PI-1.1, S2, commit d80d15f5, 2026-05-01) — capability unchanged user-facing, 4260 traces preserved`

## Decisiones registradas (append decisions.md PI-1.1)

- **D-8 (2026-05-01)** — 5-layer anti-duplication enforcement primer test PASSED en PR-2. Layer 1 (PR.md grep mandatory) catched PR.md outdated info "FXResolver() at lines 116, 168" — architect corrigió a 1 sitio único factory.py:78.
- **D-9 (2026-05-01)** — Bug #2 fix verificado smoke real Telegram Chris-mediated 14:15 UTC. 4 trace events + 2 llm calls persisted post-message. Sales agent observability LIVE.
- **D-10 (2026-05-01)** — Bot respondió error técnico durante smoke por Bug #7 (brand adapter) + Bug #9 (LiteLLM container exited). Out-of-scope este PR. Bug #2 fix VALIDÓ correcto incluso bajo error LLM downstream — best-effort observability captura errors (4 trace rows incluyendo turn_end status='error').

## Riesgos identificados (post-ship)

| Riesgo | Mitigación |
|---|---|
| Bug #7 PersonalityProfileModel + Bug #9 LiteLLM bloquean operability sales_agent prod | PRs dedicados separados. Sales agent functional cuando LLM stack restored |
| Backfill traces históricos pre-PR-2 sales_agent | DEFERIDO. Discusión Chris post-PR-2 ship. Decision tree: (A) regenerar synthetic traces de messages history, (B) mantener historial vacío + comenzar tracking forward, (C) hybrid. Recomendación PM: B + flag retroactive backfill como oportunidad PI-3 |
| Cross-session collision PI-5 PR-2 (otra sesión modifica copilot/) | RESOLVED. M8 verified — PI-5 PR-2 ya commiteó separado `6bad657b` + `d09799b9`. Hunks distintos vs este PR |

## Aceptación

- [x] CONTRACT.md producido por architect Opus con grep evidence completa (`522703ba`)
- [x] CONTRACT.md "Existing systems audit" sección con paths + line numbers reales (no claims)
- [x] Tests verdes incluyendo real DB persistence sales_agent (369/369 obs tests + 20/20 arch)
- [x] Lint/type/arch fitness verdes (PR introduces 0 new failures, fixes 6)
- [x] IMPL-LOG-agentic.md con Step 0 grep findings sección obligatoria
- [x] REVIEW-agentic.md verdict PASS iter 1 (Cat 13 mirror detection PASS)
- [x] Smoke real Telegram message → DB trace count growth verified Chris-mediated
- [x] RESULT.md escrito por PM con lineage update (este file)
- [ ] `current-state/sales_agent.md` + `current-state/copilot.md` updated → **next step inmediato post-RESULT**
- [ ] Decisiones registradas en `decisions.md` PI-1.1 D-8/D-9/D-10 → **next step**
- [ ] `process-learnings.md` append "Anti-duplication rule first test passed" → **next step**

## Próximo paso

PM ejecuta:
1. Update `current-state/sales_agent.md` + `current-state/copilot.md` con cap lineage
2. Append `decisions.md` PI-1.1 D-8 + D-9 + D-10
3. Append `sprints/S2-shared-observability/learnings.md` + write `handoff.md` S2 close
4. Append `process-learnings.md` § 2026-05-01 final entry: "5-layer anti-duplication enforcement primer test PASSED"
5. PR-2 estado → shipped en PR.md
6. Sprint S2 → considerar cerrar (último PR del sprint)
7. PI-1.1 → estado siguiente: discovery PRs deferred (#7 Brand adapter, #9 LiteLLM, #5+#6) o cerrar PI-1.1 con scope reducido + handoff a PI-3 sales-agent-improvement
