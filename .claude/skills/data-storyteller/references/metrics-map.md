# Metrics Map — Platform → Metrics → Where to Look

> This map is a STARTING POINT. Always verify against official documentation before claiming a metric exists or doesn't.

## By Platform

| Platform | Type | Key Metrics | Lookup Route |
|----------|------|-------------|-------------|
| Meta Ads | Paid | spend, impressions, reach, clicks, cpc, ctr, cpm, conversions, roas, frequency | MCP context7 → "Meta Marketing API" |
| Meta Organic (IG/FB) | Organic | reach, impressions, engagement, saves, shares, followers, stories_views, reels_plays | MCP context7 → "Instagram Graph API" |
| Google Ads | Paid | cost, clicks, impressions, conversions, cpc, ctr, conversion_rate, quality_score | MCP context7 → "Google Ads API" |
| GA4 | Analytics | sessions, users, new_users, bounce_rate, pages_per_session, avg_session_duration, events, conversions, revenue | MCP context7 → "GA4 Data API" |
| YouTube | Organic+Paid | views, watch_time_minutes, subscribers_gained, engagement_rate, avg_view_duration, cpm (ads) | MCP context7 → "YouTube Analytics API" |
| TikTok | Organic+Paid | views, likes, shares, comments, followers, profile_views, spend (ads), cpc, ctr | WebSearch → `site:business-api.tiktok.com` |
| Shopify | E-commerce | orders, revenue, aov (avg order value), refunds, customers, repeat_rate, products_sold | MCP shopify-dev → `introspect_graphql_schema` |
| Mailerlite | Email | subscribers, open_rate, click_rate, unsubscribe_rate, campaigns_sent, bounces | WebSearch → `site:developers.mailerlite.com` |
| Manychat | Messaging | subscribers, messages_sent, open_rate, ctr, flows_triggered, tags_applied | WebSearch → `"manychat API" {metric}` |
| LinkedIn | Organic+Paid | impressions, clicks, engagement_rate, followers, spend (ads), conversions | WebSearch → `site:learn.microsoft.com/linkedin` |

## Derived Metrics (Calculated, Not Extracted)

| Metric | Formula | When to Use | Better Than |
|--------|---------|-------------|-------------|
| CAC | total_spend / new_customers | Acquisition efficiency | Raw spend (lacks context) |
| LTV | avg_revenue_per_customer x avg_lifetime_months | Customer value | Single-purchase revenue |
| ROAS | revenue / ad_spend | Paid ads return | CTR (doesn't measure value) |
| Blended CPA | total_spend (all channels) / total_conversions | True cross-channel cost | Per-channel CPA (hides reality) |
| K-Factor | (invites_sent x invite_conversion_rate) | Virality | Raw referral count |
| Engagement Rate | (likes + comments + saves + shares) / reach | Organic content quality | CTR (misses saves/shares) |
| Churn Rate | lost_customers / total_customers x 100 | Retention health | Active customer count alone |
| Net MRR | new_mrr + expansion_mrr - churned_mrr | Revenue trajectory | Gross revenue (hides churn) |
| Time-to-Value | avg days from purchase to first meaningful use | Onboarding effectiveness | Activation rate alone |

## Bowtie: Metrics by Stage

| Stage | Route | Primary KPIs | Secondary KPIs |
|-------|-------|-------------|----------------|
| Atraccion (0) | atraccion-captura | Reach, Sessions | Impressions, New Visitors, CPM |
| Captura (1) | atraccion-captura | Leads, CPL | Conversion Rate (visitor → lead) |
| Nutricion (2) | nutricion-oportunidad | MQLs, Email Open Rate | Retargeting Reach, Click Rate |
| Oportunidad (3) | nutricion-oportunidad | SQLs, Pipeline Value | Checkout Init Rate, No-show Rate |
| Ventas (4) | ventas | Revenue, New Customers | CAC, Conversion Rate (SQL → customer) |
| Adopcion (5) | adopcion | Health %, Active Users | Time-to-Value, Refund % |
| Expansion (6) | expansion-evangelizacion | Net MRR, LTV | Churn Rate, Upsell Revenue |
| Evangelizacion (7) | expansion-evangelizacion | K-Factor, Referrals | NPS, Referral Revenue |

## Organic vs Paid: A Dimension, Not a Separation

Treat `source_type` (paid / organic / email / direct / referral) as a **dimension** — like country or campaign. This allows:
- Filtering any view by source type
- Grouping KPIs by paid/organic in any chart
- Cross-channel attribution without separate dashboards

The best pattern (Funnel.io model): unified view with filter toggles, not separate pages.

## Important

- This map covers the most common metrics. Each platform has dozens more.
- Always use Knowledge Routing (SKILL.md) to verify before designing.
- When proposing a metric, justify WHY it's better than alternatives (see "Better Than" column above).
- Metrics that require premium API tiers or special permissions: flag in the spec.
