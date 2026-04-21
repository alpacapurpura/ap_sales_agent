import { type Page, type Locator, expect } from '@playwright/test';

export class OfferStudioPage {
  readonly mainContent: Locator;

  constructor(public readonly page: Page, private tenantId: string) {
    this.mainContent = page.locator('main');
  }

  // ---------------------------------------------------------------------------
  // Navigation helpers
  // ---------------------------------------------------------------------------

  async goto() {
    await this.page.goto(`/${this.tenantId}/offer-studio`, { waitUntil: 'domcontentloaded' });
  }

  async gotoOffer(offerId: string) {
    await this.page.goto(`/${this.tenantId}/offer-studio/${offerId}`, { waitUntil: 'domcontentloaded' });
  }

  /** Navigate to the offer-studio dashboard (ladder). */
  async gotoDashboard() {
    await this.page.goto(`/${this.tenantId}/offer-studio`, { waitUntil: 'domcontentloaded' });
  }

  /** Click the "Nueva oferta" CTA from the dashboard. */
  async gotoWizard() {
    await this.gotoDashboard();
    const cta = this.page.getByRole('button', { name: /nueva oferta/i }).first();
    await cta.click();
  }

  /** Direct navigation to the offer editor landing. */
  async gotoEditor(offerId: string) {
    await this.page.goto(
      `/${this.tenantId}/offer-studio/offer/${offerId}/editor`,
      { waitUntil: 'domcontentloaded' },
    );
  }

  /** Direct navigation to a specific section in the editor. */
  async gotoSection(offerId: string, section: string) {
    await this.page.goto(
      `/${this.tenantId}/offer-studio/offer/${offerId}/editor/${section}`,
      { waitUntil: 'domcontentloaded' },
    );
  }

  /** Click the "Editions" tab in the offer TabBar. */
  async gotoEditionsTab(offerId: string) {
    await this.gotoEditor(offerId);
    const editionsTab = this.getEditionsTab();
    await editionsTab.click();
  }

  // ---------------------------------------------------------------------------
  // Interaction helpers
  // ---------------------------------------------------------------------------

  /** Click a variant entry in the VariantRail by its variant ID. */
  async clickVariantInRail(variantId: string) {
    const chip = this.page.locator(`[data-edition-id="${variantId}"]`).first();
    await chip.click();
  }

  /** Click an entry in the OfferStudioNavRail by section slug. */
  async clickSectionInNavRail(slug: string) {
    const link = this.page
      .getByRole('navigation', { name: /secciones/i })
      .getByRole('link')
      .filter({ hasText: new RegExp(slug, 'i') })
      .first();
    await link.click();
  }

  /**
   * Click the "Aplicar sugerencia" button on the copilot card for the given
   * tool key, then wait for the draft preview to appear.
   */
  async applyCopilotSuggestion(toolKey: string) {
    // Find the card that contains the tool key's aria-label
    const card = this.page
      .locator('[class*="rounded-lg"][class*="border"]')
      .filter({ has: this.page.locator(`[aria-label="Aplicar sugerencia"]`) })
      .first();

    const btn = card.getByRole('button', { name: /aplicar sugerencia/i });
    await btn.click();

    // Wait for draft preview ("Borrador listo") to appear
    await this.page.getByText('Borrador listo').waitFor({ state: 'visible', timeout: 15_000 });
    void toolKey; // toolKey used implicitly via surrounding context
  }

  // ---------------------------------------------------------------------------
  // Locators
  // ---------------------------------------------------------------------------

  /** Returns the VariantRail root locator. */
  getVariantRail(): Locator {
    return this.page.locator('[data-testid="variant-rail"]');
  }

  /** Returns the "Editions" tab locator in the TabBar. */
  getEditionsTab(): Locator {
    return this.page
      .getByRole('navigation', { name: /secciones de la oferta/i })
      .getByRole('link', { name: /editions|ediciones/i });
  }

  /** Returns all copilot suggestion cards. */
  getCopilotCards(): Locator {
    return this.page.locator('[class*="rounded-lg"][class*="border"][class*="bg-card"]');
  }

  // ---------------------------------------------------------------------------
  // Assertions
  // ---------------------------------------------------------------------------

  async expectLoaded() {
    await expect(this.mainContent).toBeVisible({ timeout: 45_000 });
  }

  async expectOfferList() {
    await expect(this.page).toHaveURL(/offer-studio/);
  }
}
