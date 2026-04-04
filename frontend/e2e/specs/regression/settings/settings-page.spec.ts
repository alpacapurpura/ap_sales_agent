import { test, expect } from '../../../fixtures/auth.fixture';
import { SettingsPage } from '../../../pages/settings.page';

test.describe('Settings Page', () => {
  test('renders settings page', async ({ page, tenantId }) => {
    const settingsPage = new SettingsPage(page, tenantId);
    await settingsPage.goto();
    await settingsPage.expectLoaded();
  });

  test('settings page has navigation or content', async ({ page, tenantId }) => {
    const settingsPage = new SettingsPage(page, tenantId);
    await settingsPage.goto();
    await expect(page.locator('main')).toBeVisible();
  });
});
