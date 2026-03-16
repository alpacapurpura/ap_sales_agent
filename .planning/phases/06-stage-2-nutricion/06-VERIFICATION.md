---
phase: 06-stage-2-nutricion
verified: 2026-03-16T07:30:00Z
status: gaps_found
score: 4/5 success criteria verified
re_verification: false
gaps:
  - truth: "Mailerlite newsletter engagement data (open_rate, click_rate) is integrated and contributes to lead scoring"
    status: partial
    reason: "Webhook pipeline (NUT-04 real-time path) is fully implemented and substantive. However the 6-hour ETL backup sync — intended to recover missed webhook events — is permanently a no-op: MailerLiteConnector.get_recent_campaign_activity() is not implemented. The task has a defensive hasattr() check at line 203-210 of tasks.py that silently skips ALL tenants indefinitely. The ETL backup path is registered in cron_jobs but will never produce any synced events."
    artifacts:
      - path: "backend/src/modules/analytics/workers/tasks.py"
        issue: "run_mailerlite_etl_sync() silently skips all tenants because MailerLiteConnector.get_recent_campaign_activity() is missing (lines 202-210)"
      - path: "backend/src/modules/connections/infrastructure/marketing_connectors/mailerlite.py"
        issue: "Only defines verify_connection, sync_contacts, sync_events — no get_recent_campaign_activity method"
    missing:
      - "Implement MailerLiteConnector.get_recent_campaign_activity(hours: int) -> List[Dict] using Mailerlite Campaigns Activity API"
      - "Or remove the ETL backup path from SUMMARY claims and NUT-04 acceptance criteria if it is intentionally deferred"
human_verification:
  - test: "NurtureDetail panel renders in browser"
    expected: "Clicking NUTRICION stage card shows panel with Total MQLs / CONVERSION / COSTO POR MQL header KPIs, MiniFunnel Leads->MQLs arrow, Retargeting Omnichannel accordion group with Meta/Google/TikTok rows, Automatizacion accordion group with Mailerlite row and AI SDR 'Proximamente' badge"
    why_human: "Visual layout, accordion open/close behavior, and badge rendering require browser inspection"
  - test: "CampaignDrillDown collapsible behavior"
    expected: "When campaigns array is non-empty, clicking a retargeting or Mailerlite ChannelRow expands a collapsible sub-list with pl-8 indented rows showing campaign name and metrics; ChevronDown rotates 180 degrees"
    why_human: "Collapsible toggle behavior and chevron animation cannot be verified statically — requires mock data with campaigns populated"
---

# Phase 06: Stage 2 Nutricion Verification Report

**Phase Goal:** Business owner sees which nurturing activities are converting leads into marketing-qualified prospects
**Verified:** 2026-03-16T07:30:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Nurturing detail panel shows two groups: Retargeting Omnichannel and Automation | VERIFIED | NurtureDetail.tsx renders ChannelGroup with title="Retargeting Omnichannel" (groupType="retargeting") and title="Automatizacion" (groupType="automation"); MetricsDashboard routes activeStage === 'NUTRICION' to NurtureDetail |
| 2 | `/metrics/nurturing` endpoint returns MQL conversion count based on lead_score threshold crossing | VERIFIED | GET /metrics/nurturing in metrics.py calls MetricsService.get_nurturing_metrics(); NurtureMetricsRepository.count_new_mqls() queries lifecycle_transitions WHERE to_stage = MQL; endpoint returns NurtureDetailDTO with header_kpis.total_mqls |
| 3 | Retargeting metrics sourced from Meta/Google/TikTok APIs filtered to MOFU campaigns only | VERIFIED | MetaProvider._extract_meta_retargeting() filters by custom_audiences; GoogleAdsProvider._aggregate_retargeting() uses name heuristic; TikTokProvider._extract_retargeting() uses name heuristic; extract_metrics(stage='nurturing') routes to retargeting path in all three providers |
| 4 | Mailerlite newsletter engagement data (open_rate, click_rate) integrated and contributes to lead scoring | PARTIAL | Webhook path is complete: handle_mailerlite_webhook() creates journey_events and calls lifecycle_svc.recalculate_score(). However the 6-hour ETL backup sync (run_mailerlite_etl_sync) is permanently a no-op because MailerLiteConnector.get_recent_campaign_activity() does not exist. The cron job is registered but silently skips all tenants at runtime. |
| 5 | Conversion rate (Leads to MQLs) and cost of nurturing per MQL calculated and displayed | VERIFIED | StageCostService.calculate_cost_per_mql() computes total cost/MQL; get_group_cost_per_mql() provides per-group breakdown; NurtureDetail.tsx displays conversionRate and costPerMql in header KPIs; ChannelGroup buildSummary for 'retargeting' and 'automation' cases show cost_per_mql from totals |

