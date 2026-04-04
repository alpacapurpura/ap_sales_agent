import { test, expect } from '../../../fixtures/auth.fixture';

test.describe('Tenant Isolation', () => {
  test('API calls include X-Tenant-ID header', async ({ page, tenantId }) => {
    const apiCalls: string[] = [];
    await page.route('**/api/v1/**', async (route) => {
      const headers = route.request().headers();
      apiCalls.push(headers['x-tenant-id'] || 'MISSING');
      await route.continue();
    });
    await page.goto(`/${tenantId}/brand-studio/esencia`);
    await page.waitForLoadState('load');

    expect(apiCalls.length).toBeGreaterThan(0);
    for (const tid of apiCalls) {
      expect(tid).toBe(tenantId);
    }
  });

  test('accessing another tenant URL redirects or blocks', async ({ page, tenantId }) => {
    const fakeTenantId = '00000000-0000-0000-0000-000000000000';
    await page.goto(`/${fakeTenantId}/brand-studio/esencia`);

    // Should either redirect to real tenant or show forbidden/error
    const url = page.url();
    const isForbidden = url.includes('forbidden');
    const isRedirected = url.includes(tenantId);
    const isSignIn = url.includes('sign-in');
    expect(isForbidden || isRedirected || isSignIn).toBe(true);
  });
});
