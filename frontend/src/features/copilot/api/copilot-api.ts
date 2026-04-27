import { config } from "@/lib/config";

import { useCopilotStore } from "../store/copilot-store";

const API_URL = config.api.baseUrl;

/** Parses a single SSE data payload. Returns null on malformed JSON (skip silently). */
function tryParseSSEData(dataStr: string): Record<string, unknown> | null {
  try {
    return JSON.parse(dataStr) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export interface CopilotChatPayload {
  message: string;
  conversation_id?: string | null;
  /** Structured blocks attached to the user message (images, audio, video, documents). */
  blocks?: Record<string, unknown>[];
  context?: {
    current_route?: string | null;
    selected_fields?: Record<string, string>[];
    form_data?: Record<string, unknown>;
    locale?: string;
  };
}

/**
 * SSE event types emitted by the BE.
 *
 * F8 §5.4 — the backend now emits the v2 ``block_*`` + ``message_*`` family
 * as the canonical streaming protocol. ``text_chunk`` is kept here only for
 * backwards compatibility while the dual-emit migration window closes; once
 * the BE drops it (post-deploy of F8) the frontend handler short-circuits
 * silently because the switch defaults to no-op for unknown events.
 *
 * @see backend/src/modules/copilot/application/orchestrator/chat.py
 */
export type SSEEventType =
  // ── Streaming primitives (v2 — preferred) ─────────────────────────
  | "message_start"
  | "message_end"
  | "block_start"
  | "block_delta"
  | "block_end"
  | "block_append"
  // ── Tool + UI side channels ───────────────────────────────────────
  | "tool_start"
  | "tool_result"
  | "ui_action"
  | "proposal"
  | "confirmation_required"
  // ── Lifecycle ─────────────────────────────────────────────────────
  | "status"
  | "done"
  | "error"
  // ── Legacy (removed by F8 §5.4 — kept for transitional safety) ────
  | "text_chunk";

export interface SSEEventData {
  event: SSEEventType;
  data: Record<string, unknown>;
}

/**
 * Build standard headers with tenant ID and auth for copilot API calls.
 */
export function getCopilotHeaders(token: string): Record<string, string> {
  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
  };

  if (typeof window !== "undefined") {
    const pathSegments = window.location.pathname.split("/").filter(Boolean);
    if (pathSegments.length > 0) {
      const globals = [
        "sign-in",
        "sign-up",
        "forbidden",
        "visit",
        "api",
        "p",
        "onboarding",
        "settings",
        "admin",
        "dashboard",
        "_next",
        "connections",
        "static",
        "favicon.ico",
      ];
      if (!globals.includes(pathSegments[0])) {
        headers["X-Tenant-ID"] = pathSegments[0];
      }
    }
    const stored = localStorage.getItem("x-tenant-id");
    if (stored && !headers["X-Tenant-ID"]) {
      headers["X-Tenant-ID"] = stored;
    }
  }

  return headers;
}

/**
 * Fire-and-forget event reporting to the copilot events API.
 * Auto-reads conversationId and currentRoute from the store.
 */
export function reportCopilotEvent(
  eventType: string,
  eventData: Record<string, unknown>,
  token: string,
): void {
  const state = useCopilotStore.getState();
  const headers = getCopilotHeaders(token);
  headers["Content-Type"] = "application/json";

  fetch(`${API_URL}/api/v1/copilot/events/record`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      event_type: eventType,
      event_data: eventData,
      conversation_id: state.conversationId || undefined,
      route: state.currentRoute || undefined,
    }),
  }).catch(() => {
    // Best-effort — don't block UI on event tracking failures
  });
}

/** Retry configuration for SSE stream failures. */
const SSE_RETRY_CONFIG = {
  maxAttempts: 3,
  baseDelayMs: 1000,
} as const;

/**
 * Returns true if the error is a network-level failure that warrants a retry.
 * Network errors (connection refused, timeout, etc.) may be transient.
 * Server errors (4xx/5xx) indicate the request was received — do NOT retry.
 */
