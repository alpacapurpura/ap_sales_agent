import { type Page, type Locator, expect } from '@playwright/test';

/**
 * Page Object Model for the Meta Ads Dashboard.
 *
 * Covers both the sidebar overview panel (650px) and the full-page dashboard
 * with 5 tabs (Resumen, Campañas, Creativos, Audiencia, Costos).
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
    await expect(tabList.getByText('Resumen')).toBeVisible();
    await expect(tabList.getByText('Campañas')).toBeVisible();
    await expect(tabList.getByText('Creativos')).toBeVisible();
    await expect(tabList.getByText('Audiencia')).toBeVisible();
    await expect(tabList.getByText('Costos')).toBeVisible();
  }

  /** Clicks a specific tab. */
  async clickTab(name: 'Resumen' | 'Campañas' | 'Creativos' | 'Audiencia' | 'Costos') {
    const tabList = this.page.locator('[role="tablist"]');
    await tabList.getByText(name).click();
  }

  /** Checks that Resumen tab shows charts. */
  async expectResumenTabContent() {
    await expect(this.page.getByText('Inversión vs Resultados')).toBeVisible();
  }

  /** Checks that Campañas tab shows the campaign table. */
  async expectCampanasTabContent() {
    await this.clickTab('Campañas');
    await expect(this.page.getByText('Activas / Total').first()).toBeVisible();
  }

  /** Checks that Costos tab shows cost KPI cards. */
  async expectCostosTabContent() {
    await this.clickTab('Costos');
    await expect(this.page.getByText('CPC')).toBeVisible();
    await expect(this.page.getByText('CPM')).toBeVisible();
  }

  /** Checks that Creativos tab renders. */
  async expectCreativosTabContent() {
    await this.clickTab('Creativos');
    await expect(this.page.getByText('Top anuncios por rendimiento').first()).toBeVisible();
  }

  /** Checks that Audiencia tab shows reach/frequency. */
  async expectAudienciaTabContent() {
    await this.clickTab('Audiencia');
    await expect(this.page.getByText('Alcance').first()).toBeVisible();
  }

  /** Closes the full dashboard via the "Volver" button. */
  async closeFullDashboard() {
    await this.page.getByRole('button', { name: /Volver/i }).click();
  }

  // ── Full Dashboard: Header Elements ──────────────────────

  /** Checks the sync button is visible in the full dashboard header. */
  async expectSyncButtonVisible() {
    await expect(this.page.getByRole('button', { name: /Sincronizar/i })).toBeVisible();
  }

  /** Checks the last sync timestamp is displayed. */
  async expectLastSyncVisible() {
    await expect(this.page.getByText(/Última sync:/i)).toBeVisible();
  }

  /** Checks the period selector is in the header area (top of full dashboard). */
  async expectPeriodSelectorInHeader() {
    // Period selector should be inside the header (border-b area)
    const header = this.page.locator('.fixed .border-b').first();
    await expect(header.getByText('30 días')).toBeVisible();
  }

  // ── Full Dashboard: Resumen Tab Alerts ───────────────────

  /** Checks that recommendation alert cards are visible in Resumen tab. */
  async expectResumenAlerts() {
    // At least one alert card should be visible (from campaign recommendations)
    await expect(this.page.getByText(/CPA.*alto|gastando sin resultados/i).first()).toBeVisible({ timeout: 5_000 });
  }

  // ── Full Dashboard: Audiencia Tab Demographics ───────────

  /** Checks the Audiencia tab renders age distribution chart. */
  async expectAgeDistribution() {
    await this.clickTab('Audiencia');
    await expect(this.page.getByText('Distribución por edad')).toBeVisible();
    // Check for age range labels
    await expect(this.page.getByText('25-34')).toBeVisible();
    await expect(this.page.getByText('18-24')).toBeVisible();
    // Check for dominant marker (★)
    await expect(this.page.getByText(/★/)).toBeVisible();
    // Check percentage values are shown
    await expect(this.page.getByText('42%')).toBeVisible();
  }

  /** Checks the Audiencia tab renders gender distribution. */
  async expectGenderDistribution() {
    await expect(this.page.getByText('Distribución por género')).toBeVisible();
    await expect(this.page.getByText('Femenino')).toBeVisible();
    await expect(this.page.getByText('Masculino')).toBeVisible();
    await expect(this.page.getByText('68%')).toBeVisible();
    await expect(this.page.getByText('32%')).toBeVisible();
  }

  /** Checks the Audiencia tab renders placement distribution. */
  async expectPlacementDistribution() {
    await expect(this.page.getByText('Dónde aparecen tus ads')).toBeVisible();
    await expect(this.page.getByText('Feed')).toBeVisible();
    await expect(this.page.getByText('Stories')).toBeVisible();
    await expect(this.page.getByText('Reels')).toBeVisible();
    await expect(this.page.getByText('55%')).toBeVisible();
  }
}
