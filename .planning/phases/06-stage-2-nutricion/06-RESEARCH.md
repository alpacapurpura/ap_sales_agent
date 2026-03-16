# Phase 6: Stage 2 Nutricion - Research

**Researched:** 2026-03-16
**Domain:** Marketing funnel analytics (nurturing/MOFU stage), ad platform retargeting APIs, email marketing webhooks, lead scoring
**Confidence:** HIGH

## Summary

Phase 6 builds the Nurturing (Stage 2) detail panel for the Growth Studio metrics dashboard. This phase follows the exact patterns established in Phases 4-5 (Attraction and Capture): a new `/metrics/nurturing` API endpoint, a NurtureDetailDTO, a NurtureMetricsRepository for CRM-based MQL counts, extension of existing ad platform providers with retargeting campaign filtering, Mailerlite webhook integration for real-time email engagement scoring, and a frontend NurtureDetail panel with collapsable campaign drill-down.

The primary technical challenges are: (1) classifying ad campaigns as retargeting vs. cold using Custom Audience detection per platform API, (2) integrating Mailerlite webhooks for email_opened/email_clicked events that feed into lead scoring, (3) building a new CampaignDrillDown frontend component for expandable campaign-level metrics, and (4) extending the cost service for stage-aware cost splitting.

**Primary recommendation:** Follow the established Phase 4-5 patterns exactly (DTO, repository, service method, API endpoint, frontend hook+panel). The retargeting classification should be implemented inside existing providers via a `stage` parameter, and Mailerlite webhook integration should create journey_events that trigger the existing LifecycleService.recalculate_score() flow.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Audience-first, objective-second** classification for retargeting campaigns: Custom Audience = retargeting regardless of objective. Manual override available in settings.
- **Two channel groups**: Retargeting Omnichannel (meta-retargeting, google-retargeting, tiktok-retargeting) and Automatizacion (mailerlite, ai-sdr)
- **Retargeting metrics per channel**: Reach + Clicks + Spend (no Conversions -- those belong in Stage 3)
- **Reuse existing providers** with `stage` filter parameter (no new provider classes)
- **Mailerlite metrics**: Emails Sent + Open Rate + Click Rate with per-campaign drill-down
- **Mailerlite -> Lead Scoring**: Webhook real-time + ETL backup (6h) dual strategy
- **AI SDR**: Build structure with "Proximamente" badge if no data; show real message_sent events if available
- **ManyChat = infrastructure**, not visible channel. Aggregate metrics to corresponding messaging channels
- **Mini Funnel**: Leads -> MQLs pattern (MQL = lifecycle_stage >= MQL AND transitioned in period)
- **Cost tracking**: Extend CaptureCostService to generic StageCostService. Per-group cost breakdown in group headers, combined cost/MQL in panel header
- **Cost sources**: Retargeting spend AUTO from APIs, Mailerlite subscription MANUAL, AI SDR token cost AUTO, ManyChat licensing MANUAL (shared with Stage 1)
- **No organic content** in Stage 2 (measured in Stage 0, cannot attribute to specific leads)

