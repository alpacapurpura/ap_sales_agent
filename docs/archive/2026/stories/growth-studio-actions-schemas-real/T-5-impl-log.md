# T-5 Impl Log — growth-studio-actions-schemas-real

**Ticket:** T-5 — Cross-stack contract test — BE Pydantic ↔ FE zod schema alignment + npm script export-zod-schemas
**Owner:** claude-sonnet (builder-backend) — surface=backend (arch test in tests/architecture)
**Assigned at:** 2026-05-09T06:30:00Z
**Surface:** Cross-stack (BE arch test + FE script)
**production_code:** false (test + script — R23 Sonnet OK)
**Depends on:** T-1 (DONE — `74c6b2d6`) BE Pydantic + T-2 (DONE — `41cb89da`) FE zod

## Skills Consulted

| Skill | Reason invoked | Decision |
|---|---|---|
| `backend-expert` | BE arch test patterns, ruff rules, pyproject.toml per-file ignores | Used noqa: S603 S607 for subprocess in tests (S101 already ignored for tests/); removed unused sys import |
| `tessl__fastapi` | Pydantic v2 `model_json_schema()` output shape verification | Confirmed `extra="forbid"` → `additionalProperties: false` in JSON Schema export |
| `tessl__pytest-api-testing` | Fixture scope pattern for module-scoped fixtures | Used `scope="module"` for be_schemas + fe_schemas since they're stateless reads |
| `tessl__graceful-degradation` | Not applicable — no external HTTP calls in this test | N/A |

## Plan (per 06-tickets.yaml T-5 + 03-arch.md § 5)

- FE npm script `export-zod-schemas` — produce JSON Schema via `z.toJSONSchema()` for BE consumption
- BE arch fitness test: validate Pydantic input schemas (T-1 `_analytics_inputs.py`) field shapes match FE zod schemas (T-2 `*-schema.ts`)
- Verify Literal enums + extra='forbid' / .strict() alignment
- Document accepted asymmetries (R-4: zod `.default()` lists in `required`, Pydantic doesn't)

## Iteration log

### Iteration 1 — Design + implement

**Key design decisions:**

1. **Export script strategy**: Cannot import schemas via barrel `index.ts` (pulls in React components via `../actions/registry`). Instead, inlined the slug arrays and re-declared the three input schemas in `export-zod-schemas.ts` using pure zod — no React imports needed.

2. **zod v4 compatibility**: Confirmed `z.toJSONSchema()` available in zod 4.3.6. CJS mode (tsx default) requires wrapping async code in `main()` function — top-level await not supported.

3. **`__dirname` usage**: tsx runs in CJS mode, so `__dirname` is available. Used `join(__dirname, "..", "dist")` to resolve output path from `scripts/` to `frontend/dist/`.

4. **Accepted asymmetries (R-4)**:
   - `required` list: zod lists fields with `.default()` as required; Pydantic does not. Test deliberately does NOT compare `required` arrays.
   - Optional vs nullable: Pydantic encodes `ChannelSlug | None` as `anyOf[{enum:[...]}, {type:"null"}]`; zod encodes `.optional()` as absent from `required`. `_extract_enum_values()` helper normalises both patterns.

5. **Self-healing test**: When `frontend/dist/growth-studio-zod-schemas.json` is absent (clean checkout), the fixture calls `_run_npm_export()` via subprocess.

6. **Drift detection verified**: Manually removed a stage slug from the JSON export file → test failed with clear error pointing to the drifted enum. Restored via `npm run schema:export`.

**Ruff violations fixed:**
- `S603` — subprocess with untrusted input: added `# noqa: S603` (input is hardcoded constant `NPM_SCRIPT`)
- `S607` — partial executable path: added `# noqa: S607` on `["npm", ...]` list line
- `PLW1510` — missing `check=` arg: added `check=False` explicitly
- Removed unused `import sys`

## Deliverables

| File | Change |
|---|---|
| `frontend/scripts/export-zod-schemas.ts` | NEW — exports 3 tool input schemas as JSON Schema via `z.toJSONSchema()` |
| `frontend/package.json` | MODIFIED — added `"schema:export": "npx tsx scripts/export-zod-schemas.ts"` script |
| `backend/tests/architecture/test_be_fe_schema_alignment_growth_studio.py` | NEW — 22 tests across 5 test classes |
| `docs/product/stories/growth-studio-actions-schemas-real/05-guidelines.md` | MODIFIED — section 6 reference paths updated with script invocation details |

## Test Results

- **22/22 tests pass** in `test_be_fe_schema_alignment_growth_studio.py`
- **961/961 arch fitness tests pass** (939 pre-existing + 22 new)
- Lint: `ruff check` 0 errors
- Format: `ruff format --check` 0 files to reformat
- Drift detection verified: intentional mismatch → test FAILS with clear diagnostic message

## Test classes implemented

| Class | Tests | Coverage |
|---|---|---|
| `TestSchemaExportExists` | 2 | Export artifact has all 3 schemas + valid JSON Schema objects |
| `TestAdditionalPropertiesForbidden` | 6 (3×BE + 3×FE) | Both sides have `additionalProperties: false` |
| `TestFieldNamesAlignment` | 6 (3×BE→FE + 3×FE→BE) | All field names present on both sides |
| `TestEnumValueAlignment` | 5 parametrized | stage/channel/period enums match exactly |
| `TestDriftDetection` | 3 | Count invariants (5 stages, 5 channels, 3 periods) |

## Validators

| Validator | Result |
|---|---|
| `be_zod_schema_alignment_test` (22 tests) | PASS — 22/22 |
| `be_arch_fitness_full` (961 tests) | PASS — 961/961 |
| `be_lint` (ruff check) | PASS — 0 errors |
| `be_format` (ruff format) | PASS — 0 files to reformat |
