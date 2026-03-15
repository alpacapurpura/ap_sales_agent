# Phase 4: Stage 0 Attraction Fix & Validate - Research

**Researched:** 2026-03-15
**Domain:** Provider adapter implementation, multi-platform API integration, frontend multi-metric redesign
**Confidence:** HIGH

## Summary

Phase 4 wires real API data into the existing Attraction panel by implementing 6 concrete provider adapters (MetaProvider, GoogleAnalyticsProvider, GoogleAdsProvider, TikTokProvider, YouTubeProvider, CRMInternalProvider), redesigning the ChannelRow component for multi-metric display, and building a validation script. The infrastructure is solid: `BaseMetricsProvider` ABC, `ProviderRegistry`, `ETLPipeline`, `ConnectionPortImpl`, and `MetricsCache` are all production-ready from Phases 1-2.

The primary challenge is the **DTO and frontend redesign**: the current `ChannelMetricDTO` carries a single `value` field, but the CONTEXT.md decisions require multiple metrics per channel (e.g., Reach + Engagement for organic social, Reach + Clicks + Conversions + Spend for paid). This requires changes across the full stack: DTO schema, MetricsService aggregation logic, API response format, TypeScript types, and ChannelRow/ChannelGroup components.

A secondary challenge is **missing API clients**: TikTok has no adapter in the connections module at all. Google Ads needs a new adapter (the existing `google_analytics.py` only covers GA4, not the Google Ads reporting API). Facebook organic page insights need methods added to MetaAdapter.

**Primary recommendation:** Start with the DTO/API multi-metric redesign (it unblocks everything), then implement providers in dependency order (Meta and GA4 first since clients exist, then Google Ads, YouTube, TikTok, CRM), then frontend redesign, and finish with the validation script.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Organic Social metrics:** Two primary metrics side by side: Reach (big number) + Engagement (big total with breakdown: likes, comments, shares, saves)
- **GA4 Search metrics:** Two primary metrics: Sessions + Users (unique visitors), using GA4 runReport() with sessionSource/sessionMedium dimensions
- **Paid Channel metrics:** Four primary metrics: Reach + Clicks + Conversions + Spend per channel
- **Cold Contact metrics:** Two metrics: Contacts (outbound attempts) + Responses (replies received), sourced from CRM journey_events
- **ChannelRow redesign:** Multi-metric layout replacing current single-value. Connected channels get full rich layout. Available channels show name + "Configurar" badge only
- **Error UX:** Show last known value + yellow "desactualizado" stale indicator + timestamp + refresh button (15-min cooldown)
- **"Ultima actualizacion" timestamp:** Single timestamp at top of Attraction panel header
- **Provider adapter scope:** Build ALL provider adapters for Stage 0 (MetaProvider, GoogleAnalyticsProvider, GoogleAdsProvider, TikTokProvider, YouTubeProvider, CRMInternalProvider)
- **LinkedIn:** No adapter needed -- shows in "Canales disponibles" with "Configurar" badge
- **Validation:** Automated comparison script (on-demand, not CI), 5% tolerance threshold, runs inside Docker

### Claude's Discretion
- Per-platform API field mapping to unified metrics (Reach, Engagement, Clicks, Conversions, Spend)
- Campaign type grouping logic for paid channels (TOFU vs MOFU vs BOFU classification)
- Error UX casuistry -- map all possible failure scenarios and design user-facing states
- ChannelRow component design details (spacing, typography, responsive behavior)
- GA4 dimension/filter values for AI-search referrer detection
- Validation script implementation details and report format
- Which connections module API clients need to be built vs already exist

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ATR-01 | Validate attraction data against real API responses from connected providers for tenant "Visionarias" | Validation script architecture, 5% tolerance comparison logic, per-provider API field mappings |
| ATR-02 | Implement GA4 runReport() for organic search channels (google-organic, direct, ai-search) | GoogleAnalyticsAdapter.run_report() already exists; sessionSource/sessionMedium dimensions and AI-referrer domain list documented |
| ATR-03 | Pull real reach/impressions from Instagram, YouTube, Facebook, TikTok for organic social | Per-platform API field mappings documented; MetaAdapter exists, YouTubeAnalyticsAdapter exists, TikTok needs new client |
| ATR-04 | Pull real clicks and spend from Meta Ads, Google Ads, TikTok Ads for paid channels | Meta Marketing API insights endpoint documented, Google Ads GAQL queries documented, TikTok Ads API needs new client |
| ATR-05 | Cold Contact channel shows response rate from CRM data | JourneyEventModel schema documented; query pattern for outbound events identified |