### Claude's Discretion
- Exact Custom Audience detection logic per platform API field mapping
- Campaign objective -> stage mapping edge cases
- Mailerlite webhook endpoint implementation and event validation
- ManyChat API integration for sequence metrics extraction
- ETL backup sync implementation details
- Collapsable component design (animation, state management)
- Available channels list (which non-connected nurturing platforms to show)
- Error/stale UX casuistry for nurturing-specific scenarios
- ChannelCostSettingModel extension for stage-aware cost assignment

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NUT-01 | Detail panel showing two groups: Retargeting Omnichannel and Automation | Reuse ChannelGroup/ChannelRow pattern from Phase 5; add new GroupType values `retargeting` and `automation`; new NurtureDetail component + CampaignDrillDown component |
| NUT-02 | Backend endpoint `/metrics/nurturing` tracking MQL conversion via lead_score threshold crossing | New `get_nurturing_metrics()` method in MetricsService; NurtureMetricsRepository querying lifecycle_transitions for MQL threshold crossings (score >= 40) in period |
| NUT-03 | Retargeting metrics from Meta/Google/TikTok APIs filtered to MOFU campaigns | Extend existing providers with `stage` parameter; Custom Audience detection in adset targeting (Meta: `custom_audiences` field, Google: UserList criterion, TikTok: Custom Audiences) |
| NUT-04 | Mailerlite API integration for newsletter engagement contributing to lead scoring | Webhook endpoint `/webhooks/mailerlite` receiving campaign.open/campaign.click events; creates journey_events (email_opened/email_clicked); triggers LifecycleService.recalculate_score(); ETL backup every 6h |
| NUT-05 | Conversion rate (Leads to MQLs) and cost of nurturing per MQL | Extend CaptureCostService -> StageCostService; Cost per MQL = total nurturing spend / new MQLs; per-group cost breakdown |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | existing | `/metrics/nurturing` endpoint | Project stack |
| SQLAlchemy 2.0 | existing | NurtureMetricsRepository, lifecycle_transitions queries | Project stack, async |
| Pydantic v2 | existing | NurtureDetailDTO, NurtureHeaderKpisDTO | Project stack |
| httpx | existing | Mailerlite webhook validation, API calls | Already used by MailerliteConnector |
| React/Next.js 14 | existing | NurtureDetail panel | Project stack |
| TanStack Query | existing | useNurtureDetail hook with 5-min staleTime | Established pattern |
| shadcn/Radix UI | existing | Accordion, Collapsible, Badge components | Project stack |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Redis | existing | MetricsCache 300s TTL for nurture stage | Same pattern as capture |
| lucide-react | existing | ChevronDown icon for drill-down indicator | Already in project |

### Alternatives Considered
None -- all libraries are locked by project conventions and Phase 4-5 precedent.

**Installation:**
```bash
# No new packages needed. All dependencies already in project.
# shadcn Collapsible may need to be added:
npx shadcn-ui@latest add collapsible
```

## Architecture Patterns

### Recommended Project Structure (new/modified files)
```
backend/src/modules/analytics/
  api/metrics.py                      # ADD /metrics/nurturing endpoint
  application/dto/nurture_dto.py      # NEW: NurtureDetailDTO, NurtureHeaderKpisDTO
  application/services/
    metrics_service.py                # ADD get_nurturing_metrics() method
    stage_cost_service.py             # NEW: generic StageCostService (extends CaptureCostService pattern)
    channel_registry.py               # MODIFY: expand STAGE_CHANNEL_MAP["nurture"]
  infrastructure/repositories/
    nurture_repository.py             # NEW: MQL transition counts from lifecycle_transitions
  infrastructure/providers/
    meta_provider.py                  # MODIFY: add stage parameter for retargeting filtering
    google_ads_provider.py            # MODIFY: add stage parameter for remarketing filtering
    tiktok_provider.py                # MODIFY: add stage parameter for retargeting filtering

backend/src/modules/connections/
  api/marketing_webhooks.py           # ADD Mailerlite webhook endpoint (or new file)

frontend/src/features/marketing-studio/
  types/metrics.ts                    # ADD NurtureDetail, NurtureHeaderKpis, CampaignMetric types
  api/metrics-api.ts                  # ADD getNurtureDetail(), MOCK_NURTURE_DETAIL
  hooks/useNurtureDetail.ts           # NEW: React Query hook
  components/metrics-dashboard/
    detail-panels/NurtureDetail.tsx    # NEW: main detail panel
    channel-widgets/
      CampaignDrillDown.tsx           # NEW: collapsable campaign sub-list
      ChannelGroup.tsx                # MODIFY: add retargeting/automation summary builders
      ChannelRow.tsx                  # MODIFY: add channel icons, metric labels, drill-down trigger
    MetricsDashboard.tsx              # MODIFY: add NUTRICION routing case
```

