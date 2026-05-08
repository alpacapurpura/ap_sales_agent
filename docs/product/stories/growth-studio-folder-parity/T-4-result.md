# T-4 Result — Phase 4 Legacy Purge

**Story:** growth-studio-folder-parity  
**Ticket:** T-4  
**State:** PUSHED  
**Date:** 2026-05-08  
**Builder:** claude-sonnet

## Summary

Purged 3 legacy folders from `frontend/src/features/growth-studio/`:
- `config/` → migrated to `lib/channel-display-registry.ts`, `lib/dashboard-sections.ts`; channel-stage-map superseded by lib/registries/channel-registry.ts; channel-chart-config pass-through eliminated
- `context/` → migrated to `store/growth-sync-store.tsx`
- `__mocks__/` → migrated to `__tests__/__mocks__/metrics-mock-data.ts`

All 9 dynamic mock imports in `stage-detail-api.ts` updated. All 6 consumer import paths updated atomically in same commit.

VR replacement (Playwright) deferred — story-1 T-8 not yet landed. Legacy vitest VR test passes (6/6).

## Validators

| Validator | Result |
|---|---|
| `fe_typecheck` | PASS (0 errors) |
| `fe_lint_growth` | PASS (0 errors) |
| `scenario_3_visual_bowtie_pixel_perfect` | PASS (6/6) |
| Growth-studio __tests__ suite | PASS (73/73, 7 files) |
| Architecture fitness (25 files) | PASS (51/51) |
| `visual_bowtie_pixel_perfect_e2e` | DEFERRED (story-1 T-8 not landed) |

## Files Changed

**NEW:** lib/channel-display-registry.ts, lib/dashboard-sections.ts, store/growth-sync-store.tsx, __tests__/__mocks__/metrics-mock-data.ts, __tests__/channel-display-registry.test.ts, __tests__/channel-stage-map.test.ts

**MODIFIED:** ChannelRowMetrics.tsx, ChannelRow.tsx, AttractionTrendChart.tsx, SyncProgressDialog.tsx, AttractionCaptureDetail.tsx, stage-detail-api.ts, layout.tsx

**DELETED:** config/ (6 files), context/ (1 file), __mocks__/ (1 file)

## Next

T-5: Allowlist cleanup — 6 dashboards adopt useCopilotOffset (DEPENDS story-1 T-7).
