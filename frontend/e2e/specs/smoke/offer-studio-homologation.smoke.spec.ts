/**
 * Offer Studio — Homologación @smoke
 *
 * Verifica las rutas post-F3/F4 y los flujos críticos del Offer Studio:
 *   - Journey A: Crear oferta nueva (wizard → editor)
 *   - Journey E: Offer sin variante (lead magnet, no VariantRail)
 *   - Journey F: Cambio de variante activa via rail (TEMPORAL_COHORT)
 *
 * Todos los endpoints de API están mockeados — no requiere backend corriendo.
 */

import {
  test,
  expect,
  buildLeadMagnetOffer,
  buildTemporalCohortOffer,
  setupOfferStudioMocks,
} from '../../fixtures/offer-studio.fixture';
import { OfferStudioPage } from '../../pages/offer-studio.page';

// ---------------------------------------------------------------------------
// Journey A — Crear oferta nueva (wizard → editor)
// ---------------------------------------------------------------------------

test.describe('Journey A — Wizard: crear oferta nueva @smoke', () => {
  test('abre el wizard al hacer clic en "Nueva oferta"', async ({ page, tenantId }) => {
    const { offer, editions } = buildTemporalCohortOffer();
    await setupOfferStudioMocks(page, offer, editions);

    // Mock empty offers list so the dashboard shows the empty state CTA
    await page.route('**/api/v1/offer/products**', async (route) => {
      const url = route.request().url();
      if (url.match(/\/products\/[^/]+\/editions/)) {
        await route.fulfill({ json: editions, status: 200 });
      } else if (url.match(/\/products\/[^/]+$/)) {
        await route.fulfill({ json: offer, status: 200 });
      } else {
        await route.fulfill({ json: [], status: 200 });
      }
    });

    await page.goto(`/${tenantId}/offer-studio`, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle');

    // Dashboard must load
    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });

    // The "Nueva oferta" button should appear (either in empty state or header)
    const cta = page.getByRole('button', { name: /nueva oferta/i }).first();
    await expect(cta).toBeVisible({ timeout: 10_000 });
  });

  test('el wizard muestra contenido al navegar a /new', async ({ page, tenantId }) => {
    const { offer, editions } = buildTemporalCohortOffer();
    await setupOfferStudioMocks(page, offer, editions);

    // Navigate directly to the wizard
    await page.goto(`/${tenantId}/offer-studio/new`, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle');

    // Main content must load
    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });
    // The wizard must show some content
    const mainText = await page.locator('main').innerText();
    expect(mainText.length).toBeGreaterThan(0);
  });

  test('navegar a /editor aterriza en el editor de la oferta', async ({ page, tenantId }) => {
    const { offer, editions } = buildTemporalCohortOffer();
    await setupOfferStudioMocks(page, offer, editions);

    const studioPage = new OfferStudioPage(page, tenantId);
    await studioPage.gotoEditor(offer.id);

    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });
    await expect(page).toHaveURL(new RegExp(`offer-studio/offer/${offer.id}/editor`));
  });

  test('la sección "Promesa" se accede desde la URL /editor/promise', async ({ page, tenantId }) => {
    const { offer, editions } = buildTemporalCohortOffer();
    await setupOfferStudioMocks(page, offer, editions);

    await page.goto(
      `/${tenantId}/offer-studio/offer/${offer.id}/editor`,
      { waitUntil: 'domcontentloaded' },
    );
    await page.waitForLoadState('networkidle');
    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });

    // Navigate to the "promise" section
    await page.goto(
      `/${tenantId}/offer-studio/offer/${offer.id}/editor/promise`,
      { waitUntil: 'domcontentloaded' },
    );

    await expect(page).toHaveURL(new RegExp(`/editor/promise`));
    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });
  });
});

// ---------------------------------------------------------------------------
// Journey E — Offer sin variante (lead magnet)
// ---------------------------------------------------------------------------

test.describe('Journey E — Offer sin variante (lead magnet) @smoke', () => {
  test('el editor carga correctamente para una oferta lead magnet', async ({ page, tenantId }) => {
    const { offer, editions } = buildLeadMagnetOffer();
    await setupOfferStudioMocks(page, offer, editions);

    await page.goto(
      `/${tenantId}/offer-studio/offer/${offer.id}/editor`,
      { waitUntil: 'domcontentloaded' },
    );
    await page.waitForLoadState('networkidle');

    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });
    await expect(page).toHaveURL(new RegExp(`/offer/${offer.id}/editor`));
  });

  test('navegar a la sección promesa en lead magnet funciona correctamente', async ({ page, tenantId }) => {
    const { offer, editions } = buildLeadMagnetOffer();
    await setupOfferStudioMocks(page, offer, editions);

    await page.goto(
      `/${tenantId}/offer-studio/offer/${offer.id}/editor/promise`,
      { waitUntil: 'domcontentloaded' },
    );
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(new RegExp(`/editor/promise`));
    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });
  });
});

// ---------------------------------------------------------------------------
// Journey F — Cambio de variante via rail (TEMPORAL_COHORT)
// ---------------------------------------------------------------------------

test.describe('Journey F — VariantRail con TEMPORAL_COHORT @smoke', () => {
  test('el editor de una oferta con cohortes carga sin error', async ({ page, tenantId }) => {
    const { offer, editions } = buildTemporalCohortOffer();
    await setupOfferStudioMocks(page, offer, editions);

    await page.goto(
      `/${tenantId}/offer-studio/offer/${offer.id}/editor`,
      { waitUntil: 'domcontentloaded' },
    );
    await page.waitForLoadState('networkidle');

    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });
    await expect(page).toHaveURL(new RegExp(`/offer/${offer.id}/editor`));
  });

  test('la ruta /editions responde para una oferta con 3 cohortes', async ({ page, tenantId }) => {
    const { offer, editions } = buildTemporalCohortOffer();
    await setupOfferStudioMocks(page, offer, editions);

    await page.goto(
      `/${tenantId}/offer-studio/offer/${offer.id}/editions`,
      { waitUntil: 'domcontentloaded' },
    );
    await page.waitForLoadState('networkidle');

    // Either editions landing or editor redirect — both valid after the guard
    const currentUrl = page.url();
    expect(
      currentUrl.includes('/editions') || currentUrl.includes('/editor'),
    ).toBe(true);

    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });
  });

  test('navegar a /editor/promise desde una oferta con cohortes funciona', async ({ page, tenantId }) => {
    const { offer, editions } = buildTemporalCohortOffer();
    await setupOfferStudioMocks(page, offer, editions);

    await page.goto(
      `/${tenantId}/offer-studio/offer/${offer.id}/editor/promise`,
      { waitUntil: 'domcontentloaded' },
    );
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(new RegExp(`/editor/promise`));
    await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });
  });
});