### Pattern 1: Provider Stage Filtering (Retargeting Classification)
**What:** Extend `extract_metrics()` on existing providers with an optional `stage` parameter. When `stage="nurturing"`, filter to MOFU campaigns (Custom Audience detection). When `stage="attraction"` (default), return TOFU campaigns.
**When to use:** Every time a provider extracts metrics for a specific funnel stage.
**Example:**
```python
# In MetaProvider._extract_meta_ads:
async def _extract_meta_ads(self, client, credentials, start_date, end_date, stage="attraction"):
    # Step 1: Fetch campaigns at adset level to get targeting
    # Step 2: For each adset, check targeting.custom_audiences
    # Step 3: If custom_audiences present -> retargeting (nurturing)
    #         If no custom_audiences -> classify by objective (ODAX enum)

    # Meta API: GET /act_{ad_account_id}/adsets?fields=targeting,campaign{objective}
    # targeting.custom_audiences = [{"id": "...", "name": "..."}]

    if stage == "nurturing":
        # Filter to adsets WITH custom_audiences
        filtered = [a for a in adsets if a.get("targeting", {}).get("custom_audiences")]
        channel_slug = "meta-retargeting"
    else:
        # Filter to adsets WITHOUT custom_audiences (cold traffic)
        filtered = [a for a in adsets if not a.get("targeting", {}).get("custom_audiences")]
        channel_slug = "meta-ads"
```

### Pattern 2: Mailerlite Webhook -> Journey Event -> Score Recalculation
**What:** Webhook endpoint receives Mailerlite events, creates journey_events, triggers score recalculation.
**When to use:** Real-time email engagement scoring.
**Example:**
```python
# /webhooks/mailerlite endpoint
@router.post("/webhooks/mailerlite")
async def handle_mailerlite_webhook(payload: dict, db: Session = Depends(get_db)):
    event_type = payload.get("type")  # "campaign.open" or "campaign.click"
    subscriber = payload.get("subscriber", {})
    email = subscriber.get("email")

    # 1. Find customer profile by email
    profile = customer_repo.find_by_email(tenant_id, email)
    if not profile:
        return {"status": "ignored", "reason": "unknown_subscriber"}

    # 2. Create journey_event
    event_name = "email_opened" if "open" in event_type else "email_clicked"
    journey_event = JourneyEventModel(
        profile_id=profile.id,
        tenant_id=tenant_id,
        event_name=event_name,
        event_type="track",
        properties={"campaign_id": payload.get("campaign", {}).get("id")},
    )
    db.add(journey_event)

    # 3. Recalculate score (triggers MQL transition if threshold crossed)
    lifecycle_service = LifecycleService(db)
    lifecycle_service.recalculate_score(profile.id, tenant_id)
    db.commit()
```

### Pattern 3: NurtureMetricsRepository (CRM-based MQL counting)
**What:** Query lifecycle_transitions for profiles that crossed the MQL threshold (score >= 40) in the period.
**When to use:** Building the mini funnel and header KPIs.
**Example:**
```python
class NurtureMetricsRepository:
    def count_new_mqls(self, tenant_id: UUID, start_date, end_date) -> int:
        """Count profiles that transitioned TO MQL stage within period."""
        from src.modules.crm.infrastructure.repositories.lifecycle_repository import LifecycleRepository
        # Query lifecycle_transitions where to_stage = 'mql' AND created_at in range
        stmt = (
            select(func.count(func.distinct(LifecycleTransitionModel.profile_id)))
            .where(
                LifecycleTransitionModel.tenant_id == tenant_id,
                LifecycleTransitionModel.to_stage == LifecycleStage.MQL,
                LifecycleTransitionModel.created_at >= start_date,
                LifecycleTransitionModel.created_at <= end_date,
            )
        )
        return self.db.execute(stmt).scalar() or 0
```

