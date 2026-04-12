import { type Page, expect } from '@playwright/test';

/**
 * Page Object Model for the Email Marketing (Mail) Dashboard.
 *
 * Covers the route-based full-page dashboard with 6 tabs:
 * Panorama, Campañas, Automatizaciones, Audiencia, Entregabilidad, Crecimiento.
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
    await expect(this.page.getByRole('tab', { name: 'Panorama' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: 'Campañas' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: 'Automatizaciones' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: 'Audiencia' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: 'Entregabilidad' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: 'Crecimiento' })).toBeVisible();
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

  async expectPanoramaTabContent() {
    await expect(this.page.getByText('Emails Enviados').first()).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Volumen vs Engagement').first()).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Embudo de Email').first()).toBeVisible({ timeout: 5_000 });
  }

  async expectEntregabilidadTabContent() {
    await expect(this.page.getByRole('tab', { name: 'Entregabilidad' })).toBeVisible({ timeout: 5_000 });
  }

  async expectCrecimientoTabContent() {
    await expect(this.page.getByRole('tab', { name: 'Crecimiento' })).toBeVisible({ timeout: 5_000 });
  }

  async expectAutomatizacionesTabContent() {
    await expect(this.page.getByRole('tab', { name: 'Automatizaciones' })).toBeVisible({ timeout: 5_000 });
  }

  // -- Back button --------------------------------------------------------

  async clickVolver() {
    await this.page.getByText('Volver').click();
  }
}
