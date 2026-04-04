import { test, expect } from '../../../fixtures/auth.fixture';
import { SalesPage } from '../../../pages/sales.page';

test.describe('Sales Dashboard', () => {
  test('renders sales hub', async ({ page, tenantId }) => {
    const salesPage = new SalesPage(page, tenantId);
    await salesPage.goto();
    await salesPage.expectLoaded();
  });

  test('has main content area', async ({ page, tenantId }) => {
    const salesPage = new SalesPage(page, tenantId);
    await salesPage.goto();
    await expect(page.locator('main')).toBeVisible();
  });
});
