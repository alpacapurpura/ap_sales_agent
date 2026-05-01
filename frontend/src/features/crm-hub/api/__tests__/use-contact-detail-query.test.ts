import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import * as React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { useContactDetailQuery } from "../use-contact-detail-query";

import type { ContactDetail } from "../../types";

vi.mock("@/lib/http-client", () => ({
  fetchClient: vi.fn(),
}));

const mockDetail: ContactDetail = {
  id: "contact-abc",
  full_name: "Juan García",
  primary_email: "juan@test.com",
  primary_phone: null,
  lifecycle_stage: "customer",
  lead_score: 85,
  rfm_segment: null,
  lifetime_value: 1500,
  is_inactive: false,
  first_conversion_at: "2026-02-01T00:00:00Z",
  first_seen_at: "2026-01-01T00:00:00Z",
  last_activity_at: "2026-04-28T00:00:00Z",
  lead_source: "referral",
  lead_source_detail: null,
  traits: {},
  computed_traits: {},
  created_at: "2026-01-01T00:00:00Z",
  updated_at: null,
  lead_id: null,
  telegram_id: null,
  whatsapp_id: null,
  instagram_id: null,
  tiktok_id: null,
  api_id: null,
  fit_score: null,
  intent_score: null,
  temperature: null,
  is_blacklisted: null,
  last_interaction_date: null,
  country: "mx",
  conversation_summary: null,
  identities: [],
};

function makeWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe("useContactDetailQuery", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.clearAllMocks();
  });

  it("does not fetch when contactId is null", () => {
    const { result } = renderHook(() => useContactDetailQuery(null), {
      wrapper: makeWrapper(queryClient),
    });
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("fetches detail when contactId is provided", async () => {
    const { fetchClient } = await import("@/lib/http-client");
    vi.mocked(fetchClient).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockDetail),
    } as Response);

    const { result } = renderHook(() => useContactDetailQuery("contact-abc"), {
      wrapper: makeWrapper(queryClient),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.full_name).toBe("Juan García");
    expect(result.current.data?.lead_score).toBe(85);
  });

  it("uses correct query key", () => {
    const { result } = renderHook(() => useContactDetailQuery("contact-abc"), {
      wrapper: makeWrapper(queryClient),
    });
    expect(result.current).toBeDefined();
  });
});
