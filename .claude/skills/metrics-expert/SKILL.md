---
name: metrics-expert
description: "Growth Studio metrics pipeline expert. Use when: adding channels, metrics, stages, or groups to the analytics module; modifying the progressive loading architecture; changing channel-to-group mappings; debugging missing channels in the dashboard. Triggers: 'nuevo canal', 'nueva metrica', 'agregar metrica', 'canal no aparece', 'growth studio metrics', 'stage service', 'channel registry', 'group mapping'."
---

# Growth Studio Metrics Pipeline

## ⚠️ Read this first

Two files together describe the analytics system. **Both must stay in sync**:

| File | Role |
|---|---|
| `backend/src/modules/analytics/domain/metric_catalog.py` | Semantic catalog: what each metric means, its aggregation type, unit, providers that *can* emit it. **Used at runtime.** |
| `backend/src/modules/analytics/domain/extraction_contract.py` | Extraction contract: which provider actually emits which metric, from which API endpoint, into which channel slug, when, and where it lands. **Documentation + tests.** |
| `docs/etl/extraction-contract.md` | Auto-generated human-readable rendering of the contract. **Read this FIRST when answering "where does X come from".** |

**Workflow rules** for any change to the analytics module live in `.claude/rules/etl-extraction-contract.md`. Read it before you start.

**Mandatory final step of any change** that touches a provider, the pipeline, the scheduler, the workers, or the catalog:

```bash
make extraction-contract                                                # regenerate the markdown
cd backend && .venv/bin/pytest tests/architecture/test_extraction_contract.py -x -q  # verify no drift
```

Both must pass. The provider/pipeline change, the contract update, AND the regenerated Markdown go in the same commit.

## Architecture Overview

```
Frontend (progressive loading)
  Tier 0: Bowtie Summary → SummaryStageService (cache reader)
  Tier 1: Stage Overview → StageOverviewService (cache reader)
  Tier 2: Group Detail  → GroupDetailService (cache reader)
  Tier 3: Full Detail   → {Stage}StageService (DB query + cache write)

Cache warming: overview miss → _warm_stage_cache() → stage service
```

**Key principle: Tiers 0-2 NEVER query the DB. Only Tier 3 stage services hit the DB.**

## Critical Files

| File | Role |
|---|---|
| `stage_services/constants.py` | Single source of truth for ALL shared constants |
| `channel_registry.py` | Channel definitions per stage + provider mapping |
| `stage_services/{stage}_stage.py` | One per stage — computes metrics, writes cache |
| `stage_services/overview_stage.py` | Thin cache reader for Tier 1 |
| `stage_services/group_detail.py` | Thin cache reader for Tier 2 |
| `api/metrics.py` | API routes — uses stage services directly |
| `metrics_service.py` | Legacy (sankey, bowtie summary, timeseries ONLY) |
| `frontend/.../config/channel-display-registry.ts` | Frontend channel display config |
| `frontend/.../config/dashboard-sections.ts` | Deep-link section registry |

## SOP: Adding a New Channel

Example: adding "Pinterest Organic" to attraction stage.

### 1. Channel Registry (`channel_registry.py`)

```python
# In STAGE_CHANNEL_MAP["attraction"], add:
{
    "slug": "pinterest-organic",
    "name": "Pinterest Organic",
    "channel_type": "social",        # existing type → no constants.py change needed
    "source_label": "Pinterest",
    "provider_name": "pinterest",     # new provider → step 2 needed
    "metric_names": ["impressions", "clicks", "saves"],
},
```

### 2. Provider Mapping (`channel_registry.py`) — only if new provider

```python
# In PROVIDER_TO_CHANNEL_TYPES, add:
"pinterest": {"pinterest"},
```

### 3. Group Mapping (`constants.py`) — only if new channel_type

If `channel_type` is new (not already in a GROUP_MAP), add it:

```python
# In ATTRACTION_GROUP_MAP:
"social": "organic_social",  # ← "social" already maps, so pinterest-organic auto-joins organic_social
```

**If the channel_type already exists in the GROUP_MAP, skip this step.**

### 4. Frontend Display Config (`channel-display-registry.ts`)

```typescript
'pinterest-organic': {
    summaryMetrics: [
        { name: 'impressions', label: 'Impresiones' },
        { name: 'clicks', label: 'Clics' },
        { name: 'saves', label: 'Guardados' },
    ],
    primaryMetric: { name: 'impressions', label: 'impresiones' },
},
```