</phase_requirements>

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| `facebook-business` | >=22.0,<26.0 | Meta Graph API + Marketing API (Instagram, Facebook, Meta Ads) | Installed, MetaAdapter exists |
| `google-analytics-data` | latest | GA4 Data API (BetaAnalyticsDataClient.runReport) | Installed, GoogleAnalyticsAdapter exists |
| `google-api-python-client` | latest | YouTube Analytics API v2, YouTube Data API v3 | Installed, YouTubeAnalyticsAdapter exists |
| `httpx` | latest | Async HTTP client for TikTok API, Meta Graph API | Installed, used throughout |

### New Dependencies Needed
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `google-ads` | latest | Google Ads API client (GAQL queries for campaign metrics) | GoogleAdsProvider - reporting on clicks, spend, conversions |

### No New Dependencies Needed For
| Task | Reason |
|------|--------|
| TikTok organic/ads | Use `httpx` directly against TikTok Business API REST endpoints |
| CRM Internal | Direct SQLAlchemy query against `journey_events` table |
| Meta organic/ads | Existing `facebook-business` SDK + `httpx` for Graph API |
| YouTube organic | Existing `google-api-python-client` via YouTubeAnalyticsAdapter |

## Architecture Patterns

### Recommended Project Structure
```
backend/src/modules/analytics/infrastructure/providers/
  base.py                    # (exists) BaseMetricsProvider ABC
  registry.py                # (exists) PROVIDER_REGISTRY dict + register/get functions
  meta_provider.py           # NEW: Instagram organic, Facebook organic, Meta Ads
  google_analytics_provider.py  # NEW: google-organic, direct, ai-search
  google_ads_provider.py     # NEW: Google Ads (search/display) + YouTube Ads
  tiktok_provider.py         # NEW: TikTok organic + TikTok Ads
  youtube_provider.py        # NEW: YouTube organic
  crm_internal_provider.py   # NEW: Cold Contact from journey_events

backend/src/modules/connections/infrastructure/channels/
  tiktok.py                  # NEW: TikTok Business API client (OAuth + insights)
  google_ads.py              # NEW: Google Ads API client (GAQL reporting)

backend/src/modules/analytics/application/dto/
  attraction_dto.py          # MODIFY: Multi-metric ChannelMetricDTO

frontend/src/features/marketing-studio/
  types/metrics.ts           # MODIFY: Multi-metric ChannelMetric type
  components/metrics-dashboard/channel-widgets/
    ChannelRow.tsx            # REDESIGN: Multi-metric layout
    ChannelGroup.tsx          # MODIFY: Multi-metric group headers
  components/metrics-dashboard/detail-panels/
    AttractionDetail.tsx      # MODIFY: Add timestamp header, error states

scripts/
  validate_attraction.py     # NEW: Validation comparison script
```

### Pattern 1: Provider Adapter Implementation
**What:** Each provider implements `BaseMetricsProvider`, mapping platform-specific API responses to `ExtractedMetric` objects.
**When to use:** Every new data source.
**Example:**
```python
# Source: existing base.py + Phase 2 decisions
class MetaProvider(BaseMetricsProvider):
    """Extracts metrics from Meta Graph API for Instagram organic,
    Facebook organic, and Meta Ads."""

    async def extract_metrics(
        self, tenant_id: UUID, credentials: dict,
        start_date: date, end_date: date,
    ) -> List[ExtractedMetric]:
        metrics = []
        # Instagram organic: reach + engagement breakdown
        metrics.extend(await self._extract_instagram_organic(credentials, start_date, end_date))
        # Facebook page organic: reach + engagement
        metrics.extend(await self._extract_facebook_organic(credentials, start_date, end_date))
        # Meta Ads: reach, clicks, conversions, spend
        metrics.extend(await self._extract_meta_ads(credentials, start_date, end_date))
        return metrics

    def provider_name(self) -> str:
        return "meta"

    def rate_limit_config(self) -> dict:
        return {"requests_per_minute": 200, "burst_size": 50}
```

