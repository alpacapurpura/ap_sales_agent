# Builder Agentic — PR-1-pi1-bugs-hotfix

## BLOQUE FIJO (cacheable)

Sos `nicolify-agentic` builder Opus. Implementás bug fix profundo en sales_agent observability.

**Surface allowed (PRIMARIOS — solo edit):**
- `backend/src/modules/sales_agent/observability/**`
- `backend/src/modules/sales_agent/application/orchestrator/chat.py`
- `backend/src/modules/sales_agent/application/orchestrator/outbound_orchestrator.py`
- `backend/tests/modules/sales_agent/observability/**`

**Surface read-only:**
- Cualquier archivo del repo. NO editar fuera primarios sin escalate PM.

**Skills obligatorios cargar antes de coding:**
- `sales-agent-expert` (voice, channel registry, observability invariantes, eval goldens)
- `copilot-expert` (referencia paralela — copilot tiene observability funcionando, sales_agent debería estar simétrico)
- `tessl__langgraph` (LangGraph callbacks, state machine)

**Rules vinculantes (CLAUDE.md):**
- Native-first: lint/test NATIVE WSL.
- Tenant isolation siempre: queries con `.where(Model.tenant_id == tenant_id)`.
- DDD Inside-Out: domain → infrastructure → application → api.
- SQLA 2.0 async only: `select(Model).where(...)`. NO `session.query()`.
- `structlog`, no `print`/`logging`.
- Git: development branch. Stage by name. NUNCA pull/force/revert.
- TDD: test RED before code GREEN.
- Pre-commit hooks native, NO `--no-verify`.

**Bug a resolver:**

`sales_agent_trace_event` + `sales_agent_llm_call` + `sales_agent_routing_log` = **0 filas globalmente** (ALL tenants), pese a:
- 68 mensajes reales en `messages` table (4 leads tenant `6347e21e-8112-4aa1-80d3-6adaa73bf6f9`, último 2026-04-27)
- Recording infra completa: `observability/recording/factory.py::build_sales_agent_callback_handler`
- Wired en `application/orchestrator/chat.py:327` + `application/orchestrator/outbound_orchestrator.py:226`

Hipótesis a verificar (deep RCA):
1. Handler best-effort con try/except que swallow excepción + structlog warning silencioso
2. Dual-write window legacy path (`@trace_node`) reemplaza S1 path silently
3. AsyncSession scope incorrecto — handler graba a session que nunca commitea
4. Conditional skip cuando `tenant_id` o `lead_id` es None
5. Async task scheduling pierde rows pre-commit
6. `_persist_trace_event_row` retorna early antes de DB write

**Workflow Phase 1 — Implement:**
1. Step 0 GATE — leer `PR.md` parent + cargar skills sales-agent-expert + copilot-expert + tessl__langgraph
2. Step 1 — RCA evidence gathering:
   - Read full `observability/recording/callback_handler.py` (todas las líneas)
   - Read `observability/recording/factory.py`
   - Read `observability/persistence/trace_event_repository.py`
   - Read `application/orchestrator/chat.py` lines 300-400 (callback wiring context)
   - Read `application/orchestrator/outbound_orchestrator.py` lines 200-260
   - Compare con copilot equivalent: `modules/copilot/observability/recording/` (que SÍ funciona — copilot_trace_event tiene rows)
   - Generar hipótesis ranqueada con evidencia path:line
3. Step 2 — Reproduction test (RED):
   - Crear `tests/modules/sales_agent/observability/test_real_trace_persistence.py`
   - Setup: real AsyncSession (postgres test DB) + real lead + real tenant
   - Act: instanciar `build_sales_agent_callback_handler` con valid params, simular turn lifecycle event (on_chain_start + on_llm_start + on_chain_end)
   - Assert: query `sales_agent_trace_event` después → ≥1 row con expected fields
   - Test debe estar RED inicialmente (reproducir bug)
4. Step 3 — Fix root cause:
   - Aplicar fix mínimo cohesivo que hace test GREEN
   - NO band-aid try/except. Si hay try/except actual swallowing → eliminar y dejar fallar fast con structlog error
   - Verificar parity con copilot path
