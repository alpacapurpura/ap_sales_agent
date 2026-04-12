import { type Page, type Route } from '@playwright/test';
import { IG_ORGANIC_DASHBOARD_MOCK, ATTRACTION_WITH_IG_MOCK } from './ig-organic-mock-data';
import { emptyStageOverview } from './growth-studio.fixture';

/**
 * Override options for IG Organic mocks.
 * Use these to test edge cases (empty data, error states, etc.).
 */
export interface IgOrganicMockOverrides {
  /** Custom handler for channel dashboard -- replaces default */
  channelDashboard?: (route: Route) => Promise<void>;
  /** Custom handler for attraction detail -- replaces default */
  attraction?: (route: Route) => Promise<void>;
  /** Route patterns to skip (don't register default handler) */
  skipPatterns?: ('attraction' | 'channel-dashboard')[];
}

/**
 * Intercepts IG Organic-specific API calls to provide deterministic test data.
 *
 * Base Growth Studio mocks (summary, capture, timeseries, catalog, connections)
 * are handled by the `growthStudioTest` fixture -- this function only adds
 * the channel-specific routes.
 */
export async function setupIgOrganicMocks(page: Page, overrides?: IgOrganicMockOverrides) {
  const skip = overrides?.skipPatterns ?? [];

  // Remove the base catch-all attraction handler (registered by growthStudioTest fixture)
  // before registering channel-specific data. Playwright stacks route handlers
  // and doesn't replace them, so without unroute the base empty-data handler persists.
  if (!skip.includes('attraction')) {
    await page.unroute('**/api/v1/analytics/metrics/attraction**');
  }

  // Attraction detail (with IG Organic channel data)
  if (overrides?.attraction) {
    await page.route('**/api/v1/analytics/metrics/attraction**', overrides.attraction);
  } else if (!skip.includes('attraction')) {
    await page.route('**/api/v1/analytics/metrics/attraction**', async (route) => {
      await route.fulfill({ json: ATTRACTION_WITH_IG_MOCK, status: 200 });
    });
  }

  // Stage overview with IG Organic in channel_list (Tier 1).
  // Registered AFTER detail handler → LIFO gives it priority for /overview URLs.
  await page.route('**/api/v1/analytics/metrics/attraction/overview**', async (route) => {
    await route.fulfill({
      json: {
        ...emptyStageOverview('attraction'),
        groups: [{ group_key: 'organic_social', group_label: 'Redes Orgánicas', channel_count: 1 }],
        channel_list: [{
          slug: 'ig-organic',
          name: 'Instagram Orgánico',
          channel_type: 'organic_social',
          group_key: 'organic_social',
          connected: true,
          headline_kpi: { name: 'total_interactions', value: 2450, unit: 'count' },
          last_updated: new Date().toISOString(),
          stale: false,
          provider_name: 'meta',
        }],
      },
      status: 200,
    });
  });

  // Channel dashboard
  if (overrides?.channelDashboard) {
    await page.route('**/api/v1/analytics/metrics/channel/ig-organic/dashboard**', overrides.channelDashboard);
  } else if (!skip.includes('channel-dashboard')) {
    await page.route('**/api/v1/analytics/metrics/channel/ig-organic/dashboard**', async (route) => {
      const url = route.request().url();
      const period = new URL(url).searchParams.get('period') ?? '30d';
      await route.fulfill({ json: { ...IG_ORGANIC_DASHBOARD_MOCK, period }, status: 200 });
    });
  }
}
