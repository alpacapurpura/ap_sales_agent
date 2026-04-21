---
globs: "{backend/src/modules/analytics/**/*.py,frontend/src/features/growth-studio/**/*.{ts,tsx}}"
description: Growth Studio metrics pipeline architecture — stage services, cache, progressive loading
---

# Analytics Metrics Architecture

> ETL extraction questions (*what/where/when*) → `docs/etl/extraction-contract.md` + `.claude/rules/etl-extraction-contract.md`.
>
> **This file:** runtime metrics pipeline — stage services, group mappings, channel registry, progressive loading.

Rules prevent duplication bug (two divergent `_GROUP_MAP` hid `website-total`).

## SSoT

| Concern | Canonical | Never dup in |
|---|---|---|
| Group mappings (`ATTRACTION_GROUP_MAP`, etc.) | `stage_services/constants.py` | metrics_service.py, individual stage services |
| Stage group defs (`STAGE_GROUPS`) | `stage_services/constants.py` | overview_stage.py, group_detail.py |
| Display name map | `stage_services/constants.py` | individual stage services |
| Error messages | `stage_services/constants.py` | individual stage services |
| Channel defs per stage | `channel_registry.py` → `STAGE_CHANNEL_MAP` | hardcoded en services |
| Provider→channel-type | `channel_registry.py` → `PROVIDER_TO_CHANNEL_TYPES` | hardcoded en services |

**Constant existe en `constants.py` → import. Nunca copy-paste.**

## Service Architecture

```
MetricsService (metrics_service.py)
  └── ONLY: get_bowtie_summary, get_stage_timeseries, get_marketing_sankey_metrics
      (legacy — reads caches/CRM)

Stage Services (stage_services/*.py)   ← SSoT stage data
  ├── AttractionStageService.get_metrics()  ← computes + caches
  ├── CaptureStageService, NurtureStageService, ...
  ├── StageOverviewService    ← thin cache reader (Tier 1)
  ├── GroupDetailService      ← thin cache reader (Tier 2)
  └── SummaryStageService     ← thin cache reader (Tier 0)
```

**Stage services compute. MetricsService NO computa stage metrics.**

## Progressive Loading Tiers

| Tier | Endpoint | Service | DB? |
|---|---|---|---|
| 0 | `/metrics/summary` | SummaryStageService | No (reads caches) |
| 1 | `/metrics/{stage}/overview` | StageOverviewService | No (cache, fallback warm) |
| 2 | `/metrics/{stage}/groups/{key}` | GroupDetailService | No (reads cache) |
| 3 | `/metrics/{stage}` | `{Stage}StageService` | Yes (computes+caches) |

**Tier 1-2 = cache readers. Only Tier 3 hits DB.** Nunca agregar DB queries a overview/group_detail.

## Cache Warming

`_warm_stage_cache()` en `api/metrics.py` instancia stage service correcto. Nunca route via MetricsService.

## Agregar Channel

1. Def en `STAGE_CHANNEL_MAP` (`channel_registry.py`)
2. Nuevo `channel_type` → agregar a `*_GROUP_MAP` en `constants.py`
3. Nuevo `provider_name` → agregar a `PROVIDER_TO_CHANNEL_TYPES`
4. FE config: `frontend/.../config/channel-display-registry.ts`
5. No changes overview/group_detail/MetricsService

## Agregar Stage Group

1. Agregar a `*_GROUP_MAP` en `constants.py`
2. Agregar a `STAGE_GROUPS` en `constants.py`
3. Update stage service `groups` dict + DTO
4. FE: filter en detail panel

## Prohibido

- `_GROUP_MAP`/group mapping fuera de `constants.py`
- `get_*_metrics()` methods en `MetricsService` (usar stage services)
- DB queries en `overview_stage.py`/`group_detail.py`
- Hardcodear channel slugs (usar `ChannelRegistry`)
- `website` group en attraction (website channels van en `organic_social`)
