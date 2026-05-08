# T-2 Result — growth-studio-actions-schemas-real

**Ticket:** T-2 — FE 4 Zod schemas + 5 action components + registry/index
**State:** pushed
**Builder:** claude-sonnet (builder-frontend)

## Deliverables shipped

### Schemas (`frontend/src/features/growth-studio/schemas/`)
| File | Purpose |
|---|---|
| `stage-filter-params.schema.ts` | Stage/channel/period filter — consumes STAGE_REGISTRY + CHANNEL_REGISTRY |
| `channel-config.schema.ts` | Channel config validation — hex color, etl_rate_limit bounds |
| `kpi-selection.schema.ts` | Metric catalog entry + user KPI selection (min 1, max 10) |
| `tier-loading.schema.ts` | Tier response envelope (tier 0-3, size_hint, truncated) |
| `index.ts` | Barrel + side-effect `import "../actions/registry"` |
| `__tests__/stage-filter-params.test.ts` | 10 tests |
| `__tests__/stage-filter-params-security.test.ts` | 6 security tests |
| `__tests__/channel-config.test.ts` | 11 tests |
| `__tests__/kpi-selection.test.ts` | 13 tests |
| `__tests__/tier-loading.test.ts` | 10 tests |

### Actions (`frontend/src/features/growth-studio/actions/`)
| File | Purpose |
|---|---|
| `StageMetricsAction.tsx` | KPI list with currency + truncated alert + channel breakdown |
| `ChannelOverviewAction.tsx` | Dashboard KPI grid with labels |
| `ETLRefreshAction.tsx` | Queued/success state with run_id |
| `ETLRateLimitedAction.tsx` | Rate limit alert with retry time |
| `ETLConfirmAction.tsx` | Confirm button — delegates to api/etl-api.ts |
| `registry.ts` | bootstrapGrowthStudioActions() + GROWTH_STUDIO_ACTION_KEYS |
| `index.ts` | Barrel exports |
| `__tests__/StageMetricsAction.test.tsx` | 7 tests |
| `__tests__/StageMetricsAction-large-volume.test.tsx` | 3 tests |
| `__tests__/ChannelOverviewAction.test.tsx` | 4 tests |
| `__tests__/ETLRefreshAction.test.tsx` | 4 tests |
| `__tests__/ETLRateLimitedAction.test.tsx` | 4 tests |
| `__tests__/ETLConfirmAction.test.tsx` | 4 tests |

### API extension
- `api/etl-api.ts` — added `triggerEtlChannel()` (arch compliance: fetchClient in api/ only)

## Validators

| Validator | Result |
|---|---|
| `fe_typecheck` (tsc --noEmit) | PASS — 0 errors |
| `fe_lint` (ESLint) | PASS — 0 errors, 35 warnings (standard) |
| `fe_arch_fitness` (30 arch tests) | PASS — 30/30 |
| `fe_zod_schema_unit_tests` (50 tests) | PASS — 50/50 |
| `fe_action_component_unit_tests` (26 tests) | PASS — 26/26 |
| Growth-studio full suite | PASS — 732/732 |

## Key decisions

- `fetchClient` moved to `api/etl-api.ts::triggerEtlChannel()` — arch test enforces api/-only rule
- `ETLConfirmAction` uses `useCallback` for `handleConfirm` — fixes react-perf warning
- Enum values derived from `STAGE_REGISTRY.map(s => s.slug)` + `CHANNEL_REGISTRY.map(c => c.slug)` — no hardcoding
- `schemas/index.ts` side-effect imports `../actions/registry` — mirrors brand-studio pattern
- Spanish neutro throughout: "Límite de tarifa", "Datos parciales", "Actualización en cola"
