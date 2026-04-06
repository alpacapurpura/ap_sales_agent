import { growthStudioTest as test } from '../../fixtures/growth-studio.fixture';
import { MetaAdsDashboardPage } from '../../pages/meta-ads-dashboard.page';
import { setupMetaAdsMocks } from '../../fixtures/meta-ads-setup';

test.describe('Meta Ads Dashboard @smoke', () => {
  test('sidebar opens and shows KPIs when clicking Meta Ads channel', async ({ growthStudioPage, tenantId }) => {
    const metaAds = new MetaAdsDashboardPage(growthStudioPage, tenantId);
    await setupMetaAdsMocks(growthStudioPage);

    // Reload to pick up the Meta Ads channel mocks (attraction override with channel data)
    await metaAds.gotoGrowthStudio();

    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.expectHeroKpis();
    await metaAds.expectMiniFunnel();
  });

  test('full dashboard opens from sidebar and shows all 5 redesigned tabs', async ({ growthStudioPage, tenantId }) => {
    const metaAds = new MetaAdsDashboardPage(growthStudioPage, tenantId);
    await setupMetaAdsMocks(growthStudioPage);

    await metaAds.gotoGrowthStudio();

    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.clickOpenFullDashboard();
    await metaAds.expectFullDashboardVisible();
    await metaAds.expectAllTabs();
  });

  test('each tab renders content without errors', async ({ growthStudioPage, tenantId }) => {
    const metaAds = new MetaAdsDashboardPage(growthStudioPage, tenantId);
    await setupMetaAdsMocks(growthStudioPage);

    await metaAds.gotoGrowthStudio();
    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.clickOpenFullDashboard();
    await metaAds.expectFullDashboardVisible();

    // Resumen tab (default)
    await metaAds.expectResumenTabContent();

    // Campañas tab
    await metaAds.expectCampanasTabContent();

    // Creativos tab
    await metaAds.expectCreativosTabContent();

    // Audiencia tab
    await metaAds.expectAudienciaTabContent();

    // Costos tab
    await metaAds.expectCostosTabContent();
  });
});
