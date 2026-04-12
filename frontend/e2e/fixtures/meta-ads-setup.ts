import { type Page, type Route } from '@playwright/test';
import { META_ADS_DASHBOARD_MOCK, ATTRACTION_DETAIL_MOCK } from './meta-ads-mock-data';
import { emptyStageOverview } from './growth-studio.fixture';

/**
 * Override options for Meta Ads mocks.
 * Use these to test edge cases (empty data, header capture, etc.).
 */
export interface MockOverrides {
  /** Custom handler for channel dashboard — replaces default */
  channelDashboard?: (route: Route) => Promise<void>;
  /** Custom handler for attraction detail — replaces default */
  attraction?: (route: Route) => Promise<void>;
  /** Route patterns to skip (don't register default handler) */
  skipPatterns?: ('attraction' | 'channel-dashboard')[];
}

/**
 * Intercepts Meta Ads–specific API calls to provide deterministic test data.
 *
 * Base Growth Studio mocks (summary, capture, timeseries, catalog, connections)
 * are handled by the `growthStudioTest` fixture — this function only adds
 * the channel-specific routes.
 */
export async function setupMetaAdsMocks(page: Page, overrides?: MockOverrides) {
  const skip = overrides?.skipPatterns ?? [];

  // Remove the base catch-all attraction handler (registered by growthStudioTest fixture)
  // before registering channel-specific data. Playwright stacks route handlers
  // and doesn't replace them, so without unroute the base empty-data handler persists.
  if (!skip.includes('attraction')) {
    await page.unroute('**/api/v1/analytics/metrics/attraction**');
  }

  // Attraction detail (with Meta Ads channel data)
  if (overrides?.attraction) {
    await page.route('**/api/v1/analytics/metrics/attraction**', overrides.attraction);
  } else if (!skip.includes('attraction')) {
    await page.route('**/api/v1/analytics/metrics/attraction**', async (route) => {
      await route.fulfill({ json: ATTRACTION_DETAIL_MOCK, status: 200 });
    });
  }

  // Channel dashboard
  if (overrides?.channelDashboard) {
    await page.route('**/api/v1/analytics/metrics/channel/meta-ads/dashboard**', overrides.channelDashboard);
  } else if (!skip.includes('channel-dashboard')) {
    await page.route('**/api/v1/analytics/metrics/channel/meta-ads/dashboard**', async (route) => {
      const url = route.request().url();
      const period = new URL(url).searchParams.get('period') ?? '30d';
      await route.fulfill({ json: { ...META_ADS_DASHBOARD_MOCK, period }, status: 200 });
    });
  }

  // Stage overview with Meta Ads in channel_list (Tier 1).
  await page.route('**/api/v1/analytics/metrics/attraction/overview**', async (route) => {
    await route.fulfill({
      json: {
        ...emptyStageOverview('attraction'),
        groups: [{ group_key: 'paid', group_label: 'Pagado', channel_count: 1 }],
        channel_list: [{
          slug: 'meta-ads',
          name: 'Meta Ads',
          channel_type: 'paid',
          group_key: 'paid',
          connected: true,
          headline_kpi: { name: 'spend', value: 2500, unit: 'currency', currency: 'USD' },
          last_updated: new Date().toISOString(),
          stale: false,
          provider_name: 'meta',
        }],
      },
      status: 200,
    });
  });

  // Campaign performance (Campañas tab)
  await page.route('**/api/v1/analytics/campaigns/performance**', async (route) => {
    await route.fulfill({
      json: {
        campaigns: [
          {
            external_id: 'camp_1', name: 'Curso Principal', objective: 'OUTCOME_SALES',
            status: 'ACTIVE', effective_status: 'ACTIVE', daily_budget: 50000,
            lifetime_budget: null, budget_remaining: null, start_time: null, stop_time: null,
            ad_sets_count: 3, ads_count: 8,
            metrics: { spend: 1234, conversions: 89, cpa: 13.87, roas: 4.1, ctr: 2.8, cpc: 0.42, cpm: 11.8, frequency: 1.8, impressions: 104000, clicks: 2912, reach: 58000 },
            health: 'good',
          },
          {
            external_id: 'camp_2', name: 'Black Friday Leads', objective: 'OUTCOME_SALES',
            status: 'ACTIVE', effective_status: 'ACTIVE', daily_budget: 50000,
            lifetime_budget: null, budget_remaining: null, start_time: null, stop_time: null,
            ad_sets_count: 2, ads_count: 5,
            metrics: { spend: 567, conversions: 3, cpa: 189, roas: 0.8, ctr: 0.9, cpc: 1.85, cpm: 16.6, frequency: 3.4, impressions: 34000, clicks: 306, reach: 10000 },
            health: 'critical',
          },
          {
            external_id: 'camp_3', name: 'Retargeting Carrito', objective: 'OUTCOME_SALES',
            status: 'ACTIVE', effective_status: 'IN_PROCESS', daily_budget: 50000,
            lifetime_budget: null, budget_remaining: null, start_time: null, stop_time: null,
            ad_sets_count: 1, ads_count: 3,
            metrics: { spend: 812, conversions: 23, cpa: 35.3, roas: 2.3, ctr: 1.5, cpc: 0.98, cpm: 14.7, frequency: 5.2, impressions: 55000, clicks: 825, reach: 10500 },
            health: 'warning',
          },
        ],
        recommendations: [
          { recommendation_type: 'HIGH_CPA', source: 'system', title: 'Black Friday Leads tiene CPA alto', body: 'CPA 3x por encima del promedio', importance: 'CRITICAL', lift_estimate: null, opportunity_score: 0.9, url: null, object_ids: ['camp_2'] },
        ],
        total_campaigns: 3, active_campaigns: 3, currency: 'USD', last_synced: '2026-04-06T12:00:00Z',
      },
      status: 200,
    });
  });

  // Creatives overview (Creativos tab)
  await page.route('**/api/v1/analytics/campaigns/creatives**', async (route) => {
    await route.fulfill({
      json: {
        ads: [
          { external_id: 'ad_1', name: 'Video Testimonio Laura', campaign_name: 'Curso Principal', campaign_external_id: 'camp_1', status: 'ACTIVE', effective_status: 'ACTIVE', creative_thumbnail_url: null, creative_title: 'Testimonio Laura', creative_cta: 'LEARN_MORE', preview_shareable_link: null },
          { external_id: 'ad_2', name: 'Carrusel Beneficios', campaign_name: 'Curso Principal', campaign_external_id: 'camp_1', status: 'ACTIVE', effective_status: 'ACTIVE', creative_thumbnail_url: null, creative_title: 'Beneficios', creative_cta: 'SHOP_NOW', preview_shareable_link: null },
        ],
        video_retention: { plays: 12400, p25: 9100, p50: 6800, p75: 4200, p100: 2100 },
        total_ads: 2,
      },
      status: 200,
    });
  });

  // Demographics (Audiencia tab)
  await page.route('**/api/v1/analytics/metrics/channel/meta-ads/demographics**', async (route) => {
    await route.fulfill({
      json: {
        age: [
          { label: '18-24', value: 5000, percentage: 15 },
          { label: '25-34', value: 14000, percentage: 42 },
          { label: '35-44', value: 9300, percentage: 28 },
          { label: '45-54', value: 3300, percentage: 10 },
          { label: '55+', value: 1700, percentage: 5 },
        ],
        gender: [
          { label: 'Femenino', value: 22700, percentage: 68 },
          { label: 'Masculino', value: 10600, percentage: 32 },
        ],
        placement: [
          { label: 'Feed', value: 18300, percentage: 55 },
          { label: 'Stories', value: 8300, percentage: 25 },
          { label: 'Reels', value: 5000, percentage: 15 },
          { label: 'Otros', value: 1700, percentage: 5 },
        ],
      },
      status: 200,
    });
  });
}

/**
 * Full standalone setup — includes both base Growth Studio mocks AND Meta Ads
 * channel mocks. Use this when NOT using the `growthStudioTest` fixture.
 */
export async function setupMetaAdsFullMocks(page: Page, overrides?: MockOverrides) {
  const { setupGrowthStudioBaseMocks } = await import('./growth-studio.fixture');
  await setupGrowthStudioBaseMocks(page);
  await setupMetaAdsMocks(page, overrides);
}
