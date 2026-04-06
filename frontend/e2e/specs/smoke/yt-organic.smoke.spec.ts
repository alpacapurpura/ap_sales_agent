import { growthStudioTest as test } from '../../fixtures/growth-studio.fixture';
import { YtOrganicDashboardPage } from '../../pages/yt-organic-dashboard.page';
import { setupYtOrganicMocks } from '../../fixtures/yt-organic-setup';

test.describe('YouTube Organic Dashboard @smoke', () => {
  test('sidebar abre al hacer click en canal YT Organic', async ({ growthStudioPage, tenantId }) => {
    const ytPage = new YtOrganicDashboardPage(growthStudioPage, tenantId);
    await setupYtOrganicMocks(growthStudioPage);

    await ytPage.gotoGrowthStudio();
    await ytPage.clickYtOrganicChannel();
    await ytPage.expectSidebarVisible();
    await ytPage.expectHeroKpis();
    await ytPage.expectSubscriberGrowth();
  });

  test('sidebar abre v\u00eda URL directa (?channel=yt-organic)', async ({ growthStudioPage, tenantId }) => {
    const ytPage = new YtOrganicDashboardPage(growthStudioPage, tenantId);
    await setupYtOrganicMocks(growthStudioPage);

    await ytPage.gotoSidebarViaUrl('yt-organic');
    await ytPage.expectHeroKpis();
  });

  test('navega a dashboard expandido desde sidebar', async ({ growthStudioPage, tenantId }) => {
    const ytPage = new YtOrganicDashboardPage(growthStudioPage, tenantId);
    await setupYtOrganicMocks(growthStudioPage);

    await ytPage.gotoGrowthStudio();
    await ytPage.clickYtOrganicChannel();
    await ytPage.expectSidebarVisible();
    await ytPage.clickExpandedDashboard();
    await ytPage.expectFullDashboardVisible();
    await ytPage.expectAllTabs();
  });

  test('tabs funcionan en dashboard expandido', async ({ growthStudioPage, tenantId }) => {
    const ytPage = new YtOrganicDashboardPage(growthStudioPage, tenantId);
    await setupYtOrganicMocks(growthStudioPage);

    await ytPage.gotoGrowthStudio();
    await ytPage.clickYtOrganicChannel();
    await ytPage.expectSidebarVisible();
    await ytPage.clickExpandedDashboard();
    await ytPage.expectFullDashboardVisible();

    await ytPage.clickTab('Videos');
    await ytPage.expectTabActive('Videos');

    await ytPage.clickTab('Audiencia');
    await ytPage.expectTabActive('Audiencia');

    await ytPage.clickTab('Engagement');
    await ytPage.expectTabActive('Engagement');

    await ytPage.clickTab(/Retenci\u00f3n/);
    await ytPage.expectTabActive(/Retenci\u00f3n/);

    await ytPage.clickTab('Resumen');
    await ytPage.expectTabActive('Resumen');
  });

  test('acceso directo a tab v\u00eda URL', async ({ growthStudioPage, tenantId }) => {
    const ytPage = new YtOrganicDashboardPage(growthStudioPage, tenantId);
    await setupYtOrganicMocks(growthStudioPage);

    await ytPage.gotoExpandedDashboard('yt-organic', 'engagement');
    await ytPage.expectFullDashboardVisible();
    await ytPage.expectTabActive('Engagement');
  });

  test('bot\u00f3n Volver regresa desde dashboard', async ({ growthStudioPage, tenantId }) => {
    const ytPage = new YtOrganicDashboardPage(growthStudioPage, tenantId);
    await setupYtOrganicMocks(growthStudioPage);

    await ytPage.gotoGrowthStudio();
    await ytPage.clickYtOrganicChannel();
    await ytPage.expectSidebarVisible();
    await ytPage.clickExpandedDashboard();
    await ytPage.expectFullDashboardVisible();

    await ytPage.clickVolver();
    await ytPage.expectSidebarVisible();
  });
});
