import { test, expect } from '../../../fixtures/auth.fixture';
import { OfferStudioPage } from '../../../pages/offer-studio.page';

test.describe('Offer Studio - List', () => {
  test('renders offer studio page', async ({ page, tenantId }) => {
    const offerPage = new OfferStudioPage(page, tenantId);
    await offerPage.goto();
    await offerPage.expectLoaded();
  });

  test('page has proper heading', async ({ page, tenantId }) => {
    const offerPage = new OfferStudioPage(page, tenantId);
    await offerPage.goto();

    const heading = page.getByRole('heading');
    await expect(heading.first()).toBeVisible();
  });
});