### Pattern 2: Multi-Metric DTO Extension
**What:** Extend `ChannelMetricDTO` to carry a list of named metrics instead of a single `value`.
**When to use:** This phase, for all channel types.
**Example:**
```python
class MetricValueDTO(BaseModel):
    """Single named metric within a channel."""
    name: str           # "reach", "engagement", "sessions", "clicks", "spend"
    value: float
    unit: str = "count" # "count", "currency", "percentage"
    currency: Optional[str] = None
    breakdown: Optional[dict] = None  # e.g. {"likes": 120, "comments": 45, "shares": 30}

class ChannelMetricDTO(BaseModel):
    slug: str
    name: str
    channel_type: str
    metrics: list[MetricValueDTO]  # REPLACES single `value` field
    source_label: str
    connected: bool
    cost_type: Optional[str] = None
    last_updated: Optional[str] = None
    stale: bool = False       # True when extraction failed, showing last known value
    error_message: Optional[str] = None
```

### Pattern 3: One Provider = Multiple Channel Slugs
**What:** A single provider adapter (e.g., MetaProvider) emits `ExtractedMetric` objects with different `channel_slug` values (ig-organic, fb-organic, meta-ads).
**When to use:** When one API connection serves multiple dashboard channels.
**Critical rule:** The ETL pipeline runs once per provider, but the pipeline's staging/official tables naturally separate by `channel_slug`. The MetricsService then groups by slug for the frontend.

### Anti-Patterns to Avoid
- **One adapter per channel slug:** Don't create 13 adapter classes. Group by provider (6 adapters for 13 channels).
- **Hardcoding campaign type classification:** Campaign names vary per tenant. Use a configurable mapping or simple heuristics (campaign objective field from API) rather than name-matching.
- **Mixing sync and async SDK calls:** Always wrap sync Google SDK calls with `asyncio.to_thread()`. The `facebook-business` SDK also has sync methods -- use `httpx` directly for async Graph API calls or wrap with `asyncio.to_thread()`.
- **Breaking existing single-value DTOs:** Maintain backward compatibility during migration. The `value` field can temporarily coexist with `metrics` list until all consumers are updated.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Meta Graph API calls | Raw urllib/requests | `httpx` async client (for insights) or `facebook-business` SDK (for Ads) | Token handling, pagination, error codes |
| GA4 report queries | Raw HTTP to GA4 | `GoogleAnalyticsAdapter.run_report()` (already built) | Handles BetaAnalyticsDataClient, async wrapping |
| YouTube analytics | Raw HTTP | `YouTubeAnalyticsAdapter` methods (already built) | Handles auth, channel ID resolution |
| Google Ads reporting | Raw HTTP | `google-ads` Python client with GAQL | Complex auth, pagination, micro-conversions |
| OAuth token refresh | Manual refresh flows | `ConnectionPortImpl._refresh_token()` (already built) | Handles Meta and Google refresh patterns |
| Campaign type classification | Regex on campaign names | Use campaign `objective` field from API response | Objectives are standardized; names are not |

## Common Pitfalls

### Pitfall 1: Instagram Insights Metric Deprecations (January 2025)
**What goes wrong:** Using deprecated metrics like `video_views` (for non-Reels), `email_contacts`, `profile_views`, `website_clicks` returns errors or empty data.
**Why it happens:** Meta deprecated these in Graph API v21+ (January 2025).
**How to avoid:** Use only current metrics: `reach`, `impressions`, `engagement` (likes + comments aggregate), plus per-media `likes`, `comments`, `shares`, `saved` breakdowns.
**Warning signs:** Empty `data` arrays or error responses mentioning deprecated fields.

### Pitfall 2: Meta SDK Singleton Anti-Pattern
**What goes wrong:** Using `FacebookAdsApi.init()` causes cross-tenant data leaks.
**Why it happens:** `init()` sets a process-global default API instance.
**How to avoid:** Already fixed in Phase 1. Use `FacebookSession` + per-instance `FacebookAdsApi`. The MetaProvider MUST follow the same pattern.
**Warning signs:** Metrics from wrong tenant appearing in dashboard.

