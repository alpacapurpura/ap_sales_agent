---
globs: "{backend/src/modules/analytics/**/*.py,frontend/src/features/growth-studio/**/*.{ts,tsx}}"
description: Growth Studio metrics pipeline architecture — stage services, cache, progressive loading
---

# Analytics Metrics Architecture

> **Before reading this file**, if your question is about *what the ETL extracts,
> from where, when, or where it lands*, the answer lives in
> `docs/etl/extraction-contract.md` (auto-generated from
> `backend/src/modules/analytics/domain/extraction_contract.py`).
> See `.claude/rules/etl-extraction-contract.md` for the workflow rules
> that govern reading and updating that contract.
>
> **This file** covers the runtime metrics pipeline: stage services, group
> mappings, channel registry, progressive loading. It is about how the
> metrics flow from `official_metrics` to the dashboard, not about how
> they got into `official_metrics` in the first place.

Rules for the Growth Studio metrics pipeline. Prevents the duplication bug
that made `website-total` invisible (two divergent `_GROUP_MAP` copies).

## Single Source of Truth

| Concern | Canonical file | Never duplicate in |
|---|---|---|
| Group mappings (`ATTRACTION_GROUP_MAP`, etc.) | `stage_services/constants.py` | metrics_service.py, individual stage services |
| Stage group definitions (`STAGE_GROUPS`) | `stage_services/constants.py` | overview_stage.py, group_detail.py |
| Display name map (`DISPLAY_NAME_MAP`) | `stage_services/constants.py` | individual stage services |
| Error messages (`ERROR_MESSAGES`) | `stage_services/constants.py` | individual stage services |
| Channel definitions per stage | `channel_registry.py` → `STAGE_CHANNEL_MAP` | hardcoded lists in services |
| Provider-to-channel-type mapping | `channel_registry.py` → `PROVIDER_TO_CHANNEL_TYPES` | hardcoded checks in services |

**If you need a constant that already exists in `constants.py`, import it. Never copy-paste.**

## Service Architecture

```
MetricsService (metrics_service.py)
  └── ONLY: get_bowtie_summary, get_stage_timeseries, get_marketing_sankey_metrics
      (legacy methods that read from caches or CRM)

Stage Services (stage_services/*.py)        ← source of truth for stage data
  ├── AttractionStageService.get_metrics()  ← computes + caches attraction data
  ├── CaptureStageService.get_metrics()
  ├── NurtureStageService.get_metrics()
  ├── ... (one per stage)
  ├── StageOverviewService    ← thin cache reader (Tier 1)
  ├── GroupDetailService      ← thin cache reader (Tier 2)
  └── SummaryStageService     ← thin cache reader (Tier 0)
```

**Stage services compute data. MetricsService does NOT compute stage metrics.**

## Progressive Loading Tiers

| Tier | Endpoint | Service | Queries DB? |
|---|---|---|---|
| 0 | `/metrics/summary` | SummaryStageService | No (reads stage caches) |
| 1 | `/metrics/{stage}/overview` | StageOverviewService | No (reads stage cache, falls back to warming) |
| 2 | `/metrics/{stage}/groups/{key}` | GroupDetailService | No (reads stage cache) |
| 3 | `/metrics/{stage}` | `{Stage}StageService` | Yes (computes + caches) |

**Tier 1-2 are cache readers. Only Tier 3 hits the DB. Never add DB queries to overview or group_detail.**

## Cache Warming

`_warm_stage_cache()` in `api/metrics.py` instantiates the correct stage service.
**Never route cache warming through MetricsService.**

## When Adding a New Channel

1. Add definition to `STAGE_CHANNEL_MAP` in `channel_registry.py`
2. If new `channel_type`, add mapping to the correct `*_GROUP_MAP` in `constants.py`
3. If new `provider_name`, add to `PROVIDER_TO_CHANNEL_TYPES` in `channel_registry.py`
4. Add display config in `frontend/.../config/channel-display-registry.ts`
5. No changes needed to overview, group_detail, or MetricsService

## When Adding a New Stage Group

1. Add to the correct `*_GROUP_MAP` in `constants.py`
2. Add to `STAGE_GROUPS` in `constants.py`
3. Update the stage service's `groups` dict and DTO construction
4. Frontend: add filter in the detail panel component

## Prohibited

- Defining `_GROUP_MAP` or any group mapping outside `constants.py`
- Adding `get_*_metrics()` methods to `MetricsService` (use stage services)
- Adding DB queries to `overview_stage.py` or `group_detail.py`
- Hardcoding channel slugs in services (use `ChannelRegistry`)
- Creating a `website` group in attraction (website channels go in `organic_social`)
