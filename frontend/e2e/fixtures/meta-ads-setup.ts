import { type Page, type Route } from '@playwright/test';
import { META_ADS_DASHBOARD_MOCK, ATTRACTION_DETAIL_MOCK } from './meta-ads-mock-data';

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
