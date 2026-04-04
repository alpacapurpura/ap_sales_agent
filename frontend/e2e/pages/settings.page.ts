import { type Page, type Locator, expect } from '@playwright/test';

export class SettingsPage {
  readonly sidebar: Locator;
  readonly mainContent: Locator;

  constructor(public readonly page: Page, private tenantId: string) {
    this.sidebar = page.locator('[data-testid="sidebar"]');
    this.mainContent = page.locator('main');
  }

  async goto() {
    await this.page.goto(`/${this.tenantId}/settings`);
    await this.page.waitForLoadState('load');
  }

  async expectLoaded() {
    await expect(this.mainContent).toBeVisible();
  }
}
