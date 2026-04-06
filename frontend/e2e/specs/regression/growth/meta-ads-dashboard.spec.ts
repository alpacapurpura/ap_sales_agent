import { test, expect } from '../../../fixtures/auth.fixture';
import { MetaAdsDashboardPage } from '../../../pages/meta-ads-dashboard.page';
import { setupMetaAdsMocks } from '../../../fixtures/meta-ads-setup';
import { META_ADS_DASHBOARD_MOCK } from '../../../fixtures/meta-ads-mock-data';

/**
 * Meta Ads Dashboard E2E regression tests.
 *
 * All analytics endpoints are mocked (staging backend may be unreachable
 * from the e2e_runner container). Focus is on UI behavior validation.
 */

async function setupAndNavigate(page: import('@playwright/test').Page, metaAds: MetaAdsDashboardPage) {
  await setupMetaAdsMocks(page);
  await metaAds.gotoGrowthStudio();
  await page.waitForTimeout(3000);
}

test.describe('Meta Ads Dashboard - Sidebar Overview', () => {
  let metaAds: MetaAdsDashboardPage;

  test.beforeEach(async ({ page, tenantId }) => {
    metaAds = new MetaAdsDashboardPage(page, tenantId);
  });

  test('sidebar opens with wide layout when clicking Meta Ads', async ({ page }) => {
    await setupAndNavigate(page, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();

    const panel = page.locator('[class*="w-[650px]"]');
    await expect(panel).toBeVisible({ timeout: 5_000 });
  });

  test('sidebar shows period selector with 3 options', async ({ page }) => {
    await setupAndNavigate(page, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.expectPeriodSelectorVisible();
  });

  test('sidebar shows hero KPI cards with values', async ({ page }) => {
    await setupAndNavigate(page, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.expectHeroKpis();

    const dialog = page.getByRole('dialog');
    await expect(dialog.getByText('$2,500.00')).toBeVisible();
    await expect(dialog.getByText('2.80x')).toBeVisible();
  });

  test('sidebar shows benchmark badges', async ({ page }) => {
    await setupAndNavigate(page, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.expectBenchmarkBadges();
  });

  test('sidebar shows mini conversion funnel', async ({ page }) => {
    await setupAndNavigate(page, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.expectMiniFunnel();

    const dialog = page.getByRole('dialog');
    await expect(dialog.getByText('120,000')).toBeVisible();
    await expect(dialog.getByText('2,880')).toBeVisible();
  });

  test('sidebar shows reach/frequency with alert', async ({ page }) => {
    await setupAndNavigate(page, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.expectReachFrequency();
    await metaAds.expectFrequencyAlert('warning');
  });

  test('sidebar has Dashboard completo button', async ({ page }) => {
    await setupAndNavigate(page, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await expect(page.getByRole('button', { name: /Dashboard completo/i })).toBeVisible();
  });
});

test.describe('Meta Ads Dashboard - Full Page', () => {
  let metaAds: MetaAdsDashboardPage;

  test.beforeEach(async ({ page, tenantId }) => {
    metaAds = new MetaAdsDashboardPage(page, tenantId);
  });

  test('full dashboard opens with 5 tabs', async ({ page }) => {
    await setupAndNavigate(page, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.clickOpenFullDashboard();
    await metaAds.expectFullDashboardVisible();
    await metaAds.expectAllTabs();
  });

  test('Overview tab shows composite chart', async ({ page }) => {
    await setupAndNavigate(page, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.clickOpenFullDashboard();
    await metaAds.expectFullDashboardVisible();
    await metaAds.expectOverviewTabContent();
  });

  test('Costs tab shows cost KPIs with benchmarks', async ({ page }) => {
    await setupAndNavigate(page, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.clickOpenFullDashboard();
    await metaAds.expectFullDashboardVisible();
    await metaAds.expectCostsTabContent();
  });

  test('placeholder tabs show Próximamente', async ({ page }) => {
    await setupAndNavigate(page, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.clickOpenFullDashboard();
    await metaAds.expectFullDashboardVisible();
    await metaAds.expectPlaceholderTab('Campañas');
  });

  test('Volver button closes full dashboard', async ({ page }) => {
    await setupAndNavigate(page, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.clickOpenFullDashboard();
    await metaAds.expectFullDashboardVisible();
    await metaAds.closeFullDashboard();
    await expect(page.getByText('Meta Ads · Dashboard')).not.toBeVisible();
  });
});

test.describe('Meta Ads Dashboard - API & Tenant', () => {
  let metaAds: MetaAdsDashboardPage;

  test.beforeEach(async ({ page, tenantId }) => {
    metaAds = new MetaAdsDashboardPage(page, tenantId);
  });

  test('channel dashboard API includes X-Tenant-ID', async ({ page, tenantId }) => {
    const capturedHeaders: Record<string, string>[] = [];

    // Register header capture BEFORE other mocks (first matching route wins)
    await page.route('**/api/v1/analytics/metrics/channel/*/dashboard**', async (route) => {
      capturedHeaders.push(route.request().headers());
      await route.fulfill({ json: META_ADS_DASHBOARD_MOCK, status: 200 });
    });

    // Setup remaining mocks (attraction, summary, etc.)
    await page.route('**/api/v1/analytics/metrics/attraction**', async (route) => {
      const { ATTRACTION_DETAIL_MOCK } = await import('../../../fixtures/meta-ads-mock-data');
      await route.fulfill({ json: ATTRACTION_DETAIL_MOCK, status: 200 });
    });
    await page.route('**/api/v1/analytics/metrics/summary**', async (route) => {
      await route.fulfill({ json: { attraction: { visitors: 50000 }, capture: { leads: 385 }, nurture: { mqls: 120 }, opportunity: { sqls: 45 }, sales: { revenue: 7000 }, adoption: { health_pct: 85 }, expansion: { net_mrr: 3200 }, evangelization: { k_factor: 1.2 } }, status: 200 });
    });
    await page.route('**/api/v1/analytics/metrics/capture**', async (route) => {
      await route.fulfill({ json: { header_kpis: { total_leads: 385, conversion_rate: 0.77, cost_per_lead: 6.5 }, mini_funnel: { source_label: 'V', source_value: 50000, target_label: 'L', target_value: 385, conversion_rate: 0.77 }, web_infrastructure: { totals: {}, channels: [] }, ai_agent: { totals: {}, channels: [] }, period: 'last_30_days' }, status: 200 });
    });
    await page.route('**/api/v1/analytics/metrics/timeseries**', async (route) => {
      await route.fulfill({ json: { stage: 'attraction', metric_name: 'visitors', granularity: 'daily', range_days: 30, data_points: [], channels_present: [], period_totals: {}, previous_period_totals: null }, status: 200 });
    });
    await page.route('**/api/v1/analytics/metrics/catalog**', async (route) => {
      await route.fulfill({ json: { metrics: [], count: 0 }, status: 200 });
    });
    await page.route('**/api/v1/connections/**', async (route) => {
      await route.fulfill({ json: {}, status: 200 });
    });

    await metaAds.gotoGrowthStudio();
    await page.waitForTimeout(3000);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();

    expect(capturedHeaders.length).toBeGreaterThan(0);
    expect(capturedHeaders[0]['x-tenant-id']).toBe(tenantId);
  });

  test('handles empty data gracefully without crash', async ({ page }) => {
    // Setup all mocks except dashboard (manually provide empty dashboard)
    await page.route('**/api/v1/analytics/metrics/attraction**', async (route) => {
      const { ATTRACTION_DETAIL_MOCK } = await import('../../../fixtures/meta-ads-mock-data');
      await route.fulfill({ json: ATTRACTION_DETAIL_MOCK, status: 200 });
    });
    await page.route('**/api/v1/analytics/metrics/channel/meta-ads/dashboard**', async (route) => {
      await route.fulfill({
        json: { channel_slug: 'meta-ads', channel_name: 'Meta Ads', industry_category: 'general', period: '30d', kpis: [], time_series: [], funnel: { steps: [] }, frequency_alert: null },
        status: 200,
      });
    });
    await page.route('**/api/v1/analytics/metrics/summary**', async (route) => {
      await route.fulfill({ json: { attraction: { visitors: 50000 }, capture: { leads: 385 }, nurture: { mqls: 120 }, opportunity: { sqls: 45 }, sales: { revenue: 7000 }, adoption: { health_pct: 85 }, expansion: { net_mrr: 3200 }, evangelization: { k_factor: 1.2 } }, status: 200 });
    });
    await page.route('**/api/v1/analytics/metrics/capture**', async (route) => {
      await route.fulfill({ json: { header_kpis: { total_leads: 385, conversion_rate: 0.77, cost_per_lead: 6.5 }, mini_funnel: { source_label: 'V', source_value: 50000, target_label: 'L', target_value: 385, conversion_rate: 0.77 }, web_infrastructure: { totals: {}, channels: [] }, ai_agent: { totals: {}, channels: [] }, period: 'last_30_days' }, status: 200 });
    });
    await page.route('**/api/v1/analytics/metrics/timeseries**', async (route) => {
      await route.fulfill({ json: { stage: 'attraction', metric_name: 'visitors', granularity: 'daily', range_days: 30, data_points: [], channels_present: [], period_totals: {}, previous_period_totals: null }, status: 200 });
    });
    await page.route('**/api/v1/analytics/metrics/catalog**', async (route) => {
      await route.fulfill({ json: { metrics: [], count: 0 }, status: 200 });
    });
    await page.route('**/api/v1/connections/**', async (route) => {
      await route.fulfill({ json: {}, status: 200 });
    });

    await metaAds.gotoGrowthStudio();
    await page.waitForTimeout(3000);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();

    // With empty data, sidebar should remain stable (not crash)
    // Period selector and title should still be visible
    const dialog = page.getByRole('dialog');
    await expect(dialog.getByText('Meta Ads')).toBeVisible();
    await expect(dialog.getByText('30 días')).toBeVisible();
    // No KPI cards should be present
    await expect(dialog.getByText('Inversión')).not.toBeVisible();
    await expect(dialog.getByText('ROAS')).not.toBeVisible();
  });
});
