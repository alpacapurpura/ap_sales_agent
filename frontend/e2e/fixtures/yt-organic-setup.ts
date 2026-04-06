import { type Page, type Route } from '@playwright/test';
import { YT_ORGANIC_DASHBOARD_MOCK, ATTRACTION_WITH_YT_MOCK } from './yt-organic-mock-data';

/**
 * Override options for YT Organic mocks.
 * Use these to test edge cases (empty data, error states, etc.).
 */
export interface YtOrganicMockOverrides {
  /** Custom handler for channel dashboard -- replaces default */
  channelDashboard?: (route: Route) => Promise<void>;
  /** Custom handler for attraction detail -- replaces default */
  attraction?: (route: Route) => Promise<void>;
  /** Route patterns to skip (don't register default handler) */
  skipPatterns?: ('attraction' | 'channel-dashboard')[];
}

/**
 * Intercepts YT Organic-specific API calls for E2E test determinism.
 * Base Growth Studio mocks (summary, capture, timeseries, catalog, connections)
 * are handled by the `growthStudioTest` fixture.
 */
export async function setupYtOrganicMocks(page: Page, overrides?: YtOrganicMockOverrides) {
  const skip = overrides?.skipPatterns ?? [];

  // Attraction detail (with YT Organic channel data)
  if (overrides?.attraction) {
    await page.route('**/api/v1/analytics/metrics/attraction**', overrides.attraction);
  } else if (!skip.includes('attraction')) {
    await page.route('**/api/v1/analytics/metrics/attraction**', async (route) => {
      await route.fulfill({ json: ATTRACTION_WITH_YT_MOCK, status: 200 });
    });
  }

  // Channel dashboard
  if (overrides?.channelDashboard) {
    await page.route('**/api/v1/analytics/metrics/channel/yt-organic/dashboard**', overrides.channelDashboard);
  } else if (!skip.includes('channel-dashboard')) {
    await page.route('**/api/v1/analytics/metrics/channel/yt-organic/dashboard**', async (route) => {
      const url = route.request().url();
      const period = new URL(url).searchParams.get('period') ?? '30d';
      await route.fulfill({ json: { ...YT_ORGANIC_DASHBOARD_MOCK, period }, status: 200 });
    });
  }
}
