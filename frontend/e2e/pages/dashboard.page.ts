import { type Page, type Locator, expect } from '@playwright/test';

export class DashboardPage {
  readonly sidebar: Locator;
  readonly mainContent: Locator;

  constructor(public readonly page: Page, private tenantId: string) {
    this.sidebar = page.locator('[data-testid="sidebar"]');
    this.mainContent = page.locator('main');
  }

  async goto() {
    await this.page.goto(`/${this.tenantId}`);
    await this.page.waitForLoadState('load');
  }

  async navigateTo(path: string) {
    await this.page.goto(`/${this.tenantId}/${path}`);
    await this.page.waitForLoadState('load');
  }

  async expectLoaded() {
    await expect(this.mainContent).toBeVisible();
    await expect(this.sidebar).toBeVisible();
  }

  async clickSidebarLink(name: RegExp | string) {
    await this.sidebar.getByRole('link', { name }).click();
  }
}
