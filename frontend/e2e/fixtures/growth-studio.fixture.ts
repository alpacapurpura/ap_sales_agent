import { type Page } from '@playwright/test';
import { test as base, expect } from './auth.fixture';

/**
 * Sets up base API mocks that Growth Studio needs to render without errors.
 * Channel-specific mocks (e.g. meta-ads dashboard) are NOT included here.
 */
async function setupGrowthStudioBaseMocks(page: Page) {
  await page.route('**/api/v1/analytics/metrics/attraction**', async (route) => {
    // Minimal attraction data — individual channel fixtures provide richer data
    await route.fulfill({
      json: {
        organic_social: { totals: {}, channels: [] },
        ga4_search: { totals: {}, channels: [] },
        paid: { totals: {}, channels: [] },
        outbound: { totals: {}, channels: [] },
        website: { totals: {}, channels: [] },
        period: 'last_30_days',
        last_updated: null,
      },
      status: 200,
    });
  });

  await page.route('**/api/v1/analytics/metrics/summary**', async (route) => {
    await route.fulfill({
      json: {
        attraction: { visitors: 50000, spend: 2500 },
        capture: { leads: 385, conversion_rate: 0.77 },
        nurture: { mqls: 120, conversion_rate: 31.17 },
        opportunity: { sqls: 45, conversion_rate: 37.5 },
        sales: { revenue: 7000, customers: 78 },
        adoption: { health_pct: 85, active: 66 },
        expansion: { net_mrr: 3200, churn_rate: 2.1 },
        evangelization: { k_factor: 1.2, referrals: 15 },
      },
      status: 200,
    });
  });

  await page.route('**/api/v1/analytics/metrics/capture**', async (route) => {
    await route.fulfill({
      json: {
        header_kpis: { total_leads: 385, conversion_rate: 0.77, cost_per_lead: 6.5 },
        mini_funnel: { source_label: 'Visitantes', source_value: 50000, target_label: 'Leads', target_value: 385, conversion_rate: 0.77 },
        web_infrastructure: { totals: {}, channels: [] },
        ai_agent: { totals: {}, channels: [] },
        period: 'last_30_days',
      },
      status: 200,
    });
  });

  await page.route('**/api/v1/analytics/metrics/timeseries**', async (route) => {
    await route.fulfill({
      json: { stage: 'attraction', metric_name: 'visitors', granularity: 'daily', range_days: 30, data_points: [], channels_present: [], period_totals: {}, previous_period_totals: null },
      status: 200,
    });
  });

  await page.route('**/api/v1/analytics/metrics/catalog**', async (route) => {
    await route.fulfill({ json: { metrics: [], count: 0 }, status: 200 });
  });

  await page.route('**/api/v1/connections/**', async (route) => {
    await route.fulfill({ json: {}, status: 200 });
  });
}

export { setupGrowthStudioBaseMocks, expect };

export const growthStudioTest = base.extend<{ growthStudioPage: Page }>({
  growthStudioPage: async ({ page, tenantId }, use) => {
    await setupGrowthStudioBaseMocks(page);
    await page.goto(`/${tenantId}/growth-studio/atraccion-captura`);
    await page.getByText('Atracción').first().waitFor({ state: 'visible', timeout: 10_000 });
    await use(page);
  },
});