### Pitfall 3: Google Ads `cost_micros` vs Actual Spend
**What goes wrong:** Google Ads API returns spend in micros (1/1,000,000 of currency unit). Displaying raw value shows $5,230,000 instead of $5.23.
**Why it happens:** Google Ads API convention.
**How to avoid:** Always divide `cost_micros` by 1,000,000 when creating `ExtractedMetric`.
**Warning signs:** Unrealistically large spend values in dashboard.

### Pitfall 4: GA4 AI-Search Referrer Detection
**What goes wrong:** AI-search traffic not detected because referrer domains change or new AI services emerge.
**Why it happens:** AI search is a new traffic source category without standardized attribution.
**How to avoid:** Use a configurable list of AI referrer domains. Initial list: `perplexity.ai`, `chatgpt.com`, `claude.ai`, `copilot.microsoft.com`, `gemini.google.com`, `you.com`, `phind.com`. Filter GA4 data with `sessionSource` dimension matching these domains.
**Warning signs:** Traffic from known AI tools showing up as "direct" or "referral" instead of "ai-search".

### Pitfall 5: TikTok Token 24-Hour Expiry
**What goes wrong:** TikTok access tokens expire after 24 hours, much faster than Meta (60 days) or Google (1 hour with refresh).
**Why it happens:** TikTok's OAuth implementation uses short-lived tokens.
**How to avoid:** This is already flagged as a concern in STATE.md. The TikTokProvider must handle `TokenRefreshFailed` gracefully and the ConnectionPortImpl needs TikTok refresh logic added.
**Warning signs:** TikTok extraction consistently failing after first day.

### Pitfall 6: YouTube Ads vs Google Ads API Overlap
**What goes wrong:** YouTube Ads and Google Ads both use the Google Ads API, making it unclear how to separate them.
**Why it happens:** YouTube Ads are a campaign type within Google Ads, not a separate API.
**How to avoid:** Filter by `campaign.advertising_channel_type = VIDEO` in GAQL to isolate YouTube Ads campaigns. All other campaign types (SEARCH, DISPLAY, SHOPPING, etc.) go to the google-ads channel.
**Warning signs:** YouTube ad spend double-counted in both google-ads and yt-ads rows.

### Pitfall 7: Multi-Metric DTO Breaking Frontend
**What goes wrong:** Changing `value: number` to `metrics: MetricValue[]` in the DTO breaks the existing ChannelRow component.
**Why it happens:** TypeScript strict mode catches the missing property immediately.
**How to avoid:** Update TypeScript types, ChannelRow, ChannelGroup, and useAttractionDetail hook in a single coordinated change. The backend API response format change and frontend type change must be deployed together.
**Warning signs:** TypeScript compilation errors, blank dashboard panels.

## Code Examples

### GA4 runReport for Organic Search Segmentation
```python
# Source: existing GoogleAnalyticsAdapter.run_report() signature
# Segments traffic by source/medium to identify google-organic, direct, ai-search

async def _extract_ga4_search_metrics(
    self, adapter: GoogleAnalyticsAdapter, property_id: str,
    start_date: str, end_date: str,
) -> list[ExtractedMetric]:
    report = await adapter.run_report(
        property_id=property_id,
        dimensions=["sessionSource", "sessionMedium"],
        metrics=["sessions", "totalUsers"],
        start_date=start_date,
        end_date=end_date,
    )

    AI_REFERRER_DOMAINS = {
        "perplexity.ai", "chatgpt.com", "claude.ai",
        "copilot.microsoft.com", "gemini.google.com",
        "you.com", "phind.com",
    }

    # Accumulate per channel slug
    channel_data = {
        "google-organic": {"sessions": 0, "users": 0},
        "direct": {"sessions": 0, "users": 0},
        "ai-search-organic": {"sessions": 0, "users": 0},
    }

    for row in report["rows"]:
        source = row["dimensions"][0].lower()
        medium = row["dimensions"][1].lower()
        sessions = float(row["metrics"][0])
        users = float(row["metrics"][1])

        if source in AI_REFERRER_DOMAINS:
            channel_data["ai-search-organic"]["sessions"] += sessions
            channel_data["ai-search-organic"]["users"] += users
        elif source == "google" and medium == "organic":
            channel_data["google-organic"]["sessions"] += sessions
            channel_data["google-organic"]["users"] += users
        elif source == "(direct)" and medium == "(none)":
            channel_data["direct"]["sessions"] += sessions
            channel_data["direct"]["users"] += users

    # Convert to ExtractedMetric objects
    metrics = []
    for slug, data in channel_data.items():
        for metric_name, value in data.items():
            metrics.append(ExtractedMetric(
                provider="google_analytics",
                channel_slug=slug,
                metric_name=metric_name,
                value=value,
                unit="count",
                date=date.fromisoformat(start_date) if isinstance(start_date, str) and "-" in start_date else date.today(),
            ))
    return metrics
```

