---
globs: "{backend/src/modules/analytics/**/*.py,frontend/src/features/growth-studio/**/*.{ts,tsx}}"
description: Stub — invoca metrics-expert skill
---

# Analytics Metrics Architecture

SSoT constants en `stage_services/constants.py` (group mappings, stage groups, display names, error messages). Channel registry en `channel_registry.py`. Stage services SSoT data — MetricsService NO computa stage metrics.

Tiers progressive loading: 0 summary, 1 overview (cache), 2 group-detail (cache), 3 stage (DB).

Detalle (service architecture, agregar channel/group, prohibido) en `metrics-expert` skill → `references/analytics-metrics.md`.

**No-skip:**
- ❌ `_GROUP_MAP` fuera `constants.py`
- ❌ `get_*_metrics()` en MetricsService (usar stage services)
- ❌ DB queries en `overview_stage.py`/`group_detail.py`
- ❌ Hardcodear channel slugs (usar `ChannelRegistry`)
