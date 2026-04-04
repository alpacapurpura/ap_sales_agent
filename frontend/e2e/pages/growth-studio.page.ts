import { type Page, type Locator, expect } from '@playwright/test';

export class GrowthStudioPage {
  readonly sidebar: Locator;
  readonly mainContent: Locator;

  constructor(public readonly page: Page, private tenantId: string) {
    this.sidebar = page.locator('[data-testid="sidebar"]');
    this.mainContent = page.locator('main');
  }

  async goto(stage: string = 'atraccion') {
    await this.page.goto(`/${this.tenantId}/growth-studio/${stage}`);
    await this.page.waitForLoadState('load');
  }

  async expectLoaded() {
    await expect(this.mainContent).toBeVisible();
  }

  async expectStage(stage: string) {
    await expect(this.page).toHaveURL(new RegExp(`growth-studio/${stage}`));
  }

  async navigateToStage(stage: string) {
    await this.page.goto(`/${this.tenantId}/growth-studio/${stage}`);
    await this.page.waitForLoadState('load');
  }
}
