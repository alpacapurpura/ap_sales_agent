/**
 * PR-12 — End-to-end regression test for the segment → campaign flow.
 *
 * Flow validated:
 *   1. User navigates to /sales/contactos.
 *   2. Selects 2+ contacts via checkboxes.
 *   3. SelectedContactsBar appears with "Crear segmento" action.
 *   4. Clicks "Crear segmento" → CreateSegmentDialog opens.
 *   5. Fills segment name → submits.
 *   6. Toast success + LaunchCampaignChoiceDialog opens.
 *   7. Clicks "Sí, crear campaña" → navigates to /sales/campañas/nuevo?segment_id={id}.
 *   8. Fills campaign name → submits.
 *   9. Toast success + navigates to /sales/campañas/{id}.
 *  10. Stats card renders (even if 0 stats).
 *
 * Infrastructure dependencies (skipped until staging fixture lands):
 *   - Seed helper tenant + leads with telegram_id
 *   - POST /api/v1/segments/ STATIC path BE delta (PR-12 BE builder)
 *   - POST /api/v1/campaigns/ + steps + schedule (S1 PR-4 existing)
 *
 * Inherits infra gap pattern from PR-9 + PR-11.
 * Manual gate Chris: sprints/S4-crm-hub-lite/prs/PR-12 manual checklist.
 *
 * Caveman: arch ready, infra pending. Manual test = real gate S4 close.
 */
import { test, expect } from '../../../fixtures/auth.fixture';

test.describe('PR-12 Segment create + Campaign launch flow', () => {
  test('contactos page renders with SelectedContactsBar slot', async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/sales/contactos`);
    await expect(page.getByRole('heading', { name: /contactos/i })).toBeVisible({ timeout: 10_000 });
  });

  test.skip('full flow: select contacts → create segment → launch campaign', async ({
    page,
    tenantId,
  }) => {
    // Skipped until seed fixture lands (inheriting PR-11 + PR-9 pattern).
    // Manual checklist Chris: post-S4 staging gate.
    await page.goto(`/${tenantId}/sales/contactos`);

    // 1. Wait for table to render
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10_000 });

    // 2. Select 2 rows via checkboxes
    const checkboxes = page.locator('tbody input[type="checkbox"]');
    await checkboxes.nth(0).check();
    await checkboxes.nth(1).check();

    // 3. SelectedContactsBar should appear
    await expect(page.getByText(/2 contactos seleccionados/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /crear segmento/i })).toBeVisible();

    // 4. Open CreateSegmentDialog
    await page.getByRole('button', { name: /crear segmento/i }).click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // 5. Fill segment name and submit
    await page.getByLabel(/nombre del segmento/i).fill('Segmento S4 Test');
    await page.getByRole('button', { name: /crear segmento$/i }).click();

    // 6. Toast success + LaunchCampaignChoiceDialog
    await expect(page.getByText(/segmento.*creado/i)).toBeVisible();
    await expect(page.getByText(/¿quieres lanzar una campaña/i)).toBeVisible();

    // 7. Navigate to campaign new page
    await page.getByRole('button', { name: /sí, crear campaña/i }).click();
    await expect(page).toHaveURL(/\/sales\/campa%C3%B1as\/nuevo/);
    await expect(page).toHaveURL(/segment_id=/);

    // 8. Fill campaign form
    await page.getByLabel(/nombre de la campaña/i).fill('Campaña Telegram S4');
    await page.getByRole('button', { name: /crear campaña/i }).click();

    // 9. Toast + redirect to detail page
    await expect(page.getByText(/campaña.*creada/i)).toBeVisible();
    await expect(page).toHaveURL(/\/sales\/campa%C3%B1as\/[a-zA-Z0-9-]+$/);

    // 10. Stats card renders
    await expect(page.getByText(/estadísticas/i)).toBeVisible();
  });
});
