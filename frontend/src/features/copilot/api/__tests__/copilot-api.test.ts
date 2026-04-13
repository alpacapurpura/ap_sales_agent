/**
 * Unit tests for the copilot API layer (audit item T3).
 *
 * Covers:
 *  - getCopilotHeaders: Bearer token, X-Tenant-ID from URL path and localStorage fallback
 *  - reportCopilotEvent: fire-and-forget POST with store state
 *  - streamCopilotChat: SSE parsing for every event type, HTTP error handling,
 *    network error retry (up to 3 attempts), AbortSignal cancellation
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ── Module mocks (must come before imports that use them) ─────────────────────

vi.mock("@/lib/config", () => ({
  config: { api: { baseUrl: "http://localhost:8000" } },
}));

vi.mock("@/features/copilot/store/copilot-store", () => ({
  useCopilotStore: {
    getState: vi.fn(() => ({
      conversationId: "conv-123",
      currentRoute: "/brand",
    })),
  },
}));

// Import after mocks are registered
import {
  getCopilotHeaders,
  reportCopilotEvent,
  streamCopilotChat,
  type CopilotChatPayload,
} from "../copilot-api";

// ── SSE helpers ───────────────────────────────────────────────────────────────

/**
 * Encode a list of SSE event strings into a Uint8Array stream chunk.
 * Each event is two lines: "event: <type>\n" + "data: <json>\n" + "\n"
 */
function buildSSEChunk(
  events: Array<{ event: string; data: Record<string, unknown> }>,
): Uint8Array {
  const lines = events
    .map(({ event, data }) => `event: ${event}\ndata: ${JSON.stringify(data)}\n`)
    .join("\n");
  return new TextEncoder().encode(lines + "\n");
}

/**
 * Build a minimal Response that yields a sequence of SSE chunks then ends.
 */
function buildSSEResponse(
  chunks: Array<Array<{ event: string; data: Record<string, unknown> }>>,
): Response {
  let chunkIdx = 0;
  const stream = new ReadableStream<Uint8Array>({
    pull(controller) {
      if (chunkIdx < chunks.length) {
        controller.enqueue(buildSSEChunk(chunks[chunkIdx++]));
      } else {
        controller.close();
      }
    },
  });
  return new Response(stream, { status: 200 });
}

// ── Default callback stubs ────────────────────────────────────────────────────

function makeCallbacks() {
  return {
    onTextChunk: vi.fn(),
    onToolStart: vi.fn(),
    onToolResult: vi.fn(),
    onUIAction: vi.fn(),
    onStatus: vi.fn(),
    onDone: vi.fn(),
    onError: vi.fn(),
    onRetry: vi.fn(),
  };
}

const DEFAULT_PAYLOAD: CopilotChatPayload = { message: "Hola" };

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("getCopilotHeaders", () => {
  afterEach(() => {
    localStorage.clear();
  });

  it("includes Authorization Bearer token", () => {
    const headers = getCopilotHeaders("my-token");
    expect(headers["Authorization"]).toBe("Bearer my-token");
  });

  it("extracts X-Tenant-ID from first non-global path segment", () => {
    // happy-dom starts with pathname '/'
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { ...window.location, pathname: "/acme-corp/brand" },
    });
    const headers = getCopilotHeaders("tok");
    expect(headers["X-Tenant-ID"]).toBe("acme-corp");
  });

  it("does not set X-Tenant-ID for global-only paths like /sign-in", () => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { ...window.location, pathname: "/sign-in" },
    });
    const headers = getCopilotHeaders("tok");
    expect(headers["X-Tenant-ID"]).toBeUndefined();
  });

  it("falls back to localStorage x-tenant-id when URL has no tenant segment", () => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { ...window.location, pathname: "/sign-in" },
    });
    localStorage.setItem("x-tenant-id", "stored-tenant");
    const headers = getCopilotHeaders("tok");
    expect(headers["X-Tenant-ID"]).toBe("stored-tenant");
  });

  it("prefers URL tenant over localStorage when both are present", () => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { ...window.location, pathname: "/url-tenant/page" },
    });
    localStorage.setItem("x-tenant-id", "stored-tenant");
    const headers = getCopilotHeaders("tok");
    expect(headers["X-Tenant-ID"]).toBe("url-tenant");
  });
});

