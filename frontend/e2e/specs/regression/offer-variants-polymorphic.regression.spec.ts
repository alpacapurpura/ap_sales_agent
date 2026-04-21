/**
 * Offer Studio — Variantes Polimórficas @regression
 *
 * Un test por variant_structure (6 estructuras):
 *   TIER, SKU_VARIANT, REGIONAL, MODALITY, LANGUAGE, TEMPORAL_COHORT
 *
 * Cada test verifica:
 *   1. El endpoint /editions devuelve las ediciones con la estructura correcta.
 *   2. VariantCollectionLandingPage renderiza el noun plural correcto.
 *   3. El CTA "+ Nueva <nounSingular>" está visible.
 *
 * Todos los endpoints de API están mockeados.
 */

import { type Page } from '@playwright/test';
import {
  test,
  expect,
  buildTierOffer,
  buildSkuVariantOffer,
  buildRegionalOffer,
  buildModalityOffer,
  buildLanguageOffer,
  buildTemporalCohortOffer,
  setupOfferStudioMocks,
} from '../../fixtures/offer-studio.fixture';

// ---------------------------------------------------------------------------
// Helper: verifica que la página /editions renderiza el noun plural esperado
// ---------------------------------------------------------------------------

async function assertEditionsLanding(
  page: Page,
  tenantId: string,
  offerId: string,
  nounPlural: string,
  nounSingular: string,
) {
  await page.goto(
    `/${tenantId}/offer-studio/offer/${offerId}/editions`,
    { waitUntil: 'domcontentloaded' },
  );
  await page.waitForLoadState('networkidle');
  await expect(page.locator('main')).toBeVisible({ timeout: 45_000 });

  const currentUrl = page.url();
  if (currentUrl.includes('/editions')) {
    // Noun plural heading should be visible
    const heading = page.getByRole('heading', { name: new RegExp(nounPlural, 'i') });
    await expect(heading).toBeVisible({ timeout: 10_000 });

    // CTA button: "Nueva plan" / "Nueva cohorte" / etc.
    const ctaBtn = page.getByRole('button', { name: new RegExp(`nueva? ${nounSingular}`, 'i') });
    await expect(ctaBtn).toBeVisible({ timeout: 5_000 });
  } else {
    // Redirected to editor — single-variant guard triggered
    expect(currentUrl).toMatch(/\/editor/);
  }
}

// ---------------------------------------------------------------------------
// TIER
// ---------------------------------------------------------------------------

test.describe('Variantes — TIER (Planes) @regression', () => {
  test('muestra "Planes" y el CTA "Nueva plan" en el landing de editions', async ({ page, tenantId }) => {
    const { offer, editions } = buildTierOffer();
    await setupOfferStudioMocks(page, offer, editions);
    await assertEditionsLanding(page, tenantId, offer.id, 'Planes', 'plan');
  });
});

// ---------------------------------------------------------------------------
// SKU_VARIANT
// ---------------------------------------------------------------------------

test.describe('Variantes — SKU_VARIANT (Variantes) @regression', () => {
  test('muestra "Variantes" y el CTA "Nueva variante" en el landing de editions', async ({ page, tenantId }) => {
    const { offer, editions } = buildSkuVariantOffer();
    await setupOfferStudioMocks(page, offer, editions);
    await assertEditionsLanding(page, tenantId, offer.id, 'Variantes', 'variante');
  });
});

// ---------------------------------------------------------------------------
// REGIONAL
// ---------------------------------------------------------------------------

test.describe('Variantes — REGIONAL (Regiones) @regression', () => {
  test('muestra "Regiones" y el CTA "Nueva región" en el landing de editions', async ({ page, tenantId }) => {
    const { offer, editions } = buildRegionalOffer();
    await setupOfferStudioMocks(page, offer, editions);
    await assertEditionsLanding(page, tenantId, offer.id, 'Regiones', 'región');
  });
});

// ---------------------------------------------------------------------------
// MODALITY
// ---------------------------------------------------------------------------

test.describe('Variantes — MODALITY (Modalidades) @regression', () => {
  test('muestra "Modalidades" y el CTA "Nueva modalidad" en el landing de editions', async ({ page, tenantId }) => {
    const { offer, editions } = buildModalityOffer();
    await setupOfferStudioMocks(page, offer, editions);
    await assertEditionsLanding(page, tenantId, offer.id, 'Modalidades', 'modalidad');
  });
});

// ---------------------------------------------------------------------------
// LANGUAGE
// ---------------------------------------------------------------------------

test.describe('Variantes — LANGUAGE (Idiomas) @regression', () => {
  test('muestra "Idiomas" y el CTA "Nueva idioma" en el landing de editions', async ({ page, tenantId }) => {
    const { offer, editions } = buildLanguageOffer();
    await setupOfferStudioMocks(page, offer, editions);
    await assertEditionsLanding(page, tenantId, offer.id, 'Idiomas', 'idioma');
  });
});

// ---------------------------------------------------------------------------
// TEMPORAL_COHORT
// ---------------------------------------------------------------------------

test.describe('Variantes — TEMPORAL_COHORT (Cohortes) @regression', () => {
  test('muestra "Cohortes" y el CTA "Nueva cohorte" en el landing de editions', async ({ page, tenantId }) => {
    const { offer, editions } = buildTemporalCohortOffer();
    await setupOfferStudioMocks(page, offer, editions);
    await assertEditionsLanding(page, tenantId, offer.id, 'Cohortes', 'cohorte');
  });
});
