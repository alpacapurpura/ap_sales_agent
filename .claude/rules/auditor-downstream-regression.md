# Auditor Downstream Regression Scope

**Origen:** PI-12 S1 Story A T-1 (2026-05-04). Auditor `auditor-backend` aprobó cost_recorder canonicalization PASS — pero NO corrió tests downstream que mockean callback_handler en `modules/{copilot,sales_agent}/observability/`. Bug `litellm.get_llm_provider("kimi/kimi-k2.6")` raises BadRequestError llegó a S1 (T-1-bis micro-ticket nuevo). Severidad: **CRÍTICA**.

## Regla cardinal

Cuando auditor reviewing PR toca código `shared/` o módulo con consumers conocidos, MUST run test downstream que tocan superficies dependientes — NO sólo tests del módulo modificado.

**Mecánica:** auditor lee diff `git diff --name-only HEAD~N..HEAD`. Para cada path tocado, mapea a downstream test set vía tabla SSoT abajo. Spawn gate-runner adicional con scope downstream tests si no cubierto en gate-output.json original.

## Tabla SSoT — surface → downstream test paths

> Mantener actualizada cuando agregás nueva surface shared cross-consumer.

| Surface modified (path) | Downstream test paths que MUST run | Razón |
|---|---|---|
| `shared/agent_observability/recording/turn_envelope.py` | `tests/modules/copilot/observability/`<br>`tests/modules/sales_agent/observability/` | TurnEnvelope base class — both copilot + sales_agent extend |
| `shared/agent_observability/recording/base_callback_handler.py` | `tests/modules/copilot/observability/test_callback_handler*.py`<br>`tests/modules/sales_agent/observability/test_callback_handler*.py` | Callback base class |
| `shared/agent_observability/cost/calculator.py` | `tests/modules/copilot/observability/test_callback_handler_usage*.py`<br>`tests/modules/sales_agent/observability/test_callback_handler.py`<br>`tests/shared/agent_observability/cost/` | Cost calculator consumido por todos callbacks |
| `shared/agent_observability/cost/pricing_resolver.py` | idem | Pricing resolver |
| `shared/agent_observability/cost/fx_resolver.py` | idem | FX resolver |
| `shared/agent_observability/cost/cost_recorder.py` (or similar) | `tests/modules/copilot/observability/test_callback_handler_usage_fallbacks.py`<br>`tests/modules/sales_agent/observability/test_callback_handler.py::TestOnChatModelEnd::test_persists_row_with_sales_columns` | **CASO ORIGEN D4** — cost_recorder consumido por callback handlers ambos modulos |
| `shared/agent_observability/persistence/base_trace_event_repo.py` | `tests/modules/copilot/observability/test_*_repo*.py`<br>`tests/modules/sales_agent/observability/test_*_repo*.py` | Trace event repo base |
| `shared/agent_observability/persistence/base_llm_call_repo.py` | idem | LLM call repo base |
| `shared/agent_observability/persistence/tenant_billing_config_repository.py` | `tests/shared/billing/`<br>`tests/modules/copilot/observability/`<br>`tests/modules/sales_agent/observability/` | Billing config tenant |
| `shared/agent_observability/channels/format_for_channel.py` | `tests/modules/copilot/`<br>`tests/modules/sales_agent/` | Channel format dispatcher |
| `shared/agent_observability/channels/intent_detector.py` | idem | Intent detector |
| `shared/application/extraction/base_orchestrator.py` | `tests/modules/brand/application/test_extraction*.py`<br>`tests/modules/offer/application/test_extraction*.py`<br>`tests/modules/landing/application/test_extraction*.py` | Wave-based extraction base |
| `shared/infrastructure/llm/router.py` | `tests/shared/infrastructure/llm/`<br>`tests/modules/copilot/`<br>`tests/modules/sales_agent/`<br>`tests/modules/brand/`<br>`tests/modules/offer/`<br>`tests/modules/landing/` | LLM router consumido por todos llaman LLMs |
| `shared/infrastructure/llm/providers/litellm.py` | idem | LiteLLM service |
| `shared/infrastructure/llm/providers/{kimi,deepseek,openai,qwen,gemini}.py` | `tests/shared/infrastructure/llm/`<br>`tests/modules/copilot/observability/test_callback_handler_usage*.py`<br>`tests/modules/sales_agent/observability/` | Provider adapters |
| `shared/domain_events/outbox/` | `tests/shared/`<br>`tests/modules/sales_agent/`<br>`tests/modules/copilot/`<br>`tests/modules/brand/` | Outbox pattern (per anti-default-flip USE_OUTBOX_PATTERN_*) |
| `shared/idempotency/` | `tests/shared/`<br>`tests/modules/scheduling/`<br>`tests/modules/connections/` | Idempotency keys |
| `shared/billing/` (BudgetGuard, RateLimiter) | `tests/modules/sales_agent/`<br>`tests/modules/campaigns/`<br>`tests/modules/copilot/` | Billing guards |
| `shared/compliance/` (ComplianceService) | `tests/modules/campaigns/`<br>`tests/modules/sales_agent/` | Compliance gates |
| `shared/events/` (DomainEvent base) | `tests/shared/`<br>`tests/modules/{m}/application/` para cada módulo en diff | Domain events cross-module |
| `shared/links/ports/` | `tests/modules/{m}/` que importa el port modificado | Cross-module ports |
| `shared/domain/locale.py::TenantLocale` | `tests/modules/{m}/` con timezone/locale | Locale VO |
| `core/config.py` defaults flip | Per `.claude/rules/anti-default-flip-audit.md` Step 1 grep tests path viejo | Default flip side-effect |
| `core/enums/` | grep usage cross-codebase + run all tests cross-module | Enums shared |
| `modules/copilot/observability/recording/` | `tests/modules/copilot/observability/`<br>plus arch fitness check shared abstraction non-mirror | Per anti-duplication.md |
| `modules/sales_agent/observability/recording/` | idem para sales_agent | idem |
| `modules/{m}/api/` route changes | `tests/modules/{m}/api/`<br>`frontend/src/features/{m}/api/` consumers if FE PR | Contract change ripple |
| `modules/{m}/domain/events.py` | grep `Event` class importers + run their tests | Cross-module event consumers |
| `modules/analytics/domain/extraction_contract.py` | Run `make extraction-contract` + arch test + `tests/modules/analytics/` | ETL contract regen |
| `modules/analytics/domain/metric_catalog.py` | `tests/modules/analytics/`<br>arch test catalog↔contract alignment | Catalog change |
| `modules/offer/domain/{archetype,value_level,format}_catalog.py` | bump `_CATALOG_VERSION` + arch tests both stacks | Per offer-catalogs.md |
| `modules/copilot/domain/module_registry.py` | arch test ModuleDescriptor entry required | Per SSoT guard |
| `frontend/src/lib/api/fetchClient.ts` | `frontend/src/features/*/api/` tests + smoke E2E (auth-tenant) | Cross-feature API client base |
| `frontend/src/lib/api/` (other shared API utils) | grep importers + their feature tests | Cross-feature API helpers |
| `frontend/src/lib/tokens/` design tokens | `frontend/src/__tests__/architecture/test-page-padding.test.ts`<br>studio section pages tests | Design tokens consumed cross-studio |
| `frontend/src/lib/format/` (formatMoney, formatTenantDate*) | grep importers + currency/locale tests cross-feature | Master-data formatters consumed cross-feature |
| `frontend/src/hooks/` (global hooks like `useTenantLocale`) | grep importers across `features/` + their tests | Global hooks consumed cross-feature |
| `frontend/src/components/shared/` | grep importers + their feature tests + visual smoke E2E | Shared components rendered cross-feature |
| `frontend/src/components/ui/` (Shadcn primitives) | full vitest run (used everywhere) + smoke E2E | UI primitives ripple universally |
| `frontend/src/features/{m}/api/` | `frontend/src/features/{m}/` full feature tests + smoke E2E for that route | Feature API contract change |
| `frontend/src/features/{m}/types/` exported | grep cross-feature importers + their tests | Type contract ripple cross-feature |
| `frontend/src/lib/zod-schemas/` shared schemas | grep importers + form tests cross-feature | Shared validation schemas |
| `frontend/src/__tests__/architecture/*.test.ts` allowlist shrink | full FE arch fitness suite | Ratchet enforcement |
| `frontend/e2e/auth.fixture.ts` o `e2e/fixtures/*` | full smoke project + relevant POMs | E2E fixture change ripples to all auth-protected specs |
| `frontend/playwright.config.ts` | full smoke project | Config change affects every spec |

