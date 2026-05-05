---
level: story
id: sales-agent-eval-runner-foundation
phase: DEV_T2_DONE
status: in-progress
last_artifact: 05-impl/T-2-result.md
last_modified: 2026-05-04T23:55:00Z
next_action: "/auditor revisa T-2 (pytest plumbing + 4 fixtures + 14 meta-tests TDD)"
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: false
blocked_reason: null
audit_iterations: 1
ratified_by_chris: true
po_version: 2
---

## Bitácora

- 2026-05-04 20:00 — `/pm` creó folder + `00-story.md`. Phase=PM_DRAFT, status=pending.
- 2026-05-04 20:30 — `/po` produjo `01-spec.md` (4 scenarios Gherkin AI-resistant). Phase=PO_SPEC.
- 2026-05-04 20:30 — `/po` creó `docs/product/stories/sales-agent/sales-agent-eval-runner-foundation.yaml` + actualizó INDEX + capability YAML.
- 2026-05-04 20:30 — Chris delegó 13 open questions; /po ratificó 13+2 decisiones (B1-B7 binding). Phase=PO_RATIFIED. Spec lockeada.
- 2026-05-05 03:42 — `/architect` (acting BE+Agentic — no recursion) produjo `03-arch-be.md` (441 líneas), `03-arch-agentic.md` (385 líneas), `04-tickets.yaml` (6 tickets, ~14h estimadas). Phase=ARCHITECT_COMPLETE. Owner pool todos tickets = `claude-opus` (AGENTIC story → Opus mandatory).
- 2026-05-04 22:55 — `dev-team` (Opus 4.7) tomó T-1, scaffold dirs `backend/tests/agentic_evals/sales_agent/{runner,fixtures,goldens,_artifacts}` + 4 `__init__.py` vacíos + `_artifacts/.gitignore` + `goldens/.gitkeep` + README stub (Spanish neutro). 7 archivos nuevos, 97 LOC total (95 en README). Quality gates: ruff check ✅, ruff format ✅, pytest collect-only "no tests collected" ✅. Acceptance A1/A2/A3 PASS. Anti-duplication grep clean (greenfield — `tests/quality/sales_agent_goldens/` co-existe, distinto propósito documentado en README). Phase=DEV_T1_DONE. Commit local pendiente push (controller coordina con Story A T-1).
- 2026-05-04 23:10 — `/auditor` (Opus 4.7) revisó T-1, verdict APPROVED iter 1/2. 10 checks PASS (3 NA). Acceptance A1/A2/A3 re-verificados, quality gates re-corridos clean, scope discipline impecable (zero contaminación cross-story/cross-módulo), Spanish neutro confirmado, PR-folder hygiene completa. Notes: builder eligió `*\n!.gitignore` (más robusto que `*` literal del ticket YAML — aceptado); README 113 líneas vs 95 estimadas (más completo). Phase=AUDIT_T1_APPROVED. Ticket state → audit-passed.
- 2026-05-04 23:55 — `dev-team` (Opus 4.7) tomó T-2, scaffold pytest plumbing + 4 fixtures + 14 meta-tests TDD. Archivos: `tests/agentic_evals/conftest.py` (root: --run-evals + markers + auto-skip), `tests/agentic_evals/sales_agent/conftest.py` (re-exports + auto-mark eval scoped a este dir), `fixtures/{run_id,tenant,entrypoint}.py` + `__init__.py` exports, `test_eval_runner_fixtures.py` (11 no_eval + 3 eval). Pyproject: 2 markers añadidos. Requirements-dev.txt: `langdetect>=1.0.9` (no-prod). Quality gates: ruff check ✅, ruff format ✅, default suite 11/3 (PASS/SKIP), --run-evals 10/4 (DB-skip Spanish reasons), arch fitness 823 PASS. Anti-duplication clean (greenfield, todo shared reused verbatim). 4 acceptance criteria (A1-A4) PASS. ~720 LOC añadidas, 9 archivos. Pre-existing failures (3) en copilot/sales_agent observability NO mías (origen Story A T-1). Phase=DEV_T2_DONE. Commit local pendiente push (controller coordina con Story A T-2 paralelo).

## Notas

- 2026-05-05: Architect tomó decisiones técnicas:
  - **Entry point**: `agent_app.ainvoke` en `sales_agent/application/orchestrator/graph.py:52` — limpio, no necesita extracción. Reusa `create_initial_state` + `TenantKnowledgeBuilder` (compose initial_state).
  - **Trajectory spy**: composition over subclass. `BaseCallbackHandler` (LangChain) NO subclase de `BaseAgentCallbackHandler`. Read-only observer en `RunnableConfig.callbacks` list. Anti-duplication §0 satisfied — zero new mirror.
  - **B4 tool registry mapping resolved**: `required_tools: []` (intent classifier es service `SemanticRouter`, no tool). `forbidden_tools` = 13 names canónicos cubriendo payment_* + scheduling_* + closer_finalize_* del `STAGE_TOOL_SCOPE` post-redesign.
  - **langdetect 1.0.9 MIT** — added a `[project.optional-dependencies].evals` group. Lazy import en assertions.py para no impactar default suite.
  - **Coverage 43% gate**: eval suite outside `[tool.coverage.run].source` — sin acción adicional, intacto.
  - **Tenant Visionarias seed**: option (a) precondition skip vs option (b) seed-if-missing → spec B2 ratificó "fail explicit, no silent shift" → (a). T6 README documenta `make seed-visionarias` como precondition.
  - **`--run-evals` flag** (vs env var `EVAL_SUITE=1`): pytest-native, gated via `pytest_collection_modifyitems`. Suite default → SKIP, sin gastar budget.
- All 6 tickets owner = Opus 4.7 (AGENTIC story per CLAUDE.md hard rule "AGENTIC tickets → Opus 4.7 SIEMPRE. qwen ban absoluto").
- 7 open questions del spec previo (Chris las delegó al /po): TODAS resueltas en arch-be + arch-agentic.
- Critical path: T-1 → T-2 → {T-3, T-4} → T-5 → T-6. Ningún ticket paralelo (T-3 y T-4 dependen de T-2; T-3 prepara TrajectorySpy que T-4 consume; secuencial).
- Anti-duplication audit cross-codebase ejecutado, ZERO new layers. Reutiliza:
  `BaseAgentCallbackHandler` shared, `SalesAgentCallbackHandler` subclass, `SalesAgentObservabilityContext`, `build_sales_agent_observability_context` factory, `FXResolver.default()`, `PricingResolver`, `sanitize_payload`, `TenantKnowledgeBuilder`, `agent_app` canonical entry.
- pm-nico/current-state updates: NONE (eval runner es dev-internal infrastructure, no user-facing capability).
- Quality gates each ticket: native pytest + ruff + arch fitness + TDD evidence + (T-5 only) cost <$0.01/run real LLM.

## Próximo paso

`/auditor` revisa T-2. Verdict esperado APPROVED iter 1. Tras audit-passed → controller pushea commit T-2 (coordinado con Story A T-2 paralelo); luego `/dev-team` toma T-3 (TrajectorySpy LangChain callback + artifacts writer con sanitize_payload). T-3 owner = Opus 4.7 (AGENTIC). Anti-duplication §0 enforce: spy = composition over subclass del `BaseAgentCallbackHandler`.