5. Step 4 — Quality gates:
   - `cd backend && .venv/bin/ruff check src/modules/sales_agent/`
   - `cd backend && .venv/bin/mypy src/modules/sales_agent/observability/ --strict`
   - `cd backend && .venv/bin/pytest tests/modules/sales_agent/observability/ -v`
   - `cd backend && .venv/bin/pytest tests/architecture/ -x` (arch fitness)
6. Step 5 — Smoke test real:
   - Verificar manualmente que `_persist_trace_event_row` graba commiteando (no rollback silently)
   - Si tienes acceso a real DB: ejecutar 1 turn fake desde python REPL → `SELECT count(*) FROM sales_agent_trace_event WHERE created_at > now() - interval '1 minute'` debe ser ≥1
7. Step 6 — Write `IMPL-LOG-agentic.md` en PR-folder:
   - RCA completo con paths:line
   - Diff exacto del fix
   - Tests escritos
   - Gate output
   - Hypothesis verified vs descartadas
8. Step 7 — Commit + push:
   - Stage: archivos por nombre
   - Commit: `fix(sales_agent,observability): wire callback handler real persistence — bug #2 PI-1 hotfix` con cuerpo RCA
   - Push: `git push origin development`. Falla non-fast-forward → STOP escalate PM.

**Workflow Phase 2 — Auto-audit:**
- Spawn `nicolify-agentic-auditor` (Opus) con prompt:
  > Audit PR-1-pi1-bugs-hotfix agentic surface. PR-folder: `docs/pm-nico/pis/active/PI-1.1-pi1-post-mortem/sprints/S1-stabilization/prs/PR-1-pi1-bugs-hotfix/`. Consume `gate-output.json`. Validar: real DB persistence test (no mocks), tenant isolation correcta, prompt cache slot intacto si aplica, brand voice no afectado, eval goldens sales_agent siguen verdes. Write `REVIEW-agentic.md`.

**Workflow Phase 3 — Auto-fix loop:**
- Verdict FAIL/WARN dentro scope → fix + commit `fix(sales_agent): address auditor findings iter-{N}` + re-spawn auditor. Max 3 iter.
- Post 3 iter sin PASS → escalate PM con findings + paths.

**EXIT criteria:**
- Verdict PASS auditor.
- Real persistence test verde (no mock).
- Manual smoke verifies real INSERT en DB.
- IMPL-LOG-agentic.md describe RCA completo.

**Backfill traces históricos:**
- DEFERIDO. Discusión Chris post-PR-1 ship. NO incluir en este PR.

**Restricciones absolutas:**
- NO tocar `modules/copilot/` (eso es PI-2 territory; tu cambio puede leer pero no editar copilot — referencia paralela solo).
- NO tocar `modules/brand` / `modules/offer` / cualquier business module (eso es backend builder).
- NO tocar frontend (eso es FE builder paralelo).
- NO tocar `docs/pm-nico/process/` ni `roadmap.md` ni `MEMORY.md` ni `current-state/{m}.md`.
- NO `--no-verify` commit.
- NO `git pull` / `git push --force` / `git revert` sin PM aprobación.
- NO mocking de DB session en el smoke test — debe ser real persistence assert.
- NO try/except swallow en fix (rule explicita).

---

## BLOQUE VARIABLE (per-invocation)

PR-folder absoluto: `/home/chris/AISALESHT/docs/pm-nico/pis/active/PI-1.1-pi1-post-mortem/sprints/S1-stabilization/prs/PR-1-pi1-bugs-hotfix/`

Tenant test usado: `6347e21e-8112-4aa1-80d3-6adaa73bf6f9` (visionarias).

Lead test reference: `cb711aea-e0a5-42c0-b276-7a63570207bd` (Christian Revilla, 27 mensajes Telegram, último 2026-04-16).

Iteración: 1.

Read `PR.md` en PR-folder para detalle completo bug #2 + hipótesis a verificar.

Cuando termines Phase 3 con verdict PASS, última línea de tu última respuesta debe ser:

```
<!-- @pm: agentic phase done. Próximo paso: ejecutar /pm "PR-1 agentic phase done" -->
```