## Workflow auditor (Step `downstream_regression_scope`)

```
# Pseudocode auditor agent inserts post consume_gate_output, pre audit_categories

1. List files modified in diff (git diff HEAD~N..HEAD --name-only)
2. For each path → lookup tabla SSoT
3. Aggregate downstream_test_targets = unión sets per matched path
4. Verify gate-output.json scope cubre downstream_test_targets:
   - gate-runner.command was test-backend (full suite)? → cubierto
   - gate-runner.command was scoped (e.g., tests/modules/X/)? → puede no cubrir
5. Si NO cubre → SPAWN gate-runner adicional con scope=downstream_test_targets:

   **Backend scope:**
   ```
   Agent({
     description: "Run downstream regression for T-{n}",
     subagent_type: "gate-runner",
     model: "haiku",
     prompt: "<pr_folder>: <STORY_DIR>;
              <command>: cd /home/chris/AISALESHT/backend && .venv/bin/pytest <space-separated downstream_test_targets> -v --tb=short;
              <iter>: <N>-downstream"
   })
   ```

   **Frontend scope (R3 parity, 2026-05-05):**
   ```
   Agent({
     description: "Run downstream FE regression for T-{n}",
     subagent_type: "gate-runner",
     model: "haiku",
     prompt: "<pr_folder>: <STORY_DIR>;
              <command>: cd /home/chris/AISALESHT/frontend && npx vitest run <space-separated downstream feature/component paths> --reporter=default;
              <iter>: <N>-downstream-fe"
   })
   ```

   **E2E smoke scope (when downstream targets include `frontend/e2e/`):**
   ```
   Agent({
     description: "Run downstream E2E smoke for T-{n}",
     subagent_type: "gate-runner",
     model: "haiku",
     prompt: "<pr_folder>: <STORY_DIR>;
              <command>: cd /home/chris/AISALESHT/frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke <space-separated specs>;
              <iter>: <N>-downstream-e2e"
   })
   ```
6. Read new gate-output.json (gate-runner renames previous → gate-output.iter-N.json automatic).
7. Si downstream tests FAIL → escalate REVIEW.md FAIL — Cat 10 (Tests/TDD) BE/FE,
   o Cat 1 (FSD-Lite cross-feature import) si FE — con cita exacta tests fallaron
   y mapping a surface modificada.
8. Si downstream tests PASS → continuar audit_categories.
```

