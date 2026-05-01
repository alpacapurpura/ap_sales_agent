# Builder Agentic — PR-2 shared-agent-observability

## BLOQUE FIJO (cacheable)

Sos `nicolify-agentic` builder Opus. Implementás CONTRACT.md PR-2 + auto-spawn auditor + fix-loop hasta PASS. Cap maxTurns 150.

PR-folder: `/home/chris/AISALESHT/docs/pm-nico/pis/active/PI-1.1-pi1-post-mortem/sprints/S2-shared-observability/prs/PR-2-shared-agent-observability/`

**Skills mandatory cargar Step 0 (sin estos = auditor FAIL skill-routing-violation):**
- `copilot-expert`
- `sales-agent-expert`
- `tessl__langgraph`
- `tessl__graceful-degradation`
- `tessl__pytest-api-testing`

**Rules vinculantes:**
- `.claude/rules/anti-duplication.md` (universal #12)
- `.claude/rules/backend-ddd.md`
- `.claude/rules/parallel-safety.md` M8 (PI-5 PR-2 active session — extend, no destroy)
- `.claude/rules/copilot-observability.md`
- `.claude/rules/sales-agent-brand-voice.md`
- `.claude/rules/tdd-mandatory.md`

**Lectura obligatoria orden:**
1. `{PR-folder}/CONTRACT.md` — SSoT pre-implementación 9 secciones (§ 0 surface, § 1 grep evidence, § 2 BaseObservabilityContext interface, § 3 FXResolver.default factory, § 4 migration plan sequenced, § 5 tests strategy, § 6 PI-5 coordination, § 7 out of scope, § 8 acceptance, § 9 risks)
2. `{PR-folder}/PR.md` — problema + scope (si CONTRACT incompleto)
3. CLAUDE.md root sección "Git Workflow — INVIOLABLE"

## Step 0 GATE — Anti-duplication grep ANTES de cualquier `Write` que crea file nuevo

> Origen: PR-1 PI-1.1 hotfix 2026-05-01 — builder duplicó turn_envelope.py copilot mirror. REVERT obligatorio. Este PR es PRIMER TEST del 5-layer enforcement.

Para CADA archivo nuevo en el PR (CONTRACT lista 4 nuevos):
- `backend/src/shared/agent_observability/recording/turn_envelope.py`
- `backend/src/modules/sales_agent/observability/recording/turn_envelope.py`
- `backend/tests/shared/agent_observability/test_turn_envelope_base.py`
- `backend/tests/modules/sales_agent/observability/test_real_trace_persistence.py`
- `backend/tests/modules/copilot/observability/test_envelope_inheritance.py`
- `backend/tests/architecture/test_no_fxresolver_no_arg.py`

ANTES de `Write` cada uno:
1. `find /home/chris/AISALESHT/backend -name "<basename>.py" 2>/dev/null` → confirmar no existe (esperado: no match para shared/recording, sí match para sales_agent/observability/recording que es REFACTOR copia copilot pattern con override class distinct)
2. `grep -rn "class <ClassName>" /home/chris/AISALESHT/backend/src/shared/ /home/chris/AISALESHT/backend/src/modules/` → confirmar class name único cross-codebase
3. Document Step 0 grep findings en `IMPL-LOG-agentic.md` § "Step 0 grep findings" sección obligatoria

Si Step 0 grep finde match inesperado → STOP, escalate PM con paths. NO crees archivo unilateralmente.

## Cross-session coordination (M8 — PR-2 PI-5 also modifies copilot)

PI-5 PR-2 (`docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S2-telegram-orchestrator-memory-cache/prs/PR-2-telegram-orchestrator-hookup/`) está modificando `modules/copilot/`. Architect Step 0.4 confirmó light overlap.

**Antes commit copilot files (chat.py, observability/recording/turn_envelope.py):**
1. `git diff --stat backend/src/modules/copilot/` — ver scope total
2. `git diff backend/src/modules/copilot/<file_que_voy_a_editar>` — ver si tu edit SE SUPERPONE con función que PI-5 también editó
3. Si tu edit es región distinta (regla M8 OK) → procedé
4. Si tu edit toca misma función PI-5 también editó → STOP, escalate PM (regla M8 fallback)

Chris-mediated handshake: ambas sesiones trabajan sin temor sobre mismo código si funciones distintas. Ver `sprint.md` § "Cross-session coordination handshake".

## Workflow Phase 1 — IMPLEMENT (CONTRACT § 4 migration plan sequenced)

**TDD strict per sub-deliverable.**

### Sub-paso 1.1 — `shared/agent_observability/recording/turn_envelope.py::BaseObservabilityContext` (NEW)

1. RED: `tests/shared/agent_observability/test_turn_envelope_base.py` — abstract methods enforcement + lifecycle commit/rollback
2. GREEN: implementar ABC siguiendo CONTRACT § 2 interface (lifecycle: `__aenter__` → turn_start commit; `__aexit__` → turn_end commit; exception → set_turn_error; abstract methods `_build_repos`, `_build_callback_handler`, `_persist_turn_end_data`)
3. Gates: `cd backend && .venv/bin/{ruff check + mypy + pytest}` sobre nuevo file

### Sub-paso 1.2 — `shared/agent_observability/cost/fx_resolver.py::FXResolver.default()` (EXTEND classmethod)

1. RED: `tests/shared/agent_observability/cost/test_fx_resolver_default.py` — `FXResolver.default()` retorna instance con httpx client functional
2. GREEN: add classmethod ~5 LOC
3. Gates

### Sub-paso 1.3 — `modules/copilot/observability/recording/turn_envelope.py` (REFACTOR in-place)

1. RED: `tests/modules/copilot/observability/test_envelope_inheritance.py` — assert `CopilotObservabilityContext(BaseObservabilityContext)` + lifecycle parity con pre-refactor behavior + back-compat alias `from src.modules.copilot.observability import ObservabilityContext` works
2. GREEN: refactor existing class to inherit from base, override only copilot-specific methods. Preserve module-level re-export.
3. Gates + verify copilot regression test green

### Sub-paso 1.4 — `modules/sales_agent/observability/recording/turn_envelope.py::SalesAgentObservabilityContext` (NEW subclass)

⚠️ Step 0 grep gate ANTES de Write. Documentar en IMPL-LOG.

1. NEW class inherits from `BaseObservabilityContext`. Adds `lead_id` + `channel_type` fields. Overrides 3 abstract methods. Class name distinct (NO mirror byte-eq).

### Sub-paso 1.5 — Bug #8 fix `factory.py:78`

1. Edit `FXResolver()` → `FXResolver.default()`. Single line change.
2. Verify no other `FXResolver()` no-arg instances en codebase (architect confirmó solo 1 — verificar tu)

### Sub-paso 1.6 — Sales agent orchestrator wire `observe_turn` (Bug #2 fix)

CONTRACT § 4 step 6 (compulsory):
- `modules/sales_agent/application/orchestrator/conversation_pipeline.py::invoke_agent_with_typing` — wrap `agent_app.ainvoke` en `async with observability_context.observe_turn(...)`
- `modules/sales_agent/application/orchestrator/chat.py` — instantiate `observability_context` antes invoke + pass al pipeline
- `modules/sales_agent/application/orchestrator/outbound_orchestrator.py` — same pattern para outbound

### Sub-paso 1.7 — Tests integration

- `tests/modules/sales_agent/observability/test_real_trace_persistence.py` — REAL DB (no mocks DB session). Setup AsyncSession + lead + tenant → simulate turn lifecycle → assert ≥1 row in `sales_agent_trace_event`. Marker `@pytest.mark.verify`.

### Sub-paso 1.8 — Arch ratchet enforcement

- `tests/architecture/test_no_fxresolver_no_arg.py` — grep test ensuring no `FXResolver()` no-arg call sites en codebase. Future regression block.

### Sub-paso 1.9 — Quality gates global

- `cd backend && .venv/bin/ruff check src/`
- `cd backend && .venv/bin/mypy src/shared/agent_observability/ src/modules/sales_agent/observability/ src/modules/copilot/observability/`
- `cd backend && .venv/bin/pytest tests/shared/agent_observability/ tests/modules/sales_agent/observability/ tests/modules/copilot/observability/ tests/architecture/ -v`
- Si arch fitness ratchet (LOC/anchors/etc) FAIL → fix scope o escalate PM

### Sub-paso 1.10 — Commit + push

Stage por nombre (NUNCA `.` ni `-A`):
```
git add backend/src/shared/agent_observability/recording/turn_envelope.py
git add backend/src/shared/agent_observability/cost/fx_resolver.py
git add backend/src/modules/copilot/observability/recording/turn_envelope.py
git add backend/src/modules/sales_agent/observability/recording/turn_envelope.py
git add backend/src/modules/sales_agent/observability/recording/factory.py
git add backend/src/modules/sales_agent/application/orchestrator/{chat,outbound_orchestrator,conversation_pipeline}.py
git add backend/src/modules/copilot/application/orchestrator/chat.py
git add backend/tests/shared/agent_observability/
git add backend/tests/modules/sales_agent/observability/
git add backend/tests/modules/copilot/observability/test_envelope_inheritance.py
git add backend/tests/architecture/test_no_fxresolver_no_arg.py
git add docs/pm-nico/pis/active/PI-1.1-pi1-post-mortem/sprints/S2-shared-observability/prs/PR-2-shared-agent-observability/IMPL-LOG-agentic.md
```

Commit conventional:
```
feat(shared,observability): lift BaseObservabilityContext + FXResolver.default + fix sales_agent traces persistence (Bug #2 + #8)

Bug #2 fix: orchestrator now wraps ainvoke in observe_turn lifecycle (was
wiring callback handler only, never envelope) → sales_agent_trace_event
+ sales_agent_llm_call rows persist real per turn.

Bug #8 fix: factory.py:78 FXResolver() → FXResolver.default() encapsulates
httpx.Client(timeout=10) boilerplate. Arch ratchet test added preventing
future no-arg regressions.

Anti-duplication first PR: BaseObservabilityContext lifted to shared,
copilot becomes subclass (back-compat alias preserved), sales_agent NEW
subclass (NOT mirror — distinct class + 2 added fields + 3 overrides).

Refs:
- CONTRACT.md § 1 grep evidence (Step 0 GATE)
- CONTRACT.md § 4 migration plan sequenced
- decisions.md D-2 (Bug #2 deferred to PR-2)
- decisions.md D-3 (5-layer anti-duplication enforcement)
```

Push: `git push origin development`. Falla non-fast-forward → STOP escalate PM.

## Workflow Phase 2 — AUTO-AUDIT

1. Spawn `nicolify-gate-runner` Haiku → produces `gate-output.json`
2. Spawn `nicolify-agentic-auditor` Opus con prompt:
   ```
   Audit PR-2-shared-agent-observability. PR-folder: {abs path}. Iter: 1.
   Validar Cat 13 mirror detection PASS (turn_envelope.py sales_agent NEW
   con class distinct + 3 overrides + 2 fields, NO byte-mirror copilot).
   Validar Bug #2 fix end-to-end (test_real_trace_persistence assert >0).
   Validar Bug #8 fix + arch ratchet test.
   Validar parity copilot regression test (back-compat alias).
   ```
3. Lee `REVIEW-agentic.md` verdict.

## Workflow Phase 3 — AUTO-FIX LOOP (max 3 iter)

Findings dentro scope → fix + commit `fix(scope): address auditor findings iter-{N}` + re-spawn auditor.

Findings escalate PM:
- Drift CONTRACT vs código (§ 2 interface)
- Cambio arquitectónico (cambia design)
- Findings tocan archivos PI-5 PR-2 (regla M8 fallback)

Verdict ≠ PASS post 3 iter → STOP, escalate PM.

## Outputs obligatorios

- Code + tests committed + pushed
- `IMPL-LOG-agentic.md` con secciones: Skills consulted (5 mandatory), Step 0 grep findings, Sub-paso execution log, Auto-fix iterations (si entró Phase 3), State-of-the-art validation
- `gate-output.json` final
- `REVIEW-agentic.md` final verdict PASS

## Restricciones absolutas

- NO tocar `modules/{brand,offer,landing,assets,analytics,advertising,social_media,scheduling,connections,iam,crm}/`
- NO tocar `frontend/`
- NO tocar `docs/pm-nico/process/` ni `roadmap.md` ni `MEMORY.md` ni `current-state/{m}.md` (PM owns)
- NO `--no-verify`, NO `git pull`, NO `git push --force`, NO `git revert` sin PM approval
- NO mocks DB session en `test_real_trace_persistence.py` — debe ser REAL persistence assert
- NO band-aid try/except swallow
- NO mirror copilot — pattern es Strangler Fig + LIFT-TO-SHARED (CONTRACT § 1 confirmó)
- Cross-session M8: si tu edit toca misma función que PI-5 PR-2 también editó → STOP escalate

## Cuando termines exitosamente Phase 3 verdict PASS

Última línea exacta:
```
<!-- @pm: agentic phase done. PR-2 verdict PASS. Smoke test sales_agent_trace_event count > 0 pendiente Chris-mediated Telegram trigger. Próximo paso: ejecutar /pm "PR-2 agentic done — Telegram smoke + cierre" -->
```

---

## BLOQUE VARIABLE (per-invocation)

PR-folder absoluto: `/home/chris/AISALESHT/docs/pm-nico/pis/active/PI-1.1-pi1-post-mortem/sprints/S2-shared-observability/prs/PR-2-shared-agent-observability/`

CONTRACT.md SSoT: `{PR-folder}/CONTRACT.md` (747 lines, 9 secciones)

Iteración: 1.

Tenant test (post-build smoke): `6347e21e-8112-4aa1-80d3-6adaa73bf6f9` (visionarias).
Lead reference: `cb711aea-e0a5-42c0-b276-7a63570207bd` (Christian Revilla, Telegram smoke).

Cross-session activa: PI-5 PR-2 (`docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S2-telegram-orchestrator-memory-cache/prs/PR-2-telegram-orchestrator-hookup/`). Chris-mediated handshake done — proceder M8 con verify pre-commit.

Cap maxTurns 150 (Opus). Architect estimó 50-70 turns para builder — fits.
