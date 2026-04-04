import { type Page, type Locator, expect } from '@playwright/test';

export class BrandStudioPage {
  readonly mainContent: Locator;

  constructor(public readonly page: Page, private tenantId: string) {
    this.mainContent = page.locator('main');
  }

  async goto(section: string = 'esencia') {
    await this.page.goto(`/${this.tenantId}/brand-studio/${section}`, { waitUntil: 'domcontentloaded' });
  }

  async expectLoaded() {
    await expect(this.mainContent).toBeVisible({ timeout: 45_000 });
  }

  async expectSection(section: string) {
    await expect(this.page).toHaveURL(new RegExp(`brand-studio/${section}`));
  }
}
