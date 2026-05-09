# 05-guidelines.md — Story sales-agent-goldens-3-tenants-dataset

> /architect orchestrator delivered (2026-05-08T08:00Z). Patterns required + forbidden + files in/out scope. Cero ambigüedad. Builders consultan ESTO antes de cada Edit.

## Patterns required (cero deuda — escala 1000+ tenants × N updates)

### Backend (Python 3.12 + Pydantic v2 + asyncio + PyYAML + structlog)

- **Pydantic v2 ConfigDict** — `model_config = ConfigDict(extra="forbid", frozen=True)` para `GoldenScenarioModel` + `GoldenTurnModel` + `GoldenMetadataModel`. NUNCA inner `class Config`.
- **Pydantic v2 `Literal[...]`** strict — `GoldenTenantSlug`, `GoldenPersonaKind`, `GoldenTerminationReason`. NUNCA `str` open + runtime validation.
- **`utc_now()` from `shared/domain/datetime_utils.py`** — NUNCA `datetime.utcnow()` (deprecated + naive). Tooling scripts importan via `from shared.domain.datetime_utils import utc_now` con sys.path adjustment OR usan `datetime.now(tz=UTC)` explícito en standalone scripts (`from datetime import UTC, datetime`).
- **`structlog`** logging — NUNCA `print` / `logging.{info,warn,error}`. Structured fields obligatorios (`run_id`, `tenant_slug`, `persona_kind`, `simulation_id`).
- **`yaml.safe_load` / `yaml.safe_dump`** — NUNCA `yaml.load` / `yaml.dump` (RCE risk). `safe_dump` con `sort_keys=True, default_flow_style=False, allow_unicode=True` para output deterministic.
- **`asyncio.gather + Semaphore(10)`** pattern — reusa Story B precedent. NEW per-script semaphore OK (no global cross-suite quota — script-local parallelism budget).
- **`Path` over `os.path`** — NUNCA `os.path.join` / `os.path.exists`. `pathlib.Path` only.
- **CLI argparse** — `argparse.ArgumentParser` + explicit `type=` per arg (Decimal, int, Path, choices=). NO bare `sys.argv` parsing.
- **Exit codes explicit** — 0=success, 1=PII/coverage failure, 2=parse/argument error. Documentado per script docstring.
- **`Decimal` para cost_usd** — NUNCA `float`. `from decimal import Decimal` + `Decimal(str(value))` para roundtrip-safe.
- **Anti-duplication §0** — antes Write nuevo file: grep cross-codebase + `cat .claude/rules/anti-duplication.md` inventario shared. Match → STOP escalate. Subclase desde shared, NO mirror.
- **DRY threshold 2 consumers** — al detectar duplicación cross-script (`scan_seed_pii.py` + `scan_goldens_pii.py` ambos usan PATTERNS regex), extract a módulo shared (`_pii_patterns.py`). Backward-compat: original consumer re-imports.
- **`GOLDEN_SCHEMA_MIGRATIONS` parallel registry** — NO mirror Story B `simulator/_internal/schema_migrations.py`. Distinct namespace + lifecycle (goldens YAMLs are data, simulator state is code).

### Generation script specifics (`generate_golden_candidates.py`)

- **Cost budget pre-flight strict abort** — estimated > cap → exit 2 + structlog error + sys.stderr message. NO best-effort partial run.
- **Per-cell error isolation** (`tessl__graceful-degradation` Rule 5) — one cell exception → log + skip + continue. Suite continues. Final exit 0 if ≥1 success + ≥0 failures (non-zero only if ALL fail).
- **Markdown preview format** — IDE-renderable table, sorted (tenant, persona_kind, run_n) lexicographic, escape `|` in preview text, truncate transcript previews to 120 chars in cell.
- **`run_id` auto-generated** — `--run-id` flag default `str(uuid.uuid4())`. Output dir derived from this.
- **Artifact path stable** — `_artifacts/goldens_generation/{run_id}/sim_{simulation_id}.json`. Both run_id + simulation_id deterministic via UUID5 (Story B D11 pattern).

### Promotion CLI specifics (`promote_golden.py`)

- **Idempotent overwrite** — same `--golden-id` + same `--simulation-id` → same YAML output byte-equal (modulo `curated_at` timestamp; if Chris re-promotes, curated_at refreshes — acceptable).
- **Auto-derive `expected_*` fields** (D14):
  - `expected_termination_reason` ← `result.termination_reason.value`
  - `expected_tools_invoked` ← union of `transcript[].tool_calls` per agent turn
  - `forbidden_tools` ← derived from `persona_kind` (D17): `unqualified` → `["enroll_immediate", "send_payment_link", "confirm_appointment"]`; others `[]`
  - `expected_voice_attributes` ← `_extract_voice_attributes(tenant_slug)` reads `personality_profile.dimensions.keys()` from Story A loader read-only
