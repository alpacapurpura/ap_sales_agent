<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Backend + Docs Code Review: Story C T-2 + T-9

**Date:** 2026-05-08
**Story:** sales-agent-personas-instrumented-runtime
**Tickets:** T-2 (BE — 15 archetype-aware personas YAML + arch fitness gate) + T-9 (DOCS — 4 deliverables reconciliation)
**Files Reviewed:** 21 (15 archetype-aware YAML NEW, 5 _legacy YAML moved, 1 arch test NEW, 4 docs files edited/created)
**Domains touched:** test-infra (eval simulator personas catalog), docs/product (capability + module + rule SSoT), docs/specs (rubric placeholder)
**Skills consulted:** backend-expert, tessl__pytest-api-testing, tessl__fastapi (N/A), tessl__graceful-degradation (informational — fallback rule cited in CONTEXT-BRIEF), brand-expert (N/A — synthetic personas, not Brand Studio data), offer-expert (N/A), metrics-expert (N/A)
**Verdict:** **PASS**

## /test-backend Gate Status

Source: `gate-output.json` (2026-05-08T19:23Z, exit_code=0, command_alias=`audit-full-suite (Story C)`).

| # | Gate | Result | Detail |
|---|---|---|---|
| 1 | Tools | PASS | venv 3.12, ruff, mypy, pytest |
| 2 | Postgres pre-flight | N/A | T-2 static YAML + arch test, no DB; T-9 docs only |
| 3 | Lint (ruff check) | PASS | 0 errors (T-2 fixed RUF002/RUF003 multiplication-sign + f-string no-placeholder per impl-log Issues 1+2) |
| 4 | Format (ruff format) | PASS | 0 reformats |
| 5 | Type check (mypy strict) | PASS | scoped to simulator/ + new arch test |
| 6 | Architecture fitness | PASS | 980/980 tests (1 NEW gate `test_personas_yaml_completeness.py` 19 tests + Story B 6 gates STILL GREEN per CONTEXT-BRIEF §9) |
| 7 | Tests + coverage | PASS | downstream regression suite 3492 passed/29 skipped (toolkit-dependent T-6/T-7 cases) |
| 8 | Verify marker | N/A | T-2/T-9 not analytics |
| 9 | Integration | DESELECTED | 8 deselected (`-m "not integration"` per Story C scope) |
| 10 | Migration idempotency | N/A | T-2/T-9 zero DB schema change |
| 11 | jscpd | PASS | 15 personas YAML naturally similar < 5% threshold (per CONTEXT-BRIEF §11 LOW-severity note) |
| 12 | interrogate | PASS | docstrings ≥85% on new arch test (Google-style throughout) |
| 13 | pip-audit | N/A | no dependency changes |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | N/A | T-2 = test infrastructure (arch fitness gate + YAML data); T-9 = documentation. No production layered code. |
| 2 | Tenant Isolation | N/A | Personas are SHARED synthetic catalog (NOT per-tenant DB rows). Eval runs preserve tenant-scoped invariants from Story A `eval_tenant_seeded(slug)` (per CONTEXT-BRIEF §5). |
| 3 | Soft Deletes | N/A | No DB ops |
| 4 | Code Quality | PASS | ruff/mypy/format clean; arch test uses idiomatic patterns (`pytestmark = pytest.mark.no_eval`, `frozenset` for constants, pre-compiled regex, helper extraction `_load_yaml_files`/`_get_line_2`/`_parse_comma_set`). Test functions docstring per gate per Bloom canonical mention. |
| 5 | SQLAlchemy 2.0 | N/A | No DB |
| 6 | Async Consistency | N/A | Static fixture tests; no async needed |
| 7 | Pydantic v2 / DTOs / PII | N/A | Synthetic personas, no PII (names like "Ana Torres" "Valeria Moreno" are fictional). Arch test relies on Pydantic `ConfigDict(extra="forbid")` per D-BE-3 (validation delegated to ActorProfile.model_validate downstream). |
| 8 | Migration Quality | N/A | No migrations |
| 9 | Security | PASS | No external calls, no secrets. YAML loads via `yaml.safe_load` (not `yaml.load`) — eliminates RCE risk per ruff S506. Pre-commit hook regex compiled once and re-used. |
| 10 | Tests / TDD | PASS | RED→GREEN per layer: 19 arch test functions cement YAML completeness invariants. Test names self-documenting + assertion error messages actionable. Empty allowlist = ratchet shrink-only. T-1 (schema bump) preceded T-2 (data) preceded T-3 (loader consumer) — TDD ordering correct per critical path. |
| 11 | Cross-cutting | WARN | See FAIL/WARN findings below |
| 12 | Mirror detection | PASS | `test_personas_yaml_completeness.py` is genuinely NEW (no prior). Story B `test_simulator_public_api_surface.py` + `test_simulator_no_mirrors_shared.py` are independent gates with disjoint scope. CONTEXT-BRIEF §7.5 confirms loader genuinely NEW + arch gate NEW (declarative data, no code mirror risk). |

