/**
 * Visual Regression — Growth Studio Responsive (5 stages × 3 breakpoints).
 *
 * Verifica que las 5 etapas canónicas se renderizan correctamente en:
 *  - Mobile: 375px (iPhone SE viewport)
 *  - Tablet: 768px (iPad viewport)
 *  - Desktop: 1440px (large desktop)
 *
 * Total: 5 etapas × 3 breakpoints = 15 screenshots de baseline.
 *
 * RAM constraint: SIEMPRE --workers=1 (test.describe.serial por breakpoint).
 *
 * E2E_BASE_URL=https://dev-app.nicolify.com (CF tunnel).
 */
import { test, expect } from '../../fixtures/auth.fixture';
import { setupGrowthStudioBaseMocks } from '../../fixtures/growth-studio.fixture';

const STAGE_SLUGS = [
  'atraccion-captura',
  'nutricion-oportunidad',
  'ventas',
  'adopcion',
  'expansion-evangelizacion',
] as const;

const BREAKPOINTS = [
  { name: 'mobile', width: 375, height: 800 },
  { name: 'tablet', width: 768, height: 800 },
  { name: 'desktop', width: 1440, height: 800 },
] as const;

// Serial por breakpoint para RAM safety (--workers=1 mandatory)
for (const bp of BREAKPOINTS) {
  test.describe.serial(`Growth Studio Responsive — ${bp.name} (${bp.width}px)`, () => {
    test.use({ viewport: { width: bp.width, height: bp.height } });

    for (const slug of STAGE_SLUGS) {
      test(`${slug} @ ${bp.width}px`, async ({ page, tenantId }) => {
        await setupGrowthStudioBaseMocks(page);

        await page.goto(`/${tenantId}/growth-studio/${slug}`, {
          waitUntil: 'networkidle',
          timeout: 90_000,
        });

        await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });

        // Estabilizar animaciones antes de capturar
        await page.waitForTimeout(800);

        await expect(page).toHaveScreenshot(`growth-studio-${slug}-${bp.name}.png`, {
          maxDiffPixelRatio: 0.01,
          fullPage: false,
          // Enmascarar regiones dinámicas
          mask: [
            page.locator('[data-testid="timestamp"]'),
            page.locator('[data-testid="kpi-value"]'),
            page.locator('[data-testid="last-updated"]'),
          ],
        });
      });
    }
  });
}
