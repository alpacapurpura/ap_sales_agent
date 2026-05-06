# T-2 Audit — sales-agent-eval-runner-foundation

---
ticket_id: T-2
story_id: sales-agent-eval-runner-foundation
audited_by: claude-opus-4-7 (auditor backend skill)
audited_at: 2026-05-05T00:30:00Z
commit_sha: 6abfef7b
verdict: APPROVED_WITH_NOTES
iter: 1
---

## Verdict: **APPROVED_WITH_NOTES** (2 minor WARNs · 0 FAILs)

T-2 ships its acceptance criteria cleanly. All 4 spec acceptances (A1–A4) reproduce verbatim under both flag settings. Tenant isolation, anti-duplication, scope discipline, TDD RED→GREEN trace, native quality gates: all green. Two minor code-quality nits below — non-blocking, can be self-fixed by builder in T-3 prep or left as-is at PM discretion.

## Verifier outputs (auditor re-ran)

| # | Check | Output | Status |
|---|---|---|---|
| 1 | `pytest tests/agentic_evals/sales_agent/ --override-ini="addopts=" -v` (no flag) | 11 PASS, 3 SKIPPED · all 3 skips report verbatim reason `"eval markers require --run-evals flag"` | ✅ A1 PASS |
| 2 | `pytest --run-evals --override-ini="addopts=" -v` | 10 PASS, 4 SKIPPED · DB-dependent eval tests skip with explicit Spanish reason naming Visionarias + tenant UUID + remediation hint (`make seed-visionarias`) | ✅ A2/A3 PASS |
| 3 | Co-collection `tests/agentic_evals/sales_agent/ + tests/modules/sales_agent/orchestrator/` (no flag) | 58 PASS, 3 SKIPPED · sibling sales_agent tests run normally; eval marker stays scoped to harness dir | ✅ no leak |
| 4 | `ruff check tests/agentic_evals/ --no-cache` | All checks passed | ✅ |
| 5 | `ruff format --check tests/agentic_evals/` | 10 files already formatted | ✅ |
| 6 | `pytest tests/architecture/ --override-ini="addopts=" -q` | 823 passed (no regression vs T-1 baseline) | ✅ |
| 7 | Anti-duplication grep: `visionarias_tenant_session\|class TrajectorySpy` cross-codebase | only T-2 + T-1 README forward-ref; zero pre-existing implementations | ✅ §0 GATE clean |
| 8 | Tenant-isolation grep: every DB query in fixtures | `TenantModel.id == tenant_id` (PK = tenant), `ProductModel.tenant_id == tenant_id` (explicit), LeadModel insert sets `tenant_id` column | ✅ |
| 9 | `langdetect` import-leak audit: `grep -rn langdetect src/` | zero matches — pure dev dep, consumed only by T-4 (per Decision B5) | ✅ |
| 10 | `git diff 6abfef7b~1 6abfef7b -- backend/src/` | empty — zero src/ writes | ✅ |
| 11 | Pre-existing failures (3 in copilot/sales_agent observability) | reproduce in isolation without T-2 fixtures loaded; origin Story A T-1 commit `5856be4d` | ✅ NOT T-2 caused |

## Category summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | tests-only PR; cross-module reads via lazy imports inside fixture body — read-only |
| 2 | Tenant Isolation | PASS | every DB query filters tenant_id (PK or explicit column); defensive cross-tenant double-check on offer.tenant_id post-query |
| 3 | Soft Deletes | PASS | `ProductModel.deleted_at.is_(None)` filter applied; LeadModel insert documented teardown contract |
| 4 | Code Quality | WARN | 2 minor nits (see findings) |
| 5 | SQLAlchemy 2.0 | PASS | `select(Model).where(...)` only · no legacy `session.query()` · no `Column()` |
| 6 | Async Consistency | PASS | `sales_agent_entrypoint` returns async closure; `agent_app.ainvoke` is canonical async entry; no blocking I/O inside async path |
| 7 | Pydantic v2 / DTOs / PII | PASS | tests-only PR; no DTOs added |
| 8 | Migration Quality | NA | no migrations |
| 9 | Security | PASS | synthetic lead `api_id="eval-{run_id}"` enables admin filter to keep eval traffic out of real reports; no PII echoed in logs (structlog with structured kwargs) |
| 10 | Tests / TDD | PASS | RED→GREEN evidence in impl-log + commit body; 14 meta-tests cover marker plumbing, fixture preconditions, public surface, end-to-end smoke |
| 11 | Cross-cutting | WARN | Spanish neutro skip reasons contain voseo — see Finding #2 |
| 12 | Mirror detection | PASS | greenfield; all shared abstractions reused verbatim (agent_app, create_initial_state, TenantKnowledgeBuilder, build_sales_agent_observability_context, SessionLocal, LeadModel, TenantModel, ProductModel) |

