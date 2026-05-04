import { clerk, clerkSetup, setupClerkTestingToken } from '@clerk/testing/playwright';
import { test as setup, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

setup.describe.configure({ mode: 'serial' });

const authFile = path.join(__dirname, '../../playwright/.clerk/user.json');
const FRESH_WINDOW_MS = 4 * 60 * 60 * 1000;
const CF_BM_SAFETY_MARGIN_S = 5 * 60;
const SIGNIN_RETRIES = 2;
const SIGNIN_BACKOFF_MS = 3_000;

function isAuthFileFresh(): boolean {
  if (!fs.existsSync(authFile)) return false;
  try {
    const stat = fs.statSync(authFile);
    const ageMs = Date.now() - stat.mtimeMs;
    if (ageMs > FRESH_WINDOW_MS) return false;

    const raw = JSON.parse(fs.readFileSync(authFile, 'utf-8')) as {
      cookies?: Array<{ name: string; expires?: number }>;
    };
    const cookies = raw.cookies ?? [];
    if (cookies.length === 0) return false;

    const nowS = Math.floor(Date.now() / 1000);
    const cfBm = cookies.find((c) => c.name === '__cf_bm');
    if (cfBm?.expires && cfBm.expires - nowS < CF_BM_SAFETY_MARGIN_S) return false;

    const clerkSession = cookies.find((c) => c.name.startsWith('__session') || c.name.startsWith('__client'));
    if (!clerkSession) return false;

    return true;
  } catch {
    return false;
  }
}

function wipeAuthFile(): void {
  if (fs.existsSync(authFile)) {
    fs.unlinkSync(authFile);
    console.log('[clerk.setup] wiped stale auth file');
  }
}

setup('clerk setup', async () => {
  await clerkSetup();
});

setup('authenticate', async ({ page }) => {
  setup.setTimeout(180_000);

  if (isAuthFileFresh()) {
    console.log('[clerk.setup] auth file fresh — skipping re-auth');
    return;
  }

  wipeAuthFile();
  fs.mkdirSync(path.dirname(authFile), { recursive: true });

  await setupClerkTestingToken({ page });

  let lastErr: unknown;
  for (let attempt = 1; attempt <= SIGNIN_RETRIES + 1; attempt++) {
    try {
      await page.goto('/sign-in', { waitUntil: 'networkidle', timeout: 60_000 });
      await clerk.signIn({
        page,
        signInParams: {
          strategy: 'password',
          identifier: process.env.E2E_CLERK_USER_EMAIL || process.env.E2E_CLERK_USER_USERNAME!,
          password: process.env.E2E_CLERK_USER_PASSWORD!,
        },
      });

      await page.goto('/', { waitUntil: 'domcontentloaded', timeout: 30_000 });
      const isAuthed = await page.evaluate(() => {
        const w = window as unknown as { Clerk?: { session?: unknown } };
        return Boolean(w.Clerk?.session);
      });
      expect(isAuthed, 'Clerk session not active after signIn').toBe(true);

      await page.context().storageState({ path: authFile });
      console.log(`[clerk.setup] auth state saved (attempt ${attempt})`);
      return;
    } catch (err) {
      lastErr = err;
      const msg = err instanceof Error ? err.message : String(err);
      console.warn(`[clerk.setup] attempt ${attempt} failed: ${msg}`);
      wipeAuthFile();
      if (attempt <= SIGNIN_RETRIES) {
        await new Promise((r) => setTimeout(r, SIGNIN_BACKOFF_MS * attempt));
      }
    }
  }
  throw new Error(`Clerk auth failed after ${SIGNIN_RETRIES + 1} attempts: ${String(lastErr)}`);
});