function isRetryableError(error: unknown): boolean {
  // TypeError is thrown by fetch for network failures (no response received)
  if (error instanceof TypeError) return true;
  // AbortError means the user or AbortController cancelled — do NOT retry
  if (error instanceof DOMException && error.name === "AbortError") return false;
  return false;
}

/**
 * Single canonical callback shape — both ``streamCopilotChat`` and the
 * internal ``attemptSSEStream`` accept this. Splitting it kept producing
 * drift between the two argument lists; one type, one source of truth.
 *
 * F8 §5.4 — ``onBlockDelta`` is the canonical render path. ``onTextChunk``
 * is kept optional during the dual-emit migration window and silently
 * ignored once the BE stops emitting it.
 */
export interface CopilotChatCallbacks {
  // Streaming render (v2)
  onMessageStart?: (data: { message_id: string; role: string; created_at: string }) => void;
  onBlockStart?: (data: {
    message_id: string;
    block_id: string;
    type: string;
    index: number;
  }) => void;
  onBlockDelta?: (data: {
    message_id: string;
    block_id: string;
    delta: { markdown?: string };
  }) => void;
  onBlockEnd?: (data: {
    message_id: string;
    block_id: string;
    final: Record<string, unknown>;
  }) => void;
  onBlockAppend?: (data: { message_id: string; block: Record<string, unknown> }) => void;
  onMessageEnd?: (data: { message_id: string; status: string; tokens_used?: number }) => void;
  // Tool + UI side channels
  onToolStart?: (tool: string, args: Record<string, unknown>) => void;
  onToolResult?: (tool: string, result: string) => void;
  onUIAction?: (action: Record<string, unknown>) => void;
  // Lifecycle
  onStatus: (state: string) => void;
  onDone: (conversationId: string) => void;
  onError: (message: string) => void;
  // Legacy — removed once BE drops dual-emit (F8 §5.4 cutover).
  onTextChunk?: (content: string) => void;
  // Retry feedback for the network-error backoff loop
  onRetry?: (attempt: number, maxAttempts: number) => void;
}

/**
 * Executes one SSE streaming attempt (single fetch + stream read-loop).
 * Returns true if the stream completed successfully (received "done" event).
 * Throws on network error. Calls onError + returns false on server errors.
 */
