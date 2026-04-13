import { test, expect } from '../../fixtures/auth.fixture';
import { CopilotPage } from '../../pages/copilot.pom';
import { mockCopilotEvents } from '../../fixtures/copilot-chat.fixture';

/**
 * Smoke tests for the Copilot sidebar shell.
 *
 * These tests verify the layout and open/close behaviour — they do NOT send
 * messages (that is covered by copilot-chat.smoke.spec.ts).
 *
 * All copilot API calls are mocked so no real backend is required.
 */
test.describe('Copilot Sidebar @smoke', () => {
  test.beforeEach(async ({ page }) => {
    // Silence fire-and-forget event calls so we get no unhandled request warnings
    await mockCopilotEvents(page);

    // Nudge endpoint — return empty so the rail shows no pulse dot
    await page.route('**/api/v1/copilot/nudge-context**', async (route) => {
      await route.fulfill({ json: { nudges: [] }, status: 200 });
    });
  });

  test('sidebar is present in collapsed state on initial page load', async ({ page, tenantId }) => {
    const copilot = new CopilotPage(page);
    await copilot.goto(tenantId, 'brand-studio/esencia');

    // The aside element should be rendered (collapsed — narrow rail on desktop)
    await expect(copilot.sidebar).toBeVisible({ timeout: 45_000 });

    // Chat input should NOT be visible while collapsed
    await expect(copilot.chatInput).not.toBeVisible();
  });

  test('clicking the rail icon opens the sidebar panel', async ({ page, tenantId }) => {
    const copilot = new CopilotPage(page);
    await copilot.goto(tenantId, 'brand-studio/esencia');
    await expect(copilot.sidebar).toBeVisible({ timeout: 45_000 });

    // Click the first button inside the collapsed rail (Sparkles icon)
    const railButton = page.locator('[data-testid="copilot-sidebar"] button').first();
    await railButton.click();

    // Sidebar is now open — chat input becomes visible
    await copilot.expectSidebarOpen();
  });

  test('open sidebar shows chat input and send button', async ({ page, tenantId }) => {
    const copilot = new CopilotPage(page);
    await copilot.goto(tenantId, 'brand-studio/esencia');
    await expect(copilot.sidebar).toBeVisible({ timeout: 45_000 });

    // Open the panel
    await page.locator('[data-testid="copilot-sidebar"] button').first().click();

    // Input and send button must be reachable
    await copilot.expectInputReady();
  });

  test('open sidebar shows suggested actions when chat is empty', async ({ page, tenantId }) => {
    const copilot = new CopilotPage(page);
    await copilot.goto(tenantId, 'brand-studio/esencia');
    await expect(copilot.sidebar).toBeVisible({ timeout: 45_000 });

    await page.locator('[data-testid="copilot-sidebar"] button').first().click();
    await copilot.expectSidebarOpen();

    // Suggested actions are visible when no messages are present
    await expect(copilot.suggestedActions).toBeVisible({ timeout: 10_000 });
  });

  test('close button collapses the sidebar', async ({ page, tenantId }) => {
    const copilot = new CopilotPage(page);
    await copilot.goto(tenantId, 'brand-studio/esencia');
    await expect(copilot.sidebar).toBeVisible({ timeout: 45_000 });

    // Open
    await page.locator('[data-testid="copilot-sidebar"] button').first().click();
    await copilot.expectSidebarOpen();

    // Close via header button (title="Cerrar")
    const closeButton = page.locator('[data-testid="copilot-sidebar"] button[title="Cerrar"]').first();
    await closeButton.click();

    // Chat input should be hidden again
    await expect(copilot.chatInput).not.toBeVisible({ timeout: 5_000 });
  });
});
