/**
 * Tests for useSuggestions hook — real engine version (PR-1 PI-2 S2).
 * TDD: these tests were written RED before the rewrite.
 *
 * [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
 */
import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ── Module mocks ──────────────────────────────────────────────────────

vi.mock("@/lib/config", () => ({
  config: { api: { baseUrl: "http://localhost:8000" } },
}));

const mockGetToken = vi.fn();
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: mockGetToken }),
}));

const mockFetchSuggestions = vi.fn();
vi.mock("../../api/suggestions-api", () => ({
  fetchSuggestions: (...args: unknown[]) => mockFetchSuggestions(...args),
}));

// ── Import after mocks ────────────────────────────────────────────────

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";

import { useCopilotStore } from "../../store/copilot-store";
import { useSuggestions } from "../use-suggestions";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children);
}

describe("useSuggestions (real engine)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCopilotStore.setState({ currentRoute: null, conversationId: null });
    mockGetToken.mockResolvedValue("mock-token");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns chips from API on success", async () => {
    const chips = [
      { id: "1", label: "Crea una oferta", prompt: "Ayúdame", confidence: 0.9, category: "action", source_module: "offer" },
      { id: "2", label: "Revisa escalera", prompt: "Analiza", confidence: 0.8, category: "action", source_module: "offer" },
    ];
    mockFetchSuggestions.mockResolvedValue({ suggestions: chips, breakdown: { offer: 2 }, latency_ms: 10 });

    const { result } = renderHook(() => useSuggestions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.chips).toHaveLength(2);
    expect(result.current.chips[0].id).toBe("1");
    expect(result.current.chips[0].label).toBe("Crea una oferta");
  });

  it("returns empty chips on API failure (graceful — D-10)", async () => {
    mockFetchSuggestions.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useSuggestions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.chips).toHaveLength(0);
    expect(result.current.isLoading).toBe(false);
  });

  it("does not throw without auth token", async () => {
    mockGetToken.mockResolvedValue(null);

    const { result } = renderHook(() => useSuggestions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.chips).toHaveLength(0);
    expect(mockFetchSuggestions).not.toHaveBeenCalled();
  });

  it("re-fetches when currentRoute changes", async () => {
    mockFetchSuggestions.mockResolvedValue({ suggestions: [], breakdown: {}, latency_ms: 0 });

    const { result } = renderHook(() => useSuggestions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    const initialCallCount = mockFetchSuggestions.mock.calls.length;

    act(() => {
      useCopilotStore.setState({ currentRoute: "/offer-studio" });
    });

    await waitFor(() => {
      expect(mockFetchSuggestions.mock.calls.length).toBeGreaterThan(initialCallCount);
    });
  });

  it("re-fetches when conversationId changes", async () => {
    mockFetchSuggestions.mockResolvedValue({ suggestions: [], breakdown: {}, latency_ms: 0 });

    const { result } = renderHook(() => useSuggestions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    const initialCallCount = mockFetchSuggestions.mock.calls.length;

    act(() => {
      useCopilotStore.setState({ conversationId: "conv-abc-123" });
    });

    await waitFor(() => {
      expect(mockFetchSuggestions.mock.calls.length).toBeGreaterThan(initialCallCount);
    });
  });

  it("passes correct body params to fetchSuggestions", async () => {
    useCopilotStore.setState({ currentRoute: "/brand-studio", conversationId: "conv-xyz" });
    mockFetchSuggestions.mockResolvedValue({ suggestions: [], breakdown: {}, latency_ms: 0 });

    renderHook(() => useSuggestions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(mockFetchSuggestions).toHaveBeenCalledWith(
        "mock-token",
        expect.objectContaining({
          current_route: "/brand-studio",
          conversation_id: "conv-xyz",
          recent_message_ids: [],
          incomplete_fields: [],
        }),
      );
    });
  });
});