## Cross-scope flags

None for T-2 (BE test infrastructure) and T-9 (docs reconciliation). T-9 row 3 edits `.claude/rules/auditor-downstream-regression.md` adding 4 SSoT rows for downstream surfaces — appropriate for /pm domain (auditor agents read this rule but PM owns its evolution). Auditor itself does not modify the rule during audit.

Note: Story C touches `modules/sales_agent/observability/eval_simulator/` and `modules/copilot/` indirectly (T-3 through T-8) — those are out of scope here (this review is for T-2 + T-9 only). Other tickets reviewed in their own audit scopes.

## Findings

### WARN: T-2 + T-9 commit bodies do not cite "Decisions honored"
**Category:** 11 (Cross-cutting — R6 process-improvement 2026-05-05)
**Files:** commit `b92b5871` (T-2), commit `415db986` (T-9)
**Issue:** R6 expects builder commit body to include "Decisions honored" section listing each `D#` from ticket `decisions_applicable` field. T-2 has `decisions_applicable: [D14, D2, D-BE-1, D-BE-2, D-BE-3, D-BE-4]`; commit body cites D14 + D-BE-* via prose ("3x5 matrix enforcement (D14)") but no explicit "Decisions honored" header listing all 6. T-9 has `decisions_applicable: [D-BE-5]`; commit body covers D-BE-5 in prose ("`docs/specs/rubrics/qualification-accuracy.md` (NEW) — placeholder") but no explicit cite block.
**Impact:** LOW — implementation honors all 6 D# decisions correctly (verified §"Decisions honored cite verification" below). Commit body prose substitutes for explicit block. R6 enforcement is "WARN" tier, not "FAIL".
**Fix (next time):** add commit body section:
```
## Decisions honored
- D14 (3 kinds × 5 tenants matrix): 15 archetype-aware YAMLs + arch test enforces matrix
- D2 (5 LEGACY preserved): git mv into _legacy/ + arch test validates frozenset of 5 names
- D-BE-1 (15+5 split): impl per spec
- D-BE-2 (NEW arch fitness gate empty allowlist shrink-only): 19 tests
- D-BE-3 (Pydantic ConfigDict(extra="forbid") delegated): arch test cross-references ActorProfile.model_validate
- D-BE-4 (es-AR magic comment línea 2): 3 files include comment + arch test enforces
```
**Skill ref:** `.claude/rules/anti-default-flip-audit.md` § R6 (analog) + auditor `<audit_checklist>` Cat 11

### Info: D-BE-4 magic comment format deviation (HTML→YAML comment) — implementation correct
**Category:** 11 (Cross-cutting — Spanish neutro / hook compatibility)
**File:** All 3 es-AR YAMLs (`ceo-b2b-escala-ar.yaml`, `pre-pmf-zero-revenue-ar.yaml`, `pregunton-comparador-3-agencias-ar.yaml`)
**Issue:** 03-arch.md § D-BE-4 prescribed HTML format `<!-- voseo-allowed: ... -->`. Builder used YAML format `# voseo-allowed: ...` (T-2 impl-log Note rationale: "HTML comment `<!-- ... -->` is not valid YAML and would cause parse errors"). 
**Resolution:** ✅ Correct deviation. Pre-commit hook regex per `.claude/rules/spanish-text.md` § R25 accepts both forms (line 105 `(#\s*voseo-allowed([: \t]|$)|<!--\s*voseo-allowed[^>]*-->)`). Arch test `_VOSEO_ALLOWED_PATTERN` mirrors the same regex. The Pydantic `safe_load` would fail on HTML; YAML `#` is the canonical comment form. Builder correctly translated arch decision from doc-language ergonomics into YAML-language constraints.
**Action:** None needed. This is a meta-doc clarity issue — recommend updating 03-arch.md § D-BE-4 to read "magic comment per `.claude/rules/spanish-text.md` § R25 (YAML `#` form for `.yaml` files, HTML form for `.md`)" in a future docs polish pass. NOT blocking.

### PASS findings (positive notes)

