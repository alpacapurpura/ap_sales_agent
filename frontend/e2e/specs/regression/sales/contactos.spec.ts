/**
 * PR-11 — End-to-end smoke test for /sales/contactos page.
 *
 * Flow validated:
 *   1. Auth user navega `/sales/contactos`.
 *   2. Tabla render con seed data (consume PR-10 GET /api/v1/contacts).
 *   3. Apply filter `lifecycle_stage_in=mql` → URL state actualizado, results filtered.
 *   4. Click row → drawer Sheet abre con detail (PR-10 GET /api/v1/contacts/{id}).
 *   5. Search debounced 300ms → URL `q=` actualizado.
 *   6. Check 2 rows → SelectedContactsBar visible con count.
 *
 * Infrastructure dependencies (skipped hasta staging fixture):
 *   - Seed helper tenant + leads + customer_profiles (heredando deuda PR-9)
 *   - Mock /api/v1/contacts response shape consistente con PR-10 DTOs
 *
 * Hasta full infra setup ship (post-S4 cleanup PR), spec valida:
 *   - Page renders without 500
 *   - Auth flow + tenant header injection
 *
 * Caveman: arch ready, infra pending. Manual gate Chris staging post-merge.
 */
import { test, expect } from '../../../fixtures/auth.fixture';

test.describe('PR-11 Sales Contactos page', () => {
  test('page loads under /sales/contactos route', async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/sales/contactos`);
    // Header visible (server-rendered)
    await expect(page.getByRole('heading', { name: /contactos/i })).toBeVisible({ timeout: 10_000 });
  });

  test.skip('full flow: filter → row click drawer → search → multi-select', async ({ page, tenantId }) => {
    // Skipped hasta seed fixture lands (heredando PR-9 pattern).
    // Manual checklist Chris: sprints/S4-crm-hub-lite/manual-test-checklist.md (post-PR-12 cierre).
    await page.goto(`/${tenantId}/sales/contactos`);

    // 1. Tabla render
    await expect(page.getByRole('table')).toBeVisible();

    // 2. Apply filter lifecycle MQL
    await page.getByRole('checkbox', { name: /MQL/i }).check();
    await expect(page).toHaveURL(/lifecycle_stage_in=mql/);

    // 3. Click row → drawer
    await page.locator('tbody tr').first().click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // 4. Search debounced
    await page.getByPlaceholder(/buscar/i).fill('juan');
    await page.waitForTimeout(400);
    await expect(page).toHaveURL(/q=juan/);

    // 5. Multi-select bar
    await page.locator('thead input[type="checkbox"]').first().click();
    await expect(page.getByText(/contactos seleccionados/i)).toBeVisible();
  });
});
