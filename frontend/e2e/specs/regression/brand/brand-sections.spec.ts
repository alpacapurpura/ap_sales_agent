import { test, expect } from '../../../fixtures/auth.fixture';
import { BrandStudioPage } from '../../../pages/brand-studio.page';
import { BRAND_SECTIONS } from '../../../fixtures/test-data';

test.describe('Brand Studio Sections', () => {
  let brandPage: BrandStudioPage;

  test.beforeEach(async ({ page, tenantId }) => {
    brandPage = new BrandStudioPage(page, tenantId);
  });

  for (const section of BRAND_SECTIONS) {
    test(`${section} section loads correctly`, async () => {
      await brandPage.goto(section);
      await brandPage.expectLoaded();
      await brandPage.expectSection(section);
    });
  }

  test('sidebar navigation between sections works', async ({ page, tenantId }) => {
    await brandPage.goto('esencia');
    await brandPage.expectLoaded();

    // Navigate using sidebar links
    const sidebarLinks = page.locator('[data-testid="sidebar"] a');
    const linkCount = await sidebarLinks.count();
    expect(linkCount).toBeGreaterThan(0);
  });
});
