# Prompt — Builder kickoff (PR-1 Business surface)

> Builder: `nicolify-backend` (Sonnet)
> Surface: `brand`, `shared`, `crm`, `campaigns`, `core`, `tests/conftest.py`, `tests/architecture/test_ddd_boundaries.py`, `tests/architecture/test_folder_naming.py`, `frontend` stash fix
> Owns: `tests/conftest.py` (singleton fixture exhaustivo) + EventBus mocks migration business
> Stash apply OWNER: business builder hace `git stash pop` en Phase 1 Step 1

## Spawn pattern

```
Agent({
  description: "Build PR-1 business surface",
  subagent_type: "nicolify-backend",
  model: "sonnet",
  prompt: <BLOQUE FIJO + BLOQUE VARIABLE abajo>
})
```

## Prompt body

```
[BLOQUE FIJO — cacheable]

Sos `nicolify-backend` (Sonnet). Trabajo: implementar PR-1 business surface + apply stash + extender singleton fixture exhaustivo + migrar EventBus mocks business + bug fix litellm.py + LegacyEventBus deprecation warning.

Step 0 OBLIGATORIO:
  date -u +%Y-%m-%d   # captura today

Lectura obligatoria (en orden):
1. {pr_folder}/CONTEXT-BRIEF.md — pre-flight Haiku
2. {pr_folder}/CONTRACT.md — design singleton fixture + EventBus migration strategy + litellm clamp + LegacyEventBus deprecation
3. {pr_folder}/PR.md — scope expandido completo
4. PI-11/PI.md — § Decisión arquitectónica clave (D1-D7)
5. CLAUDE.md — Git Workflow inviolable + tenant isolation + DDD

Skills obligatorios (invocar ANTES de tocar código):
- backend-expert
- tessl__pytest-api-testing (singleton fixture pattern)

Restricciones DURAS:
- Tocás SOLO archivos surface business: `brand`, `shared`, `crm`, `campaigns`, `core`, `tests/conftest.py`, `tests/architecture/test_ddd_boundaries.py`, `tests/architecture/test_folder_naming.py`, `tests/modules/brand/`, `tests/shared/`.
- NO tocás `modules/copilot/`, `modules/sales_agent/` (escalate `nicolify-agentic`).
- NO tocás `tests/modules/copilot/`, `tests/modules/sales_agent/`, `tests/architecture/test_sales_agent_*` (agentic builder).
- FE fix `frontend/src/features/closer-studio/components/inbox/__tests__/CampaignTag.test.tsx` SÍ (parte stash, single-line URL slug fix; vitest run nativo confirma).
- NO tocás archivos otros PRs activos (regla M7).
- PROHIBIDO: git pull, git fetch && merge, git push --force, git revert, git reset --hard, git add .|-A|-u, git commit --no-verify.
- Push falla non-fast-forward → STOP, reportar. NO git pull.

Workflow Phase 1 — APPLY STASH + IMPLEMENT:

Step 1 — APPLY STASH:
  cd /home/chris/AISALESHT
  git stash list  # confirmar stash@{0} existe con label "WIP PI-11 PR-1 partial — 16 tests/source fixes from paused pase-produccion 2026-05-04"
  git status --short  # confirmar tree clean
  git stash pop   # aplicar 16 archivos

  Si conflict → resolución manual file-by-file (NO descartar stash). Append IMPL-LOG bloqueador si no resoluble.

Step 2 — REVISAR cada archivo del stash vs scope nuevo (decisión D2):
  Archivos stash con `monkeypatch.setattr(USE_OUTBOX_PATTERN_*=False)` son BAND-AID. Approach correcto = migración mock al `adapter_bus` (decisión D2).

  Lista re-revisar:
  - tests/modules/brand/test_outbox_adapter_integration.py — REVISAR vs migración adapter_bus
  - tests/modules/brand/test_brand_section_updated_event.py — REVISAR vs migración adapter_bus + tabla outbox fixture
  - tests/shared/domain_events/test_event_bus_adapter.py — REVISAR vs migración adapter_bus

  Para cada test stash con monkeypatch False:
    a) Mantener monkeypatch False SOLO si test específicamente prueba comportamiento legacy capability
    b) De lo contrario migrar a `adapter_bus` mock o outbox table query

Step 3 — SINGLETON FIXTURE EXHAUSTIVO (extender stash version):
  Grep cross-codebase obligatorio:
    grep -rn "_instance = None\|_instance: Optional\|cls._instance" /home/chris/AISALESHT/backend/src/ 2>/dev/null
    grep -rn "@lru_cache\|@cache" /home/chris/AISALESHT/backend/src/shared/ /home/chris/AISALESHT/backend/src/modules/ 2>/dev/null

  Build lista exhaustiva. Lista mínima esperada (validar via grep):
    - LLMFactory._instance (src/shared/infrastructure/llm/factory.py)
    - ChatOrchestrator._instance
    - SemanticRouter._instance
    - +cualquier otro detectado

  Extender `backend/tests/conftest.py::_reset_singletons_between_tests`:
    - Comment per-singleton: `# {ClassName}._instance — reset reason: {why}`
    - Reset pre-test (yield)
    - Reset post-test (cleanup)
    - Si singleton tiene cleanup específico → invocar antes reset

  Documentar lista completa + grep evidence en IMPL-LOG.md sección "Singleton inventory + fixture extension".

Step 4 — EVENTBUS MIGRATION AUDIT BUSINESS:
  Grep cross-codebase:
    grep -rn "EventBus\.publish\|LegacyEventBus\|event_bus\.publish" /home/chris/AISALESHT/backend/tests/modules/brand/ /home/chris/AISALESHT/backend/tests/shared/ /home/chris/AISALESHT/backend/tests/modules/crm/ 2>/dev/null

  Cada test detectado → migrar mock al path real:
    - asserts EVENT FUE PUBLICADO → switch `adapter_bus.publish` mock o query DB outbox table
    - asserts HANDLER FUE INVOCADO → switch outbox enqueue inspection + simulación dispatcher

  Documentar lista completa migrated en IMPL-LOG sección "EventBus migration audit business".

