// [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
// API client for the suggestions engine (PR-1 PI-2 S2).

import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type {
  SuggestionAcceptRequest,
  SuggestionAcceptResponse,
  SuggestionsRequest,
  SuggestionsResponse,
} from "../types/suggestions";

const BASE = `${config.api.baseUrl}/api/v1/copilot`;

/**
 * POST /api/v1/copilot/suggestions
 *
 * Best-effort: returns empty response on non-401 failures (D-10 mirror).
 * 401 throws so the caller (hook) can surface auth errors.
 */
export async function fetchSuggestions(
  token: string,
  body: SuggestionsRequest,
): Promise<SuggestionsResponse> {
  const response = await fetchClient(`${BASE}/suggestions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    // 401 is the only hard fail — auth must be fixed upstream
    if (response.status === 401) throw new Error("Unauthorized");
    // All other failures: best-effort empty (D-10)
    return { suggestions: [], breakdown: {}, latency_ms: 0 };
  }

  return response.json() as Promise<SuggestionsResponse>;
}

/**
 * POST /api/v1/copilot/suggestions/accept
 *
 * Fire-and-forget telemetry producer. Never throws upstream — telemetry
 * failure must not affect user flow (D-13).
 */
export async function acceptSuggestion(
  token: string,
  body: SuggestionAcceptRequest,
): Promise<SuggestionAcceptResponse> {
  const response = await fetchClient(`${BASE}/suggestions/accept`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    // Fire-and-forget: never throw. Telemetry failure ≠ user-facing error.
    return { ok: false };
  }

  return response.json() as Promise<SuggestionAcceptResponse>;
}
