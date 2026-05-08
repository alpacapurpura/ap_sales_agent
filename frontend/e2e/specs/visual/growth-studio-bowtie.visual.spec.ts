/**
 * Visual Regression — Growth Studio Bowtie (pixel-perfect post-refactor).
 *
 * Captura baseline del bowtie summary + metrics dashboard después del refactor
 * growth-studio-folder-parity (T-4). Chris ratifica diffs manualmente.
 *
 * Threshold: maxDiffPixelRatio ≤ 0.01 (1% — invariante de negocio Scenario 3).
 *
 * Mascaras:
 *  - [data-testid="timestamp"]: fechas/horas que cambian entre runs
 *  - [data-testid="kpi-value"]: valores de KPI que cambian con datos reales
 *
 * Nota: Esta spec usa fixtures de growth-studio (mocks de API) para
 * estabilizar los datos y producir screenshots reproducibles.
 *
 * E2E_BASE_URL=https://dev-app.nicolify.com (CF tunnel).
 * RAM constraint: SIEMPRE --workers=1.
 */
import { test, expect } from '../../fixtures/auth.fixture';
import { setupGrowthStudioBaseMocks } from '../../fixtures/growth-studio.fixture';

test.describe('Growth Studio Bowtie — Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await setupGrowthStudioBaseMocks(page);
  });

  test('bowtie summary página principal (post-refactor baseline)', async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/growth-studio/atraccion-captura`, {
      waitUntil: 'networkidle',
      timeout: 90_000,
    });

    // Esperar que el contenido principal sea visible
    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });

    // Estabilizar animaciones CSS antes de capturar
    await page.waitForTimeout(1000);

    await expect(page).toHaveScreenshot('growth-studio-bowtie.png', {
      maxDiffPixelRatio: 0.01,
      fullPage: false,
      // Enmascarar regiones dinámicas (timestamps, valores de KPIs en vivo)
      mask: [
        page.locator('[data-testid="timestamp"]'),
        page.locator('[data-testid="kpi-value"]'),
        page.locator('[data-testid="last-updated"]'),
      ],
    });
  });
});
