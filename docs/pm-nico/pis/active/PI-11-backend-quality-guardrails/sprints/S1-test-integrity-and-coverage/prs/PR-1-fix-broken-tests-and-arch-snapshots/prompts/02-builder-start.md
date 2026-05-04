# Prompt — Builder kickoff (Business surface)

> Builder: `nicolify-backend` (Sonnet)
> Surface: `brand`, `shared`, `crm`, `campaigns`, `arch fitness tests`

## Spawn pattern

```
Agent({
  description: "Build PR-1 business surface",
  subagent_type: "nicolify-backend",
  model: "sonnet",
  prompt: <bloque abajo>
})
```

## Prompt body

```
[BLOQUE FIJO — cacheable]

Sos nicolify-backend (Sonnet). Trabajo: fixear tests rotos de surface business en PR-1.

Step 0 OBLIGATORIO:
  date -u +%Y-%m-%d

Restricciones DURAS:
- Tocás SOLO archivos de brand, shared, campaigns, crm (solo tests/ y src/shared/domain_events/ si bug real).
- NO tocás modules/copilot/ ni modules/sales_agent/.
- NO tocás archivos de otros PRs activos.
- PROHIBIDO: git pull, git fetch && merge, git push --force, git revert, git reset --hard, git add .|-A|-u, git commit --no-verify.
- Push falla non-fast-forward → STOP, reportar.

Skills obligatorios:
- backend-expert (cargar ANTES de tocar código)

Workflow Phase 1 — IMPLEMENT:
1. Fix tests business surface (lista abajo).
2. Quality gates locales NATIVE:
   cd backend && .venv/bin/ruff check src/ tests/ --no-cache
   cd backend && .venv/bin/pytest tests/modules/brand/ tests/shared/domain_events/ tests/architecture/test_ddd_boundaries.py tests/architecture/test_folder_naming.py -v --timeout=60
3. Stage + conventional commit + push origin development.
4. IMPL-LOG.md completo.

Workflow Phase 2 — AUTO-AUDIT:
5. Spawn nicolify-gate-runner Haiku:
   Agent({ description: "Run gates iter-1", subagent_type: "nicolify-gate-runner", model: "haiku",
     prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots; <command>: test-backend; <iter>: 1" })
6. Esperá gate-output.json. Si any_fail en gates 3-7,11-13 → fix, re-commit, re-spawn.
7. Spawn nicolify-backend-auditor Opus:
   Agent({ description: "Audit PR-1 business", subagent_type: "nicolify-backend-auditor", model: "opus",
     prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots; <surface>: business; <iter>: 1" })
8. Si verdict ≠ PASS → fix loop max 3 iter.

Outputs:
- Code + tests committed + pushed
- IMPL-LOG.md
- gate-output.json final
- REVIEW.md (output auditor)

[BLOQUE VARIABLE]

Tests a fixear (business surface):
1. tests/modules/brand/test_outbox_adapter_integration.py::TestBrandOutboxAdapterFlagOff::test_flag_off_is_default_for_brand_module
   - Assert result is False; código retorna True. Verificar si es bug de código o test desactualizado.
2. tests/modules/brand/test_outbox_adapter_integration.py::TestBrandOutboxAdapterFlagOff::test_monkeypatch_env_flag_off
   - monkeypatch.setenv("USE_OUTBOX_PATTERN_BRAND", "false") no surte efecto. Investigar _is_outbox_enabled.
3. tests/modules/brand/test_brand_section_updated_event.py::test_save_settings_publishes_brand_section_updated
   - sqlite3.OperationalError: no such table: domain_event_outbox. Agregar fixture/setup de tabla.
4. tests/modules/brand/test_brand_section_updated_event.py::test_event_dispatched_after_commit_only
   - Mismo error de tabla faltante.
5. tests/architecture/test_ddd_boundaries.py::test_no_new_cross_module_imports
   - Nuevos imports cruzados detectados:
     * campaigns -> sales_agent | campaigns/infrastructure/external/sales_agent_adapter.py
     * crm -> campaigns | crm/api/contacts.py (x2)
     * crm -> campaigns | crm/application/services/contact_query_service.py
   - Decidir: agregar a KNOWN_CROSS_MODULE_IMPORTS si intencionales, o refactor.
6. tests/architecture/test_folder_naming.py::test_all_python_files_snake_case
   - Violation: copilot/api/_dependencies.py no pasa SNAKE_CASE_RE.
   - Fix: agregar a KNOWN_PRIVATE_FILE_EXCEPTIONS en el test.
7. tests/shared/domain_events/test_event_bus_adapter.py::TestEventBusAdapterFlagOn::test_is_outbox_enabled_returns_false_by_default
   - Assert result is False; retorna True. Mismo problema que brand outbox.

Código posible a tocar:
- src/shared/domain_events/outbox/application/event_bus_adapter.py (_is_outbox_enabled)
- src/core/config.py (default flags outbox)
- tests/conftest.py (fixture tabla domain_event_outbox si no existe)

PR folder: docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots
Surface: business
Iter actual: 1
```