Step 5 — LITELLM.PY KIMI CLAMP (REVISAR stash):
  - Verificar fix stash en `backend/src/shared/infrastructure/llm/providers/litellm.py` cubre TODOS los casos kimi (no solo K2.6).
  - Mirror del clamp adapter legacy `kimi.py`.
  - Test regresión: si no existe en stash, crear `tests/shared/infrastructure/llm/providers/test_litellm_kimi_clamp.py`.

Step 6 — LEGACYEVENTBUS DEPRECATION RUNTIME WARNING:
  - `backend/src/shared/domain_events/legacy_event_bus.py` (path real validar) — emit `warnings.warn(DeprecationWarning, ...)` + `structlog.warning(...)` cuando `publish()` invoked Y outbox flag `True`.
  - Excepción: tests internos capability (suppress via context).
  - Test: `test_legacy_event_bus_emits_deprecation_warning_when_outbox_on`.

Step 7 — QUALITY GATES LOCALES NATIVE:
   cd backend && .venv/bin/ruff check src/ tests/ --no-cache
   cd backend && .venv/bin/ruff format --check src/ tests/
   cd backend && .venv/bin/pytest tests/architecture/ -v --override-ini="addopts="
   cd backend && .venv/bin/pytest tests/modules/brand/ tests/shared/domain_events/ tests/modules/crm/ --timeout=60
   cd frontend && npx vitest run src/features/closer-studio/  # FE stash fix verify

Step 8 — IMPL-LOG.md:
  - Step 0 grep findings (singleton inventory + EventBus migration audit)
  - Stash apply audit (16 archivos revisados, decisiones per-archivo D2)
  - Singleton fixture exhaustive design + grep evidence
  - EventBus migration list business (path-by-path)
  - litellm.py clamp validation
  - LegacyEventBus deprecation pattern
  - Skills consulted
  - Quality gates output
  - EXTEND-vs-NEW decisions
  - Commits conventional

Step 9 — STAGE + COMMITS + PUSH:
  Conventional commits granulares:
    git add backend/tests/conftest.py
    git commit -m "test(conftest): extend singleton fixture exhaustivo (PI-11 PR-1)"
    git add backend/src/shared/infrastructure/llm/providers/litellm.py tests/shared/infrastructure/llm/providers/test_litellm_kimi_clamp.py
    git commit -m "fix(llm): clamp kimi temperature in litellm provider (production bug — Kimi K2.6 HTTP 400)"
    git add backend/src/shared/domain_events/legacy_event_bus.py
    git commit -m "feat(events): emit DeprecationWarning when LegacyEventBus.publish called with outbox flag on"
    git add backend/tests/architecture/test_ddd_boundaries.py backend/tests/architecture/test_folder_naming.py
    git commit -m "test(arch): allowlist 3 cross-module imports + naming exception (stash apply)"
    git add backend/tests/modules/brand/ backend/tests/shared/domain_events/test_event_bus_adapter.py
    git commit -m "test(brand,shared): migrate EventBus mocks to adapter_bus path (D2)"
    git add frontend/src/features/closer-studio/components/inbox/__tests__/CampaignTag.test.tsx
    git commit -m "test(closer-studio): fix CampaignTag URL slug to ASCII /campanas/"

  git push origin development

Workflow Phase 2 — AUTO-GATE-RUN + AUTO-AUDIT:

Step 10 — Spawn gate-runner Haiku:
  Agent({
    description: "Run /test-backend gates iter-1",
    subagent_type: "nicolify-gate-runner",
    model: "haiku",
    prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots; <command>: test-backend; <iter>: 1"
  })
  Esperá gate-output.json. Si overall.any_fail = true → fix scope, re-stage + re-commit + re-spawn gate-runner.

Step 11 — Spawn auditor Opus:
  Agent({
    description: "Audit PR-1 business iter-1",
    subagent_type: "nicolify-backend-auditor",
    model: "opus",
    prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots; <surface>: business; <iter>: 1"
  })
  Esperá REVIEW-backend.md. Verdict PASS → terminás. Verdict ≠ PASS → fix loop max 3 iter.

Workflow Phase 3 — AUTO-FIX LOOP (max 3):
- Findings file:line dentro scope business → fix.
- Findings drift CONTRACT → STOP, escalate PM.
- Findings cross-PR → ignorar + nota IMPL-LOG (regla M7).
- Re-stage + commit `fix(scope): address auditor findings iter-{N}` + push + re-spawn gate-runner + auditor.
- Iter 3 sin PASS → STOP, escalate PM.

Outputs:
- Code + tests committed + pushed (granular commits)
- IMPL-LOG.md completo
- gate-output.json final
- REVIEW-backend.md (auditor verdict PASS)

Última línea respuesta verdict PASS:
<!-- @pm: implementación + gate-runner + auditoría done business (verdict PASS). PR-1 business surface listo. Esperar agentic surface PASS para /pm "PR-1 cerrar" -->

Reportar a Chris brief < 300 palabras: stash applied + tests fixed + EventBus migration count + singleton fixture coverage + gate iters + audit iters + verdict.

[BLOQUE VARIABLE — específico de esta invocación]

Surface a implementar: business
PR folder: docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots
Modules touched: brand, shared, crm, campaigns, core, frontend/closer-studio (FE stash fix)
Iter actual: 1
Stash apply OWNER: TÚ (business builder)
```
