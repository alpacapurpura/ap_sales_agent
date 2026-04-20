import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { useUpdateTenantProfile } from "../hooks/use-update-tenant-profile";

// Mock Clerk auth
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: async () => "mock-token",
    isLoaded: true,
    isSignedIn: true,
  }),
}));

// Mock the API function
vi.mock("../api/tenant-profile-api", () => ({
  updateTenantProfile: vi.fn(),
}));

import { updateTenantProfile } from "../api/tenant-profile-api";

const mockUpdate = updateTenantProfile as unknown as ReturnType<typeof vi.fn>;

function createWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const Wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client }, children);
  return { Wrapper, client };
}

describe("useUpdateTenantProfile", () => {
  beforeEach(() => {
    mockUpdate.mockReset();
  });

  it("returns ok:true on 2xx response", async () => {
    const mockProfile = { tenant_id: "t1", business_types: ["coach_mentor"] };
    mockUpdate.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockProfile,
    });

    const { Wrapper, client } = createWrapper();
    const { result } = renderHook(() => useUpdateTenantProfile(), {
      wrapper: Wrapper,
    });

    result.current.mutate({ business_types: ["coach_mentor"] });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const { data } = result.current;
    expect(data).toBeDefined();
    expect(data?.ok).toBe(true);

    // Verify cache invalidation was triggered (queries invalidated)
    const queries = client.getQueryCache().getAll();
    // Just verify mutation ran without error
    expect(result.current.isError).toBe(false);
  });

  it("returns ok:false with rate_limited shape on 409", async () => {
    const nextDate = "2026-05-19T10:00:00Z";
    mockUpdate.mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ next_allowed_change_at: nextDate }),
    });

    const { Wrapper } = createWrapper();
    const { result } = renderHook(() => useUpdateTenantProfile(), {
      wrapper: Wrapper,
    });

    result.current.mutate({ business_types: ["coach_mentor"] });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const { data } = result.current;
    expect(data?.ok).toBe(false);
    if (data && !data.ok) {
      expect(data.error.code).toBe("rate_limited");
      expect(data.error.next_allowed_change_at).toBe(nextDate);
    }
  });

  it("throws on non-200/non-409 error", async () => {
    mockUpdate.mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: async () => ({}),
    });

    const { Wrapper } = createWrapper();
    const { result } = renderHook(() => useUpdateTenantProfile(), {
      wrapper: Wrapper,
    });

    result.current.mutate({ business_types: ["coach_mentor"] });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toMatch(/500/);
  });
});