### Anti-Patterns to Avoid
- **Direct CRM model import in analytics service layer:** Use NurtureMetricsRepository as DDD boundary (same as CaptureMetricsRepository)
- **Creating new provider classes for retargeting:** Reuse existing MetaProvider/GoogleAdsProvider/TikTokProvider with stage filter
- **Summing ad-platform conversions for MQL count:** CRM lifecycle_transitions is the authoritative source for stage transitions (project decision)
- **Showing ManyChat as a visible channel row:** ManyChat is infrastructure; aggregate its metrics into the corresponding messaging channel
- **Hard-coding campaign classification:** Always check Custom Audiences first, then fall back to objective-based classification

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Collapsable UI sections | Custom height animation | shadcn `Collapsible` + `CollapsibleContent` | Handles enter/exit transitions, accessibility, keyboard nav |
| Lead scoring | Custom point system | Existing `LifecycleService.recalculate_score()` + `SCORING_WEIGHTS` | Already has event weights (email_opened=2.0, email_clicked=3.0), threshold transitions, FOR UPDATE locking |
| Cache management | Custom Redis logic | Existing `MetricsCache` with per-stage TTL | 300s default for nurture stage, consistent API |
| Channel connection detection | Custom provider lookup | Existing `ChannelRegistry.get_available_channels()` | Already splits connected/available using ConnectionPort |
| Cost calculation | New cost calculation logic | Extend `CaptureCostService` pattern | Already handles manual costs, prorated agency costs, CAL formula |
| Webhook event dedup | Custom dedup logic | Use journey_events unique constraint or idempotency key | Mailerlite may retry webhooks; dedup prevents double-counting |

**Key insight:** Phase 6 is 90% pattern replication from Phase 5 (Capture). The main new complexity is retargeting campaign classification and the Mailerlite webhook integration. Everything else (DTOs, repository, service method, API endpoint, frontend panel) follows established templates.

## Common Pitfalls

### Pitfall 1: Meta API Custom Audience Field Access
**What goes wrong:** The `custom_audiences` field in targeting requires reading at the adset level, not the campaign level. Querying at campaign level misses audience data.
**Why it happens:** Meta campaigns don't have targeting directly; targeting lives on adsets.
**How to avoid:** Always query `GET /act_{ad_account_id}/adsets?fields=targeting,campaign{objective}` at the adset level, then aggregate metrics per campaign.
**Warning signs:** Getting empty targeting objects when querying campaigns.

### Pitfall 2: MQL Threshold Mismatch
**What goes wrong:** CONTEXT.md references "lead_score threshold (e.g., >75 pts)" in NUT-02, but the actual scoring.py has MQL threshold at 40 (not 75).
**Why it happens:** Requirements doc used placeholder values before Phase 3 implementation.
**How to avoid:** Use `SCORING_THRESHOLDS.mql` (40.0) from `scoring.py` as the authoritative source. The lifecycle_transitions table already records the correct transitions.
**Warning signs:** MQL counts differ between direct score queries and transition table queries.

### Pitfall 3: Webhook Tenant Resolution
**What goes wrong:** Mailerlite webhooks don't include tenant_id. The webhook endpoint needs to resolve which tenant owns the Mailerlite API key.
**Why it happens:** External webhooks have no concept of multi-tenancy.
**How to avoid:** Option A: Include tenant_id in the webhook URL path (`/webhooks/mailerlite/{tenant_id}`). Option B: Look up tenant by Mailerlite account_id from the connections table. Option A is simpler and recommended.
**Warning signs:** All webhook events going to the wrong tenant.

### Pitfall 4: Weighted Average for Open/Click Rates
**What goes wrong:** Simple average of open rates across campaigns is misleading (a campaign sent to 100 people vs 10,000 people should not have equal weight).
**Why it happens:** Treating open_rate as a plain number to average.
**How to avoid:** Use weighted average: `total_opens / total_sent * 100` for group-level open rate. Same for click rate.
**Warning signs:** Group open rate being higher than any individual campaign's rate.

