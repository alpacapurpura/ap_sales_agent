# T-5 Result — growth-studio-actions-schemas-real

**Ticket:** T-5 — Cross-stack contract test — BE Pydantic ↔ FE zod schema alignment + npm script export-zod-schemas
**State:** pushed
**Builder:** claude-sonnet (builder-backend)

## Deliverables shipped

| File | Change |
|---|---|
| `frontend/scripts/export-zod-schemas.ts` | NEW — exports StageFilterParams, ChannelOverviewParams, TriggerEtlRefreshParams schemas as JSON Schema via `z.toJSONSchema()` |
| `frontend/package.json` | MODIFIED — added `"schema:export": "npx tsx scripts/export-zod-schemas.ts"` script |
| `backend/tests/architecture/test_be_fe_schema_alignment_growth_studio.py` | NEW — 22 arch fitness tests across 5 test classes |
| `docs/product/stories/growth-studio-actions-schemas-real/05-guidelines.md` | MODIFIED — section 6 updated with schema:export script invocation reference |

## Test Results

| Validator | Result |
|---|---|
| `be_zod_schema_alignment_test` (22 tests) | PASS — 22/22 |
| `be_arch_fitness_full` | PASS — 961/961 (939 pre-existing + 22 new) |
| `be_lint` (ruff check) | PASS — 0 errors |
| `be_format` (ruff format) | PASS — 0 files to reformat |

## Architecture

### Export script (`frontend/scripts/export-zod-schemas.ts`)

- Uses `npx tsx` (CJS mode) — top-level await wrapped in `main()` function
- Imports zod schemas directly (NOT via barrel `index.ts` to avoid React component imports)
- Slug arrays inlined to avoid `@/` path alias resolution issues in Node.js context
- Outputs to `frontend/dist/growth-studio-zod-schemas.json` (gitignored)

### Arch test (`test_be_fe_schema_alignment_growth_studio.py`)

**5 test classes, 22 tests:**

| Class | What it checks |
|---|---|
| `TestSchemaExportExists` | 3 schemas present + valid JSON Schema object shape |
| `TestAdditionalPropertiesForbidden` | `additionalProperties: false` on BE + FE (adversarial defense) |
| `TestFieldNamesAlignment` | All field names bidirectionally present |
| `TestEnumValueAlignment` | Exact enum values for stage/channel/period |
| `TestDriftDetection` | Count invariants (5 stages, 5 channels, 3 periods) |

**Accepted asymmetries (documented, not checked):**
- `required` list: zod `.default()` fields appear in `required`; Pydantic doesn't include defaults
- Optional fields: Pydantic = `anyOf[T, null]`; zod = absent from `required`
- `_extract_enum_values()` helper normalises both representations for enum comparison

**Self-healing:** When `frontend/dist/growth-studio-zod-schemas.json` is absent, the test auto-runs `npm run schema:export` via subprocess.

**Drift detection verified:** Manually removed a stage slug → test FAILs with clear error pointing to the drifted enum and canonical source files.