- **`notes: str = ""`** Chris freeform override — `--notes` CLI flag.
- **Path target deterministic** — `goldens/{tenant_slug}/{persona_kind}/{golden_id}.yaml`.
- **Validation failure exit 2** — Pydantic ValidationError → CLI prints error + exit 2. NO partial write.

### PII scanner specifics (`scan_goldens_pii.py`)

- **NO whitelist** (D10 strict block) — vs Story A's `.eval-whitelist`. Scanner does NOT read whitelist file.
- **Recursive YAML walk** — `Path.rglob('*.yaml')` from `_DEFAULT_GOLDENS_ROOT`.
- **Context guards** — DNI_PE skips matches preceded by `=`/`:`/`#`/`/`/`id=`/`version=` (Story A pattern reused).
- **Per-line error reporting** — yaml_path + pattern_name + matched substring printed to stderr.
- **Exit codes** — 0=clean, 1=PII detected, 2=YAML parse error.
- **Adversarial fixtures location** — `tests/_pii_fixtures/` (NOT `goldens/` — would trigger recursive scan during arch test).

### Pre-commit hook Section 9 specifics

- **Mirror Section 8 structure** — same shell pattern, same VENV_PY guard, same color codes, same cat <<EOF error block.
- **Triggers ONLY on staged YAMLs under `goldens/`** — `git diff --cached --name-only --diff-filter=ACM | grep ...`.
- **Runs scanner against full goldens dir** — not just staged (catches drift).
- **Section number 9** — appended after current Section 8 (line ~563 `exit 0`).
- **Exit code propagation** — scanner exit 1 → hook exit 1 + actionable message + NO `--no-verify` instruction.

### Schema versioning forward-compat

- **`schema_version: Literal[1] = 1` cement** in `GoldenScenarioModel`. v1 cement.
- **First future bump** (v1→v2) registers identity migrator in `GOLDEN_SCHEMA_MIGRATIONS` SAME COMMIT. Bump `CURRENT_GOLDEN_SCHEMA_VERSIONS["GoldenScenarioModel"]` to 2.
- **20-30 committed goldens carry `schema_version: 1`** — never edit committed YAMLs except Chris-triggered migration via `promote_golden --migrate-goldens` (future flag).

### Tenant isolation

- **One tenant per golden** — `tenant_slug` field cement. `test_goldens_schema.py` enforces (heuristic check + assertion).
- **Generation script `run_simulation(tenant_archetype_slug=...)`** — Story B carries tenant_id internally.
- **`promote_golden`** reads tenant_slug from artifact JSON — never mutates DB.

### Voice + Spanish

- **Goldens `transcript[].content` voseo permitted** ONLY when `dialect_code: es-AR`. Pre-commit voseo hook (Section 1) excludes `goldens/` path explicitly OR uses magic comment per file (TBD builder-backend final decision — recommend exclusion path-based to avoid magic comment proliferation).
- **`expected_voice_attributes` extracted read-only** — never mutate `personality_profiles.system_instruction` SSoT.
- **Resto código Spanish neutro** — script structlog events + CLI messages + comments + README + arch test messages en español neutro LatAm. Aplica `.claude/rules/spanish-text.md` glosario.

## Patterns forbidden (cero deuda)

