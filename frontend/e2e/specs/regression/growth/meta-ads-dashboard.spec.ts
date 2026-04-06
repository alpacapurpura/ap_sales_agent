import { growthStudioTest as test, expect } from '../../../fixtures/growth-studio.fixture';
import { MetaAdsDashboardPage } from '../../../pages/meta-ads-dashboard.page';
import { setupMetaAdsMocks } from '../../../fixtures/meta-ads-setup';
import { META_ADS_DASHBOARD_MOCK, ATTRACTION_DETAIL_MOCK } from '../../../fixtures/meta-ads-mock-data';

/**
 * Meta Ads Dashboard E2E regression tests.
 *
 * All analytics endpoints are mocked (staging backend may be unreachable
 * from the e2e_runner container). Focus is on UI behavior validation.
 */

async function setupAndNavigate(page: import('@playwright/test').Page, metaAds: MetaAdsDashboardPage) {
  await setupMetaAdsMocks(page);
  await metaAds.gotoGrowthStudio();
}

test.describe('Meta Ads Dashboard - Sidebar Overview', () => {
  let metaAds: MetaAdsDashboardPage;

  test.beforeEach(async ({ growthStudioPage, tenantId }) => {
    metaAds = new MetaAdsDashboardPage(growthStudioPage, tenantId);
  });

  test('sidebar opens with wide layout when clicking Meta Ads', async ({ growthStudioPage }) => {
    await setupAndNavigate(growthStudioPage, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();

    const panel = growthStudioPage.locator('[class*="w-[650px]"]');
    await expect(panel).toBeVisible({ timeout: 5_000 });
  });

  test('sidebar shows period selector with 3 options', async ({ growthStudioPage }) => {
    await setupAndNavigate(growthStudioPage, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.expectPeriodSelectorVisible();
  });

  test('sidebar shows hero KPI cards with values', async ({ growthStudioPage }) => {
    await setupAndNavigate(growthStudioPage, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.expectHeroKpis();

    const dialog = growthStudioPage.getByRole('dialog');
    await expect(dialog.getByText('$2,500.00')).toBeVisible();
    await expect(dialog.getByText('2.80x')).toBeVisible();
  });

  test('sidebar shows benchmark badges', async ({ growthStudioPage }) => {
    await setupAndNavigate(growthStudioPage, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.expectBenchmarkBadges();
  });

  test('sidebar shows mini conversion funnel', async ({ growthStudioPage }) => {
    await setupAndNavigate(growthStudioPage, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.expectMiniFunnel();

    const dialog = growthStudioPage.getByRole('dialog');
    await expect(dialog.getByText('120,000')).toBeVisible();
    await expect(dialog.getByText('2,880')).toBeVisible();
  });

  test('sidebar shows reach/frequency with alert', async ({ growthStudioPage }) => {
    await setupAndNavigate(growthStudioPage, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.expectReachFrequency();
    await metaAds.expectFrequencyAlert('warning');
  });

  test('sidebar has Dashboard completo button', async ({ growthStudioPage }) => {
    await setupAndNavigate(growthStudioPage, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await expect(growthStudioPage.getByRole('button', { name: /Dashboard completo/i })).toBeVisible();
  });
});

test.describe('Meta Ads Dashboard - Full Page', () => {
  let metaAds: MetaAdsDashboardPage;

  test.beforeEach(async ({ growthStudioPage, tenantId }) => {
    metaAds = new MetaAdsDashboardPage(growthStudioPage, tenantId);
  });

  test('full dashboard opens with 5 tabs', async ({ growthStudioPage }) => {
    await setupAndNavigate(growthStudioPage, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.clickOpenFullDashboard();
    await metaAds.expectFullDashboardVisible();
    await metaAds.expectAllTabs();
  });

  test('Resumen tab shows composite chart', async ({ growthStudioPage }) => {
    await setupAndNavigate(growthStudioPage, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.clickOpenFullDashboard();
    await metaAds.expectFullDashboardVisible();
    await metaAds.expectResumenTabContent();
  });

  test('Costos tab shows cost KPIs with benchmarks', async ({ growthStudioPage }) => {
    await setupAndNavigate(growthStudioPage, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.clickOpenFullDashboard();
    await metaAds.expectFullDashboardVisible();
    await metaAds.expectCostosTabContent();
  });

  test('Campañas tab shows campaign table', async ({ growthStudioPage }) => {
    await setupAndNavigate(growthStudioPage, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.clickOpenFullDashboard();
    await metaAds.expectFullDashboardVisible();
    await metaAds.expectCampanasTabContent();
  });

  test('Volver button closes full dashboard', async ({ growthStudioPage }) => {
    await setupAndNavigate(growthStudioPage, metaAds);
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.clickOpenFullDashboard();
    await metaAds.expectFullDashboardVisible();
    await metaAds.closeFullDashboard();
    await expect(growthStudioPage.getByText('Meta Ads · Dashboard')).not.toBeVisible();
  });
});

test.describe('Meta Ads Dashboard - API & Tenant', () => {
  let metaAds: MetaAdsDashboardPage;

  test.beforeEach(async ({ growthStudioPage, tenantId }) => {
    metaAds = new MetaAdsDashboardPage(growthStudioPage, tenantId);
  });

  test('channel dashboard API includes X-Tenant-ID', async ({ growthStudioPage, tenantId }) => {
    const capturedHeaders: Record<string, string>[] = [];

    // Use override to capture headers while still returning valid data
    await setupMetaAdsMocks(growthStudioPage, {
      channelDashboard: async (route) => {
        capturedHeaders.push(route.request().headers());
        await route.fulfill({ json: META_ADS_DASHBOARD_MOCK, status: 200 });
      },
    });

    await metaAds.gotoGrowthStudio();
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();

    expect(capturedHeaders.length).toBeGreaterThan(0);
    expect(capturedHeaders[0]['x-tenant-id']).toBe(tenantId);
  });

  test('handles empty data gracefully without crash', async ({ growthStudioPage }) => {
    // Use override to provide empty dashboard data
    await setupMetaAdsMocks(growthStudioPage, {
      channelDashboard: async (route) => {
        await route.fulfill({
          json: { channel_slug: 'meta-ads', channel_name: 'Meta Ads', industry_category: 'general', period: '30d', kpis: [], time_series: [], funnel: { steps: [] }, frequency_alert: null },
          status: 200,
        });
      },
    });

    await metaAds.gotoGrowthStudio();
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();

    // With empty data, sidebar should remain stable (not crash)
    // Period selector and title should still be visible
    const dialog = growthStudioPage.getByRole('dialog');
    await expect(dialog.getByText('Meta Ads')).toBeVisible();
    await expect(dialog.getByText('30 días')).toBeVisible();
    // No KPI cards should be present
    await expect(dialog.getByText('Inversión')).not.toBeVisible();
    await expect(dialog.getByText('ROAS')).not.toBeVisible();
  });
});
