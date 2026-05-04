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

  // Full filter→drawer→search→multi-select flow removed 2026-05-04 (was test.skip permanent).
  // Restore from git history when seed fixture infra lands.
});
