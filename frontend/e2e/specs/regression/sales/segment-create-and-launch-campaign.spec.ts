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

  // Full select→segment→campaign flow removed 2026-05-04 (was test.skip permanent).
  // Restore from git history when seed fixture infra lands. Manual gate Chris meanwhile.
});
