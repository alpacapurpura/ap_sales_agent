import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import * as React from "react";
import { describe, expect, it, vi } from "vitest";

import { CampaignDetailClient } from "../components/CampaignDetailClient";

import type { CampaignResponse, CampaignStatsResponse } from "../types";

const mockCampaign: CampaignResponse = {
  id: "camp-1",
  tenant_id: "tenant-abc",
  name: "Campaña Test Telegram",
  description: "Descripción de prueba",
  campaign_type: "AGENT_CONVERSATION",
  status: "DRAFT",
  segment_id: "seg-123",
  channel_priority: ["telegram"],
  offer_id: null,
  brand_summary_id: null,
  config: {},
  created_at: "2026-04-30T10:00:00Z",
  updated_at: null,
  scheduled_for: null,
  launched_at: null,
};

const mockStats: CampaignStatsResponse = {
  campaign_id: "camp-1",
  total_tasks: 50,
  sent_count: 30,
  responded_count: 10,
  converted_count: 3,
  response_rate: 0.33,
  conversion_rate: 0.1,
  currency: null,
};

vi.mock("../api/use-campaign-detail-query", () => ({
  useCampaignDetailQuery: (_id: string) => ({
    data: mockCampaign,
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
}));

vi.mock("../api/use-campaign-stats-query", () => ({
  useCampaignStatsQuery: (_id: string) => ({
    data: mockStats,
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
}));

vi.mock("@/lib/http-client", () => ({
  fetchClient: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe("CampaignDetailClient", () => {
  it("renders campaign name", () => {
    render(<CampaignDetailClient campaignId="camp-1" />, { wrapper: createWrapper() });
    expect(screen.getByText("Campaña Test Telegram")).toBeInTheDocument();
  });

  it("renders status badge as Borrador for DRAFT", () => {
    render(<CampaignDetailClient campaignId="camp-1" />, { wrapper: createWrapper() });
    expect(screen.getByText("Borrador")).toBeInTheDocument();
  });

  it("renders Lanzar button for DRAFT status", () => {
    render(<CampaignDetailClient campaignId="camp-1" />, { wrapper: createWrapper() });
    expect(screen.getByRole("button", { name: /lanzar campaña/i })).toBeInTheDocument();
  });

  it("renders stats from stats query", () => {
    render(<CampaignDetailClient campaignId="camp-1" />, { wrapper: createWrapper() });
    expect(screen.getByText("50")).toBeInTheDocument(); // total_tasks
    expect(screen.getByText("30")).toBeInTheDocument(); // sent_count
  });
});
