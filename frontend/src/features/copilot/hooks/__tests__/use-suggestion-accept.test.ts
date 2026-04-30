/**
 * Tests for useSuggestionAccept hook — fire-and-forget mutation (PR-1 PI-2 S2).
 * TDD: these tests were written RED before implementation.
 *
 * [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
 */
import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ── Module mocks ──────────────────────────────────────────────────────

vi.mock("@/lib/config", () => ({
  config: { api: { baseUrl: "http://localhost:8000" } },
}));

const mockGetToken = vi.fn();
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: mockGetToken }),
}));

const mockAcceptSuggestion = vi.fn();
vi.mock("../../api/suggestions-api", () => ({
  acceptSuggestion: (...args: unknown[]) => mockAcceptSuggestion(...args),
}));

// ── Import after mocks ────────────────────────────────────────────────

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";

import type { Suggestion } from "../../types/suggestions";
import { useSuggestionAccept } from "../use-suggestion-accept";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

const mockChip: Suggestion = {
  id: "uuid-chip-1",
  label: "Crea tu primera oferta",
  prompt: "Ayúdame a crear mi primera oferta",
  confidence: 0.9,
  category: "action",
  source_module: "offer",
};

describe("useSuggestionAccept", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, "warn").mockImplementation(() => {});
    mockGetToken.mockResolvedValue("mock-token");
    mockAcceptSuggestion.mockResolvedValue({ ok: true });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("mutation calls acceptSuggestion API with correct payload", async () => {
    const { result } = renderHook(() => useSuggestionAccept(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        suggestion: mockChip,
        conversationId: "conv-123",
        currentRoute: "/offer-studio",
      });
    });

    await waitFor(() => expect(result.current.isIdle).toBe(false));

    await waitFor(() => {
      expect(mockAcceptSuggestion).toHaveBeenCalledWith(
        "mock-token",
        expect.objectContaining({
          suggestion_id: "uuid-chip-1",
          conversation_id: "conv-123",
          current_route: "/offer-studio",
          category: "action",
          source_module: "offer",
        }),
      );
    });
  });

  it("accepted_at is an ISO 8601 UTC string", async () => {
    const { result } = renderHook(() => useSuggestionAccept(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        suggestion: mockChip,
        conversationId: null,
        currentRoute: null,
      });
    });

    await waitFor(() => {
      const call = mockAcceptSuggestion.mock.calls[0];
      const payload = call?.[1] as { accepted_at: string };
      expect(payload.accepted_at).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
    });
  });

  it("mutation does NOT invalidate suggestions query (D-13)", async () => {
    const queryClient = new QueryClient({
      defaultOptions: { mutations: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const wrapper = ({ children }: { children: React.ReactNode }) =>
      createElement(QueryClientProvider, { client: queryClient }, children);

    const { result } = renderHook(() => useSuggestionAccept(), { wrapper });

    await act(async () => {
      result.current.mutate({
        suggestion: mockChip,
        conversationId: null,
        currentRoute: null,
      });
    });

    await waitFor(() => expect(result.current.isIdle).toBe(false));

    // No query invalidation should have occurred for suggestions
    const suggestionInvalidations = invalidateSpy.mock.calls.filter(
      (call) => JSON.stringify(call[0]).includes("suggestions"),
    );
    expect(suggestionInvalidations).toHaveLength(0);
  });

  it("mutation onError logs warning and does not throw", async () => {
    mockAcceptSuggestion.mockRejectedValue(new Error("Bus failure"));

    const { result } = renderHook(() => useSuggestionAccept(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        suggestion: mockChip,
        conversationId: null,
        currentRoute: null,
      });
    });

    await waitFor(() => {
      expect(console.warn).toHaveBeenCalledWith(
        "[copilot] suggestion accept telemetry failed",
        expect.any(Error),
      );
    });
  });
});
