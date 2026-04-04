import { test as base, expect } from '@playwright/test';
import { setupClerkTestingToken } from '@clerk/testing/playwright';

type TenantFixtures = { tenantId: string };

export const test = base.extend<TenantFixtures>({
  tenantId: [process.env.E2E_TENANT_ID!, { option: true }],
  page: async ({ page, tenantId }, use) => {
    // Inject testing token interceptor so Clerk FAPI calls bypass bot protection
    await setupClerkTestingToken({ page });
    await page.addInitScript((tid) => {
      localStorage.setItem('x-tenant-id', tid);
    }, tenantId);
    await use(page);
  },
});
export { expect };
