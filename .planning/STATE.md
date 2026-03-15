# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-15)

**Core value:** Business owner sees their entire customer lifecycle at a glance and understands where the funnel is healthy, leaking, or needs action.
**Current focus:** Phase 1 — Critical Bug Fixes

## Current Position

Phase: 1 of 11 (Critical Bug Fixes)
Plan: 0 of 2 in current phase
Status: Ready to plan
Last activity: 2026-03-15 — Roadmap created with 11 phases covering 54 requirements

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: none
- Trend: N/A

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: Provider adapter pattern chosen as architecture for source-agnostic design
- Roadmap: CRM is authoritative source of truth for conversion counts (never sum ad-platform conversions)
- Roadmap: Shopify uses test data behind feature flag until connection is repaired
- Roadmap: Stages 5-6 combined into one phase (both CRM-heavy retention lifecycle)

### Pending Todos

None yet.

### Blockers/Concerns

- Meta API v19.0 is completely broken in production (HTTP 400). Must be fixed before any Meta data flows.
- Meta SDK singleton causes cross-tenant data leaks. Security-critical fix.
- CRM move_stage() is a pass placeholder. All stages 1-7 will return zero until Phase 3 completes.
- CRM scoring thresholds (e.g., lead_score > 70 = MQL) need product input before Phase 3 implementation.
- TikTok token 24h expiry needs refresh job that differs from Google/Meta patterns.
- Stage 7 K-Factor depends on whether referral codes exist in CRM schema — verify before Phase 10.

## Session Continuity

Last session: 2026-03-15
Stopped at: Roadmap creation complete. Ready to plan Phase 1.
Resume file: None