### Pitfall 5: Cost Split for Shared Services
**What goes wrong:** ManyChat and AI SDR costs are shared between Stage 1 (capture) and Stage 2 (nurturing). Double-counting inflates both stages' costs.
**Why it happens:** The same monthly cost entry applies to both stages.
**How to avoid:** Split by event_type in journey_events: capture conversations (message_received with initial contact) -> Stage 1, follow-up conversations (sdr_followup_sent) -> Stage 2. Or use a configurable percentage split in ChannelCostSettingModel (simpler for v1).
**Warning signs:** Sum of all stage costs exceeds actual total spend.

### Pitfall 6: Google Ads Remarketing Detection Differs from Meta
**What goes wrong:** Google Ads uses UserList/AdGroupCriterion for remarketing, not a simple `custom_audiences` field like Meta.
**Why it happens:** Different API structures across platforms.
**How to avoid:** For Google Ads, query `ad_group_criterion` where `criterion.type = USER_LIST` to identify remarketing ad groups. Alternatively, query campaigns with `advertising_channel_type = DISPLAY` that have remarketing list criteria.
**Warning signs:** Google retargeting showing zero campaigns despite active remarketing.

## Code Examples

### NurtureDetailDTO (backend)
```python
# Source: Pattern from capture_dto.py
from typing import Optional, List
from pydantic import BaseModel
from src.modules.analytics.application.dto.attraction_dto import (
    AvailableChannelsDTO,
    TrafficGroupDTO,
)

class NurtureHeaderKpisDTO(BaseModel):
    total_mqls: int
    conversion_rate: float  # percentage 0-100
    cost_per_mql: Optional[float] = None

class CampaignMetricDTO(BaseModel):
    campaign_name: str
    campaign_id: Optional[str] = None
    metrics: list  # List of MetricValueDTO

class NurtureDetailDTO(BaseModel):
    header_kpis: NurtureHeaderKpisDTO
    mini_funnel: MiniFunnelDTO  # reuse from capture_dto
    retargeting: TrafficGroupDTO
    automation: TrafficGroupDTO
    available: Optional[AvailableChannelsDTO] = None
    period: str = "last_30_days"
    last_updated: Optional[str] = None
```

### STAGE_CHANNEL_MAP expansion (channel_registry.py)
```python
# Source: Existing channel_registry.py pattern
"nurture": [
    # Retargeting Omnichannel
    {"slug": "meta-retargeting", "name": "Meta Retargeting", "channel_type": "retargeting", "source_label": "Meta Ads", "provider_name": "meta", "metric_names": ["reach", "clicks", "spend"]},
    {"slug": "google-retargeting", "name": "Google Retargeting", "channel_type": "retargeting", "source_label": "Google Ads", "provider_name": "google_ads", "metric_names": ["reach", "clicks", "spend"]},
    {"slug": "tiktok-retargeting", "name": "TikTok Retargeting", "channel_type": "retargeting", "source_label": "TikTok Ads", "provider_name": "tiktok", "metric_names": ["reach", "clicks", "spend"]},
    # Automatizacion
    {"slug": "mailerlite", "name": "Mailerlite", "channel_type": "email", "source_label": "MailerLite", "provider_name": "mailerlite", "metric_names": ["emails_sent", "open_rate", "click_rate"]},
    {"slug": "ai-sdr", "name": "AI SDR", "channel_type": "automation", "source_label": "AI SDR", "provider_name": "internal", "metric_names": ["followups", "response_rate"]},
],
```

### NurtureDetail frontend component (pattern)
```tsx
// Source: CaptureDetail.tsx pattern
'use client';
import { useCaptureDetail } from '../../../hooks/useNurtureDetail';
import { ChannelGroup } from '../channel-widgets/ChannelGroup';
import { MiniFunnel } from '../channel-widgets/MiniFunnel';

export function NurtureDetail() {
  const { data, isLoading, error } = useNurtureDetail();
  // Same structure as CaptureDetail: header KPIs + MiniFunnel + 2 ChannelGroups + available
  // Add NUTRICION case in MetricsDashboard.tsx routing
}
```

