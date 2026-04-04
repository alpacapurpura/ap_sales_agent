import { test, expect } from '../../../fixtures/auth.fixture';
import { GrowthStudioPage } from '../../../pages/growth-studio.page';
import { GROWTH_STAGES } from '../../../fixtures/test-data';

test.describe('Growth Studio - Stages', () => {
  let growthPage: GrowthStudioPage;

  test.beforeEach(async ({ page, tenantId }) => {
    growthPage = new GrowthStudioPage(page, tenantId);
  });

  for (const stage of GROWTH_STAGES) {
    test(`${stage} stage renders`, async () => {
      await growthPage.goto(stage);
      await growthPage.expectLoaded();
      await growthPage.expectStage(stage);
    });
  }
});