**Score:** 4/5 truths verified (1 partial due to ETL backup gap)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/src/modules/analytics/application/dto/nurture_dto.py` | NurtureDetailDTO, NurtureHeaderKpisDTO, CampaignMetricDTO | VERIFIED | 49 lines; all three DTOs present; reuses TrafficGroupDTO, MiniFunnelDTO |
| `backend/src/modules/analytics/infrastructure/repositories/nurture_repository.py` | MQL counting from lifecycle_transitions | VERIFIED | 190 lines; count_new_mqls, count_leads_in_period, get_mql_sources, count_email_events, count_followup_events — all with tenant_id isolation |
| `backend/src/modules/analytics/application/services/stage_cost_service.py` | Per-group cost/MQL breakdown | VERIFIED | 145 lines; get_channel_costs, get_retargeting_spend, calculate_cost_per_mql, get_group_cost_per_mql for retargeting and automation groups |
| `backend/src/modules/analytics/api/metrics.py` | GET /metrics/nurturing endpoint | VERIFIED | Route present at line 81; calls MetricsService.get_nurturing_metrics(user.tenant_id); response_model=NurtureDetailDTO |
| `backend/src/modules/connections/api/marketing_webhooks.py` | Mailerlite webhook pipeline | VERIFIED | handle_mailerlite_webhook() at /mailerlite/{tenant_id} creates journey_events and triggers recalculate_score; legacy endpoint preserved |
| `backend/src/modules/analytics/workers/tasks.py` | run_mailerlite_etl_sync 6h backup | STUB | Function exists and is registered in cron, but hasattr() guard at line 203 means it will never sync events — MailerLiteConnector.get_recent_campaign_activity() is unimplemented |
| `frontend/src/features/marketing-studio/types/metrics.ts` | NurtureHeaderKpis, CampaignMetric, NurtureDetail types; GroupType extended | VERIFIED | All types present at lines 91-115; GroupType union includes 'retargeting' and 'automation' at line 27 |
| `frontend/src/features/marketing-studio/api/metrics-api.ts` | getNurtureDetail method, mapNurtureResponse | VERIFIED | getNurtureDetail fetches from /api/v1/analytics/metrics/nurturing; mapNurtureResponse maps all fields correctly; falls back to MOCK_NURTURE_DETAIL |
| `frontend/src/features/marketing-studio/api/metrics-mock-data.ts` | MOCK_NURTURE_DETAIL with cost_per_mql | VERIFIED | MOCK_NURTURE_DETAIL at line 355; retargeting totals include cost_per_mql: 8.75; automation totals include cost_per_mql: 3.75; NUTRICION hasDetail: true at line 29 |
| `frontend/src/features/marketing-studio/hooks/useNurtureDetail.ts` | useNurtureDetail React Query hook | VERIFIED | Exports useNurtureDetail; queryKey ['nurture-detail']; calls metricsApi.getNurtureDetail(token); staleTime 5 min |
| `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/NurtureDetail.tsx` | NurtureDetail panel with header KPIs, MiniFunnel, groups | VERIFIED | 93 lines; renders TOTAL MQLs / CONVERSION / COSTO POR MQL; MiniFunnel; ChannelGroup Retargeting Omnichannel + Automatizacion; loading skeleton + error state |
| `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/CampaignDrillDown.tsx` | Collapsible campaign sub-list | VERIFIED | 87 lines; uses shadcn Collapsible; renders normally when campaigns.length === 0; expands with pl-8/bg-muted/20 when campaigns populated; ChevronDown rotation |
| `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelRow.tsx` | CampaignDrillDown wiring, icons, labels, AI SDR badge | VERIFIED | Imports CampaignDrillDown; shouldWrapWithDrillDown for retargeting/email channels; CHANNEL_ICONS contains meta-retargeting, google-retargeting, tiktok-retargeting, ai-sdr; METRIC_LABELS contains emails_sent, open_rate, click_rate, followups, response_rate; AI SDR Proximamente badge |
| `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/ChannelGroup.tsx` | retargeting/automation buildSummary cases | VERIFIED | case 'retargeting' with cost_per_mql at line 49; case 'automation' with cost_per_mql at line 54 |
| `frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx` | NUTRICION routing to NurtureDetail | VERIFIED | Imports NurtureDetail at line 10; activeStage === 'NUTRICION' condition at line 44 routes to NurtureDetail |
| `frontend/src/components/ui/collapsible.tsx` | shadcn Collapsible component | VERIFIED | Uses @radix-ui/react-collapsible; exports Collapsible, CollapsibleTrigger, CollapsibleContent |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| MetricsDashboard.tsx | NurtureDetail.tsx | activeStage === 'NUTRICION' conditional | WIRED | Line 44 confirmed |
| useNurtureDetail.ts | metrics-api.ts getNurtureDetail() | React Query queryFn | WIRED | queryFn calls metricsApi.getNurtureDetail(token) |
| ChannelRow.tsx | CampaignDrillDown.tsx | shouldWrapWithDrillDown for retargeting/email | WIRED | Import at line 10; wrapping at lines 250-256 |
| ChannelGroup.tsx | buildSummary() | case 'retargeting' and case 'automation' | WIRED | Lines 49-58 |
| metrics.py /nurturing | MetricsService.get_nurturing_metrics() | FastAPI dependency injection | WIRED | Line 94 confirmed |
| MetricsService | NurtureMetricsRepository | Direct instantiation in get_nurturing_metrics() | WIRED | Line 650; count_new_mqls called at line 651 |
| MetricsService | StageCostService | Direct instantiation; get_group_cost_per_mql called | WIRED | Lines 655-668 |
| handle_mailerlite_webhook | LifecycleService.recalculate_score | Called after journey_event creation | WIRED | Line 115 confirmed |
| run_mailerlite_etl_sync | MailerLiteConnector.get_recent_campaign_activity | hasattr() guard at line 203 | NOT_WIRED | Method does not exist on connector; guard causes permanent silent skip |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| NUT-01 | 06-02-PLAN.md | Detail panel showing Retargeting Omnichannel and Automation groups | SATISFIED | NurtureDetail.tsx renders both groups; MetricsDashboard routes NUTRICION stage |
| NUT-02 | 06-01-PLAN.md | Backend endpoint /metrics/nurturing tracking MQL conversion | SATISFIED | GET /metrics/nurturing returns NurtureDetailDTO; NurtureMetricsRepository counts lifecycle_transitions to MQL stage |
| NUT-03 | 06-01-PLAN.md | Retargeting metrics from Meta/Google/TikTok APIs filtered to MOFU campaigns | SATISFIED | All three providers implement stage='nurturing' path with retargeting filters |
| NUT-04 | 06-01-PLAN.md | Mailerlite API integration for newsletter engagement contributing to lead scoring | PARTIALLY SATISFIED | Webhook pipeline is complete and functional. ETL backup sync (6h recovery) is permanently inoperative — MailerLiteConnector.get_recent_campaign_activity() not implemented. Webhook delivery failures will not be recovered. |
| NUT-05 | 06-01-PLAN.md + 06-02-PLAN.md | Conversion rate Leads->MQLs with cost of nurturing per MQL | SATISFIED | StageCostService calculates cost_per_mql; NurtureDetail.tsx displays header KPIs; ChannelGroup summaries show per-group cost/MQL |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/src/modules/analytics/workers/tasks.py` | 202-210 | `if not hasattr(connector, "get_recent_campaign_activity"): continue` | Warning | ETL backup sync silently no-ops for all tenants; missed webhook events are never recovered |
| `backend/src/modules/connections/api/marketing_webhooks.py` | 36 | `# TODO: Use Communication Service or Event Bus to handle this` (in Shopify handler) | Info | Unrelated to NUT requirements; pre-existing Shopify TODO |

