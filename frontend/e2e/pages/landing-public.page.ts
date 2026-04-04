import { type Page, type Locator, expect } from '@playwright/test';

export class LandingPublicPage {
  readonly mainContent: Locator;
  readonly heroSection: Locator;

  constructor(public readonly page: Page) {
    this.mainContent = page.locator('main');
    this.heroSection = page.locator('[data-testid="hero"]');
  }

  async goto(slug: string) {
    await this.page.goto(`/p/${slug}`);
    await this.page.waitForLoadState('load');
  }

  async expectLoaded() {
    await expect(this.mainContent).toBeVisible();
  }

  async expectNotFound() {
    await expect(this.page.getByText(/not found|no encontrad/i)).toBeVisible();
  }
}
