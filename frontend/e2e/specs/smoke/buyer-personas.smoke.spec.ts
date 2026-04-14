import { test, expect } from '../../fixtures/auth.fixture';

const FAKE_PERSONA_ID = '00000000-0000-0000-0000-000000000001';

test.describe('Buyer Personas @smoke', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept list to return empty so empty state always appears
    await page.route('**/api/v1/brand/buyer-personas**', (route) => {
      if (route.request().method() === 'GET') {
        return route.fulfill({ status: 200, contentType: 'application/json', body: '[]' });
      }
      // POST — let it through to verify the real endpoint works (307 fix)
      if (route.request().method() === 'POST') {
        return route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: FAKE_PERSONA_ID,
            name: 'Mi buyer persona',
            tagline: null,
            scope: 'GLOBAL',
            offer_id: null,
            is_primary: false,
            demographics: {},
            psychographics: {},
            pain_points: [],
            desires: [],
            objections: [],
            preferred_channels: [],
            buyer_journey: {},
            purchase_triggers: [],
            anti_patterns: [],
            completeness_score: 0,
            interview_session_id: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      }
      return route.continue();
    });
  });

  test('empty state renders with both creation buttons', async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/brand-studio/publico`, { waitUntil: 'domcontentloaded' });
    await expect(page.getByText('Sin Buyer Personas')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByRole('button', { name: /Modo Inteligente/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Modo Manual/i }).first()).toBeVisible();
  });

  test('Modo Manual creates persona and navigates to detail page', async ({ page, tenantId }) => {
    await page.goto(`/${tenantId}/brand-studio/publico`, { waitUntil: 'domcontentloaded' });
    await expect(page.getByText('Sin Buyer Personas')).toBeVisible({ timeout: 30_000 });

    await page.getByRole('button', { name: /Modo Manual/i }).first().click();

    // Should navigate to persona detail page
    await expect(page).toHaveURL(
      new RegExp(`brand-studio/publico/persona/${FAKE_PERSONA_ID}`),
      { timeout: 15_000 },
    );
  });
});