- ❌ `datetime.utcnow()` — use `datetime.now(tz=UTC)` (standalone scripts) or `utc_now()` (importable contexts)
- ❌ `DateTime()` sin `timezone=True` (N/A here — no DB models)
- ❌ Hardcoded `'USD'` — read `result.cost_summary.total_cost_usd` Decimal directly
- ❌ Hardcoded model names — N/A (no LLM dispatch in tooling — consumed via Story B)
- ❌ Cross-module imports excepto whitelisted: `tests.agentic_evals.sales_agent.simulator` (Story B + C public/internal-pin) + `tests.fixtures.eval.tenants` (Story A) + `tests.agentic_evals.sales_agent.goldens._schema` (intra-story)
- ❌ `session.query()` (SA 1.x — N/A here, no SA models)
- ❌ `op.create_table()` / `op.add_column()` no idempotente — N/A (no migrations this story)
- ❌ Mirror Story B `simulator/_internal/schema_migrations.py` — STOP escalate; use parallel `goldens/_schema_migrations.py` instead
- ❌ Mirror PII PATTERNS dict copy-paste in two scripts — STOP, lift to `_pii_patterns.py`
- ❌ Modify `simulator/__init__.py` 7-name surface (Story B H9 cement)
- ❌ Modify Story C `_internal/personas_loader.py` (consume only)
- ❌ Modify Story C 15 personas YAML files (consume only — referential integrity check)
- ❌ Modify Story A 5 tenant seeds (consume only)
- ❌ Modify `personality_profiles.system_instruction` (read-only auto-extract for `expected_voice_attributes`)
- ❌ Modify `eval_simulator_*` DB schema (R5 cement Story B)
- ❌ Add new file in `modules/sales_agent/{domain,application,api,observability}/` — Story D NEVER touches sales_agent runtime (R5 schema-mirror exception NOT applicable here — Story D is tooling, not schema mirror)
- ❌ Touch §3 protected surfaces sales-agent (`closer_studio.py`, `SmartBufferService`, `OutputManager.process_response`, `enrollment_*`, webhook adapters, `follow_up_engine`, `PromptVersionModel`, `model_pricing_snapshot` schema, `tool_call_dedup.py`) — STOP escalate
- ❌ Touch Story B simulator non-public symbols beyond `_internal/personas_loader` documented pin (Story C D-AG-2). E.g., `_internal/runner.py`, `_internal/customer_node.py`, `_internal/graph.py` — STOP escalate
- ❌ Use `yaml.load` / `yaml.dump` (RCE risk) — `safe_load` / `safe_dump` only
- ❌ Use `eval()` / `exec()` ANYWHERE in scripts
- ❌ Use `subprocess` to invoke Python — `import` and call directly (faster + clearer + traceable)
- ❌ Use `print()` for logs — `structlog` only (CLI user output to `sys.stdout` OK via `sys.stdout.write`)
- ❌ Use `os.path.*` — `pathlib.Path` only
- ❌ Bare `except:` — always specific exception class + structlog warning
- ❌ Use `--no-verify` git flag — `.claude/rules/git-safety.md` prohibits
- ❌ `git add .` / `git add -A` — stage por nombre exacto
- ❌ `git pull` / `git fetch && merge` — parallel-safety multi-instancia
- ❌ Crear feature branches/worktrees — `development` única
- ❌ Add whitelist mechanism for goldens scanner (D10 strict block)
- ❌ Modify `scan_seed_pii.py` behavior — only refactor: re-import `PATTERNS` from `_pii_patterns.py`. Verify Story A regression test `test_seed_pii_scanner.py` PASS post-refactor

## Files in scope (builders edit ONLY these)

### Schema + parallel migrations registry
- `backend/tests/agentic_evals/sales_agent/goldens/_schema.py` (NEW — `GoldenScenarioModel` + `GoldenTurnModel` + `GoldenMetadataModel`)
- `backend/tests/agentic_evals/sales_agent/goldens/_schema_migrations.py` (NEW — `GOLDEN_SCHEMA_MIGRATIONS` registry + `apply_golden_migrations` + `register_golden_migration`)
- `backend/tests/agentic_evals/sales_agent/goldens/__init__.py` (NEW — empty or thin re-exports)

### Tooling scripts
- `backend/scripts/_pii_patterns.py` (NEW — LIFT from `scan_seed_pii.py::PATTERNS` + `DNI_PE_GUARD_PREFIXES`)
- `backend/scripts/scan_seed_pii.py` (1-2 line REFACTOR — `from _pii_patterns import PATTERNS, DNI_PE_GUARD_PREFIXES`. Backward-compat preserved.)
- `backend/scripts/scan_goldens_pii.py` (NEW — strict-block scanner, no whitelist)
- `backend/scripts/generate_golden_candidates.py` (NEW — matrix orchestrator + Markdown preview)
- `backend/scripts/promote_golden.py` (NEW — promotion CLI, deterministic YAML write)

