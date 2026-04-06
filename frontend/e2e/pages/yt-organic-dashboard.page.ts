import { type Page, expect } from '@playwright/test';

/**
 * Page Object Model for the YouTube Organic Dashboard.
 *
 * Covers the sidebar overview panel (650px) and the full-page dashboard
 * with 5 tabs (Resumen, Videos, Audiencia, Engagement, Retenci\u00f3n).
 */
export class YtOrganicDashboardPage {
  constructor(
    public readonly page: Page,
    private tenantId: string,
  ) {}

  // -- Navigation ----------------------------------------------------------

  async gotoGrowthStudio() {
    await this.page.goto(`/${this.tenantId}/growth-studio/atraccion-captura`);
    await this.page.getByText('Atracci\u00f3n').first().waitFor({ state: 'visible', timeout: 10_000 });
  }

  async gotoSidebarViaUrl(channelSlug: string) {
    await this.page.goto(`/${this.tenantId}/growth-studio/atraccion-captura?channel=${channelSlug}`);
    await this.page.getByText('Atracci\u00f3n').first().waitFor({ state: 'visible', timeout: 10_000 });
  }

  async gotoExpandedDashboard(channelSlug: string, tab?: string) {
    const url = tab
      ? `/${this.tenantId}/growth-studio/channel/${channelSlug}?tab=${tab}`
      : `/${this.tenantId}/growth-studio/channel/${channelSlug}`;
    await this.page.goto(url);
  }

  // -- Channel Click -------------------------------------------------------

  async clickYtOrganicChannel() {
    const channelRow = this.page.getByText('YouTube Org\u00e1nico').first();
    await channelRow.click();
  }

  // -- Sidebar -------------------------------------------------------------

  async expectSidebarVisible() {
    await expect(this.page.getByText('YouTube Org\u00e1nico').first()).toBeVisible({ timeout: 10_000 });
    await expect(this.page.getByText('30 d\u00edas')).toBeVisible({ timeout: 5_000 });
  }

  async expectHeroKpis() {
    await expect(this.page.getByText('Vistas')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Minutos Vistos')).toBeVisible({ timeout: 5_000 });
  }

  async expectSubscriberGrowth() {
    await expect(this.page.getByText('Crecimiento de Suscriptores')).toBeVisible({ timeout: 5_000 });
  }

  async clickExpandedDashboard() {
    await this.page.getByText('Dashboard completo').click();
  }

  // -- Full-page Dashboard -------------------------------------------------

  async expectFullDashboardVisible() {
    await expect(this.page.getByText(/YouTube Org\u00e1nico.*Dashboard/)).toBeVisible({ timeout: 10_000 });
  }

  async expectAllTabs() {
    await expect(this.page.getByRole('tab', { name: 'Resumen' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: 'Videos' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: 'Audiencia' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: 'Engagement' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: /Retenci\u00f3n/ })).toBeVisible();
  }

  async clickTab(tabName: string | RegExp) {
    await this.page.getByRole('tab', { name: tabName }).click();
  }

  async expectTabActive(tabName: string | RegExp) {
    await expect(this.page.getByRole('tab', { name: tabName })).toHaveAttribute('data-state', 'active');
  }

  async expectChartVisible(chartTitle: string) {
    await expect(this.page.getByText(chartTitle)).toBeVisible({ timeout: 5_000 });
  }

  async clickVolver() {
    await this.page.getByText('Volver').click();
  }
}
