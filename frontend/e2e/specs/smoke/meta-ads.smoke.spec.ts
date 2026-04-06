import { test } from '../../fixtures/auth.fixture';
import { MetaAdsDashboardPage } from '../../pages/meta-ads-dashboard.page';
import { setupMetaAdsMocks } from '../../fixtures/meta-ads-setup';

test.describe('Meta Ads Dashboard @smoke', () => {
  test('sidebar opens and shows KPIs when clicking Meta Ads channel', async ({ page, tenantId }) => {
    const metaAds = new MetaAdsDashboardPage(page, tenantId);
    await setupMetaAdsMocks(page);

    await metaAds.gotoGrowthStudio();
    await page.waitForTimeout(3000);

    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.expectHeroKpis();
    await metaAds.expectMiniFunnel();
  });

  test('full dashboard opens from sidebar and shows tabs', async ({ page, tenantId }) => {
    const metaAds = new MetaAdsDashboardPage(page, tenantId);
    await setupMetaAdsMocks(page);

    await metaAds.gotoGrowthStudio();
    await page.waitForTimeout(3000);

    await metaAds.clickMetaAdsChannel();
    await metaAds.expectSidebarVisible();
    await metaAds.clickOpenFullDashboard();
    await metaAds.expectFullDashboardVisible();
    await metaAds.expectAllTabs();
  });
});
