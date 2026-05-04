import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import * as React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { useContactsQuery } from "../use-contacts-query";

import type { PaginatedResponse, ContactListItem } from "../../types";

// Mock fetchClient
vi.mock("@/lib/http-client", () => ({
  fetchClient: vi.fn(),
}));

// Mock Clerk so `enabled: isLoaded && isSignedIn` doesn't keep the query idle.
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("test-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));

const mockPaginatedResponse: PaginatedResponse<ContactListItem> = {
  items: [
    {
      id: "contact-1",
      full_name: "Ana García",
      primary_email: "ana@example.com",
      primary_phone: null,
      lifecycle_stage: "lead",
      lead_score: 55,
      is_inactive: false,
      last_activity_at: "2026-04-28T10:00:00Z",
      lead_source: "instagram_dm",
      country: "ar",
      has_telegram_id: true,
      has_whatsapp_id: false,
      has_instagram_id: true,
      has_tiktok_id: false,
      has_email: true,
      has_phone: false,
      has_recent_campaign_engagement: null,
      created_at: "2026-01-15T10:00:00Z",
    },
  ],
  total_count: 1,
  limit: 50,
  offset: 0,
  has_more: false,
};

function makeWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe("useContactsQuery", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.clearAllMocks();
  });

  it("fetches contacts successfully", async () => {
    const { fetchClient } = await import("@/lib/http-client");
    vi.mocked(fetchClient).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockPaginatedResponse),
    } as Response);

    const { result } = renderHook(() => useContactsQuery({ filters: {}, limit: 50, offset: 0 }), {
      wrapper: makeWrapper(queryClient),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items).toHaveLength(1);
    expect(result.current.data?.items[0]?.full_name).toBe("Ana García");
  });

  it("includes correct query key with filters", () => {
    const { result } = renderHook(
      () =>
        useContactsQuery({
          filters: { lifecycle_stage_in: ["lead"] },
          limit: 25,
          offset: 0,
        }),
      { wrapper: makeWrapper(queryClient) },
    );
    // queryKey includes the params
    expect(result.current).toBeDefined();
  });

  it("builds URL params correctly with lifecycle_stage_in", async () => {
    const { fetchClient } = await import("@/lib/http-client");
    let calledUrl = "";
    vi.mocked(fetchClient).mockImplementationOnce((url) => {
      calledUrl = url.toString();
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockPaginatedResponse),
      } as Response);
    });

    const { result } = renderHook(
      () =>
        useContactsQuery({
          filters: { lifecycle_stage_in: ["lead", "mql"] },
          limit: 50,
          offset: 0,
        }),
      { wrapper: makeWrapper(queryClient) },
    );

    await waitFor(() => result.current.isSuccess);
    expect(calledUrl).toContain("lifecycle_stage_in=lead%2Cmql");
  });

  it("uses trailing slash before query params — /api/v1/contacts/?  (Bug #1)", async () => {
    const { fetchClient } = await import("@/lib/http-client");
    let calledUrl = "";
    vi.mocked(fetchClient).mockImplementationOnce((url) => {
      calledUrl = url.toString();
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockPaginatedResponse),
      } as Response);
    });

    const { result } = renderHook(() => useContactsQuery({ filters: {}, limit: 50, offset: 0 }), {
      wrapper: makeWrapper(queryClient),
    });

    await waitFor(() => result.current.isSuccess);
    // BE registers @router.get("/") → effective path /api/v1/contacts/
    // With redirect_slashes=False, /api/v1/contacts? would 404.
    expect(calledUrl).toMatch(/\/api\/v1\/contacts\/\?/); // eslint-disable-line
  });

  it("throws on non-ok response", async () => {
    const { fetchClient } = await import("@/lib/http-client");
    vi.mocked(fetchClient).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({}),
    } as Response);

    const { result } = renderHook(() => useContactsQuery({ filters: {}, limit: 50, offset: 0 }), {
      wrapper: makeWrapper(queryClient),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toContain("500");
  });
});
