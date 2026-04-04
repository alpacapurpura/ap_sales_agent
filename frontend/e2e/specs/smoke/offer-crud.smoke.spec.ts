import { test, expect } from '../../fixtures/auth.fixture';
import { OfferStudioPage } from '../../pages/offer-studio.page';

test.describe('Offer Studio CRUD @smoke', () => {
  test('renders offer list', async ({ page, tenantId }) => {
    const offerPage = new OfferStudioPage(page, tenantId);
    await offerPage.goto();
    await offerPage.expectLoaded();
    await offerPage.expectOfferList();
  });

  test('offer list shows content or empty state', async ({ page, tenantId }) => {
    const offerPage = new OfferStudioPage(page, tenantId);
    await offerPage.goto();
    await offerPage.expectLoaded();

    // Wait for data to load, then check for either offers or empty state
    await page.waitForTimeout(3_000);
    const mainContent = page.locator('main');
    const hasCards = await mainContent.locator('[class*="card"], [class*="Card"]').count() > 0;
    const hasButton = await mainContent.locator('button').count() > 0;
    const hasText = await mainContent.locator('text=/crear|create|nueva|añadir|empez/i').count() > 0;
    expect(hasCards || hasButton || hasText).toBe(true);
  });
});
