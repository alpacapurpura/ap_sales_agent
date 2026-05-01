import { test, expect } from '../../fixtures/auth.fixture';

/**
 * Smoke tests — sales/campanas route (Bug #4 fix: renamed from campañas → campanas).
 * Verifies:
 *  1. /sales/campanas/nuevo loads without 404 (Next.js 16 does not compile ñ in folder names)
 *  2. Sidebar Closer Studio group contains "Campañas" link pointing to campanas route
 */
test.describe('Sales campanas route @smoke', () => {
  test('/sales/campanas/nuevo renders (not 404)', async ({ page, tenantId }) => {
    test.setTimeout(120_000);
    await page.goto(`/${tenantId}/sales/campanas/nuevo`, { waitUntil: 'domcontentloaded' });
    await expect(page).not.toHaveURL(/forbidden/);
    // Should render main content, not 404 text
    await expect(page.locator('main')).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('text=404')).toHaveCount(0);
  });

  test('sidebar Closer Studio group contains "Campañas" link to campanas route', async ({
    page,
    tenantId,
  }) => {
    test.setTimeout(120_000);
    await page.goto(`/${tenantId}/sales/studio/inbox`, { waitUntil: 'domcontentloaded' });
    await expect(page.locator('main')).toBeVisible({ timeout: 60_000 });

    // Sidebar should have a link pointing to the campanas route (ASCII, no ñ)
    const campañasLink = page.locator(`a[href="/${tenantId}/sales/campanas/nuevo"]`);
    await expect(campañasLink).toBeVisible({ timeout: 10_000 });
    await expect(campañasLink).toContainText('Campañas');
  });

  test('old campañas URL (encoded ñ) returns 404', async ({ page, tenantId }) => {
    const response = await page.goto(`/${tenantId}/sales/campa%C3%B1as/nuevo`, {
      waitUntil: 'domcontentloaded',
    });
    expect(response?.status()).toBe(404);
  });
});