### Tests (BE non-prod-code)
- `backend/tests/agentic_evals/sales_agent/test_goldens_schema.py` (NEW — schema deserialization + referential integrity + `test_no_pii_in_committed_goldens`)
- `backend/tests/agentic_evals/sales_agent/test_goldens_coverage.py` (NEW — `test_all_cells_covered` + `test_reports_all_cells_with_gaps`)
- `backend/tests/agentic_evals/sales_agent/test_goldens_pii_scanner.py` (NEW — fixtures 4 categories × 3 dialects)
- `backend/tests/_pii_fixtures/` (NEW dir — adversarial fixtures NOT in goldens/, used by test_goldens_pii_scanner.py)
- `backend/tests/scripts/test_generate_golden_candidates.py` (NEW — argparse + matrix shape + cost guard + filter + preview deterministic)
- `backend/tests/scripts/test_promote_golden.py` (NEW — auto-derive + idempotent overwrite + voice attr extraction)
- `backend/tests/scripts/test_pre_commit_hook.py` (EXTEND existing — add `test_blocks_pii_in_goldens` + `test_blocks_invalid_golden_yaml` test cases)

### Architecture fitness gates (BE non-prod-code, allowlists empty shrink-only)
- `backend/tests/architecture/test_goldens_schema_completeness.py` (NEW)
- `backend/tests/architecture/test_goldens_no_mirror_simulator_schema.py` (NEW)
- `backend/tests/architecture/test_pii_patterns_single_source.py` (NEW)
- `backend/tests/architecture/test_goldens_no_committed_pii.py` (NEW)
- `backend/tests/architecture/test_goldens_cost_bucket_invariant.py` (NEW — env-gated `EVAL_GOLDENS_COST_BUCKET_VERIFY=1`)

### Pre-commit hook
- `scripts/git-hooks/pre-commit` (EXTEND — append Section 9 after current Section 8 / line 563 `exit 0`. Update voseo Section 1 to exclude `goldens/` path OR use magic comment per dialect=es-AR golden — recommend path exclusion)

### README
- `backend/tests/agentic_evals/sales_agent/goldens/README.md` (NEW — pipeline + how-to + refresh policy + schema reference + cost budget + coverage gate + PII defense)

### SSoT updates (rules + capability + module narrative — POST-MERGE by /pm, T-5 ticket)
- `.claude/rules/auditor-downstream-regression.md` (1-line entries — see arch §10):
  - `backend/tests/agentic_evals/sales_agent/goldens/**` → downstream tests
  - `backend/scripts/_pii_patterns.py` → downstream tests
  - `backend/scripts/generate_golden_candidates.py` → downstream tests
  - `backend/scripts/promote_golden.py` → downstream tests
- `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` (10+ new fields appended in `eval:` block)
- `docs/product/modules/sales-agent.md` (1-2 sentence narrative update — synthetic-first goldens)

### Goldens dataset (CHRIS-CURATED OUT-OF-TICKET — NOT delivered by builder)
- `backend/tests/agentic_evals/sales_agent/goldens/{tenant_slug}/{persona_kind}/{golden_id}.yaml` (20-30 files — Chris produces post-build via `generate_golden_candidates.py` + `promote_golden.py` workflow)

> **CRITICAL**: builder delivers TOOLING + TESTS + DOCS. Chris produces 20-30 actual golden YAML files post-build via the tooling. The build is GREEN when:
> 1. Tooling tests PASS (mocked `run_simulation`)
> 2. Schema tests PASS (synthetic test fixtures, NOT real curated goldens)
> 3. Coverage tests PASS (synthetic test fixtures covering 15 cells)
> 4. Arch fitness gates PASS
> 5. Pre-commit hook integration verified
> 6. README + capability extension documented
>
> Real 20-30 goldens curation is a **post-build manual step** Chris executes. Spec target 20-30 is achieved during curation phase, NOT during builder phase.

## Files NEVER touched (escalate to Chris if needed)