### 5. Tests

- Backend: test in `tests/modules/analytics/` that the channel appears in the correct group
- Frontend: test in `config/__tests__/channel-display-registry.test.ts`

### 6. What you DON'T touch

- `metrics_service.py` — never add stage metrics logic here
- `overview_stage.py` / `group_detail.py` — never modify for new channels
- `_warm_stage_cache()` — no changes for new channels
- No new GROUP_MAP copies anywhere

## SOP: Adding a New Metric to an Existing Channel

1. Add metric name to `metric_names` list in `STAGE_CHANNEL_MAP` (`channel_registry.py`)
2. Ensure ETL extractor produces the metric (provider-specific)
3. If metric needs special aggregation, add to `aggregation_helpers.py`
4. If metric is DERIVED (computed from others), add to `_enrich_with_derived_metrics()` in `attraction_stage.py`
5. Update frontend `channel-display-registry.ts` summaryMetrics
6. No service changes needed — channels auto-discover their metrics from `official_metrics` table

## SOP: Adding a New Stage Group

Example: adding "ai_search" group to attraction.

### 1. Constants (`constants.py`)

```python
# In ATTRACTION_GROUP_MAP, add:
"ai_search": "ai_search",

# In STAGE_GROUPS["attraction"], add:
("ai_search", "Busqueda IA", "ai_search"),
```

### 2. Stage Service (`attraction_stage.py`)

```python
# In groups dict:
groups: dict[str, list[ChannelMetricDTO]] = {
    "organic_social": [],
    "ga4_search": [],
    "paid": [],
    "outbound": [],
    "ai_search": [],  # ← new group
}

# In result DTO construction — update AttractionDetailDTO to include new field
```

### 3. Stage DTO (`attraction_dto.py`)

```python
class AttractionDetailDTO(BaseModel):
    organic_social: TrafficGroupDTO
    ga4_search: TrafficGroupDTO
    paid: TrafficGroupDTO
    outbound: TrafficGroupDTO
    ai_search: TrafficGroupDTO | None = None  # ← new optional group
```

### 4. Frontend

- Add group filter in `AttractionCaptureDetail.tsx`
- Add `LazyChannelGroup` for the new group

## SOP: Adding a New Funnel Stage

This is rare (8 stages cover the full Bowtie). If needed:

1. Create `stage_services/{name}_stage.py` with `get_metrics()` method
2. Create DTO in `application/dto/{name}_dto.py`
3. Add constants to `constants.py` (GROUP_MAP if applicable, STAGE_GROUPS entry)
4. Add API endpoint in `api/metrics.py` using the new stage service
5. Add to `_warm_stage_cache()` in `api/metrics.py`
6. Add to `FunnelStage` enum in `api/metrics.py`
7. Export from `stage_services/__init__.py`

## Debugging: Channel Not Appearing

Checklist (in order):

1. **Channel in registry?** → Check `STAGE_CHANNEL_MAP` in `channel_registry.py`
2. **Provider connected?** → Check `PROVIDER_TO_CHANNEL_TYPES` + tenant's `channel_connections` table
3. **Group mapping exists?** → Check `constants.py` for the `channel_type` → group mapping
4. **Cache stale?** → `docker exec visionarias_redis redis-cli DEL "metrics:{tenant_id}:{stage}:last_30_days"`
5. **Stage service uses constants.py?** → Verify import, never local copy
6. **Overview reads the group?** → Check `STAGE_GROUPS` in `constants.py` includes the group
7. **Frontend filters include it?** → Check detail panel's `useMemo` filter for `groupKey`

## Anti-Patterns (PROHIBITED)

- Defining group mappings outside `constants.py`
- Adding `get_*_metrics()` to `MetricsService` (it's legacy — use stage services)
- Putting DB queries in `overview_stage.py` or `group_detail.py`
- Hardcoding channel slugs in services instead of using `ChannelRegistry`
- Creating duplicate constant dictionaries "for convenience"
- Modifying `MetricsService` for new stage metrics features

## Project invariants (read on demand)

- `references/etl-extraction-contract.md` — SSoT 2-files, 5-step workflow tras provider/pipeline change, best practices
- `references/analytics-metrics.md` — stage services, group mappings, tiers progressive loading, agregar channel
- `references/data-reliability.md` — 4-layer verification protocol, trigger matrix, agregar provider
