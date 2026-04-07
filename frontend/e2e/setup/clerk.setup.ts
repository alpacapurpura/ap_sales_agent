import { clerk, clerkSetup, setupClerkTestingToken } from '@clerk/testing/playwright';
import { test as setup } from '@playwright/test';
import path from 'path';

setup.describe.configure({ mode: 'serial' });
const authFile = path.join(__dirname, '../../playwright/.clerk/user.json');

setup('clerk setup', async ({}) => {
  await clerkSetup();
});

setup('authenticate', async ({ page }) => {
  setup.setTimeout(120_000);

  // Inject testing token into page — required for Clerk FAPI to accept requests
  await setupClerkTestingToken({ page });

  // Navigate to sign-in (public route — Clerk loads without middleware redirect)
  await page.goto('/sign-in', { waitUntil: 'networkidle', timeout: 60_000 });

  // Sign in programmatically
  await clerk.signIn({
    page,
    signInParams: {
      strategy: 'password',
      identifier: process.env.E2E_CLERK_USER_EMAIL || process.env.E2E_CLERK_USER_USERNAME!,
      password: process.env.E2E_CLERK_USER_PASSWORD!,
    },
  });

  await page.context().storageState({ path: authFile });
});