- `backend/src/modules/sales_agent/{domain,application,api,observability}/` — Story D NEVER touches sales_agent runtime
- `backend/src/modules/copilot/**` — agentic builder territory only
- `backend/src/shared/**` — solo lectura (Story D consumes Story B's wiring via `run_simulation` public API; never touches `shared/agent_observability/`, `shared/links/`, etc.)
- `backend/src/core/config.py` — R31 anti-default-flip-audit aplica
- `backend/alembic/versions/*.py` — Story D no migrations
- `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` — Story B H9 7-name surface frozen
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py` — Story C owns
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/runner.py` / `customer_node.py` / `graph.py` / `agent_bridge.py` — Story B owns
- `backend/tests/agentic_evals/sales_agent/simulator/actor_profile.py` / `state.py` / `result.py` / `termination.py` — Story B owns (Story C bumps `actor_profile.py` schema_version + Literal — Story D no toca)
- `docs/specs/personas/archetype-aware/*.yaml` — Story C 15 personas (consume only)
- `docs/specs/personas/_legacy/*.yaml` — Story C legacy preserved
- `backend/tests/fixtures/eval/tenants/` — Story A 5 tenant seeds (consume only)
- `backend/tests/fixtures/eval/tenants/dialect_catalog.yaml` — Story A (consume only)
- `client_simulator/src/simulator/*.py` — Story B D6 preservation gate
- `frontend/**` — N/A esta story FE no toca
- `.claude/skills/`, `.claude/agents/` — skill/agent edits manual via /pm
- `.claude/rules/` (excepto auditor-downstream-regression entry add — T-5 ticket /pm) — rule edits manual via /pm
- §3 sales-agent protected surfaces — STOP, ASK CHRIS

## Reference docs (load before coding — orden estricto)

### Universal (load primero, todos tickets)
1. `01-spec.md` (re-read 4 scenarios + decisions D1-D17 + non-functional invariants mid-build)
2. `03-arch.md` (consolidated cross-cutting decisions + reference impl)
3. `04-validators.yaml` (test commands ejecutables — non-functional + functional + agentic_eval + scenario_coverage)
4. `00-story.md` (JTBD + outcome esperado + asunciones)

### Story dependencies (consume only)
- `docs/archive/2026/stories/eval-foundation-tenant-seed-data/` (Story A done)
  - `backend/tests/fixtures/eval/tenants/loader.py::load_eval_tenant`
  - `backend/tests/fixtures/eval/tenants/dialect_catalog.yaml`
  - `backend/scripts/scan_seed_pii.py` (precedent + LIFT target)
- `docs/archive/2026/stories/eval-foundation-simulator-homologation/` (Story B done)
  - `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` (7 public names)
  - `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/golden_v1_simulation_result.yaml` (frozen reference)
- `docs/product/stories/sales-agent-personas-instrumented-runtime/` (Story C refined → ready → pending build)
  - `03-arch.md§4.1` reference impl `personas_loader.py`
  - `06-tickets.yaml` T-3 deliverable signature

### Skills (per surface)
- `backend-expert` — DDD patterns, arch fitness, currency, master-data, schema-mirror exception R5 alcance estricto
- `sales-agent-expert` — §3 protected surfaces, anti-patterns, decisiones cross-fase, brand voice cement, surfaces compartidas con copilot
- `tessl__pytest-api-testing` — pytest-asyncio patterns, fixtures, parametrize, mocks
- `tessl__fastapi` — Pydantic v2 patterns (ConfigDict, Literal, Field, model_dump)
- `tessl__graceful-degradation` — Rule 5 per-dependency error isolation in generation script
- `claude-api` — N/A this story (no LLM dispatch)

### Rules (cement before each Edit)
- `.claude/rules/anti-duplication.md` — inventario shared SSoT (CONSULTAR antes Write nuevo file). DRY threshold 2 consumers → lift to shared module
- `.claude/rules/architectural-fitness.md` — 5 NEW gates con allowlists vacías shrink-only
- `.claude/rules/backend-ddd.md` — Story D NO toca `modules/sales_agent/{domain,application,api,observability}/` (R5 N/A — Story D is tooling, not schema mirror)
- `.claude/rules/backend-quality.md` — Ruff 70+ rules, mypy strict
- `.claude/rules/auditor-downstream-regression.md` — UPDATE entries post-merge T-5 (4 entries)
- `.claude/rules/parallel-safety.md` — `git add` por nombre, no force push, no pull
- `.claude/rules/sales-agent-brand-voice.md` — voseo permitted en goldens transcript content si `dialect_code=es-AR` (sales_agent voice exception preserved)
- `.claude/rules/spanish-text.md` — voseo glosario + magic comment escape (path-exclusion preferred over per-file magic comment for goldens/)
- `.claude/rules/tdd-mandatory.md` — RED → GREEN → REFACTOR per layer (schema → scripts → arch tests → pre-commit hook integration)
- `.claude/rules/tenant-isolation.md` — every golden YAML 1 tenant
- `.claude/rules/git-safety.md` — Conventional Commits, branch=development
- `.claude/rules/anti-default-flip-audit.md` — N/A (no flag flips this story)

### Templates (consult during ticket execution)
- `docs/specs/templates/T-handoff-template.md`
- `docs/specs/templates/T-impl-log-template.md`
- `docs/specs/templates/T-result-template.md`
- `docs/specs/templates/T-review-template.md`

## Native-first execution (mandatory)

Toda lint/test/type-check NATIVE WSL — NUNCA Docker:
- BE: `cd backend && .venv/bin/{ruff,pytest,mypy,jscpd}` (venv 3.12)
- Scripts: `cd backend && .venv/bin/python scripts/{generate_golden_candidates,promote_golden,scan_goldens_pii}.py ...`

Pre-commit hook native enforced — `--no-verify` PROHIBIDO.

## TDD obligatorio (RED → GREEN → REFACTOR per layer)

Orden estricto:
1. **Schema layer** RED → GREEN → REFACTOR (`_schema.py` + `_schema_migrations.py` + tests `test_goldens_schema.py`)
2. **PII pattern lift** RED (verify Story A regression test fails on broken refactor) → GREEN (LIFT + re-import) → REFACTOR
3. **Scanner script** RED (failing detection on adversarial fixtures) → GREEN (`scan_goldens_pii.py`) → REFACTOR
4. **Pre-commit hook integration** RED (test_pre_commit_hook fails) → GREEN (Section 9 added) → REFACTOR
5. **Generation script** RED (mocked simulation matrix shape fails) → GREEN (`generate_golden_candidates.py`) → REFACTOR
6. **Promotion CLI** RED (auto-derive returns wrong values) → GREEN (`promote_golden.py`) → REFACTOR
7. **Coverage tests** RED (15 cells fixtures missing) → GREEN (synthetic test fixtures) → REFACTOR
8. **Arch fitness gates** RED (gate definitions exist but not yet enforced) → GREEN (allowlists empty shrink-only) → REFACTOR

Cada layer: tests primero (failing) → implementación mínima (passing) → refactor.

Default flag flips: N/A esta story (no flag en `core/config.py`).

## Anti-telephone-game (subagent return contract)

Cada builder/auditor MUST devolver UNA línea final:
```
<verdict> -> <path-to-artifact>
```

Examples:
- `done -> docs/product/stories/sales-agent-goldens-3-tenants-dataset/T-1-result.md`
- `blocked -> docs/product/stories/sales-agent-goldens-3-tenants-dataset/checkpoint.md (Story C build pending)`
- `failed -> backend/tests/agentic_evals/sales_agent/test_goldens_schema.py:42 [referential_integrity_actor_profile_id]`

NUNCA inline >500 tokens de artifact body. Caller lee file on demand.

## Process metrics (R12 Layer 1 — emit on each ticket close)

Builder Step 5.5 + Auditor Step 4.5 emit metrics via `scripts/emit_process_metric.py`. Default fields: ticket_id, story_id, phase, duration_minutes, tokens_consumed, model_used, validators_pass_count, validators_fail_count.

## Decisiones de owner routing (per /architect)

| Ticket | Surface | production_code | Owner recomendado | Justificación |
|---|---|---|---|---|
| T-1 | BE test-infra (schema + parallel migrations) | false | `builder-backend` Sonnet | Pydantic v2 cement + parallel registry — declarative, R23 OK |
| T-2 | BE tooling (PII scanner + LIFT + pre-commit hook) | false | `builder-backend` Sonnet | Standalone scripts + shell hook + DRY refactor — R23 OK. Backward-compat verification critical |
| T-3 | BE tooling (generate + promote scripts) | false | `builder-backend` Sonnet | argparse + asyncio + Pydantic + YAML I/O — R23 OK. Cost guard pre-flight + per-cell isolation |
| T-4 | BE test-infra (schema + coverage + arch fitness gates + README) | false | `builder-backend` Sonnet | Test + arch fitness + docs — declarative R23 OK |
| T-5 | DOCS (capability + module + downstream rule) | false | `/pm` post-merge | Documentation reconciliation — pm post-merge ratification |

> **Decisión final routing**: Per `CLAUDE.md` cost-routing matrix + R23 + Chris mandato cero deuda 1000+ tenants. Story D is **service-story BE-only tooling** — no agentic surfaces touched. Sonnet eligible across all 5 tickets per R23 `production_code: false`. PM confirms final routing antes Conv 2 arranca.

## Build order ack (HARD blocker)

> Story D build BLOCKED until Story C build done. Architect phase parallel-safe (design-only, no code change). Chris ratification of Story C build done event triggers Story D `/dev-team` spawn.

Story C build done = arch fitness ratchet GREEN + 5 acceptance gates GREEN + downstream regression rule SSoT updated + capability YAML + module narrative updated + 9 Story C tickets all done.

Validation Story D Conv 2 entry: `state=ready` + Story C `state=done` + checkpoint.md asserts `build_blocked_by_external_story: false`.
