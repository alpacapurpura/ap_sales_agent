import { type Page, type Route } from '@playwright/test';
import { YT_ORGANIC_DASHBOARD_MOCK, ATTRACTION_WITH_YT_MOCK } from './yt-organic-mock-data';
import { emptyStageOverview } from './growth-studio.fixture';

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

  // Remove the base catch-all attraction handler (registered by growthStudioTest fixture)
  // before registering channel-specific data. Playwright stacks route handlers
  // and doesn't replace them, so without unroute the base empty-data handler persists.
  if (!skip.includes('attraction')) {
    await page.unroute('**/api/v1/analytics/metrics/attraction**');
  }

  // Attraction detail (with YT Organic channel data)
  if (overrides?.attraction) {
    await page.route('**/api/v1/analytics/metrics/attraction**', overrides.attraction);
  } else if (!skip.includes('attraction')) {
    await page.route('**/api/v1/analytics/metrics/attraction**', async (route) => {
      await route.fulfill({ json: ATTRACTION_WITH_YT_MOCK, status: 200 });
    });
  }

  // Stage overview with YT Organic in channel_list (Tier 1).
  await page.route('**/api/v1/analytics/metrics/attraction/overview**', async (route) => {
    await route.fulfill({
      json: {
        ...emptyStageOverview('attraction'),
        groups: [{ group_key: 'organic_social', group_label: 'Redes Orgánicas', channel_count: 1 }],
        channel_list: [{
          slug: 'yt-organic',
          name: 'YouTube Orgánico',
          channel_type: 'organic_social',
          group_key: 'organic_social',
          connected: true,
          headline_kpi: { name: 'views', value: 125000, unit: 'count' },
          last_updated: new Date().toISOString(),
          stale: false,
          provider_name: 'youtube',
        }],
      },
      status: 200,
    });
  });

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
