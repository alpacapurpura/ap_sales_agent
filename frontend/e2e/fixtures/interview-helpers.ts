/**
 * Helpers for E2E tests that interact with the real AI backend.
 *
 * These helpers are designed for *.verify.spec.ts tests that:
 * - Hit the real backend (no Playwright route mocking)
 * - Wait for actual AI responses (non-deterministic, slow)
 * - Capture and evaluate buyer persona quality
 *
 * All API calls go through the browser via page.evaluate() so that
 * the real Clerk session token is used automatically.
 */

import { type Page, type BrowserContext } from '@playwright/test';
import { type CopilotPage } from '../pages/copilot.pom';

// ── Types (mirrored from lib/api/buyer-persona.ts) ───────────────────────────

export interface BuyerPersona {
  id: string;
  name: string;
  tagline: string | null;
  scope: 'GLOBAL' | 'OFFER' | 'CAMPAIGN';
  offer_id: string | null;
  is_primary: boolean;
  demographics: Record<string, unknown>;
  psychographics: Record<string, unknown>;
  pain_points: Record<string, unknown>[];
  desires: Record<string, unknown>[];
  objections: Record<string, unknown>[];
  preferred_channels: Record<string, unknown>[];
  buyer_journey: Record<string, unknown>;
  purchase_triggers: string[];
  anti_patterns: string[];
  completeness_score: number;
  interview_session_id: string | null;
  created_at: string | null;
  updated_at: string | null;
}

// ── Config ───────────────────────────────────────────────────────────────────

const BACKEND_URL = process.env.E2E_BACKEND_URL ?? 'http://localhost:8000';

// ── Token helper ─────────────────────────────────────────────────────────────

/**
 * Get the current Clerk JWT from the browser session.
 * Requires the page to have a loaded Clerk session (authenticated route).
 */
export async function getClerkToken(page: Page): Promise<string> {
  const token = await page.evaluate(async () => {
    // window.Clerk is injected by @clerk/nextjs in the browser
    const t = await (window as unknown as { Clerk?: { session?: { getToken: () => Promise<string> } } })
      .Clerk?.session?.getToken();
    return t ?? null;
  });
  if (!token) {
    throw new Error('Could not obtain Clerk token from page. Is the user authenticated?');
  }
  return token;
}

// ── API helpers ──────────────────────────────────────────────────────────────

/**
 * Fetch all buyer personas for the tenant via the real backend API.
 * Uses the browser's Clerk session — page must be on an authenticated route.
 */
export async function listPersonasViaAPI(
  page: Page,
  tenantId: string,
): Promise<BuyerPersona[]> {
  return page.evaluate(
    async ({ backendUrl, tid }) => {
      const token = await (window as unknown as { Clerk?: { session?: { getToken: () => Promise<string> } } })
        .Clerk?.session?.getToken();
      const res = await fetch(`${backendUrl}/api/v1/brand/buyer-personas/`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tid,
        },
      });
      if (!res.ok) return [];
      return res.json() as Promise<unknown[]>;
    },
    { backendUrl: BACKEND_URL, tid: tenantId },
  ) as Promise<BuyerPersona[]>;
}

/**
 * Fetch a single buyer persona by ID.
 * Returns null if not found or request fails.
 */
export async function getPersonaViaAPI(
  page: Page,
  personaId: string,
  tenantId: string,
): Promise<BuyerPersona | null> {
  return page.evaluate(
    async ({ backendUrl, tid, id }) => {
      const token = await (window as unknown as { Clerk?: { session?: { getToken: () => Promise<string> } } })
        .Clerk?.session?.getToken();
      const res = await fetch(`${backendUrl}/api/v1/brand/buyer-personas/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tid,
        },
      });
      if (!res.ok) return null;
      return res.json() as Promise<unknown>;
    },
    { backendUrl: BACKEND_URL, tid: tenantId, id: personaId },
  ) as Promise<BuyerPersona | null>;
}

/**
 * Delete all buyer personas for the tenant (cleanup).
 * Safe to call even if there are no personas.
 */
export async function deleteAllPersonasViaAPI(
  page: Page,
  tenantId: string,
): Promise<number> {
  return page.evaluate(
    async ({ backendUrl, tid }) => {
      const token = await (window as unknown as { Clerk?: { session?: { getToken: () => Promise<string> } } })
        .Clerk?.session?.getToken();

      const listRes = await fetch(`${backendUrl}/api/v1/brand/buyer-personas/`, {
        headers: { Authorization: `Bearer ${token}`, 'X-Tenant-ID': tid },
      });
      if (!listRes.ok) return 0;

      const personas = (await listRes.json()) as Array<{ id: string }>;
      let deleted = 0;

      for (const persona of personas) {
        const delRes = await fetch(`${backendUrl}/api/v1/brand/buyer-personas/${persona.id}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}`, 'X-Tenant-ID': tid },
        });
        if (delRes.ok) deleted++;
      }

      return deleted;
    },
    { backendUrl: BACKEND_URL, tid: tenantId },
  ) as Promise<number>;
}

/**
 * Abandon any active interview session for the tenant (cleanup).
 * Returns true if an active session was found and abandoned.
 */
export async function abandonActiveInterviewViaAPI(
  page: Page,
  tenantId: string,
): Promise<boolean> {
  return page.evaluate(
    async ({ backendUrl, tid }) => {
      const token = await (window as unknown as { Clerk?: { session?: { getToken: () => Promise<string> } } })
        .Clerk?.session?.getToken();

      // Get active session
      const activeRes = await fetch(`${backendUrl}/api/v1/copilot/interview/active`, {
        headers: { Authorization: `Bearer ${token}`, 'X-Tenant-ID': tid },
      });
      if (activeRes.status === 204) return false; // No active session

      const active = (await activeRes.json()) as { session_id?: string };
      if (!active.session_id) return false;

      // Abandon it
      const abandonRes = await fetch(
        `${backendUrl}/api/v1/copilot/interview/${active.session_id}/abandon`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}`, 'X-Tenant-ID': tid },
        },
      );
      return abandonRes.ok;
    },
    { backendUrl: BACKEND_URL, tid: tenantId },
  ) as Promise<boolean>;
}

