import { type Page } from '@playwright/test';

export async function mockExternalServices(page: Page) {
  await page.route('**/graph.facebook.com/**', (route) => route.abort());
  await page.route('**/analyticsdata.googleapis.com/**', (route) => route.abort());
  await page.route('**/*.shopify.com/**', (route) => route.abort());
}

export async function mockApiResponse(page: Page, pattern: string, data: unknown) {
  await page.route(pattern, async (route) => {
    await route.fulfill({ json: data, status: 200 });
  });
}
