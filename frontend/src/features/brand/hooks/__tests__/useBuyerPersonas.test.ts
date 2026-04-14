import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock Clerk
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("test-token"),
  }),
}));

// Mock the API module
const mockList = vi.fn();
vi.mock("@/lib/api/buyer-persona", () => ({
  buyerPersonaApi: {
    list: (...args: unknown[]) => mockList(...args),
  },
}));

import { useBuyerPersonas } from "../useBuyerPersonas";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe("useBuyerPersonas", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches buyer personas and returns data", async () => {
    const personas = [
      { id: "1", name: "Mamá Rural", completeness_score: 45 },
      { id: "2", name: "Joven Pro", completeness_score: 80 },
    ];
    mockList.mockResolvedValue(personas);

    const { result } = renderHook(() => useBuyerPersonas(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.personas).toHaveLength(2);
    expect(result.current.personas[0].name).toBe("Mamá Rural");
    expect(mockList).toHaveBeenCalledWith("test-token");
  });

  it("returns empty array when API returns empty", async () => {
    mockList.mockResolvedValue([]);

    const { result } = renderHook(() => useBuyerPersonas(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.personas).toHaveLength(0);
  });

  it("handles fetch error gracefully", async () => {
    mockList.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useBuyerPersonas(), {
      wrapper: createWrapper(),
    });

    // When an error occurs, personas falls back to [] regardless of loading state
    await waitFor(() => expect(result.current.error).toBeTruthy(), { timeout: 5000 });
    expect(result.current.personas).toHaveLength(0);
  });
});
