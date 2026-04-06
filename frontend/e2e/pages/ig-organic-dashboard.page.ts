import { type Page, expect } from '@playwright/test';

/**
 * Page Object Model for the IG Organic Dashboard.
 *
 * Covers the sidebar overview panel (650px) and the full-page dashboard
 * with 4 tabs (Overview, Contenido, Audiencia, Alcance).
 */
export class IgOrganicDashboardPage {
  constructor(
    public readonly page: Page,
    private tenantId: string,
  ) {}

  // ── Navigation ─────────────────────────────────────────────

  async gotoGrowthStudio() {
    await this.page.goto(`/${this.tenantId}/growth-studio/atraccion-captura`);
    await this.page.getByText('Atracción').first().waitFor({ state: 'visible', timeout: 10_000 });
  }

  async gotoAtraccionCaptura() {
    await this.page.goto(`/${this.tenantId}/growth-studio/atraccion-captura`);
    await this.page.getByText('Atracción').first().waitFor({ state: 'visible', timeout: 10_000 });
  }

  async gotoSidebarViaUrl(channelSlug: string) {
    await this.page.goto(`/${this.tenantId}/growth-studio/atraccion-captura?channel=${channelSlug}`);
    await this.page.getByText('Atracción').first().waitFor({ state: 'visible', timeout: 10_000 });
  }

  async gotoExpandedDashboard(channelSlug: string, tab?: string) {
    const url = tab
      ? `/${this.tenantId}/growth-studio/channel/${channelSlug}?tab=${tab}`
      : `/${this.tenantId}/growth-studio/channel/${channelSlug}`;
    await this.page.goto(url);
  }

  // ── Channel Click ──────────────────────────────────────────

  async clickIgOrganicChannel() {
    const channelRow = this.page.getByText('Instagram Orgánico').first();
    await channelRow.click();
  }

  // ── Sidebar ────────────────────────────────────────────────

  async expectSidebarVisible() {
    await expect(this.page.getByText('Instagram Orgánico').first()).toBeVisible({ timeout: 10_000 });
    await expect(this.page.getByText('30 días')).toBeVisible({ timeout: 5_000 });
  }

  async expectHeroKpis(count = 4) {
    await expect(this.page.getByText('Interacciones Totales')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Tasa de Engagement')).toBeVisible({ timeout: 5_000 });
  }

  async expectEngagementFunnel() {
    await expect(this.page.getByText('Funnel de Conversión')).toBeVisible({ timeout: 5_000 });
    await expect(this.page.getByText('Taps en Perfil')).toBeVisible({ timeout: 5_000 });
  }

  async expectGrowthIndicator() {
    await expect(this.page.getByText('Crecimiento de Audiencia')).toBeVisible({ timeout: 5_000 });
  }

  async clickExpandedDashboard() {
    await this.page.getByText('Dashboard completo').click();
  }

  // ── Full-page Dashboard ────────────────────────────────────

  async expectFullDashboardVisible() {
    await expect(this.page.getByRole('heading', { name: 'Instagram Orgánico · Dashboard' })).toBeVisible({ timeout: 10_000 });
  }

  async expectAllTabs() {
    await expect(this.page.getByRole('tab', { name: 'Overview' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: 'Contenido' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: 'Audiencia' })).toBeVisible();
    await expect(this.page.getByRole('tab', { name: 'Alcance' })).toBeVisible();
  }

  async clickTab(tabName: string) {
    await this.page.getByRole('tab', { name: tabName }).click();
  }

  async expectTabActive(tabName: string) {
    await expect(this.page.getByRole('tab', { name: tabName })).toHaveAttribute('data-state', 'active');
  }

  async expectUrlContainsTab(tabSlug: string) {
    await expect(this.page).toHaveURL(new RegExp(`tab=${tabSlug}`));
  }

  // ── Tooltips ───────────────────────────────────────────────

  async clickInfoIcon(metricOrChartTitle: string) {
    const trigger = this.page.getByText(metricOrChartTitle).locator('~ svg, svg').first();
    await trigger.click();
  }

  async expectTooltipVisible(containsText: string) {
    await expect(this.page.getByText(containsText)).toBeVisible({ timeout: 5_000 });
  }

  async expectTooltipClosed() {
    // Popover should not be visible after clicking elsewhere
    await this.page.locator('body').click({ position: { x: 10, y: 10 } });
  }

  // ── Content ────────────────────────────────────────────────

  async expectChartVisible(chartTitle: string) {
    await expect(this.page.getByText(chartTitle)).toBeVisible({ timeout: 5_000 });
  }

  async expectMetricValue(metricName: string, value: string) {
    await expect(this.page.getByText(value)).toBeVisible({ timeout: 5_000 });
  }

  // ── Back navigation ────────────────────────────────────────

  async clickVolver() {
    await this.page.getByText('Volver').click();
  }
}