describe("reportCopilotEvent", () => {
  it("fires a POST to the events endpoint with store state", () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, { status: 200 })
    );

    reportCopilotEvent("click", { target: "button" }, "tok-abc");

    expect(fetchSpy).toHaveBeenCalledOnce();
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/v1/copilot/events/record");
    expect(init.method).toBe("POST");
    const body = JSON.parse(init.body as string) as Record<string, unknown>;
    expect(body.event_type).toBe("click");
    expect(body.event_data).toEqual({ target: "button" });
    expect(body.conversation_id).toBe("conv-123");
    expect(body.route).toBe("/brand");

    fetchSpy.mockRestore();
  });

  it("does not throw when the fetch call rejects (best-effort)", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockRejectedValue(
      new TypeError("Network failure")
    );

    // Should not throw
    expect(() => reportCopilotEvent("ping", {}, "tok")).not.toThrow();

    // Wait a tick so the rejected promise is handled
    await Promise.resolve();

    fetchSpy.mockRestore();
  });
});

describe("streamCopilotChat — SSE event parsing", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, "fetch");
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("calls onTextChunk for each text_chunk event", async () => {
    fetchSpy.mockResolvedValue(
      buildSSEResponse([
        [{ event: "text_chunk", data: { content: "Hola " } }],
        [{ event: "text_chunk", data: { content: "mundo" } }],
        [{ event: "done", data: { conversation_id: "c1" } }],
      ])
    );

    const cbs = makeCallbacks();
    await streamCopilotChat(DEFAULT_PAYLOAD, cbs, "tok");

    expect(cbs.onTextChunk).toHaveBeenCalledTimes(2);
    expect(cbs.onTextChunk).toHaveBeenCalledWith("Hola ");
    expect(cbs.onTextChunk).toHaveBeenCalledWith("mundo");
  });

  it("calls onDone with conversation_id from done event", async () => {
    fetchSpy.mockResolvedValue(
      buildSSEResponse([
        [{ event: "done", data: { conversation_id: "conv-xyz" } }],
      ])
    );

    const cbs = makeCallbacks();
    await streamCopilotChat(DEFAULT_PAYLOAD, cbs, "tok");

    expect(cbs.onDone).toHaveBeenCalledWith("conv-xyz");
  });

  it("calls onStatus for status events", async () => {
    fetchSpy.mockResolvedValue(
      buildSSEResponse([
        [{ event: "status", data: { state: "thinking" } }],
        [{ event: "done", data: { conversation_id: "c2" } }],
      ])
    );

    const cbs = makeCallbacks();
    await streamCopilotChat(DEFAULT_PAYLOAD, cbs, "tok");

    expect(cbs.onStatus).toHaveBeenCalledWith("thinking");
  });

  it("calls onToolStart and onToolResult for tool events", async () => {
    fetchSpy.mockResolvedValue(
      buildSSEResponse([
        [{ event: "tool_start", data: { tool: "search", args: { q: "brand" } } }],
        [{ event: "tool_result", data: { tool: "search", result: "Found" } }],
        [{ event: "done", data: { conversation_id: "c3" } }],
      ])
    );

    const cbs = makeCallbacks();
    await streamCopilotChat(DEFAULT_PAYLOAD, cbs, "tok");

    expect(cbs.onToolStart).toHaveBeenCalledWith("search", { q: "brand" });
    expect(cbs.onToolResult).toHaveBeenCalledWith("search", "Found");
  });

  it("calls onUIAction for ui_action events", async () => {
    const action = { type: "navigate", route: "/offer", event: "ui_action" };
    fetchSpy.mockResolvedValue(
      buildSSEResponse([
        [{ event: "ui_action", data: action }],
        [{ event: "done", data: { conversation_id: "c4" } }],
      ])
    );

    const cbs = makeCallbacks();
    await streamCopilotChat(DEFAULT_PAYLOAD, cbs, "tok");

    expect(cbs.onUIAction).toHaveBeenCalledWith(action);
  });

  it("calls onError for server-sent error events", async () => {
    fetchSpy.mockResolvedValue(
      buildSSEResponse([
        [{ event: "error", data: { message: "Rate limit exceeded" } }],
      ])
    );

    const cbs = makeCallbacks();
    await streamCopilotChat(DEFAULT_PAYLOAD, cbs, "tok");

    expect(cbs.onError).toHaveBeenCalledWith("Rate limit exceeded");
  });

  it("calls onError for HTTP error responses (no retry)", async () => {
    fetchSpy.mockResolvedValue(
      new Response("Unauthorized", { status: 401 })
    );

    const cbs = makeCallbacks();
    await streamCopilotChat(DEFAULT_PAYLOAD, cbs, "tok");

    expect(cbs.onError).toHaveBeenCalledWith(
      expect.stringContaining("401")
    );
    // HTTP errors must not trigger retry
    expect(cbs.onRetry).not.toHaveBeenCalled();
    // Fetch should be called only once
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("skips malformed JSON lines without calling onError", async () => {
    // Craft a raw SSE chunk with invalid JSON
    const badChunk = new TextEncoder().encode(
      "event: text_chunk\ndata: {not json}\n\n" +
      "event: done\ndata: {\"conversation_id\":\"c5\"}\n\n"
    );
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(badChunk);
        controller.close();
      },
    });
    fetchSpy.mockResolvedValue(new Response(stream, { status: 200 }));

    const cbs = makeCallbacks();
    await streamCopilotChat(DEFAULT_PAYLOAD, cbs, "tok");

    // Bad JSON is silently skipped, done event still processed
    expect(cbs.onTextChunk).not.toHaveBeenCalled();
    expect(cbs.onDone).toHaveBeenCalledWith("c5");
    expect(cbs.onError).not.toHaveBeenCalled();
  });
});

