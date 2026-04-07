import { clerk, clerkSetup, setupClerkTestingToken } from '@clerk/testing/playwright';
import { test as setup } from '@playwright/test';
import path from 'path';

setup.describe.configure({ mode: 'serial' });
const authFile = path.join(__dirname, '../../playwright/.clerk/user.json');

async function withRetry<T>(
  fn: () => Promise<T>,
  opts: { retries: number; label: string },
): Promise<T> {
  const delays = [2_000, 4_000, 8_000];
  for (let attempt = 1; attempt <= opts.retries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      const isLast = attempt === opts.retries;
      const msg = error instanceof Error ? error.message : String(error);
      console.warn(
        `[clerk-setup] ${opts.label} attempt ${attempt}/${opts.retries} failed: ${msg}`,
      );
      if (isLast) throw error;
      const delay = delays[attempt - 1] ?? 8_000;
      console.warn(`[clerk-setup] Retrying in ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('unreachable');
}

setup('clerk setup', async ({}) => {
  await clerkSetup();
});

setup('authenticate', async ({ page }) => {
  setup.setTimeout(60_000);
  await page.goto('/', { waitUntil: 'domcontentloaded', timeout: 45_000 });
  await withRetry(
    () =>
      clerk.signIn({
        page,
        signInParams: {
          strategy: 'password',
          identifier: process.env.E2E_CLERK_USER_EMAIL || process.env.E2E_CLERK_USER_USERNAME!,
          password: process.env.E2E_CLERK_USER_PASSWORD!,
        },
      }),
    { retries: 3, label: 'clerk.signIn' },
  );
  await page.context().storageState({ path: authFile });
});