### Meta Ads Insights Query
```python
# Source: Meta Marketing API docs, facebook-business SDK pattern
# Uses httpx for async Graph API call

async def _extract_meta_ads(
    self, credentials: dict, start_date: date, end_date: date,
) -> list[ExtractedMetric]:
    ad_account_id = credentials.get("ad_account_id")
    access_token = credentials.get("access_token")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"https://graph.facebook.com/v24.0/act_{ad_account_id}/insights",
            params={
                "fields": "reach,clicks,spend,actions",
                "time_range": json.dumps({
                    "since": start_date.isoformat(),
                    "until": end_date.isoformat(),
                }),
                "level": "account",
                "access_token": access_token,
            },
        )
    data = response.json().get("data", [{}])[0]

    conversions = 0
    for action in data.get("actions", []):
        if action.get("action_type") in ("offsite_conversion.fb_pixel_purchase", "onsite_conversion.purchase"):
            conversions += int(action.get("value", 0))

    return [
        ExtractedMetric(provider="meta", channel_slug="meta-ads", metric_name="reach", value=float(data.get("reach", 0)), unit="count", date=end_date),
        ExtractedMetric(provider="meta", channel_slug="meta-ads", metric_name="clicks", value=float(data.get("clicks", 0)), unit="count", date=end_date),
        ExtractedMetric(provider="meta", channel_slug="meta-ads", metric_name="conversions", value=float(conversions), unit="count", date=end_date),
        ExtractedMetric(provider="meta", channel_slug="meta-ads", metric_name="spend", value=float(data.get("spend", 0)), unit="currency", currency="USD", date=end_date),
    ]
```

### Google Ads GAQL Query for Campaign Metrics
```python
# Source: Google Ads API docs, google-ads Python client
# Separates YouTube Ads (VIDEO campaigns) from Search/Display

GAQL_CAMPAIGN_METRICS = """
    SELECT
        campaign.id,
        campaign.name,
        campaign.advertising_channel_type,
        metrics.impressions,
        metrics.clicks,
        metrics.conversions,
        metrics.cost_micros
    FROM campaign
    WHERE segments.date BETWEEN '{start}' AND '{end}'
        AND campaign.status = 'ENABLED'
"""

# After fetching:
for row in response:
    channel_type = row.campaign.advertising_channel_type
    slug = "yt-ads" if channel_type == "VIDEO" else "google-ads"
    spend = row.metrics.cost_micros / 1_000_000  # CRITICAL: convert micros
```

### Instagram Organic Insights via Graph API
```python
# Source: Meta Instagram Platform docs
# GET /{ig-user-id}/insights for account-level reach
# GET /{ig-user-id}/media for per-post engagement breakdown

async def _extract_instagram_organic(
    self, credentials: dict, start_date: date, end_date: date,
) -> list[ExtractedMetric]:
    access_token = credentials.get("access_token")
    ig_account_id = credentials.get("instagram_account_id")
    base = f"https://graph.facebook.com/v24.0"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Account-level reach (last 30 days)
        insights_resp = await client.get(
            f"{base}/{ig_account_id}/insights",
            params={
                "metric": "reach",
                "period": "day",
                "since": int(datetime.combine(start_date, datetime.min.time()).timestamp()),
                "until": int(datetime.combine(end_date, datetime.min.time()).timestamp()),
                "access_token": access_token,
            },
        )
        # Sum daily reach values
        reach_data = insights_resp.json().get("data", [])
        total_reach = sum(
            v.get("value", 0) for item in reach_data for v in item.get("values", [])
        )

        # Per-media engagement breakdown (recent media)
        media_resp = await client.get(
            f"{base}/{ig_account_id}/media",
            params={
                "fields": "like_count,comments_count,timestamp",
                "since": start_date.isoformat(),
                "limit": 100,
                "access_token": access_token,
            },
        )
        media_items = media_resp.json().get("data", [])
        total_likes = sum(m.get("like_count", 0) for m in media_items)
        total_comments = sum(m.get("comments_count", 0) for m in media_items)

    return [
        ExtractedMetric(provider="meta", channel_slug="ig-organic", metric_name="reach", value=float(total_reach), unit="count", date=end_date),
        ExtractedMetric(provider="meta", channel_slug="ig-organic", metric_name="engagement", value=float(total_likes + total_comments), unit="count", date=end_date,
            extra={"likes": total_likes, "comments": total_comments, "shares": 0, "saves": 0}),
    ]
```

