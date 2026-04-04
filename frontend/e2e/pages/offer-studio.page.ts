import { type Page, type Locator, expect } from '@playwright/test';

export class OfferStudioPage {
  readonly mainContent: Locator;

  constructor(public readonly page: Page, private tenantId: string) {
    this.mainContent = page.locator('main');
  }

  async goto() {
    await this.page.goto(`/${this.tenantId}/offer-studio`, { waitUntil: 'domcontentloaded' });
  }

  async gotoOffer(offerId: string) {
    await this.page.goto(`/${this.tenantId}/offer-studio/${offerId}`, { waitUntil: 'domcontentloaded' });
  }

  async expectLoaded() {
    await expect(this.mainContent).toBeVisible({ timeout: 45_000 });
  }

  async expectOfferList() {
    await expect(this.page).toHaveURL(/offer-studio/);
  }
}
