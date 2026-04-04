import { test, expect } from '@playwright/test';
import { mockApiResponse } from '../../fixtures/api-mock.fixture';

test.describe('Landing Page Visual Regression', () => {
  test('landing page renders correctly', async ({ page }) => {
    await mockApiResponse(page, '**/api/v1/landing/public/**', {
      id: 'visual-test',
      title: 'Visual Test Landing',
      slug: 'visual-test',
      sections: [],
      published: true,
    });

    await page.goto('/p/visual-test');
    await page.waitForLoadState('load');

    await expect(page).toHaveScreenshot('landing-public.png', {
      maxDiffPixelRatio: 0.01,
      fullPage: false,
    });
  });
});
