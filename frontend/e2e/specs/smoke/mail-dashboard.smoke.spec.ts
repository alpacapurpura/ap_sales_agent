import { growthStudioTest as test } from '../../fixtures/growth-studio.fixture';
import { MailDashboardPage } from '../../pages/mail-dashboard.page';
import { setupMailDashboardMocks } from '../../fixtures/mail-dashboard-setup';

test.describe('Email Marketing Dashboard @smoke', () => {
  test('dashboard carga vía URL directa con título y 5 tabs', async ({ growthStudioPage, tenantId }) => {
    const mailPage = new MailDashboardPage(growthStudioPage, tenantId);
    await setupMailDashboardMocks(growthStudioPage);

    await mailPage.gotoExpandedDashboard();
    await mailPage.expectFullDashboardVisible();
    await mailPage.expectAllTabs();
    await mailPage.expectPeriodSelector();
  });

  test('tab Resumen muestra hero KPIs, gráfico y funnel', async ({ growthStudioPage, tenantId }) => {
    const mailPage = new MailDashboardPage(growthStudioPage, tenantId);
    await setupMailDashboardMocks(growthStudioPage);

    await mailPage.gotoExpandedDashboard();
    await mailPage.expectFullDashboardVisible();
    await mailPage.expectOverviewTabContent();
  });

  test('tab Engagement muestra CTOR, Click Rate, Reenvíos y gráficos', async ({ growthStudioPage, tenantId }) => {
    const mailPage = new MailDashboardPage(growthStudioPage, tenantId);
    await setupMailDashboardMocks(growthStudioPage);

    await mailPage.gotoExpandedDashboard();
    await mailPage.clickTab('Engagement');
    await mailPage.expectTabActive('Engagement');
    await mailPage.expectEngagementTabContent();
  });

  test('tab Entregabilidad muestra health score, bounce rate y gráficos', async ({ growthStudioPage, tenantId }) => {
    const mailPage = new MailDashboardPage(growthStudioPage, tenantId);
    await setupMailDashboardMocks(growthStudioPage);

    await mailPage.gotoExpandedDashboard();
    await mailPage.clickTab('Entregabilidad');
    await mailPage.expectTabActive('Entregabilidad');
    await mailPage.expectHealthScoreVisible();
    await mailPage.expectEntregabilidadTabContent();
  });

  test('tab Lista muestra suscriptores, churn ratio y gráfico de crecimiento', async ({ growthStudioPage, tenantId }) => {
    const mailPage = new MailDashboardPage(growthStudioPage, tenantId);
    await setupMailDashboardMocks(growthStudioPage);

    await mailPage.gotoExpandedDashboard();
    await mailPage.clickTab('Lista');
    await mailPage.expectTabActive('Lista');
    await mailPage.expectListaTabContent();
  });

  test('tab Automatización muestra completadas, tasa y funnel', async ({ growthStudioPage, tenantId }) => {
    const mailPage = new MailDashboardPage(growthStudioPage, tenantId);
    await setupMailDashboardMocks(growthStudioPage);

    await mailPage.gotoExpandedDashboard();
    await mailPage.clickTab(/Automatización/);
    await mailPage.expectTabActive(/Automatización/);
    await mailPage.expectAutomatizacionTabContent();
  });

  test('navegación directa a tab vía URL con ?tab=engagement', async ({ growthStudioPage, tenantId }) => {
    const mailPage = new MailDashboardPage(growthStudioPage, tenantId);
    await setupMailDashboardMocks(growthStudioPage);

    await mailPage.gotoExpandedDashboard('engagement');
    await mailPage.expectFullDashboardVisible();
    await mailPage.expectTabActive('Engagement');
    await mailPage.expectEngagementTabContent();
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

    await mailPage.clickTab('Engagement');
    await mailPage.expectTabActive('Engagement');

    await mailPage.clickTab('Entregabilidad');
    await mailPage.expectTabActive('Entregabilidad');

    await mailPage.clickTab('Lista');
    await mailPage.expectTabActive('Lista');

    await mailPage.clickTab(/Automatización/);
    await mailPage.expectTabActive(/Automatización/);

    await mailPage.clickTab('Resumen');
    await mailPage.expectTabActive('Resumen');
  });
});
