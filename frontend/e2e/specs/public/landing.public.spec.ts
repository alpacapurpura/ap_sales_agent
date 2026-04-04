import { test, expect } from '@playwright/test';
import { LandingPublicPage } from '../../pages/landing-public.page';
import { mockApiResponse } from '../../fixtures/api-mock.fixture';

test.describe('Public Landing Pages', () => {
  test('landing page renders with valid slug', async ({ page }) => {
    // Mock the landing page API to avoid backend dependency
    await mockApiResponse(page, '**/api/v1/landing/public/**', {
      id: 'test-landing',
      title: 'Test Landing Page',
      slug: 'test-page',
      sections: [],
      published: true,
    });

    const landingPage = new LandingPublicPage(page);
    await landingPage.goto('test-page');
    await landingPage.expectLoaded();
  });

  test('non-existent landing shows 404', async ({ page }) => {
    await page.route('**/api/v1/landing/public/**', async (route) => {
      await route.fulfill({ status: 404, json: { detail: 'Not found' } });
    });

    const landingPage = new LandingPublicPage(page);
    await landingPage.goto('non-existent-slug');
    await landingPage.expectNotFound();
  });
});
