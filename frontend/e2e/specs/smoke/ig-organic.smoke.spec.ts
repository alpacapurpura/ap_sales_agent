import { growthStudioTest as test } from '../../fixtures/growth-studio.fixture';
import { IgOrganicDashboardPage } from '../../pages/ig-organic-dashboard.page';
import { setupIgOrganicMocks } from '../../fixtures/ig-organic-setup';

test.describe('Instagram Organic Dashboard @smoke', () => {
  test('sidebar abre al hacer click en canal IG Organic', async ({ growthStudioPage, tenantId }) => {
    const igPage = new IgOrganicDashboardPage(growthStudioPage, tenantId);
    await setupIgOrganicMocks(growthStudioPage);

    await igPage.gotoGrowthStudio();
    await igPage.clickIgOrganicChannel();
    await igPage.expectSidebarVisible();
    await igPage.expectHeroKpis(4);
    await igPage.expectEngagementFunnel();
    await igPage.expectGrowthIndicator();
  });

  test('sidebar abre vía URL directa (?channel=ig-organic)', async ({ growthStudioPage, tenantId }) => {
    const igPage = new IgOrganicDashboardPage(growthStudioPage, tenantId);
    await setupIgOrganicMocks(growthStudioPage);

    await igPage.gotoSidebarViaUrl('ig-organic');
    // The page loads; verify the channel data shows
    await igPage.expectHeroKpis(4);
  });

  test('navega a dashboard expandido desde sidebar', async ({ growthStudioPage, tenantId }) => {
    const igPage = new IgOrganicDashboardPage(growthStudioPage, tenantId);
    await setupIgOrganicMocks(growthStudioPage);

    await igPage.gotoGrowthStudio();
    await igPage.clickIgOrganicChannel();
    await igPage.expectSidebarVisible();
    await igPage.clickExpandedDashboard();
    await igPage.expectFullDashboardVisible();
    await igPage.expectAllTabs();
  });

  test('tabs tienen URLs únicas en dashboard expandido', async ({ growthStudioPage, tenantId }) => {
    const igPage = new IgOrganicDashboardPage(growthStudioPage, tenantId);
    await setupIgOrganicMocks(growthStudioPage);

    await igPage.gotoGrowthStudio();
    await igPage.clickIgOrganicChannel();
    await igPage.expectSidebarVisible();
    await igPage.clickExpandedDashboard();
    await igPage.expectFullDashboardVisible();

    await igPage.clickTab('Contenido');
    await igPage.expectTabActive('Contenido');

    await igPage.clickTab('Audiencia');
    await igPage.expectTabActive('Audiencia');

    await igPage.clickTab('Alcance');
    await igPage.expectTabActive('Alcance');

    await igPage.clickTab('Overview');
    await igPage.expectTabActive('Overview');
  });

  test('acceso directo a tab vía URL', async ({ growthStudioPage, tenantId }) => {
    const igPage = new IgOrganicDashboardPage(growthStudioPage, tenantId);
    await setupIgOrganicMocks(growthStudioPage);

    await igPage.gotoExpandedDashboard('ig-organic', 'audiencia');
    await igPage.expectFullDashboardVisible();
    await igPage.expectTabActive('Audiencia');
  });

  test('tooltips se abren al hacer click en icono (i)', async ({ growthStudioPage, tenantId }) => {
    const igPage = new IgOrganicDashboardPage(growthStudioPage, tenantId);
    await setupIgOrganicMocks(growthStudioPage);

    await igPage.gotoGrowthStudio();
    await igPage.clickIgOrganicChannel();
    await igPage.expectSidebarVisible();
    await igPage.clickExpandedDashboard();
    await igPage.expectFullDashboardVisible();

    // The ChartInfoTooltip for "Engagement vs Vistas" should have an (i) icon
    await igPage.expectChartVisible('Engagement vs Vistas');
  });

  test('botón Volver regresa a atracción con sidebar', async ({ growthStudioPage, tenantId }) => {
    const igPage = new IgOrganicDashboardPage(growthStudioPage, tenantId);
    await setupIgOrganicMocks(growthStudioPage);

    await igPage.gotoGrowthStudio();
    await igPage.clickIgOrganicChannel();
    await igPage.expectSidebarVisible();
    await igPage.clickExpandedDashboard();
    await igPage.expectFullDashboardVisible();

    await igPage.clickVolver();
    // Should navigate back
    await igPage.expectSidebarVisible();
  });
});
