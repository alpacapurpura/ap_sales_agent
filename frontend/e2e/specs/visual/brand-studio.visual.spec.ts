import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Brand Studio Visual Regression', () => {
  test('esencia section renders correctly', async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/brand-studio/esencia`);
    await page.waitForLoadState('load');

    await expect(page).toHaveScreenshot('brand-esencia.png', {
      maxDiffPixelRatio: 0.01,
      fullPage: false,
    });
  });

  test('estrategia section renders correctly', async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/brand-studio/estrategia`);
    await page.waitForLoadState('load');

    await expect(page).toHaveScreenshot('brand-estrategia.png', {
      maxDiffPixelRatio: 0.01,
      fullPage: false,
    });
  });
});
