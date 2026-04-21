import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Navigation @smoke', () => {
  test('authenticated user lands on Brand Studio', async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/brand-studio/identity`, { waitUntil: 'domcontentloaded' });
    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });
  });

  test('can navigate to Offer Studio', async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/offer-studio`, { waitUntil: 'domcontentloaded' });
    await expect(page).not.toHaveURL(/forbidden/);
    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });
  });

  test('can navigate to Settings', async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/settings`, { waitUntil: 'domcontentloaded' });
    await expect(page).not.toHaveURL(/forbidden/);
    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });
  });
});