### Human Verification Required

#### 1. NurtureDetail Panel Visual Rendering

**Test:** Start the frontend container (`docker compose up -d`), navigate to Growth Studio metrics dashboard, click the NUTRICION stage card.
**Expected:** Panel opens showing three header KPIs (TOTAL MQLs, CONVERSION, COSTO POR MQL), a MiniFunnel arrow from Leads to MQLs, an expanded "Retargeting Omnichannel" accordion with Meta/Google/TikTok retargeting rows, and an expanded "Automatizacion" accordion with Mailerlite row (with metrics) and AI SDR row (with "Proximamente" badge).
**Why human:** Visual layout correctness, accordion defaultOpen behavior, and badge rendering cannot be verified statically.

#### 2. CampaignDrillDown Collapsible Behavior with Campaign Data

**Test:** Temporarily modify MOCK_NURTURE_DETAIL to add a `campaigns` array to the meta-retargeting channel mock, then click that channel row.
**Expected:** ChevronDown appears and rotates 180 degrees on click; sub-list expands with pl-8 indented rows showing campaign name and metrics on bg-muted/20 background.
**Why human:** Toggle animation and visual indentation require browser inspection; static analysis cannot verify Collapsible expand behavior.

### Gaps Summary

**1 gap blocks full NUT-04 compliance:**

