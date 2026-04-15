/**
 * Regression tests for useCopilotChat race condition.
 *
 * Audit item R2: if the user sends a second message before the first
 * response finishes streaming, the first stream's callbacks must NOT
 * write to the second assistant-message placeholder.
 */
import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { useCopilotChat } from "@/features/copilot/hooks/useCopilotChat";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";

// ── Mocks ─────────────────────────────────────────────────────────────────────

// Clerk: always return a valid token
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("tok-test") }),
}));

type StreamCallbacks = Record<string, (...args: unknown[]) => void>;

// Store callbacks per stream invocation so tests can simulate stale events
const allStreamCallbacks: StreamCallbacks[] = [];
let streamCallCount = 0;
const resolveStreams: (() => void)[] = [];

vi.mock("@/features/copilot/api/copilot-api", () => ({
  streamCopilotChat: vi.fn((_payload, callbacks, _token, _signal) => {
    const idx = streamCallCount;
    streamCallCount++;
    allStreamCallbacks[idx] = callbacks as StreamCallbacks;
    return new Promise<void>((resolve) => {
      resolveStreams[idx] = resolve;
    });
  }),
  reportCopilotEvent: vi.fn(),
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

function resetStore() {
  useCopilotStore.setState({
    sidebarState: "collapsed",
    conversationId: null,
    messages: [],
    status: "idle",
    currentRoute: null,
    pendingUIActions: [],
    activeProcedure: null,
    selectedFields: [],
    focusEntity: null,
    focusSnapshot: null,
    interviewSessionId: null,
    interviewProgress: null,
    previewData: null,
  });
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("useCopilotChat — single-flight guarantee", () => {
  beforeEach(() => {
    resetStore();
    allStreamCallbacks.length = 0;
    resolveStreams.length = 0;
    streamCallCount = 0;
    vi.spyOn(window, "dispatchEvent").mockImplementation(() => true);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    // Cleanup: resolve any pending streams
    resolveStreams.forEach((r) => r?.());
  });

  it("second sendMessage aborts first request before adding new messages", async () => {
    const { result } = renderHook(() => useCopilotChat());

    // Send message 1 — stream 0 starts
    await act(async () => {
      void result.current.sendMessage("Hola");
    });

    expect(streamCallCount).toBe(1);
    const messages1 = useCopilotStore.getState().messages;
    // user + assistant placeholder
    expect(messages1).toHaveLength(2);
    const assistantId1 = messages1[1].id;

    // Simulate partial chunk arriving for stream 0 (msg1)
    act(() => {
      allStreamCallbacks[0].onTextChunk?.("chunk-from-msg1");
    });
    expect(useCopilotStore.getState().messages[1].content).toBe("chunk-from-msg1");

    // Send message 2 BEFORE msg1 finishes — this is the race condition
    await act(async () => {
      void result.current.sendMessage("Segunda pregunta");
    });

    expect(streamCallCount).toBe(2);
    const messages2 = useCopilotStore.getState().messages;
    // Store should now have 4 messages: user1, assistant1, user2, assistant2
    expect(messages2).toHaveLength(4);
    const assistantId2 = messages2[3].id;

    // Sanity: the two assistant placeholders are different messages
    expect(assistantId1).not.toBe(assistantId2);

    // Now fire a STALE chunk using stream 0's callbacks (the aborted stream)
    // It must NOT write to assistant2 (which is now "last assistant")
    const contentBefore = useCopilotStore.getState().messages[3].content;
    act(() => {
      allStreamCallbacks[0].onTextChunk?.("STALE-chunk");
    });

    // assistant2 content must not have changed
    const contentAfter = useCopilotStore.getState().messages[3].content;
    expect(contentAfter).toBe(contentBefore);

    // assistant1 content stays at the partial chunk it received before abort
    expect(useCopilotStore.getState().messages[1].content).toBe("chunk-from-msg1");
    // Total message count is still 4
    expect(useCopilotStore.getState().messages).toHaveLength(4);
  });

  it("stopStreaming aborts in-flight request and sets status to idle", async () => {
    const { result } = renderHook(() => useCopilotChat());

    await act(async () => {
      void result.current.sendMessage("Pregunta larga");
    });

    expect(useCopilotStore.getState().status).toBe("thinking");

    act(() => {
      result.current.stopStreaming();
    });

    expect(useCopilotStore.getState().status).toBe("idle");
  });

  it("does not add duplicate messages when second send is called immediately", async () => {
    const { result } = renderHook(() => useCopilotChat());

    // Both sends happen synchronously (before awaiting)
    await act(async () => {
      void result.current.sendMessage("Mensaje A");
      await Promise.resolve(); // yield to event loop once
      void result.current.sendMessage("Mensaje B");
    });

    const { messages } = useCopilotStore.getState();
    // Should have exactly 4 messages: userA, assistantA, userB, assistantB
    const userMessages = messages.filter((m) => m.role === "user");
    const assistantMessages = messages.filter((m) => m.role === "assistant");
    expect(userMessages).toHaveLength(2);
    expect(assistantMessages).toHaveLength(2);
  });
});