### ChannelGroup summary builder additions
```typescript
// Add to buildSummary() switch in ChannelGroup.tsx
case 'retargeting':
  return `Alcance: ${formatNumber(totals.reach ?? 0)} | Clicks: ${formatNumber(totals.clicks ?? 0)} | Gasto: ${formatCurrency(totals.spend ?? 0)}`;
case 'automation':
  return `Emails: ${formatNumber(totals.emails_sent ?? 0)} | Apertura: ${(totals.open_rate ?? 0).toFixed(1)}% | Click Rate: ${(totals.click_rate ?? 0).toFixed(1)}%`;
```

### Meta retargeting classification logic
```python
# Fetch adsets with targeting info
adsets_resp = await client.get(
    f"{GRAPH_API_BASE}/act_{ad_account_id}/adsets",
    params={
        "fields": "targeting,campaign{objective},insights.time_range({time_range}){reach,clicks,spend}",
        "filtering": json.dumps([{"field": "effective_status", "operator": "IN", "value": ["ACTIVE", "PAUSED"]}]),
        "limit": 100,
        "access_token": access_token,
    },
)

for adset in adsets_data:
    targeting = adset.get("targeting", {})
    custom_audiences = targeting.get("custom_audiences", [])
    is_retargeting = len(custom_audiences) > 0

    if stage == "nurturing" and is_retargeting:
        # Include: retargeting campaign
        pass
    elif stage == "attraction" and not is_retargeting:
        # Include: cold traffic campaign
        pass
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Aggregate all Meta Ads as single slug | Stage-filtered extraction (TOFU vs MOFU) | Phase 6 (new) | Enables retargeting vs. cold separation |
| CaptureCostService (stage-specific) | StageCostService (generic, stage parameter) | Phase 6 (new) | DRY cost calculation across stages |
| MailerLite connector: verify_connection only | + webhook integration + campaign stats | Phase 6 (new) | Real-time email engagement scoring |
| STAGE_CHANNEL_MAP["nurture"]: 2 channels | 5 channels (3 retargeting + mailerlite + ai-sdr) | Phase 6 (new) | Complete nurturing channel coverage |

**Deprecated/outdated:**
- MailerLite API V1/V2 (Classic): Deprecated. Use the new MailerLite API (accounts created after March 2022). Current connector uses `connect.mailerlite.com` which is the new API.

## Open Questions

1. **Mailerlite webhook tenant resolution strategy**
   - What we know: Webhooks don't include tenant_id. Need to resolve tenant from webhook context.
   - What's unclear: Whether to use URL-path tenant_id or lookup by account_id.
   - Recommendation: Use `/webhooks/mailerlite/{tenant_id}` (simpler, no extra DB lookup). Store webhook URL with tenant_id when user configures Mailerlite connection.

2. **Campaign-level metrics storage for drill-down**
   - What we know: ExtractedMetric already has `campaign_id` field. OfficialMetricsRepository aggregates to channel level.
   - What's unclear: Whether to store campaign-level detail in official_metrics or a separate table.
   - Recommendation: Store campaign-level rows in official_metrics with campaign_id populated. The channel-level aggregation happens in the service layer. This reuses existing infrastructure.

3. **Google Ads GAQL for remarketing audience detection**
   - What we know: Google Ads uses UserList criterion at ad group level.
   - What's unclear: Exact GAQL query to join campaign metrics with audience targeting.
   - Recommendation: Query `ad_group_criterion` with `criterion.type = USER_LIST` to get retargeting ad group IDs, then filter campaign metrics by those ad groups. Alternatively, use campaign-level `customer_match_audience` segments.

4. **ChannelCostSettingModel stage awareness**
   - What we know: Current model has `channel_slug` and `cost_type` but no `stage` field.
   - What's unclear: Whether to add a `stage` column or use channel_slug convention (e.g., "mailerlite" for capture, "mailerlite-nurture" for nurturing).
   - Recommendation: Add optional `stage` column (nullable, default NULL = applies to all stages). Simpler than slug conventions and supports the shared cost splitting use case.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (inside Docker container) |
| Config file | `backend/pyproject.toml` |
| Quick run command | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q` |
| Full suite command | `docker exec -t visionarias_brain_dev pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NUT-01 | NurtureDetail panel renders two groups | unit (frontend) | Manual verification via ENABLE_MOCKS | -- Wave 0 |
| NUT-02 | `/metrics/nurturing` returns MQL conversion count | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_nurture_metrics.py -x` | -- Wave 0 |
| NUT-03 | Retargeting metrics filtered to MOFU campaigns | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_retargeting_filter.py -x` | -- Wave 0 |
| NUT-04 | Mailerlite webhook creates journey_event + triggers scoring | integration | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_mailerlite_webhook.py -x` | -- Wave 0 |
| NUT-05 | Cost per MQL calculated correctly | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_stage_cost_service.py -x` | -- Wave 0 |

### Sampling Rate
- **Per task commit:** `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q`
- **Per wave merge:** `docker exec -t visionarias_brain_dev pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/modules/analytics/test_nurture_metrics.py` -- covers NUT-02 (MQL counting from lifecycle_transitions)
- [ ] `tests/modules/analytics/test_retargeting_filter.py` -- covers NUT-03 (Custom Audience detection logic)
- [ ] `tests/modules/analytics/test_mailerlite_webhook.py` -- covers NUT-04 (webhook -> journey_event -> scoring)
- [ ] `tests/modules/analytics/test_stage_cost_service.py` -- covers NUT-05 (StageCostService calculations)

## Sources

### Primary (HIGH confidence)
- Existing codebase: `analytics/application/services/metrics_service.py` (MetricsService.get_capture_metrics pattern)
- Existing codebase: `analytics/application/dto/capture_dto.py` (CaptureDetailDTO structure)
- Existing codebase: `analytics/application/services/channel_registry.py` (STAGE_CHANNEL_MAP, ChannelRegistry)
- Existing codebase: `analytics/application/services/capture_cost_service.py` (CaptureCostService pattern)
- Existing codebase: `crm/domain/scoring.py` (SCORING_THRESHOLDS.mql = 40.0)
- Existing codebase: `crm/application/services/lifecycle_service.py` (recalculate_score, threshold transitions)
- Existing codebase: `analytics/infrastructure/providers/meta_provider.py` (MetaProvider extraction pattern)
- Existing codebase: `analytics/infrastructure/providers/google_ads_provider.py` (GAQL queries)
- Existing codebase: Frontend CaptureDetail.tsx, ChannelGroup.tsx, ChannelRow.tsx (component patterns)
- Phase 06 UI-SPEC: `.planning/phases/06-stage-2-nutricion/06-UI-SPEC.md`

### Secondary (MEDIUM confidence)
- [MailerLite Webhooks Documentation](https://developers.mailerlite.com/docs/webhooks) -- campaign.open, campaign.click events confirmed
- [Meta Custom Audience API](https://developers.facebook.com/docs/marketing-api/reference/custom-audience/) -- targeting.custom_audiences field on adsets
- [Google Ads Audience Management](https://developers.google.com/google-ads/api/docs/remarketing/overview) -- UserList criterion, AdGroupCriterion targeting

### Tertiary (LOW confidence)
- TikTok Custom Audience API field mapping -- inferred from Meta pattern, needs validation against actual TikTok Business API docs
- ManyChat API sequence metrics extraction -- deferred to Claude's discretion, not critical path for v1

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already in project, patterns established in Phases 4-5
- Architecture: HIGH - direct replication of capture stage pattern with well-defined extensions
- Retargeting classification: MEDIUM - Custom Audience detection confirmed for Meta, Google uses different mechanism (UserList), TikTok needs validation
- Mailerlite webhooks: HIGH - official docs confirm campaign.open/campaign.click events
- Cost service: HIGH - direct extension of existing CaptureCostService pattern
- Frontend components: HIGH - UI-SPEC exists with detailed layout contract

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable -- internal codebase patterns unlikely to change)