## Cross-scope flags

None. T-2 is fully scoped to `tests/agentic_evals/sales_agent/`. The diff touches `tests/agentic_evals/` (new), `pyproject.toml` (additive markers only), `requirements-dev.txt` (additive `langdetect` dep). Zero `src/modules/copilot/` or `src/modules/sales_agent/` writes — auditor-backend scope confirmed.

## Findings

### WARN #1: `is not "__missing__"` identity comparison on string literal

**Category:** 4 (Code Quality)
**File:** `backend/tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py:70`
**Issue:**
```python
assert flag_value is not "__missing__", (  # noqa: F632 — explicit identity check
    "Flag --run-evals must be registered via pytest_addoption in root conftest."
)
```
F632 is suppressed via `# noqa: F632`, but identity comparison (`is not`) on a str literal is semantically wrong — Python emits `SyntaxWarning: "is not" with 'str' literal. Did you mean "!="?`. The test "passes" only because `False is not "__missing__"` happens to be True (different objects). The intent is value comparison; `getoption("--run-evals", default="__missing__")` returns False (the registered default), so `flag_value != "__missing__"` is the correct expression.

**Fix:** swap `is not` for `!=` and drop the `# noqa: F632`:
```python
flag_value = pytestconfig.getoption("--run-evals", default="__missing__")
assert flag_value != "__missing__", (
    "Flag --run-evals must be registered via pytest_addoption in root conftest."
)
```

**Skill ref:** `backend-expert/references/runtime-quality-checklist.md` (anti-pattern: silencing lint instead of fixing); ruff F632.

**Impact:** non-blocking. Test passes today; the bug is latent. Trivial self-fix.

### WARN #2: Voseo in Spanish-neutro skip reasons

**Category:** 11 (Cross-cutting · Spanish neutro)
**File:** `backend/tests/agentic_evals/sales_agent/fixtures/tenant.py:101, 127, 133`
**Issue:** three skip reasons use voseo imperatives (`Verificá`, `Corré`, `configurá`) that the rule explicitly forbids:

- L101: `f"Verificá que Postgres esté corriendo. Detalle: {exc}"`
- L127: `f"Verificá que Postgres esté accesible desde WSL nativo. ..."`
- L133: `f"Corré \`make seed-visionarias\` o configurá VISIONARIAS_TENANT_ID."`

The impl-log and result.md claim "Spanish neutro LATAM (sin voseo). Verified" — claim is incorrect. `Verificá/Corré/configurá` appear on the explicit voseo blacklist in `.claude/rules/spanish-text.md` (glosario: `verificá → verifica`, `corré → corre`, `configurá → configura`).

Note: precedent for the strict reading lives in `tests/modules/copilot/test_deep_agent_prompt_voseo_compliance.py` (existing arch-test that lists `configurá` as a forbidden token). Skip messages are surfaced to humans reading pytest output and are arguably user-facing (CI logs, contributor diagnostics). The rule's explicit scope `aplica: ... BE catalogs user-facing, DTOs messages, ... emails, notificaciones` is broad enough to cover diagnostic messages that humans read.

**Fix:** swap to neutro tuteo. Three minimal edits:
```python
# L101
pytest.skip(
    f"No se pudo abrir la sesión DB para Visionarias ({tenant_id}). "
    f"Verifica que Postgres esté corriendo. Detalle: {exc}",
)
# L127
f"Verifica que Postgres esté accesible desde WSL nativo. "
# L133
f"Ejecuta `make seed-visionarias` o configura VISIONARIAS_TENANT_ID.",
```

