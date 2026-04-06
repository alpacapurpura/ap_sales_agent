import { type Page, expect } from '@playwright/test';

/**
 * Page Object Model for the Email Marketing (Mail) Dashboard.
 *
 * Covers the route-based full-page dashboard with 5 tabs
 * (Resumen, Engagement, Entregabilidad, Lista, Automatización).
 */
export class MailDashboardPage {
  constructor(
    public readonly page: Page,
    private tenantId: string,
  ) {}

  // -- Navigation ----------------------------------------------------------

  async gotoExpandedDashboard(tab?: string) {
    const url = tab
      ? `/${this.tenantId}/growth-studio/channel/email-nurture?tab=${tab}`
      : `/${this.tenantId}/growth-studio/channel/email-nurture`;
    await this.page.goto(url);
  }

  // -- Full-page Dashboard -------------------------------------------------

  async expectFullDashboardVisible() {
    await expect(
      this.page.getByRole('heading', { name: /Email Marketing.*Dashboard/ }),
    ).toBeVisible({ timeout: 10_000 });
  }

  async expectAllTabs() {
    await expect(this.page.getByRole('tab', { name: 'Resumen' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: 'Engagement' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: 'Entregabilidad' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: 'Lista' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: /Automatización/ })).toBeVisible();
  }

  async clickTab(tabName: string | RegExp) {
    await this.page.getByRole('tab', { name: tabName }).click();
  }

  async expectTabActive(tabName: string | RegExp) {
    await expect(this.page.getByRole('tab', { name: tabName })).toHaveAttribute('data-state', 'active');
  }

  // -- Period Selector ---------------------------------------------------

  async expectPeriodSelector() {
    await expect(this.page.getByText('30 días')).toBeVisible();
    await expect(this.page.getByText('7 días')).toBeVisible();
    await expect(this.page.getByText('90 días')).toBeVisible();
  }

  // -- Tab Content -------------------------------------------------------

  async expectOverviewTabContent() {
    await expect(this.page.getByText('Tasa de Apertura')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Volumen vs Engagement')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Crecimiento de Lista')).toBeVisible({ timeout: 5_000 });
  }

  async expectEngagementTabContent() {
    await expect(this.page.getByText('CTOR')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Click Rate')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Reenvíos')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Desglose de Engagement Diario')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Tendencia CTOR')).toBeVisible({ timeout: 5_000 });
  }

  async expectEntregabilidadTabContent() {
    await expect(this.page.getByText('Bounce Rate')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Spam Reports')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Desuscripción')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Desglose de Rebotes')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Tendencia de Salud')).toBeVisible({ timeout: 5_000 });
  }

  async expectListaTabContent() {
    await expect(this.page.getByText('Suscriptores Activos')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Nuevos (periodo)')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Ratio de Churn')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Crecimiento de Lista')).toBeVisible({ timeout: 5_000 });
  }

  async expectAutomatizacionTabContent() {
    await expect(this.page.getByText('Automatizaciones Completadas')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Tasa de Completado')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Funnel de Automatización')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Tendencia Tasa de Completado')).toBeVisible({ timeout: 5_000 });
  }

  // -- Health Score -------------------------------------------------------

  async expectHealthScoreVisible() {
    // The health component shows one of these statuses
    const healthText = this.page.locator('text=/Saludable|Atención|Crítico/');
    await expect(healthText.first()).toBeVisible({ timeout: 5_000 });
  }

  // -- Back button --------------------------------------------------------

  async clickVolver() {
    await this.page.getByText('Volver').click();
  }
}
