import { test, expect } from '../../fixtures/auth.fixture';
import { PersonalityPage } from '../../pages/personality.page';

/**
 * Smoke tests for the Personality Engine section in Brand Studio → Esencia.
 *
 * These tests verify that the #voice-personality section renders correctly in
 * both the empty state (no profile configured) and the configured state (active
 * personality profile).  They do NOT test saving, editing, or cloning — those
 * are covered by integration/regression tests.
 *
 * The dev server must be running (`docker compose up -d`) before executing.
 * Auth is handled by the shared Clerk fixture (storageState from clerk.setup.ts).
 */
test.describe('Personality Engine @smoke', () => {
  test('personality section is visible in Esencia tab', async ({ page, tenantId }) => {
    const personality = new PersonalityPage(page);
    await personality.navigateToEsencia(tenantId);

    // Section must be in the DOM regardless of profile state
    await personality.expectSectionVisible();

    // Loading skeleton must resolve before we make assertions
    await personality.expectLoaded();
  });

  test('personality section heading "Voz & Personalidad" is rendered', async ({ page, tenantId }) => {
    const personality = new PersonalityPage(page);
    await personality.navigateToEsencia(tenantId);
    await personality.expectSectionVisible();

    // The SectionHeader title is always rendered above the PersonalitySection card
    await expect(page.getByRole('heading', { name: /voz & personalidad/i }).first())
      .toBeVisible({ timeout: 45_000 });
  });

  test('personality section shows preset CTAs or active profile (not blank)', async ({ page, tenantId }) => {
    const personality = new PersonalityPage(page);
    await personality.navigateToEsencia(tenantId);
    await personality.expectSectionVisible();
    await personality.expectLoaded();

    // The section must render content in one of the two known states
    await personality.expectEitherState();
  });

  test('empty state exposes "Elegir preset" and "Clonar personalidad" buttons', async ({
    page,
    tenantId,
  }) => {
    const personality = new PersonalityPage(page);
    await personality.navigateToEsencia(tenantId);
    await personality.expectSectionVisible();
    await personality.expectLoaded();

    const isEmpty = await personality.selectPresetButton.isVisible().catch(() => false);
    if (!isEmpty) {
      // Profile is already configured — skip this assertion rather than failing
      test.info().annotations.push({
        type: 'info',
        description: 'Personality already configured — empty-state buttons not shown (expected).',
      });
      return;
    }

    await personality.expectEmptyState();
  });

  test('configured state shows profile name and edit button', async ({ page, tenantId }) => {
    const personality = new PersonalityPage(page);
    await personality.navigateToEsencia(tenantId);
    await personality.expectSectionVisible();
    await personality.expectLoaded();

    const isConfigured = await personality.profileName.isVisible().catch(() => false);
    if (!isConfigured) {
      // No profile saved — skip this assertion rather than failing
      test.info().annotations.push({
        type: 'info',
        description: 'No personality profile configured — configured-state assertions skipped (expected).',
      });
      return;
    }

    await personality.expectConfiguredState();
  });

  test('personality section does not crash on navigation (page has no JS errors)', async ({
    page,
    tenantId,
  }) => {
    const jsErrors: string[] = [];
    page.on('pageerror', (err) => jsErrors.push(err.message));

    const personality = new PersonalityPage(page);
    await personality.navigateToEsencia(tenantId);
    await personality.expectSectionVisible();
    await personality.expectLoaded();

    // No unhandled JS exceptions while rendering the personality section
    expect(jsErrors, `Unexpected JS errors: ${jsErrors.join('; ')}`).toHaveLength(0);
  });
});