**Skill ref:** `.claude/rules/spanish-text.md` § R2 + glosario (voseo→neutro).

**Impact:** non-blocking. Skip reasons surface only when DB is down (uncommon native-WSL path). Trivial self-fix; matches precedent of `test_deep_agent_prompt_voseo_compliance.py` which already polices these tokens elsewhere.

### Notes (informational, not WARN/FAIL)

- **`Any` return type on `visionarias_tenant_session`** (tenant.py:69): documented inline ("generator yields dict, but mypy gets noisy"). A more precise type would be `Generator[dict[str, Any], None, None]`. Not blocking — fixture body is short and the comment justifies the choice. Builder's call.
- **Cross-tenant `AssertionError` raise inside fixture** (tenant.py:168–173): builder chose `raise AssertionError` for the defensive cross-tenant check rather than `pytest.fail`. This is correct because cross-tenant leak is a security invariant, not a precondition skip — explicit raise will halt the test loud. Good defensive coding.
- **Lazy `from src.X import Y` inside fixture bodies**: documented as cost optimization for default-suite collection. Aligns with anti-duplication and DDD read-only access pattern.
- **Master conftest is NOT mirrored**: T-2 fixtures intentionally bypass the SQLite in-memory `db_session` from `backend/tests/conftest.py` (Decision B6 — needs real Postgres for cost layer). This is documented in `_get_real_db_session` docstring and is correct.

## Contract Compliance (T-2 surface)

- [x] A1: default suite reports SKIPPED for eval-marked items with verbatim reason — verified
- [x] A2: `--run-evals` runs the meta-tests (DB-skips OK on native WSL) — verified
- [x] A3: `visionarias_tenant_session` skips with explicit Spanish reason naming Visionarias when DB unavailable — verified (modulo voseo nit Finding #2)
- [x] A4: coverage gate 43% NOT lowered (eval suite outside coverage source) — confirmed via pyproject inspection
- [x] Public fixture surface (`__all__`) exports the 4 names exactly as documented — verified
- [x] `langdetect` in requirements-dev only, NOT runtime, NOT imported by `src/` — verified
- [x] Anti-duplication §0 GATE: greenfield, zero mirrors — verified
- [x] Cohabitation with parallel Story A T-2: zero overlap (Makefile/pricing/workers/runtime untouched) — verified

## Allowlist Movement

- No allowlist changes (no arch fitness allowlist edits, no ruff per-file overrides added).

## Native-First Audit

- [x] No `docker exec ... ruff|pytest|tsc|vitest|mypy|eslint` in commit body or fixture code — clean
- [x] No `git add .` / `git add -A` / `git add -u` evidence — commit staged 13 files by name
- [x] No push to `main` (push is to `development` per parallel-safety) — confirmed checkpoint phase

## Verdict math

- 0 FAILs in categories 1/2/8/9/12 → no auto-FAIL
- 0 allowlist growth → no auto-FAIL
- 0 `/test-backend` gate FAILs (auditor re-ran lint, format, arch, eval suite both flag values, co-collection)
- IMPL-LOG.md § Skills Consulted populated (backend-expert + tessl__pytest-api-testing + tessl__fastapi NA + tessl__graceful-degradation Rule 6 + sales-agent-expert + anti-duplication + tdd-mandatory + parallel-safety + spanish-text) — all required skills cited
- `runtime-quality-checklist.md` cited in IMPL-LOG — confirmed
- 2 category WARNs (Cat 4, Cat 11) → overall **WARN** per verdict math
- Both WARNs are trivially self-fixable; ratifying as **APPROVED_WITH_NOTES** (semantically equivalent to WARN — pass with minor fixes recommended).

## Auditor handoff to PM

- T-2 may proceed to push (coordinated with Story A T-2 controller per parallel-safety M3).
- WARN #1 + #2 should be picked up either:
  - (a) self-fixed by builder pre-push as a follow-up amendment (3 string edits, no logic change), OR
  - (b) tracked as a follow-up nano-ticket appended to T-3 prep (low priority).
- Story B is unblocked for T-3 (TrajectorySpy + artifacts writer).

