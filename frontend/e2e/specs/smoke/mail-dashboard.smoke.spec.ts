import { growthStudioTest as test } from '../../fixtures/growth-studio.fixture';
import { MailDashboardPage } from '../../pages/mail-dashboard.page';
import { setupMailDashboardMocks } from '../../fixtures/mail-dashboard-setup';

test.describe('Email Marketing Dashboard @smoke', () => {
  test('dashboard carga vía URL directa con título y 6 tabs', async ({ growthStudioPage, tenantId }) => {
    const mailPage = new MailDashboardPage(growthStudioPage, tenantId);
    await setupMailDashboardMocks(growthStudioPage);

    await mailPage.gotoExpandedDashboard();
    await mailPage.expectFullDashboardVisible();
    await mailPage.expectAllTabs();
    await mailPage.expectPeriodSelector();
  });

  test('tab Panorama muestra hero KPIs, gráfico y embudo', async ({ growthStudioPage, tenantId }) => {
    const mailPage = new MailDashboardPage(growthStudioPage, tenantId);
    await setupMailDashboardMocks(growthStudioPage);

    await mailPage.gotoExpandedDashboard();
    await mailPage.expectFullDashboardVisible();
    await mailPage.expectPanoramaTabContent();
  });

  test('tab Entregabilidad está disponible', async ({ growthStudioPage, tenantId }) => {
    const mailPage = new MailDashboardPage(growthStudioPage, tenantId);
    await setupMailDashboardMocks(growthStudioPage);

    await mailPage.gotoExpandedDashboard();
    await mailPage.clickTab('Entregabilidad');
    await mailPage.expectTabActive('Entregabilidad');
    await mailPage.expectEntregabilidadTabContent();
  });

  test('tab Crecimiento está disponible', async ({ growthStudioPage, tenantId }) => {
    const mailPage = new MailDashboardPage(growthStudioPage, tenantId);
    await setupMailDashboardMocks(growthStudioPage);

    await mailPage.gotoExpandedDashboard();
    await mailPage.clickTab('Crecimiento');
    await mailPage.expectTabActive('Crecimiento');
    await mailPage.expectCrecimientoTabContent();
  });

  test('tab Automatizaciones está disponible', async ({ growthStudioPage, tenantId }) => {
    const mailPage = new MailDashboardPage(growthStudioPage, tenantId);
    await setupMailDashboardMocks(growthStudioPage);

    await mailPage.gotoExpandedDashboard();
    await mailPage.clickTab('Automatizaciones');
    await mailPage.expectTabActive('Automatizaciones');
    await mailPage.expectAutomatizacionesTabContent();
  });

  test('navegación directa a tab vía URL con ?tab=entregabilidad', async ({ growthStudioPage, tenantId }) => {
    const mailPage = new MailDashboardPage(growthStudioPage, tenantId);
    await setupMailDashboardMocks(growthStudioPage);

    await mailPage.gotoExpandedDashboard('entregabilidad');
    await mailPage.expectFullDashboardVisible();
    await mailPage.expectTabActive('Entregabilidad');
  });

  test('todos los tabs son navegables cíclicamente', async ({ growthStudioPage, tenantId }) => {
    const mailPage = new MailDashboardPage(growthStudioPage, tenantId);
    await setupMailDashboardMocks(growthStudioPage);

    await mailPage.gotoExpandedDashboard();
    await mailPage.expectFullDashboardVisible();

    await mailPage.clickTab('Campañas');
    await mailPage.expectTabActive('Campañas');

    await mailPage.clickTab('Entregabilidad');
    await mailPage.expectTabActive('Entregabilidad');

    await mailPage.clickTab('Crecimiento');
    await mailPage.expectTabActive('Crecimiento');

    await mailPage.clickTab('Automatizaciones');
    await mailPage.expectTabActive('Automatizaciones');

    await mailPage.clickTab('Panorama');
    await mailPage.expectTabActive('Panorama');
  });
});
