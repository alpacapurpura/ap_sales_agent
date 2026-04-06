import { type Page, type Locator, expect } from '@playwright/test';

/**
 * Page Object Model for the Meta Ads Dashboard.
 *
 * Covers both the sidebar overview panel (650px) and the full-page dashboard
 * with 5 tabs (Overview, Campañas, Audiencia, Video, Costos).
 */
export class MetaAdsDashboardPage {
  readonly mainContent: Locator;

  constructor(
    public readonly page: Page,
    private tenantId: string,
  ) {
    this.mainContent = page.locator('main');
  }

  // ── Navigation ─────────────────────────────────────────────

  async gotoGrowthStudio() {
    await this.page.goto(`/${this.tenantId}/growth-studio/atraccion-captura`);
    // Wait for a concrete element instead of arbitrary timeout
    await this.page.getByText('Atracción').first().waitFor({ state: 'visible', timeout: 10_000 });
  }

  // ── Channel Click ────────���─────────────────────────────────

  /** Clicks the Meta Ads channel row in the Attraction detail panel. */
  async clickMetaAdsChannel() {
    const channelRow = this.page.getByText('Meta Ads').first();
    await channelRow.click();
  }

  // ── Sidebar (MetaAdsOverviewPanel) ───────────��─────────────

  /** Waits for the sidebar panel to be visible. */
  async expectSidebarVisible() {
    // The sidebar renders the channel name as a heading inside DetailPanelTitle
    await expect(this.page.getByText('Meta Ads').first()).toBeVisible({ timeout: 10_000 });
    // Verify period selector is present (confirms it's our custom sidebar, not generic)
    await expect(this.page.getByText('30 días')).toBeVisible({ timeout: 5_000 });
  }

  /** Checks that the period selector shows all 3 options. */
  async expectPeriodSelectorVisible() {
    await expect(this.page.getByRole('button', { name: '7 días' })).toBeVisible();
    await expect(this.page.getByRole('button', { name: '30 días' })).toBeVisible();
    await expect(this.page.getByRole('button', { name: '90 días' })).toBeVisible();
  }

  /** Selects a specific period in the sidebar. */
  async selectPeriod(label: '7 días' | '30 días' | '90 días') {
    await this.page.getByRole('button', { name: label }).click();
  }

  /** Checks that the 4 hero KPI cards are displayed. */
  async expectHeroKpis() {
    // Scope to the dialog (sidebar panel) to avoid strict mode violations
    const dialog = this.page.getByRole('dialog');
    await expect(dialog.getByText('Inversión')).toBeVisible();
    await expect(dialog.getByText('ROAS')).toBeVisible();
    await expect(dialog.getByText('CPL').first()).toBeVisible();
    await expect(dialog.getByText('CTR')).toBeVisible();
  }

  /** Checks that the mini funnel section is visible. */
  async expectMiniFunnel() {
    const dialog = this.page.getByRole('dialog');
    await expect(dialog.getByText('Funnel de Conversión')).toBeVisible();
    await expect(dialog.getByText('Impresiones')).toBeVisible();
    await expect(dialog.getByText('Clics')).toBeVisible();
  }

  /** Checks that the reach/frequency section is visible. */
  async expectReachFrequency() {
    const dialog = this.page.getByRole('dialog');
    await expect(dialog.getByText('Alcance y Frecuencia')).toBeVisible();
    await expect(dialog.getByText('Alcance').first()).toBeVisible();
    await expect(dialog.getByText('Frecuencia').first()).toBeVisible();
  }

  /** Checks for the frequency fatigue alert badge. */
  async expectFrequencyAlert(severity: 'warning' | 'critical') {
    const dialog = this.page.getByRole('dialog');
    if (severity === 'warning') {
      await expect(dialog.getByText('Frecuencia elevada')).toBeVisible();
    } else {
      await expect(dialog.getByText('Fatiga de audiencia')).toBeVisible();
    }
  }

  /** Checks for benchmark badges in the sidebar. */
  async expectBenchmarkBadges() {
    const dialog = this.page.getByRole('dialog');
    const badges = dialog.locator('span').filter({
      hasText: /mejor que promedio|En promedio|bajo promedio|sobre promedio/,
    });
    await expect(badges.first()).toBeVisible();
  }

  /** Clicks the "Dashboard completo" button to open full-page view. */
  async clickOpenFullDashboard() {
    await this.page.getByRole('button', { name: /Dashboard completo/i }).click();
  }

  /** Closes the sidebar via the close button. */
  async closeSidebar() {
    await this.page.getByRole('button', { name: /cerrar/i }).first().click();
  }

  // ── Full-page Dashboard (MetaAdsDashboard) ────────���────────

  /** Expects the full dashboard overlay to be visible. */
  async expectFullDashboardVisible() {
    await expect(this.page.getByText('Meta Ads · Dashboard')).toBeVisible({ timeout: 10_000 });
  }

  /** Expects the tab bar to show all 5 tabs. */
  async expectAllTabs() {
    const tabList = this.page.locator('[role="tablist"]');
    await expect(tabList.getByText('Overview')).toBeVisible();
    await expect(tabList.getByText('Campañas')).toBeVisible();
    await expect(tabList.getByText('Audiencia')).toBeVisible();
    await expect(tabList.getByText('Video')).toBeVisible();
    await expect(tabList.getByText('Costos')).toBeVisible();
  }

  /** Clicks a specific tab. */
  async clickTab(name: 'Overview' | 'Campañas' | 'Audiencia' | 'Video' | 'Costos') {
    const tabList = this.page.locator('[role="tablist"]');
    await tabList.getByText(name).click();
  }

  /** Checks that Overview tab shows charts. */
  async expectOverviewTabContent() {
    await expect(this.page.getByText('Inversión vs Conversiones')).toBeVisible();
  }

  /** Checks that Costs tab shows cost KPI cards. */
  async expectCostsTabContent() {
    await this.clickTab('Costos');
    await expect(this.page.getByText('CPC')).toBeVisible();
    await expect(this.page.getByText('CPM')).toBeVisible();
  }

  /** Checks placeholder tabs show "Próximamente". */
  async expectPlaceholderTab(tabName: 'Campañas' | 'Audiencia' | 'Video') {
    await this.clickTab(tabName);
    await expect(this.page.getByText('Próximamente')).toBeVisible();
  }

  /** Closes the full dashboard via the "Volver" button. */
  async closeFullDashboard() {
    await this.page.getByRole('button', { name: /Volver/i }).click();
  }
}