- **Voseo check (CRITICAL Cat 11):** zero voseo in 12 non-AR personas (es-PE×3, es-MX×3, es-CO×3, es-419×3) per grep `\b(vos|sos|tenés|querés|podés|sabés|hacés|venís|decís|mirá|dejá|poné|usá|hacé|elegí|seleccioná|arrancá|empezá|agregá|configurá|revisá|escribí|guardá|abrí|volvé|andá|cambiá)\b`. Tuteo throughout. 3 es-AR personas correctly include magic comment línea 2 + may use voseo (1 of 3 actually does — pregunton-comparador-3-agencias-ar.yaml). The other 2 use neutral Spanish; magic comment is preventive scope, acceptable.
- **Arch test ratchet pattern correctness:** 19 test functions, each with explicit error message naming the file + expected vs actual, supports debugging future drift. `_EXPECTED_LEGACY_NAMES` is `frozenset` (immutable, shrink-only intent encoded in type). `_VALID_*` constants are `frozenset` not `set` — type system reflects ratchet semantics.
- **Coverage 3×5 matrix invariant (test 13):** `test_each_tenant_has_happy_nurture_unqualified_personas` enforces D14 at the tenant level (each of 5 tenants must have 3 distinct kinds). Catches any imbalance future authors might introduce.
- **Required schema fields invariant (test 14, 15):** `_REQUIRED_TOP_LEVEL_KEYS` (14 fields) and `_REQUIRED_METADATA_KEYS` (5 fields) frozensets mirror Pydantic ActorProfile contract — runtime + static validation belt-and-suspenders.
- **Cross-validator with ARCHETYPE_DIALECT_MAP (test 9):** D-AG-1 enforced statically — loader cross-check has zero runtime mismatches because static gate catches them first. Beautiful defense-in-depth.

## Contract Compliance (T-2 + T-9 vs CONTRACT/spec)

T-2 acceptance criteria from `06-tickets.yaml` (lines 88-165):
- [x] A1: 15 archetype-aware + 5 legacy count → arch test 1 + 2 PASS, shell count PASS per T-2-result.md
- [x] A2: arch fitness gate 19/19 tests → PASS per gate-output
- [x] A3: es-AR voseo magic comment line 2 → arch test 12 PASS

T-9 acceptance criteria from `06-tickets.yaml` (lines 643-663):
- [x] A1: `grep -q 'personas_archetype_aware_count' docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` — PASS (1 match line 82)
- [x] A2: `grep -q '15 archetype-aware personas' docs/product/modules/sales-agent.md` — PASS (1 match line 55)
- [x] A3: `grep -q 'personas_loader' .claude/rules/auditor-downstream-regression.md` — PASS (2 matches in 4 NEW SSoT rows)
- [x] A4: `test -f docs/specs/rubrics/qualification-accuracy.md` — PASS (32 lines, neutro tuteo)

## Decisions honored cite verification

T-2 ticket `decisions_applicable: [D14, D2, D-BE-1, D-BE-2, D-BE-3, D-BE-4]`:
- D14 (3 kinds × 5 tenants): ✅ implemented + arch test 13 enforces matrix
- D2 (5 LEGACY preserved via git mv): ✅ 5 files in `_legacy/` + arch test 18 (`_EXPECTED_LEGACY_NAMES` frozenset)
- D-BE-1 (15 archetype-aware + 5 LEGACY moved): ✅ implemented
- D-BE-2 (NEW arch fitness gate empty allowlist shrink-only): ✅ `test_personas_yaml_completeness.py` empty allowlist (frozensets are SSoT enums, not allowlists)
- D-BE-3 (Pydantic ConfigDict(extra="forbid") delegated, no custom validator): ✅ arch test docstring line 463-468 cross-refs ActorProfile contract; required-field check is belt-and-suspenders
- D-BE-4 (es-AR magic comment línea 2): ✅ implemented (YAML `#` form per R25 hook compatibility — see info finding above)

T-9 ticket `decisions_applicable: [D-BE-5]`:
- D-BE-5 (rubric placeholder Story E owns runtime): ✅ created at `docs/specs/rubrics/qualification-accuracy.md` (32 lines, defers runtime to Story E explicitly)

All 7 D# decisions honored implementation-side. **Cite-side WARN:** explicit "Decisions honored" header missing in commit bodies. R6 WARN tier.