The ETL backup sync for Mailerlite (`run_mailerlite_etl_sync`) is registered as a 6-hour cron job and appears fully wired in settings.py. However, the function body at lines 202-210 of `tasks.py` contains a defensive guard:

```python
if not hasattr(connector, "get_recent_campaign_activity"):
    logger.warning("MailerLiteConnector.get_recent_campaign_activity() not implemented yet...")
    continue
```

`MailerLiteConnector` in `marketing_connectors/mailerlite.py` only defines `verify_connection`, `sync_contacts`, and `sync_events`. The `get_recent_campaign_activity` method was never implemented. The cron job will log a warning for every active Mailerlite tenant and produce zero synced events — indefinitely.

This means the "6-hour backup sync ensures missed webhook events are recovered" claim in the SUMMARY is false. The real-time webhook path works correctly and is the only functional route for Mailerlite engagement scoring.

**Impact on goal:** The business owner's lead scoring will still reflect Mailerlite engagement (via webhooks), but webhook delivery failures (downtime, Mailerlite retries) will not be recovered by the ETL fallback. Under normal conditions this gap is invisible; it only materializes on webhook delivery failure.

**Recommended resolution:** Implement `MailerLiteConnector.get_recent_campaign_activity(hours: int)` using the Mailerlite Campaigns API subscriber activity endpoints, or explicitly defer the ETL backup to a later phase and remove it from NUT-04 acceptance criteria.

---

_Verified: 2026-03-16T07:30:00Z_
_Verifier: Claude (gsd-verifier)_
