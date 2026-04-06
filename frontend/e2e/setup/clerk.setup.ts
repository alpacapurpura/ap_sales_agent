import { clerk, clerkSetup, setupClerkTestingToken } from '@clerk/testing/playwright';
import { test as setup } from '@playwright/test';
import path from 'path';

setup.describe.configure({ mode: 'serial' });
const authFile = path.join(__dirname, '../../playwright/.clerk/user.json');

setup('clerk setup', async ({}) => {
  await clerkSetup();
});

setup('authenticate', async ({ page }) => {
  setup.setTimeout(60_000);
  await setupClerkTestingToken({ page });
  await page.goto('/sign-in', { waitUntil: 'domcontentloaded', timeout: 45_000 });
  await clerk.signIn({
    page,
    signInParams: {
      strategy: 'password',
      identifier: process.env.E2E_CLERK_USER_EMAIL || process.env.E2E_CLERK_USER_USERNAME!,
      password: process.env.E2E_CLERK_USER_PASSWORD!,
    },
  });
  // Save storage state immediately after sign-in (cookies + localStorage)
  // Individual tests will use setupClerkTestingToken in the auth fixture
  await page.context().storageState({ path: authFile });
});
