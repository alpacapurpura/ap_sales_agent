import { config } from "@/lib/config";

const API_URL = config.api.baseUrl;

export interface CopilotChatPayload {
  message: string;
  conversation_id?: string | null;
  context?: {
    current_route?: string | null;
    selected_fields?: Array<Record<string, string>>;
    form_data?: Record<string, unknown>;
    locale?: string;
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
 * Streams a copilot chat response via SSE.
 * Uses native fetch + ReadableStream (no external lib needed).
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
  },
  signal?: AbortSignal,
): Promise<void> {
  // Build headers with tenant ID
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
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

  const response = await fetch(`${API_URL}/api/v1/copilot/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    const text = await response.text();
    callbacks.onError(`Error ${response.status}: ${text}`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError("No readable stream available");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
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
