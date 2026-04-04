import { type Page, type Locator, expect } from '@playwright/test';

export class BookingPage {
  readonly mainContent: Locator;
  readonly calendar: Locator;

  constructor(public readonly page: Page) {
    this.mainContent = page.locator('main');
    this.calendar = page.locator('[data-testid="booking-calendar"]');
  }

  async goto(slug: string) {
    await this.page.goto(`/book/${slug}`);
    await this.page.waitForLoadState('load');
  }

  async expectLoaded() {
    await expect(this.mainContent).toBeVisible();
  }
}
