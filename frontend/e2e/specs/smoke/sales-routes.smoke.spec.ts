import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Sales routes @smoke', () => {
  test('redirects /sales to /sales/studio/inbox (deprecated /sales/resumen removed)', async ({
    page,
    tenantId,
  }) => {
    await page.goto(`/${tenantId}/sales`, { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(new RegExp(`/${tenantId}/sales/studio/inbox$`), {
      timeout: 45_000,
    });
    await expect(page).not.toHaveURL(/sales\/resumen/);
    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });
  });

  test('deprecated /sales/resumen returns 404', async ({ page, tenantId }) => {
    const response = await page.goto(`/${tenantId}/sales/resumen`, {
      waitUntil: 'domcontentloaded',
    });
    expect(response?.status()).toBe(404);
  });

  test('sidebar (Closer Studio group) does not contain "Resumen" entry', async ({
    page,
    tenantId,
  }) => {
    await page.goto(`/${tenantId}/sales/studio/inbox`, { waitUntil: 'domcontentloaded' });
    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });

    const closerHrefResumen = page.locator(`a[href="/${tenantId}/sales/resumen"]`);
    await expect(closerHrefResumen).toHaveCount(0);
  });

  // Split active-routes verification per-slug so each goto stays well under
  // the per-test 60s budget (Next dev server compiles route on first hit).
  for (const slug of [
    'studio/inbox',
    'studio/pipeline',
    'studio/frozen',
    'contactos',
    'enrollments',
  ]) {
    test(`active route /sales/${slug} renders`, async ({ page, tenantId }) => {
      test.setTimeout(120_000);
      await page.goto(`/${tenantId}/sales/${slug}`, { waitUntil: 'domcontentloaded' });
      await expect(page).not.toHaveURL(/forbidden/);
      await expect(page.locator('main')).toBeVisible({ timeout: 60_000 });
    });
  }
});