### Frontend Multi-Metric ChannelRow (TypeScript)
```typescript
// Source: redesign based on CONTEXT.md decisions
interface MetricValue {
  name: string;       // "reach", "engagement", "sessions", "clicks", "spend"
  value: number;
  unit?: string;      // "count" | "currency" | "percentage"
  currency?: string;
  breakdown?: Record<string, number>;  // e.g. {likes: 120, comments: 45}
}

interface ChannelMetric {
  slug: string;
  name: string;
  channelType: string;
  metrics: MetricValue[];
  sourceLabel: string;
  connected: boolean;
  costType?: string;
  lastUpdated?: string;
  stale?: boolean;
  errorMessage?: string;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Instagram `video_views` metric | Use `reach` + `impressions` | Jan 2025 (v21) | Must not use deprecated metrics |
| Meta API v19.0 | v24.0 | Fixed in Phase 1 | Already handled |
| `FacebookAdsApi.init()` singleton | Per-instance via `FacebookSession` | Fixed in Phase 1 | Already handled |
| Single `value` per channel | Multiple named metrics per channel | This phase | DTO + frontend redesign required |
| Mock/zero data in attraction panel | Real ETL-sourced data | This phase | Core deliverable |

## API Field Mappings (Claude's Discretion Resolution)

### Organic Social - Per-Platform Normalization

| Platform | Reach Metric | Engagement Source | Breakdown Fields |
|----------|-------------|-------------------|------------------|
| Instagram | `GET /{ig-id}/insights?metric=reach&period=day` (sum daily values) | Per-media `like_count` + `comments_count` | likes, comments, shares (via shares endpoint), saves (via saved endpoint) |
| YouTube | `YouTubeAnalyticsAdapter.get_channel_overview()` -> `views` | Same response -> `likes` + `dislikes` (no shares/saves in YT Analytics API) | likes, comments (via separate query) |
| Facebook | `GET /{page-id}/insights?metric=page_impressions_unique` | `GET /{page-id}/insights?metric=page_post_engagements` | reactions, comments, shares |
| TikTok | `GET /business/get/` -> `profile_views` or aggregate video `video_views` | Per-video: `likes` + `comments` + `shares` | likes, comments, shares |

### Paid Channels - Universal Field Mapping

| Platform | Reach | Clicks | Conversions | Spend |
|----------|-------|--------|-------------|-------|
| Meta Ads | `insights.reach` | `insights.clicks` | `insights.actions[purchase]` | `insights.spend` (float, already in currency) |
| Google Ads | `metrics.impressions` (reach proxy) | `metrics.clicks` | `metrics.conversions` | `metrics.cost_micros / 1,000,000` |
| TikTok Ads | `metrics.reach` | `metrics.clicks` | `metrics.conversions` | `metrics.spend` |
| YouTube Ads | Same as Google Ads, filtered by `campaign.advertising_channel_type = VIDEO` | Same | Same | Same |

### GA4 Search - Session Attribution

| Channel Slug | GA4 Filter Logic |
|-------------|------------------|
| `google-organic` | `sessionSource = 'google' AND sessionMedium = 'organic'` |
| `direct` | `sessionSource = '(direct)' AND sessionMedium = '(none)'` |
| `ai-search-organic` | `sessionSource IN ('perplexity.ai', 'chatgpt.com', 'claude.ai', 'copilot.microsoft.com', 'gemini.google.com', 'you.com', 'phind.com')` |

## Connections Module Gap Analysis

### Existing Clients (Ready to Use)
| Client | File | Used By Provider |
|--------|------|-----------------|
| `MetaAdapter` | `connections/infrastructure/channels/meta.py` | MetaProvider (Instagram organic, Facebook organic, Meta Ads) |
| `GoogleAnalyticsAdapter` | `connections/infrastructure/channels/google_analytics.py` | GoogleAnalyticsProvider |
| `YouTubeAnalyticsAdapter` | `connections/infrastructure/channels/youtube_analytics.py` | YouTubeProvider |

### Missing Clients (Must Build)
| Client | File to Create | Scope |
|--------|---------------|-------|
| `TikTokAdapter` | `connections/infrastructure/channels/tiktok.py` | OAuth flow + organic insights + ads reporting |
| `GoogleAdsAdapter` | `connections/infrastructure/channels/google_ads.py` | GAQL reporting client for campaign metrics |

### ChannelType Enum Additions Needed
| New Value | Purpose |
|-----------|---------|
| `TIKTOK` | TikTok Business account connection |
| `TIKTOK_ADS` | TikTok Ads account (may share OAuth with organic) |

**Note:** Adding ChannelType enum values requires an Alembic migration since it is a PG Enum via `class ChannelType(str, Enum)`. However, since it is `str, Enum` (not a PG native ENUM), it is stored as VARCHAR - no migration needed, just add the Python enum value.

## Error UX Casuistry (Claude's Discretion Resolution)

| Scenario | User Sees | Technical Detail |
|----------|-----------|------------------|
| **Token expired** | Last known value + yellow "Desactualizado" badge + "Token expirado" tooltip + Refresh button | `ConnectionRevokedException` / `TokenRefreshFailed` |
| **Rate limited** | Last known value + yellow "Desactualizado" badge + "Reintentando..." | ExtractionRun status = RETRYING |
| **Provider API down** | Last known value + yellow "Desactualizado" badge + "Servicio no disponible" | HTTP 5xx from provider |
| **No data ever extracted** | Metric shows "---" (dash) instead of 0 + "Sin datos" label | No rows in official_metrics for this channel |
| **Partial extraction** | Show successfully extracted metrics, yellow badge on failed ones | Per-channel error isolation within provider |
| **Refresh cooldown active** | Refresh button disabled + "Disponible en X min" tooltip | 15-min cooldown per Phase 2 decision |
| **Connection not configured** | Channel in "Canales disponibles" section with "Configurar" badge | ChannelRegistry classifies as available |

## Open Questions

1. **TikTok API Access Level**
   - What we know: TikTok Business API exists but requires app approval and specific access levels
   - What's unclear: Whether the Visionarias tenant has an approved TikTok app with organic insights + ads access
   - Recommendation: Build the TikTok adapter, but if credentials don't exist, it gracefully shows as "available" channel. Check connection status before running validation.

2. **Google Ads API Developer Token**
   - What we know: Google Ads API requires a developer token (separate from OAuth) with approved access level
   - What's unclear: Whether the project has a Google Ads developer token configured
   - Recommendation: Check settings/env for `GOOGLE_ADS_DEVELOPER_TOKEN`. If missing, Google Ads provider returns empty and channel shows "Configurar".

3. **Instagram Shares and Saves Metrics**
   - What we know: Instagram deprecated some engagement breakdown metrics in v21 (Jan 2025). `like_count` and `comments_count` remain available on media objects.
   - What's unclear: Whether `shares` and `saved` counts are still accessible via the current API version
   - Recommendation: Implement with available metrics (likes, comments); set shares/saves to 0 in breakdown with a TODO comment. Update when API access is verified.

4. **Facebook Page Insights vs User Insights**
   - What we know: MetaAdapter has `get_business_assets()` which fetches pages with `page_access_token`. Page insights require the page token, not user token.
   - What's unclear: The exact credentials structure stored for Facebook organic
   - Recommendation: The MetaProvider should use `page_access_token` from the stored connection config for page-level insights queries.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (inside Docker container) |
| Config file | `backend/pytest.ini` or `pyproject.toml` |
| Quick run command | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q` |
| Full suite command | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ATR-01 | Validation script compares ETL vs API with 5% tolerance | integration (manual) | `docker exec -t visionarias_brain_dev python scripts/validate_attraction.py` | No - Wave 0 |
| ATR-02 | GA4 provider extracts sessions/users segmented by source | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_google_analytics_provider.py -x` | No - Wave 0 |
| ATR-03 | Organic social providers extract reach + engagement | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_meta_provider.py tests/modules/analytics/test_youtube_provider.py tests/modules/analytics/test_tiktok_provider.py -x` | No - Wave 0 |
| ATR-04 | Paid providers extract reach + clicks + conversions + spend | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_meta_provider.py::TestMetaAds tests/modules/analytics/test_google_ads_provider.py -x` | No - Wave 0 |
| ATR-05 | CRM internal provider reads journey_events for cold contact | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_crm_internal_provider.py -x` | No - Wave 0 |