/**
 * Full cleanup: abandon active interviews + delete all personas.
 * Call in beforeEach and afterEach to ensure a clean slate.
 */
export async function cleanupForTest(page: Page, tenantId: string): Promise<void> {
  await abandonActiveInterviewViaAPI(page, tenantId);
  await deleteAllPersonasViaAPI(page, tenantId);
}

// ── AI interaction helpers ───────────────────────────────────────────────────

/**
 * Send a message and wait for the AI to finish responding.
 *
 * Waits for the typing indicator to appear (AI started) then disappear (AI done).
 * Adds a short settle delay for DOM to stabilize after streaming.
 *
 * @param copilot - CopilotPage POM instance
 * @param message - Text to send
 * @param timeoutMs - Max wait for AI response (default 60s — real AI can be slow)
 */
export async function sendAndWaitForAI(
  copilot: CopilotPage,
  message: string,
  timeoutMs = 60_000,
): Promise<void> {
  await copilot.chatInput.fill(message);
  await copilot.sendButton.click();

  // Wait for typing indicator to appear (AI received the message)
  await copilot.typingIndicator.waitFor({ state: 'visible', timeout: 15_000 });

  // Wait for typing indicator to disappear (AI finished responding)
  await copilot.typingIndicator.waitFor({ state: 'hidden', timeout: timeoutMs });

  // Short DOM settle — SSE events are processed async, preview pane may still update
  await copilot.page.waitForTimeout(800);
}

/**
 * Wait for a checkpoint card to appear. Returns true if it appeared within the timeout.
 *
 * Use this after sending messages that should trigger a block summary.
 */
export async function waitForCheckpoint(
  copilot: CopilotPage,
  timeoutMs = 90_000,
): Promise<boolean> {
  try {
    await copilot.checkpointCard.waitFor({ state: 'visible', timeout: timeoutMs });
    return true;
  } catch {
    return false;
  }
}

/**
 * Wait for the interview-complete card. Returns true if it appeared.
 */
export async function waitForInterviewComplete(
  copilot: CopilotPage,
  timeoutMs = 120_000,
): Promise<boolean> {
  try {
    await copilot.interviewCompleteCard.waitFor({ state: 'visible', timeout: timeoutMs });
    return true;
  } catch {
    return false;
  }
}

/**
 * Count messages in the copilot chat by role.
 */
export async function countMessages(copilot: CopilotPage): Promise<{ user: number; assistant: number }> {
  const page = copilot.page;
  const userCount = await page.locator('[data-role="user"]').count();
  const assistantCount = await page.locator('[data-role="assistant"]').count();
  return { user: userCount, assistant: assistantCount };
}

/**
 * Capture the full conversation transcript from the DOM.
 * Returns an array of {role, text} objects.
 */
export async function captureTranscript(
  copilot: CopilotPage,
): Promise<Array<{ role: string; text: string }>> {
  return copilot.page.evaluate(() => {
    const messages = document.querySelectorAll('[data-role]');
    return Array.from(messages).map((el) => ({
      role: el.getAttribute('data-role') ?? 'unknown',
      text: el.textContent?.trim() ?? '',
    }));
  });
}

/**
 * Intercept POST /brand/buyer-personas response to capture the created persona ID.
 * Call this BEFORE the action that creates the persona.
 *
 * @returns Promise that resolves with the persona ID once the POST fires
 */
export function captureCreatedPersonaId(page: Page): Promise<string> {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('Persona creation timed out')), 30_000);

    page.on('response', async (response) => {
      if (
        response.url().includes('/api/v1/brand/buyer-personas') &&
        response.request().method() === 'POST'
      ) {
        clearTimeout(timeout);
        try {
          const body = (await response.json()) as { id: string };
          resolve(body.id);
        } catch {
          reject(new Error('Could not parse persona creation response'));
        }
      }
    });
  });
}
