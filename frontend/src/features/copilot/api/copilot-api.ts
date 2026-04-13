import { config } from "@/lib/config";
import { useCopilotStore } from "../store/copilot-store";

const API_URL = config.api.baseUrl;

export interface CopilotChatPayload {
  message: string;
  conversation_id?: string | null;
  context?: {
    current_route?: string | null;
    selected_fields?: Array<Record<string, string>>;
    form_data?: Record<string, unknown>;
    locale?: string;
    focus?: {
      domain: string;
      entity_id?: string | null;
    } | null;
    interview_session_id?: string | null;
  };
}

export type SSEEventType =
  | "text_chunk"
  | "tool_start"
  | "tool_result"
  | "ui_action"
  | "proposal"
  | "confirmation_required"
  | "status"
  | "done"
  | "error";

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
        "sign-in", "sign-up", "forbidden", "visit", "api", "p",
        "onboarding", "settings", "admin", "dashboard", "_next",
        "connections", "static", "favicon.ico",
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
 * Executes one SSE streaming attempt (single fetch + stream read-loop).
 * Returns true if the stream completed successfully (received "done" event).
 * Throws on network error. Calls onError + returns false on server errors.
 */
async function attemptSSEStream(
  payload: CopilotChatPayload,
  callbacks: {
    onTextChunk: (content: string) => void;
    onToolStart?: (tool: string, args: Record<string, unknown>) => void;
    onToolResult?: (tool: string, result: string) => void;
    onUIAction?: (action: Record<string, unknown>) => void;
    onStatus: (state: string) => void;
    onDone: (conversationId: string) => void;
    onError: (message: string) => void;
  },
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
          try {
            const data = JSON.parse(dataStr);
            handleSSEEvent(currentEvent as SSEEventType, data, callbacks);
          } catch {
            // Skip malformed JSON
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
export async function streamCopilotChat(
  payload: CopilotChatPayload,
  callbacks: {
    onTextChunk: (content: string) => void;
    onToolStart?: (tool: string, args: Record<string, unknown>) => void;
    onToolResult?: (tool: string, result: string) => void;
    onUIAction?: (action: Record<string, unknown>) => void;
    onStatus: (state: string) => void;
    onDone: (conversationId: string) => void;
    onError: (message: string) => void;
    onRetry?: (attempt: number, maxAttempts: number) => void;
  },
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

function handleSSEEvent(
  event: SSEEventType,
  data: Record<string, unknown>,
  callbacks: Parameters<typeof streamCopilotChat>[1],
) {
  switch (event) {
    case "text_chunk":
      callbacks.onTextChunk(data.content as string);
      break;
    case "tool_start":
      callbacks.onToolStart?.(data.tool as string, (data.args ?? {}) as Record<string, unknown>);
      break;
    case "tool_result":
      callbacks.onToolResult?.(data.tool as string, data.result as string);
      break;
    case "ui_action":
      callbacks.onUIAction?.(data);
      break;
    case "status":
      callbacks.onStatus(data.state as string);
      break;
    case "done":
      callbacks.onDone(data.conversation_id as string);
      break;
    case "error":
      callbacks.onError(data.message as string);
      break;
  }
}
