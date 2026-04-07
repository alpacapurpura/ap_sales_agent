import { clerk, clerkSetup } from '@clerk/testing/playwright';
import { test as setup } from '@playwright/test';
import path from 'path';

setup.describe.configure({ mode: 'serial' });
const authFile = path.join(__dirname, '../../playwright/.clerk/user.json');

setup('clerk setup', async ({}) => {
  console.log('[clerk-setup] env check:', {
    CLERK_PUBLISHABLE_KEY: process.env.CLERK_PUBLISHABLE_KEY ? 'SET' : 'UNSET',
    CLERK_SECRET_KEY: process.env.CLERK_SECRET_KEY ? 'SET' : 'UNSET',
    CLERK_TESTING_TOKEN: process.env.CLERK_TESTING_TOKEN ? 'SET' : 'UNSET',
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ? 'SET' : 'UNSET',
    E2E_CLERK_USER_EMAIL: process.env.E2E_CLERK_USER_EMAIL ? 'SET' : 'UNSET',
    E2E_BASE_URL: process.env.E2E_BASE_URL ?? 'UNSET',
  });
  await clerkSetup();
  console.log('[clerk-setup] clerkSetup() completed');
});

setup('authenticate', async ({ page }) => {
  setup.setTimeout(120_000);

  // Navigate to sign-in (public route — no middleware redirect)
  console.log('[clerk-setup] Navigating to /sign-in ...');
  await page.goto('/sign-in', { waitUntil: 'networkidle', timeout: 60_000 });
  console.log('[clerk-setup] Page URL after goto:', page.url());

  // Diagnostic: check if Clerk JS loaded
  const clerkState = await page.evaluate(() => ({
    clerkDefined: typeof (window as any).Clerk !== 'undefined',
    clerkLoaded: !!(window as any).Clerk?.loaded,
    clerkVersion: (window as any).Clerk?.version ?? null,
    documentTitle: document.title,
    bodyText: document.body?.innerText?.slice(0, 200) ?? '',
  }));
  console.log('[clerk-setup] Clerk state:', JSON.stringify(clerkState));

  if (!clerkState.clerkLoaded) {
    console.log('[clerk-setup] Clerk not loaded yet, waiting up to 30s...');
    try {
      await page.waitForFunction(
        () => (window as any).Clerk?.loaded === true,
        { timeout: 30_000 },
      );
      console.log('[clerk-setup] Clerk loaded after explicit wait');
    } catch {
      // Take screenshot for diagnostics and re-check state
      const state2 = await page.evaluate(() => ({
        clerkDefined: typeof (window as any).Clerk !== 'undefined',
        clerkLoaded: !!(window as any).Clerk?.loaded,
        url: window.location.href,
        bodyText: document.body?.innerText?.slice(0, 300) ?? '',
      }));
      console.error('[clerk-setup] Clerk STILL not loaded after 30s:', JSON.stringify(state2));
      throw new Error(`Clerk JS never loaded. State: ${JSON.stringify(state2)}`);
    }
  }

  // Sign in with extended timeout
  console.log('[clerk-setup] Calling clerk.signIn...');
  await clerk.signIn({
    page,
    signInParams: {
      strategy: 'password',
      identifier: process.env.E2E_CLERK_USER_EMAIL || process.env.E2E_CLERK_USER_USERNAME!,
      password: process.env.E2E_CLERK_USER_PASSWORD!,
    },
  });
  console.log('[clerk-setup] clerk.signIn completed');

  await page.context().storageState({ path: authFile });
  console.log('[clerk-setup] Auth state saved to', authFile);
});
