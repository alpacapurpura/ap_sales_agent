import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';
import path from 'path';

// Load env vars from the root .env BEFORE defineConfig runs.
// Playwright's Node process does not read .env automatically (Next.js does,
// but Playwright is a separate Node process). Without this, clerk.setup.ts
// sees undefined E2E_CLERK_USER_EMAIL / NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
// and authentication fails with a misleading "invalid credentials" error.
//
// We load from the repo-root .env (frontend/.env is a symlink to it) and
// allow .env.e2e to override specific values for E2E-only tweaks.
dotenv.config({ path: path.resolve(__dirname, '../.env') });
dotenv.config({ path: path.resolve(__dirname, '.env.e2e'), override: true });

// Fail fast with a clear message if the essential Clerk E2E vars are missing.
// This catches misconfiguration before the first test runs, instead of
// producing cryptic "clerk.signIn() timed out" errors 60 seconds in.
const requiredEnvVars = [
  'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY',
  'CLERK_SECRET_KEY',
  'E2E_CLERK_USER_EMAIL',
  'E2E_CLERK_USER_PASSWORD',
  'E2E_TENANT_ID',
] as const;
const missing = requiredEnvVars.filter((k) => !process.env[k]);
if (missing.length > 0) {
  throw new Error(
    `[playwright.config] Missing required env vars for Clerk E2E setup: ` +
      `${missing.join(', ')}. ` +
      `Check /home/chris/AISALESHT/.env and frontend/.env.e2e.example.`,
  );
}

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : (process.env.E2E_BASE_URL ? 1 : 0),
  // Setup project pins itself to mode:'serial' (clerk.setup.ts). Smoke/regression/public/verify
  // can run in parallel safely — each test fixture re-injects Clerk testing token per page.
  workers: process.env.CI ? 2 : 4,
  reporter: process.env.CI
    ? [['html', { open: 'never' }], ['github']]
    : [['html', { open: 'never', host: '0.0.0.0' }]],

  timeout: 60_000,
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
    actionTimeout: 15_000,
    navigationTimeout: 45_000,
    launchOptions: {
      args: ['--disable-dev-shm-usage'],
    },
  },

  projects: [
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
      retries: 1,
      timeout: 60_000,
    },
    {
      name: 'smoke',
      testMatch: /.*\.smoke\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.clerk/user.json',
      },
      dependencies: ['setup'],
    },
    {
      name: 'regression',
      testMatch: /.*\.spec\.ts/,
      testIgnore: [/.*\.smoke\.spec\.ts/, /.*\.public\.spec\.ts/, /.*\.visual\.spec\.ts/, /.*\.verify\.spec\.ts/],
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.clerk/user.json',
      },
      dependencies: ['setup'],
    },
    {
      name: 'public',
      testMatch: /.*\.public\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
      dependencies: ['setup'],
    },
    {
      name: 'verify',
      testMatch: /.*\.verify\.spec\.ts/,
      // Real AI interviews take 5-12 min per scenario (scripted turns + drain loop).
      // 600s = enough for 6-7 scripted responses (~3 min) + drain to completion (~5 min).
      timeout: 600_000,
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.clerk/user.json',
        actionTimeout: 45_000,
        navigationTimeout: 60_000,
      },
      dependencies: ['setup'],
    },
    {
      // Visual regression specs — pixel-perfect baselines + responsive checks.
      // Run with: npx playwright test --project=visual --workers=1 [spec-file]
      // Baseline capture: add --update-snapshots on first run.
      name: 'visual',
      testMatch: /.*\.visual\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.clerk/user.json',
      },
      dependencies: ['setup'],
    },
  ],

  ...(process.env.E2E_BASE_URL ? {} : {
    webServer: {
      command: 'npm run dev',
      url: 'http://localhost:3000',
      reuseExistingServer: true,
      timeout: 120_000,
    },
  }),
});