### Sampling Rate
- **Per task commit:** `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q`
- **Per wave merge:** `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -v`
- **Phase gate:** Full suite green + validation script passes for connected providers

### Wave 0 Gaps
- [ ] `tests/modules/analytics/test_meta_provider.py` -- covers ATR-03, ATR-04 (Instagram organic, Facebook organic, Meta Ads)
- [ ] `tests/modules/analytics/test_google_analytics_provider.py` -- covers ATR-02
- [ ] `tests/modules/analytics/test_google_ads_provider.py` -- covers ATR-04
- [ ] `tests/modules/analytics/test_youtube_provider.py` -- covers ATR-03
- [ ] `tests/modules/analytics/test_tiktok_provider.py` -- covers ATR-03, ATR-04
- [ ] `tests/modules/analytics/test_crm_internal_provider.py` -- covers ATR-05
- [ ] `tests/modules/analytics/test_multi_metric_dto.py` -- covers multi-metric DTO transformation
- [ ] `scripts/validate_attraction.py` -- covers ATR-01

## Sources

### Primary (HIGH confidence)
- Codebase exploration: `BaseMetricsProvider`, `ProviderRegistry`, `ETLPipeline`, `MetaAdapter`, `GoogleAnalyticsAdapter`, `YouTubeAnalyticsAdapter`, `ConnectionPortImpl`, `ChannelRegistry`, `MetricsService`, `ChannelMetricDTO`, `ChannelRow.tsx`, `AttractionDetail.tsx` -- all read directly from source
- [Meta Instagram Platform Insights docs](https://developers.facebook.com/docs/instagram-platform/insights/) -- available metrics, deprecations
- [Meta Marketing API Ad Account Insights](https://developers.facebook.com/docs/marketing-api/reference/ad-account/insights/) -- reach, clicks, spend, actions fields
- [GA4 Data API runReport](https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport) -- dimensions, metrics, filtering

### Secondary (MEDIUM confidence)
- [Google Ads API Video Campaigns](https://developers.google.com/google-ads/api/docs/video/overview) -- campaign.advertising_channel_type = VIDEO for YouTube Ads separation
- [Google Ads API Reporting](https://developers.google.com/google-ads/api/docs/reporting/example) -- GAQL query patterns for cost_micros, clicks, conversions
- [Instagram Insights deprecation details](https://docs.emplifi.io/platform/latest/home/instagram-insights-metrics-deprecation-april-2025) -- v21+ deprecations confirmed
- [Meta Marketing API June 2025 attribution changes](https://windsor.ai/documentation/facebook-ads-meta-api-updates-june-10-2025/) -- action attribution timing changes

### Tertiary (LOW confidence)
- TikTok Business API specifics -- official docs at business-api.tiktok.com require authenticated access; exact endpoint paths and field names need verification during implementation
- Google Ads developer token requirements -- need to verify project has GOOGLE_ADS_DEVELOPER_TOKEN in environment

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries verified in existing codebase; only `google-ads` is new
- Architecture: HIGH - follows established provider adapter pattern from Phase 2
- API field mappings: MEDIUM - Meta and Google verified via official docs; TikTok needs runtime verification
- Pitfalls: HIGH - based on documented deprecations and known issues in STATE.md
- Frontend redesign: HIGH - existing component structure is well understood

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable infrastructure, API versions locked)
