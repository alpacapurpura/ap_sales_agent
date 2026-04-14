import { type Page, type Locator, expect } from '@playwright/test';

/**
 * Page Object Model for the Personality Engine section in Brand Studio → Esencia.
 *
 * Locator strategy:
 * - Role-based selectors preferred (getByRole, getByText, getByLabel)
 * - #voice-personality anchor for scoping to the personality section
 * - Never CSS attribute selectors
 *
 * The section renders in two states:
 *   - Empty: no profile configured — shows CTAs to select preset or clone
 *   - Configured: active personality profile — shows name, dimensions, sample
 */
export class PersonalityPage {
  /** The #voice-personality wrapper div in EsenciaView */
  readonly personalitySection: Locator;

  // ── Empty-state locators ─────────────────────────────────────────────────

  /** "Elegir preset" button — visible when no profile is configured */
  readonly selectPresetButton: Locator;

  /** "Clonar personalidad" button — visible when no profile is configured */
  readonly cloneButton: Locator;

  /** Description text visible in empty state */
  readonly emptyStateText: Locator;

  // ── Configured-state locators ────────────────────────────────────────────

  /** Profile name — any text rendered as <p class="font-semibold"> */
  readonly profileName: Locator;

  /** "Editar" button — visible when a profile is active */
  readonly editButton: Locator;

  /** Dimension label text — rendered per each of the 6 dimensions */
  readonly dimensionLabels: Locator;

  /** Badge showing profile type (Preset / Clonado / Entrevista / Manual) */
  readonly profileTypeBadge: Locator;

  // ── Loading state ────────────────────────────────────────────────────────

  /** Loading pulse shown while the API request is in-flight */
  readonly loadingIndicator: Locator;

  constructor(public readonly page: Page) {
    this.personalitySection = page.locator('#voice-personality');

    // Empty state
    this.selectPresetButton = page.getByRole('button', { name: /elegir preset/i });
    this.cloneButton = page.getByRole('button', { name: /clonar personalidad/i });
    this.emptyStateText = page.getByText(/define la personalidad de tu agente/i);

    // Configured state
    this.profileName = page.locator('#voice-personality p.font-semibold').first();
    this.editButton = page.getByRole('button', { name: /editar/i }).first();
    this.dimensionLabels = page.getByText(/energía|calidez|humor|expresividad|narrativa|verbosidad/i);
    this.profileTypeBadge = page.getByText(/^(Preset|Clonado|Entrevista|Manual)$/);

    // Loading
    this.loadingIndicator = page.getByText(/cargando perfil de personalidad/i);
  }

  // ── Navigation ────────────────────────────────────────────────────────────

  /** Navigate to Brand Studio → Esencia for a given tenant. */
  async navigateToEsencia(tenantId: string) {
    await this.page.goto(`/${tenantId}/brand-studio/esencia`, {
      waitUntil: 'domcontentloaded',
    });
  }

  // ── State assertions ──────────────────────────────────────────────────────

  /**
   * Assert that the personality section wrapper is present in the DOM.
   * Works for both empty and configured states.
   */
  async expectSectionVisible() {
    await expect(this.personalitySection).toBeVisible({ timeout: 45_000 });
  }

  /**
   * Assert that the empty state is rendered — description text and action
   * buttons are both visible.
   */
  async expectEmptyState() {
    await expect(this.emptyStateText).toBeVisible({ timeout: 10_000 });
    await expect(this.selectPresetButton).toBeVisible();
    await expect(this.cloneButton).toBeVisible();
  }

  /**
   * Assert that a configured profile is rendered — profile name and the
   * edit button are visible.
   */
  async expectConfiguredState() {
    await expect(this.profileName).toBeVisible({ timeout: 10_000 });
    await expect(this.editButton).toBeVisible();
  }

  /**
   * Assert that the section is in either empty OR configured state.
   * Use this when the test environment may or may not have a profile saved.
   */
  async expectEitherState() {
    const isEmpty = await this.selectPresetButton.isVisible().catch(() => false);
    const isConfigured = await this.profileName.isVisible().catch(() => false);
    expect(isEmpty || isConfigured, 'Expected personality section to be in empty or configured state').toBeTruthy();
  }

  /**
   * Assert that the loading state is NOT shown (i.e. the API call has resolved).
   */
  async expectLoaded() {
    await expect(this.loadingIndicator).not.toBeVisible({ timeout: 15_000 });
  }
}