async function attemptSSEStream(
  payload: CopilotChatPayload,
  callbacks: CopilotChatCallbacks,
  token: string,
  signal?: AbortSignal,
): Promise<boolean> {
  const headers = getCopilotHeaders(token);
  headers["Content-Type"] = "application/json";

  // Network errors here (connection refused, timeout) bubble up as TypeError
  const response = await fetch(`${API_URL}/api/v1/copilot/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    // Server returned an HTTP error — request was received, do not retry
    const text = await response.text();
    callbacks.onError(`Error ${response.status}: ${text}`);
    return false;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError("No readable stream available");
    return false;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      // Network drop mid-stream throws TypeError here — let it bubble up
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events from buffer
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // Keep incomplete line in buffer

      let currentEvent = "";
      for (const line of lines) {
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          const dataStr = line.slice(6);
          const parsed = tryParseSSEData(dataStr);
          // eslint-disable-next-line max-depth -- SSE parsing is inherently 5 levels deep; extracting further would obscure intent
          if (parsed !== null) {
            handleSSEEvent(currentEvent as SSEEventType, parsed, callbacks);
          }
          currentEvent = "";
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  return true;
}

/**
 * Streams a copilot chat response via SSE.
 * Uses native fetch + ReadableStream (no external lib needed).
 *
 * Retry strategy: network errors (TypeError) are retried up to 3 times with
 * exponential backoff (1s, 2s, 4s). Server errors (4xx/5xx) are NOT retried
 * because the request was received by the server. AbortSignal cancellations
 * are never retried.
 */
// eslint-disable-next-line sonarjs/cognitive-complexity -- Irreducible: retry loop (3 attempts), abort propagation, error classification, and exponential back-off are each a branch but tightly coupled — extracting further would not reduce the total branching, only relocate it.
export async function streamCopilotChat(
  payload: CopilotChatPayload,
  callbacks: CopilotChatCallbacks,
  token: string,
  signal?: AbortSignal,
): Promise<void> {
  const { maxAttempts, baseDelayMs } = SSE_RETRY_CONFIG;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      // If AbortSignal is already aborted, stop immediately without an error
      if (signal?.aborted) return;

      await attemptSSEStream(payload, callbacks, token, signal);
      // Attempt returned without throwing — stream completed (or server error
      // was already reported via onError). Either way, we're done.
      return;
    } catch (error) {
      // Propagate abort cancellations immediately — user intent, not a failure
      if (signal?.aborted) return;

      if (!isRetryableError(error)) {
        // Non-network error (unexpected) — report and bail
        const message = error instanceof Error ? error.message : String(error);
        callbacks.onError(`Stream error: ${message}`);
        return;
      }

      // Network error — retry if attempts remain
      if (attempt < maxAttempts) {
        callbacks.onRetry?.(attempt, maxAttempts);
        const delayMs = baseDelayMs * Math.pow(2, attempt - 1); // 1s, 2s, 4s
        await new Promise<void>((resolve) => setTimeout(resolve, delayMs));
      } else {
        // All attempts exhausted
        const message = error instanceof Error ? error.message : String(error);
        callbacks.onError(`Connection failed after ${maxAttempts} attempts: ${message}`);
      }
    }
  }
}

/** Wire-level update payload for POST /conversations/{id}/mutations/apply. */
export interface ApplyMutationUpdate {
  field_id: string;
  new_value: unknown;
  reason?: string;
}

/** Wire-level applied row returned by the apply endpoint. */
export interface AppliedMutationRow {
  id: string;
  field_path: string;
  domain: string;
  status: "applied" | "existing";
}

/** Wire-level rejected row returned by the apply endpoint. */
export interface RejectedMutationRow {
  field_id: string;
  reason: string;
}

/** Wire-level response from POST /conversations/{id}/mutations/apply. */
export interface ApplyMutationsResult {
  applied: AppliedMutationRow[];
  rejected: RejectedMutationRow[];
}

/**
 * Server-side fallback for ``ProposalCard.handleApply`` when no
 * ``FormRuntimeBridge`` is connected (B22-FP1 AC2). Persists each update
 * idempotently into ``copilot_mutation_journal`` and dispatches the
 * per-domain side-effect handler so a page reload renders the new value.
 *
 * Throws on network or HTTP errors so the caller can transition the
 * card UI to ``status="failed"``. Successful HTTP returns may still
 * include rejected rows — the caller decides how to render mixed
 * outcomes (currently: any rejected → ``status="failed"``).
 */
export async function applyCopilotMutations(
  conversationId: string,
  messageId: string,
  updates: ApplyMutationUpdate[],
  token: string,
): Promise<ApplyMutationsResult> {
  const headers = getCopilotHeaders(token);
  headers["Content-Type"] = "application/json";

  const response = await fetch(
    `${API_URL}/api/v1/copilot/conversations/${conversationId}/mutations/apply`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({ message_id: messageId, updates }),
    },
  );

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`apply_mutations_${response.status}: ${text}`);
  }

  return (await response.json()) as ApplyMutationsResult;
}

/** Wire-level row returned by GET /conversations/{id}/mutations. */
export interface MutationJournalEntry {
  id: string;
  message_id: string;
  domain: string;
  entity_id: string | null;
  field_path: string;
  applied_at: string;
}

interface MutationJournalListResponse {
  entries: MutationJournalEntry[];
}

/**
 * Fetch active (non-reverted) mutation-journal entries for a conversation.
 *
 * Used by ``ProposalCard`` to repaint per-field "applied" status after a
 * refresh — without this rehydrate the card always re-renders ``pending``
 * regardless of the underlying journal state. ``messageId`` narrows the
 * lookup to a single proposal so the BE only returns rows the card cares
 * about.
 *
 * Returns ``null`` on any failure (network drop, non-2xx, parse error)
 * so the caller falls back to the default ``pending`` initial state and
 * the card stays usable even if observability is briefly unavailable.
 */
export async function fetchAppliedMutations(
  conversationId: string,
  messageId: string,
  token: string,
): Promise<MutationJournalEntry[] | null> {
  const headers = getCopilotHeaders(token);
  const url = `${API_URL}/api/v1/copilot/conversations/${conversationId}/mutations?message_id=${encodeURIComponent(
    messageId,
  )}`;
  let response: Response;
  try {
    response = await fetch(url, { headers });
  } catch {
    return null;
  }
  if (!response.ok) return null;
  try {
    const body = (await response.json()) as MutationJournalListResponse;
    return body.entries;
  } catch {
    return null;
  }
}

/** Wire-level shape of ActiveJobProgressDTO from the backend. */
export interface ActiveJobProgressDTO {
  job_id: string;
  module: string;
  entity_id: string | null;
  source_kind: string;
  source_ref: string;
  scope: string;
  mode: string;
  started_at: string;
  status: string | null;
  progress: number | null;
  stage: string | null;
  filled_fields: string[];
  filled_fields_by_section: Record<string, string[]>;
  sections_touched: string[];
  sections_completed: string[];
  finished_at: string | null;
  poll_endpoint: string;
}

interface ActiveJobsResponse {
  jobs: ActiveJobProgressDTO[];
}

/**
 * Fetch the active extraction jobs for a conversation.
 * Returns the jobs array, or null on any failure (network, non-ok, parse error).
 */
export async function fetchActiveJobs(
  conversationId: string,
  token: string,
): Promise<ActiveJobProgressDTO[] | null> {
  const headers = getCopilotHeaders(token);
  let response: Response;
  const activeJobsUrl = `${API_URL}/api/v1/copilot/conversations/${conversationId}/active-jobs`;
  try {
    response = await fetch(activeJobsUrl, {
      headers,
    });
  } catch {
    return null;
  }
  if (!response.ok) return null;
  try {
    const body = (await response.json()) as ActiveJobsResponse;
    return body.jobs;
  } catch {
    return null;
  }
}

/**
 * Dispatch a parsed SSE frame to the matching callback.
 *
 * F8 §5.4 — block_* / message_* are the canonical render path. Unknown or
 * deprecated events fall through silently (no throw) so the BE can drop a
 * frame mid-deploy without breaking older FE tabs that haven't refreshed.
 */

function handleSSEEvent(
  event: SSEEventType,
  data: Record<string, unknown>,
  callbacks: CopilotChatCallbacks,
) {
  switch (event) {
    // ── Streaming primitives (v2 — preferred) ─────────────────────
    case "message_start":
      callbacks.onMessageStart?.(data as { message_id: string; role: string; created_at: string });
      break;
    case "message_end":
      callbacks.onMessageEnd?.(
        data as { message_id: string; status: string; tokens_used?: number },
      );
      break;
    case "block_start":
      callbacks.onBlockStart?.(
        data as { message_id: string; block_id: string; type: string; index: number },
      );
      break;
    case "block_delta":
      callbacks.onBlockDelta?.(
        data as { message_id: string; block_id: string; delta: { markdown?: string } },
      );
      break;
    case "block_end":
      callbacks.onBlockEnd?.(
        data as { message_id: string; block_id: string; final: Record<string, unknown> },
      );
      break;
    case "block_append":
      callbacks.onBlockAppend?.(data as { message_id: string; block: Record<string, unknown> });
      break;
    // ── Tool + UI side channels ───────────────────────────────────
    case "tool_start":
      callbacks.onToolStart?.(data.tool as string, (data.args ?? {}) as Record<string, unknown>);
      break;
    case "tool_result":
      callbacks.onToolResult?.(data.tool as string, data.result as string);
      break;
    case "ui_action":
      callbacks.onUIAction?.(data);
      break;
    // ── Lifecycle ─────────────────────────────────────────────────
    case "status":
      callbacks.onStatus(data.state as string);
      break;
    case "done":
      callbacks.onDone(data.conversation_id as string);
      break;
    case "error":
      callbacks.onError(data.message as string);
      break;
    // ── Legacy (removed by F8 §5.4 cutover) ───────────────────────
    case "text_chunk":
      callbacks.onTextChunk?.(data.content as string);
      break;
    // proposal / confirmation_required: reserved frames, no FE action yet.
    case "proposal":
    case "confirmation_required":
      break;
  }
}