## Anti-patterns prohibidos

- ❌ Auditor APPROVED PR `shared/agent_observability/` modify sin run downstream tests `modules/copilot/observability/` + `modules/sales_agent/observability/`
- ❌ Auditor APPROVED PR `shared/infrastructure/llm/` modify sin run consumers (todos modules llaman LLM)
- ❌ Auditor APPROVED PR enum shared modify sin grep importers + run sus tests
- ❌ Auditor APPROVED PR `core/config.py` flag flip sin Step 1 grep + run AMBOS valores per anti-default-flip-audit.md
- ❌ Skip downstream lookup porque "module change parece self-contained" — si toca shared anything, downstream puede ser invisible

## Enforcement layers

| Layer | Mecanismo | Owner |
|---|---|---|
| 1 Auditor agent | Step `downstream_regression_scope` MANDATORY post `consume_gate_output` | `auditor-{backend,agentic}` |
| 2 /auditor SKILL | Step 2 prompt sub-auditor referencia este file | `/auditor` skill |
| 3 Reviews | T-{n}-review.md sección "Downstream regression" obligatoria con tests targets + gate-output result | sub-auditor |
| 4 Self-audit | Si CASO ORIGEN D4 reproduce — auditor verdict FAIL automático | sub-auditor |

## Penalizaciones

