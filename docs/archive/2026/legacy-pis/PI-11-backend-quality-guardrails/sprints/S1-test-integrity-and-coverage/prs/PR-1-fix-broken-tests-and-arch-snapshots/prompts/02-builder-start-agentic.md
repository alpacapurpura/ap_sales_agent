# Prompt — Builder kickoff (PR-1 Agentic surface) — POLLUTER HUNT INCLUIDO

> Builder: `nicolify-agentic` (Opus)
> Surface: `sales_agent`, `copilot`, `tests/architecture/test_sales_agent_*`, `tests/modules/copilot/`, `tests/modules/sales_agent/`, `tests/integration/test_outbound_orchestrator_e2e.py`
> Owns: snapshot helpers outbox-aware + polluter hunt sistemático + EventBus migration agentic
> Polluter hunt sin band-aid `@pytest.mark.flaky` final (decisión D4).

## Spawn pattern

```
Agent({
  description: "Build PR-1 agentic surface + polluter hunt",
  subagent_type: "nicolify-agentic",
  model: "opus",
  prompt: <BLOQUE FIJO + BLOQUE VARIABLE abajo>
})
```

## Prompt body

```
[BLOQUE FIJO — cacheable]

Sos `nicolify-agentic` (Opus 4.7[1M]). Trabajo: implementar PR-1 agentic surface + migrar EventBus mocks agentic + snapshot helpers outbox-aware + polluter hunt sistemático SIN band-aid final.

Step 0 OBLIGATORIO:
  date -u +%Y-%m-%d   # captura today

Lectura obligatoria (en orden):
1. {pr_folder}/CONTEXT-BRIEF.md — pre-flight Haiku
2. {pr_folder}/CONTRACT.md — design singleton fixture (PR-1 § 1-2) + EventBus migration (§ 3) + snapshot helpers outbox-aware (§ 4) + polluter hunt methodology (§ 6)
3. {pr_folder}/PR.md — scope expandido completo
4. PI-11/PI.md — § Decisión arquitectónica clave (D1-D7)
5. CLAUDE.md — Git Workflow inviolable + tenant isolation + DDD

Skills obligatorios (invocar ANTES tocar código):
- copilot-expert
- sales-agent-expert
- tessl__langgraph
- tessl__pytest-api-testing (singleton fixture + polluter detection patterns)
- tessl__graceful-degradation (si fixes tocan external calls)

Restricciones DURAS:
- Tocás SOLO archivos surface agentic: `modules/sales_agent`, `modules/copilot`, `tests/modules/sales_agent/`, `tests/modules/copilot/`, `tests/architecture/test_sales_agent_*`, `tests/integration/test_outbound_orchestrator_e2e.py`.
- NO tocás `tests/conftest.py` (business builder owns — singleton fixture exhaustivo es business surface).
- NO tocás `modules/{brand,offer,landing,assets,analytics,advertising,social_media,scheduling,connections,iam,crm,core}/`.
- NO tocás `frontend/`.
- NO tocás archivos otros PRs activos.
- PROHIBIDO: git pull, git fetch && merge, git push --force, git revert, git reset --hard, git add .|-A|-u, git commit --no-verify.
- Push falla non-fast-forward → STOP, reportar.

NOTA STASH:
- Stash{0} apply lo hace business builder (Phase 1 Step 1 de business prompt). NO hagas `git stash pop` vos.
- Esperá señal PM o branch state que confirme stash applied antes de Phase 1.
- Si arrancás antes que business apply stash → archivos agentic del stash NO estarán presentes. Espera o coordina via @pm comment.

Workflow Phase 1 — IMPLEMENT (asumiendo stash ya applied por business builder):

Step 1 — REVISAR archivos agentic del stash (modificar/extender vs scope nuevo D2/D4):
  Archivos stash agentic:
  - tests/architecture/test_sales_agent_anchors.py — `SALES-AGENT-OUTBOUND-PR7` (verificar)
  - tests/architecture/test_sales_agent_system_prompt_order.py — `CAMPAIGN_CONTEXT` (verificar)
  - tests/modules/sales_agent/prompts/test_compose_system_prompt.py — `CAMPAIGN_CONTEXT` (verificar)
  - tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py — **REMOVER `@pytest.mark.flaky(reruns=2)` post Phase 4 polluter fix**
  - tests/modules/copilot/test_outbox_adapter_integration.py — REVISAR vs migración adapter_bus (D2 — NO monkeypatch False)
  - tests/modules/copilot/test_offer_section_tools.py — `next_step_hint` (verificar)
  - tests/modules/copilot/test_voice_api.py — 410 Gone (verificar)
  - tests/modules/copilot/test_voice_combined.py — 410 Gone (verificar)
  - tests/integration/test_outbound_orchestrator_e2e.py — mock target rename (verificar)

Step 2 — EVENTBUS MIGRATION AUDIT AGENTIC:
  Grep:
    grep -rn "EventBus\.publish\|LegacyEventBus\|event_bus\.publish" /home/chris/AISALESHT/backend/tests/modules/sales_agent/ /home/chris/AISALESHT/backend/tests/modules/copilot/ /home/chris/AISALESHT/backend/tests/integration/ 2>/dev/null

  Cada test detectado → migrar al path real (D2):
    - asserts EVENT FUE PUBLICADO → switch `adapter_bus.publish` mock o query DB outbox table
    - asserts HANDLER FUE INVOCADO → switch outbox enqueue inspection

  Documentar lista completa migrated en IMPL-LOG.md sección "EventBus migration audit agentic".

Step 3 — SNAPSHOT HELPERS OUTBOX-AWARE:
  Target: `backend/tests/modules/sales_agent/orchestrator/_chat_flow_snapshot_helpers.py` (+ similares).

  Problema actual: helpers capturan `domain_events=[]` siempre porque mockean `EventBus.publish` legacy (path muerto post-flag-flip).

  Migración:
    - Helper consume outbox table directamente: `select(DomainEventOutbox).where(tenant_id=...).order_by(created_at)`
    - O instala `adapter_bus.publish` probe que captura events real
    - Snapshot ahora refleja realidad post-flag-flip
    - Tests usando helpers: actualizar baseline si snapshot cambia (revisar baselines existentes)

Step 4 — POLLUTER HUNT SISTEMÁTICO (decisión D4 — SIN band-aid final):

Target: `tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py::test_chat_flow_telegram_new_lead_snapshot`. Falla en suite completa, pasa en isolation.

Methodology obligatoria:

Phase 4.1 — Bisección de orden:
  cd /home/chris/AISALESHT/backend
  .venv/bin/pytest --collect-only -q | tee /tmp/pi11-pr1-test-order.txt

  Binary search: ejecutar parciales hasta target con halves de orden hasta identificar mínimo set de tests previos que mutan estado:
    .venv/bin/pytest <first_half> tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py::test_chat_flow_telegram_new_lead_snapshot
    .venv/bin/pytest <second_half> tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py::test_chat_flow_telegram_new_lead_snapshot

  Iterar hasta identificar specific test(s) culprit.

Phase 4.2 — JSON diff exhaustivo:
  Capturar baseline snapshot (test isolation):
    .venv/bin/pytest tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py::test_chat_flow_telegram_new_lead_snapshot --snapshot-update
  Capturar snapshot suite-completa cuando falla:
    Run suite con --snapshot-update + capture output snapshot post-failure
  Diff campo a campo entre baseline vs failed → identificar campos mutados

Phase 4.3 — Setup-only suite:
  .venv/bin/pytest --setup-only tests/modules/sales_agent/orchestrator/ -v
  Identificar fixtures cargadas + state shared

Phase 4.4 — Sospechosos primarios (orden investigación):
  1. LangGraph global compilation cache (graphs compiled once + reused; mutación cross-test posible). Inspeccionar `langgraph.graph.compiled_graph` references o caches modulo-level.
  2. deepagents subagent state cache. Inspeccionar `deepagents.SubAgentMiddleware` state.
  3. Módulo-level `uuid.uuid4` patches (tests previos patchean uuid module-wide → leak). Grep `uuid.uuid4 =`, `monkeypatch.setattr.*uuid`.
  4. LLM router/factory state leak (singleton fixture business builder cubre, validar después business commit).
  5. Settings mutation persistente (settings cached, monkeypatch restore falla). Grep `Settings()` calls outside fixture scope.
  6. `langgraph.checkpoint` state shared. Inspeccionar checkpointer instances.
  7. Mocks de `httpx.AsyncClient` que persisten cross-test. Grep `mock_httpx`, `respx`.

Phase 4.5 — Documentar IMPL-LOG sección "Polluter hunt log":
  - Hipótesis cada Phase 4.4 sospechoso
  - Experimento ejecutado
  - Resultado
  - Polluter identificado (root cause) o ESCALATE PM si supera 6h Opus

Phase 4.6 — Fix at source (NO marker, NO xfail):
  Si polluter es módulo del sistema → fix de raíz aunque requiera refactor:
    - LangGraph compilation cache reset → fixture autouse o reset method
    - deepagents global state isolation → context manager fixture
    - mock module-level uuid scoping → tighten scope (function vs module)

Phase 4.7 — Pre-PR-1 ship:
  REMOVER `@pytest.mark.flaky(reruns=2)` del test (stash band-aid).
  Test debe pasar 1.0 sin reruns en suite completa.
  Validar 5 runs consecutivos suite completa green.

Sin budget cap explícito. Si supera 6h Opus → escalate PM Chris budget extra. **NO ship con band-aid permanente.**

Step 5 — QUALITY GATES LOCALES NATIVE:
   cd backend && .venv/bin/ruff check src/ tests/ --no-cache
   cd backend && .venv/bin/ruff format --check src/ tests/
   cd backend && .venv/bin/pytest tests/architecture/test_sales_agent_*.py -v --override-ini="addopts="
   cd backend && .venv/bin/pytest tests/modules/sales_agent/ tests/modules/copilot/ --timeout=60
   # 5 runs validation polluter fix:
   for i in 1 2 3 4 5; do
     .venv/bin/pytest --tb=short -x -q 2>&1 | tail -20
   done

Step 6 — IMPL-LOG.md sections:
  - Step 0 grep findings
  - Stash agentic files revisión
  - EventBus migration audit agentic (path-by-path)
  - Snapshot helpers outbox-aware design
  - Polluter hunt log (Phase 4.1-4.7 detallado)
  - Polluter root cause + fix at source
  - Validation 5 runs consecutivos green
  - Skills consulted (copilot-expert/sales-agent-expert/tessl__langgraph)
  - Quality gates output
  - Commits conventional

Step 7 — STAGE + COMMITS + PUSH (conventional granular):
  git add backend/tests/architecture/test_sales_agent_anchors.py backend/tests/architecture/test_sales_agent_system_prompt_order.py
  git commit -m "test(arch): register SALES-AGENT-OUTBOUND-PR7 anchor + CAMPAIGN_CONTEXT cacheable (stash)"
  git add backend/tests/modules/sales_agent/prompts/test_compose_system_prompt.py
  git commit -m "test(sales_agent): expect CAMPAIGN_CONTEXT in cacheable fragments (stash)"
  git add backend/tests/modules/copilot/
  git commit -m "test(copilot): migrate EventBus mocks to adapter_bus + 410 Gone voice legacy + next_step_hint contract"
  git add backend/tests/modules/sales_agent/orchestrator/_chat_flow_snapshot_helpers.py
  git commit -m "test(sales_agent): make snapshot helpers outbox-aware (capture from outbox table)"
  git add backend/tests/integration/test_outbound_orchestrator_e2e.py
  git commit -m "test(integration): rename mock target to build_sales_agent_observability_context"
  # Polluter fix at source — paths según hunt findings:
  git add <polluter_fix_paths>
  git commit -m "fix(<scope>): isolate <polluter_root_cause> to prevent cross-test pollution"
  git add backend/tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py
  git commit -m "test(sales_agent): remove flaky band-aid (polluter fixed at source)"

  git push origin development

Workflow Phase 2 — AUTO-GATE-RUN + AUTO-AUDIT:

Step 8 — Spawn gate-runner Haiku:
  Agent({ description: "Run /test-backend gates iter-1 agentic", subagent_type: "nicolify-gate-runner", model: "haiku",
    prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots; <command>: test-backend; <iter>: 1" })
  Esperá gate-output.json. any_fail → fix scope.

Step 9 — Spawn agentic auditor Opus:
  Agent({ description: "Audit PR-1 agentic iter-1", subagent_type: "nicolify-agentic-auditor", model: "opus",
    prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots; <surface>: agentic; <iter>: 1" })
  Esperá REVIEW-agentic.md. PASS → terminás.

Workflow Phase 3 — AUTO-FIX LOOP (max 3):
- Findings dentro scope agentic → fix.
- Findings drift CONTRACT → STOP, escalate PM.
- Findings cross-PR → ignorar + nota IMPL-LOG.
- Re-spawn gate-runner + auditor cada iter.
- Iter 3 sin PASS → STOP, escalate PM.

Outputs:
- Code + tests committed + pushed (granular)
- IMPL-LOG.md completo
- gate-output.json
- REVIEW-agentic.md verdict PASS

Última línea verdict PASS:
<!-- @pm: implementación + gate-runner + auditoría done agentic (verdict PASS). Polluter fixed at source (sin band-aid). PR-1 agentic surface listo. Esperar business surface PASS para /pm "PR-1 cerrar" -->

Reportar a Chris brief < 350 palabras: tests fixed agentic + EventBus migration count + snapshot helpers migrated + POLLUTER ROOT CAUSE + fix applied + 5-runs validation + iters audit + verdict.

[BLOQUE VARIABLE — específico de esta invocación]

Surface a implementar: agentic
PR folder: docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots
Modules touched: sales_agent, copilot
Iter actual: 1
Stash apply OWNER: NO TÚ — business builder hace pop. Esperá señal/check git status muestra files agentic stash pre-Phase 1.
Polluter target: tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py::test_chat_flow_telegram_new_lead_snapshot
Polluter budget: sin cap — escalate PM Chris si supera 6h Opus
Polluter band-aid: REMOVER pre-ship (decisión D4)
```
