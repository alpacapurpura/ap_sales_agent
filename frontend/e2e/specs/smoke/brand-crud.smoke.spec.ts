import { test, expect } from '../../fixtures/auth.fixture';
import { BrandStudioPage } from '../../pages/brand-studio.page';

test.describe('Brand Studio CRUD @smoke', () => {
  test('renders esencia section', async ({ page, tenantId }) => {
    const brandPage = new BrandStudioPage(page, tenantId);
    await brandPage.goto('esencia');
    await brandPage.expectLoaded();
    await brandPage.expectSection('esencia');
  });

  test('esencia section has interactive content', async ({ page, tenantId }) => {
    const brandPage = new BrandStudioPage(page, tenantId);
    await brandPage.goto('esencia');
    await brandPage.expectLoaded();

    const hasContent = page.locator('main').locator('input, textarea, button, [role="button"]');
    await expect(hasContent.first()).toBeVisible({ timeout: 45_000 });
  });
});