- Auditor missing downstream regression cuando surface lo requiere → process-learnings.md case study + re-audit
- Cambio shared/ sin update SSoT tabla este file → process-learnings.md case study (catch en commit hook futuro)

## Mantenimiento tabla

Cuando agregás:
- Nueva surface en `shared/X/` cross-consumer → MUST add row con downstream_test_targets
- Nuevo módulo importer de surface listada → MUST add path a downstream_test_targets row existente
- Cambia downstream test path (rename) → update row

Tabla SSoT vive aquí. NO duplicar en agent files.

## Ejemplos

### Ejemplo CORRECTO (auditor caso D4 reproducido):

```
git diff HEAD~1..HEAD --name-only
→ backend/src/shared/agent_observability/cost/cost_recorder.py

Lookup tabla:
  shared/agent_observability/cost/cost_recorder.py →
    tests/modules/copilot/observability/test_callback_handler_usage_fallbacks.py
    tests/modules/sales_agent/observability/test_callback_handler.py::TestOnChatModelEnd::test_persists_row_with_sales_columns

Spawn gate-runner downstream:
  command: cd backend && .venv/bin/pytest \
    tests/modules/copilot/observability/test_callback_handler_usage_fallbacks.py \
    tests/modules/sales_agent/observability/test_callback_handler.py \
    -v --tb=short

Resultado: 2 fail con `cost_usd > 0` AssertionError → bug `kimi/kimi-k2.6 → BadRequestError`.

Verdict: REVIEW.md FAIL Cat 10 (Tests/TDD) — "T-1 cost_recorder canonicalization
introduces regression: litellm.get_llm_provider() doesn't recognize 'kimi' as
provider (custom yaml alias). Add fallback in cost_recorder.py: if get_llm_provider()
raises, set provider = model.split('/')[0].lower() if '/' in model else 'unknown'.
Re-run downstream tests."
```

### Ejemplo INCORRECTO (lo que pasó D4):

```
git diff HEAD~1..HEAD --name-only
→ backend/src/shared/agent_observability/cost/cost_recorder.py

Auditor scope: tests/shared/agent_observability/ → 100% pass
Auditor APPROVED.

Bug downstream silencioso. Llegó a S1. T-1-bis nuevo micro-ticket creado.
80min hunt + 500k tokens.
```

## Referencia cruzada

- `.claude/rules/anti-duplication.md` — inventario shared abstractions (este file lista cuáles tienen consumers que requieren downstream regression)
- `.claude/rules/anti-default-flip-audit.md` — Step 1 grep tests path viejo (ortogonal pero análogo: detect ripple)
- `.claude/agents/auditor-backend.md` — Step `downstream_regression_scope` (integrado 2026-05-05)
- `.claude/agents/auditor-agentic.md` — Step idem (integrado 2026-05-05)
- `.claude/agents/auditor-frontend.md` — Step idem FE-side (integrado 2026-05-05, B1 parity)
- `docs/process/process-improvement-handoff-2026-05-05.md` — R3 (D4 origen)
- `docs/process/learnings.md` 2026-05-05 entry — closure ciclo R1-R9 + B1 FE parity
</content>
</invoke>