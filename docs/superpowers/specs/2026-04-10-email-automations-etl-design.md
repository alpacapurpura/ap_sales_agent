# Email Automations ETL + Service — Design Spec

**Date:** 2026-04-10
**Status:** Approved (conversational)

## Problem

The Automatizaciones tab in the Email Intelligence Hub always shows "Sin automatizaciones" because:

1. `PROVIDER_STAGES["mailerlite"]` only includes `["capture", "nurture"]` — the `"delivery"` stage (where `_extract_automations` runs) is never invoked
2. Even if invoked, the existing `_extract_automations` only saves **aggregate** metrics (totals across all automations), not per-automation detail
3. The service `get_automations()` always returns `automations=[]` with a TODO comment

Meanwhile, the tenant has **8 automations** (7 active) in Mailerlite with real data.

## Design

Follow the **same pattern as campaigns**: ETL saves per-item rows with `campaign_id`, service reads and groups them, frontend already handles the list.

### 1. ETL: Rewrite `_extract_automations`

**Where it runs:** Within the `nurture` stage extraction (not a separate `delivery` stage). Automations are a delivery mechanism for nurture, not a separate funnel stage.

**Change in `extract_data()`:** When `stage == "nurture"`, after extracting campaigns, also call `_extract_automations` with `slug = "email-nurture"`.

**What `_extract_automations` saves per automation:**

Each automation gets multiple `ExtractedMetric` rows with `campaign_id = str(automation_id)`:

| metric_name | value | unit | source |
|---|---|---|---|
| `emails_sent` | stats.sent | count | extra |
| `open_rate` | stats.open_rate.float * 100 | percentage | extra |
| `click_rate` | stats.click_rate.float * 100 | percentage | extra |
| `click_to_open_rate` | stats.click_to_open_rate.float * 100 | percentage | extra |
| `unsubscribes` | stats.unsubscribes_count | count | extra |

**`extra` metadata per row:**
```json
{
  "source": "automation",
  "automation_name": "BIENVENIDA: nuevas inscritas",
  "automation_status": "active",
  "automation_type": "welcome",
  "subscribers_in_queue": 8,
  "completed_subscribers": 11,
  "steps_count": 2
}
```

**Automation type classification:** Infer from name keywords:
- "bienvenida" / "welcome" → `welcome`
- "nurtur" / "nutrición" → `nurture`
- "re-engagement" / "reactivación" → `reengagement`
- "post-compra" / "post compra" → `post_compra`
- default → `workflow`

**No `/automations/{id}/activity` call needed.** Stats come directly in the automation object from `GET /automations`, saving API calls and rate limit budget.

**`metric_date`:** Use `end_date` (snapshot of the day). Stats are cumulative — delta vs previous period comes from comparing snapshots.

### 2. Service: Rewrite `get_automations()`

Read from `official_metrics` where `channel_slug = "email-nurture"` and `extra->>'source' = 'automation'`, grouped by `campaign_id` (= automation_id).

Build `EmailAutomationDTO` list from the grouped rows, extracting metadata from `extra`.

KPIs: Compute from the automation rows (total sent, avg open rate, avg click rate, completion rate).

### 3. DTOs: No changes needed

`EmailAutomationDTO` and `EmailAutomationsResponseDTO` already have the right fields. The frontend types and mappers already match.

### 4. Frontend: No changes needed

`MailAutomatizacionesTab` already renders the automation list, KPIs, and comparison table. It just needs data.

## Data Flow

```
Mailerlite API: GET /automations?filter[enabled]=true&limit=100
  → _extract_automations: per-automation rows → official_metrics (campaign_id=auto_id, extra.source=automation)
    → get_automations: SELECT ... WHERE source='automation' GROUP BY campaign_id
      → EmailAutomationsResponseDTO { kpis, automations[] }
        → Frontend: MailAutomatizacionesTab renders table + KPIs
```

## Risks / Notes

- Automation stats are **cumulative** (lifetime), not per-period. The ETL saves daily snapshots; the service shows the latest snapshot for the period. Delta calculation compares current vs previous-period snapshot.
- Disabled automations (`enabled=false`) are excluded by the API filter. Only active ones appear.
- Rate limit: one API call total (`GET /automations`), no per-automation calls needed.