## Allowlist Movement
- [x] `test_personas_yaml_completeness.py` introduces NEW frozensets (canonical enum SSoT, not allowlists). No "DROP" or "EXEMPTION" allowlist that could grow.
- [x] No existing arch test allowlists touched by T-2 / T-9 (Story B 6 gates STILL GREEN unchanged per CONTEXT-BRIEF §9).
- [x] `.claude/rules/auditor-downstream-regression.md` SSoT inventory shrink-only direction: T-9 ADDED 4 rows (covering NEW surfaces), no rows removed. Per rule's own docs ("shrink-only excepto cuando agregás surface nueva") this is correct extension.

## Native-First Audit
- [x] No `docker exec ... ruff|pytest|mypy` in commit bodies of `b92b5871` or `415db986`.
- [x] No `git add .` / `git add -A` / `git add -u` evidenced (per parallel-safety; Story C builders used scoped staging).
- [x] T-2/T-9 not pushed to `main` directly (development branch); `make ci-parity` not required.

## Downstream regression scope (auditor R3 protocol)

Per `.claude/rules/auditor-downstream-regression.md` § Workflow auditor:

Surfaces modified in T-2 + T-9 PR scope:
- `docs/specs/personas/archetype-aware/*.yaml` (NEW × 15)
- `docs/specs/personas/_legacy/*.yaml` (MOVED × 5)
- `backend/tests/architecture/test_personas_yaml_completeness.py` (NEW)
- `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` (EDIT)
- `docs/product/modules/sales-agent.md` (EDIT)
- `.claude/rules/auditor-downstream-regression.md` (EDIT — adds 4 rows)
- `docs/specs/rubrics/qualification-accuracy.md` (NEW placeholder)

Lookup SSoT tabla post-T-9 update (rule lines 44-47):
- `personas_loader.py` → tests/agentic_evals/sales_agent/simulator/test_personas_loader.py + test_simulator_smoke.py + test_customer_prompt_v2_unit.py + test_customer_node_unit.py + tests/architecture/test_personas_yaml_completeness.py
- `archetype-aware/*.yaml` → tests/architecture/test_personas_yaml_completeness.py + test_personas_loader.py

Coverage in `gate-output.json`: command runs `pytest tests/agentic_evals/sales_agent/simulator/ tests/modules/sales_agent/ tests/modules/copilot/ tests/shared/ -m "not integration"` — covers ALL downstream test paths above. Plus full `tests/architecture/` (980 tests) covers the new gate. Plus `tests/architecture/test_simulator_public_api_surface.py` + `test_simulator_no_mirrors_shared.py` validate Story B invariants STILL GREEN.

| Surface modified | Downstream test targets | gate-runner status |
|---|---|---|
| `docs/specs/personas/archetype-aware/*.yaml` | tests/architecture/test_personas_yaml_completeness.py + tests/agentic_evals/sales_agent/simulator/test_personas_loader.py | PASS (980 arch + 3492 downstream) |
| `tests/architecture/test_personas_yaml_completeness.py` | self (19 tests) + included in arch suite | PASS |
| `docs/product/{capabilities,modules}/...` + `.claude/rules/...` + `docs/specs/rubrics/...` | DOCS — no test target. /pm verifier shell greps PASS. | N/A (docs verifier) |

**No additional gate-runner spawn needed.** Existing `audit-full-suite (Story C)` covers all downstream surfaces per `auditor-downstream-regression.md` SSoT.

## Verdict Math

- T-2 BE: all categories PASS or N/A. Cat 11 WARN (R6 cite block missing — non-blocking).
- T-9 DOCS: all 4 acceptance criteria PASS. Cat 11 same WARN.
- gate-output GREEN (980 arch + 3492 downstream + lint + format + mypy).
- Allowlist movement clean (shrink-only direction respected).
- Native-First clean.
- Downstream regression covered.
- Skills consulted documented in T-2-impl-log (backend-expert + tessl__pytest-api-testing + tessl__fastapi).
- Mirror detection (Cat 12): NEW arch test is genuinely new, no duplication of Story B gates.
- Voseo (Cat 11 CRITICAL): 12 non-AR personas zero voseo, 3 es-AR personas have magic comment línea 2 (R25 compliant).

**WARN count:** 1 (R6 cite block). Below the "two or more category WARNs → overall WARN" threshold.

**Verdict:** **PASS**

Recommendation to /pm: T-2 + T-9 are mergeable. Optional follow-up — append "Decisions honored" cite section retroactively to commit messages via `git commit --amend` (Chris approval required, since `415db986` is HEAD). Alternatively, accept WARN as historical learning and apply R6 enforcement strictly on subsequent stories.

## Last line

done -> /home/chris/AISALESHT/docs/product/stories/sales-agent-personas-instrumented-runtime/REVIEW-be-docs.md