describe("streamCopilotChat — retry on network error", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, "fetch");
    // Speed up retry delays
    vi.useFakeTimers();
  });

  afterEach(() => {
    fetchSpy.mockRestore();
    vi.useRealTimers();
  });

  it("retries up to 3 times on TypeError (network failure) and calls onError on exhaustion", async () => {
    fetchSpy.mockRejectedValue(new TypeError("Failed to fetch"));

    const cbs = makeCallbacks();
    const promise = streamCopilotChat(DEFAULT_PAYLOAD, cbs, "tok");

    // Advance through all retry delays: 1s, 2s, 4s
    await vi.advanceTimersByTimeAsync(1000);
    await vi.advanceTimersByTimeAsync(2000);
    await vi.advanceTimersByTimeAsync(4000);
    await promise;

    expect(fetchSpy).toHaveBeenCalledTimes(3);
    expect(cbs.onRetry).toHaveBeenCalledTimes(2); // called before attempt 2 and 3
    expect(cbs.onRetry).toHaveBeenNthCalledWith(1, 1, 3);
    expect(cbs.onRetry).toHaveBeenNthCalledWith(2, 2, 3);
    expect(cbs.onError).toHaveBeenCalledWith(
      expect.stringContaining("Connection failed after 3 attempts")
    );
  });

  it("succeeds on the second attempt after one network failure", async () => {
    fetchSpy
      .mockRejectedValueOnce(new TypeError("Transient error"))
      .mockResolvedValue(
        buildSSEResponse([
          [{ event: "done", data: { conversation_id: "retry-conv" } }],
        ])
      );

    const cbs = makeCallbacks();
    const promise = streamCopilotChat(DEFAULT_PAYLOAD, cbs, "tok");

    // Advance through first retry delay
    await vi.advanceTimersByTimeAsync(1000);
    await promise;

    expect(fetchSpy).toHaveBeenCalledTimes(2);
    expect(cbs.onRetry).toHaveBeenCalledTimes(1);
    expect(cbs.onDone).toHaveBeenCalledWith("retry-conv");
    expect(cbs.onError).not.toHaveBeenCalled();
  });

  it("does not retry non-TypeError errors", async () => {
    fetchSpy.mockRejectedValue(new SyntaxError("Unexpected token"));

    const cbs = makeCallbacks();
    const promise = streamCopilotChat(DEFAULT_PAYLOAD, cbs, "tok");
    await promise;

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    expect(cbs.onRetry).not.toHaveBeenCalled();
    expect(cbs.onError).toHaveBeenCalledWith(
      expect.stringContaining("Stream error")
    );
  });
});

describe("streamCopilotChat — AbortSignal", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, "fetch");
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("returns immediately without calling fetch when signal is already aborted", async () => {
    const controller = new AbortController();
    controller.abort();

    const cbs = makeCallbacks();
    await streamCopilotChat(DEFAULT_PAYLOAD, cbs, "tok", controller.signal);

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(cbs.onError).not.toHaveBeenCalled();
  });

  it("does not call onError when fetch throws AbortError (user cancelled)", async () => {
    const abortError = new DOMException("Aborted", "AbortError");
    fetchSpy.mockRejectedValue(abortError);

    // Signal is aborted BEFORE the rejection arrives (simulates mid-flight abort)
    const controller = new AbortController();
    controller.abort();

    const cbs = makeCallbacks();
    await streamCopilotChat(DEFAULT_PAYLOAD, cbs, "tok", controller.signal);

    // onError must NOT be called for intentional cancellations
    expect(cbs.onError).not.toHaveBeenCalled();
  });

  it("passes AbortSignal through to fetch", async () => {
    fetchSpy.mockResolvedValue(
      buildSSEResponse([[{ event: "done", data: { conversation_id: "c6" } }]])
    );
    const controller = new AbortController();

    await streamCopilotChat(DEFAULT_PAYLOAD, makeCallbacks(), "tok", controller.signal);

    const [, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(init.signal).toBe(controller.signal);
  });
});
