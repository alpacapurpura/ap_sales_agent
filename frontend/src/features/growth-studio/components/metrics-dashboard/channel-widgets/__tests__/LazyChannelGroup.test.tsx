import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// ── Mocks ──────────────────────────────────────────────────────────────────────

let mockIsVisible = false;
vi.mock("../../../../hooks/use-intersection-observer", () => ({
  useIntersectionObserver: () => ({
    ref: vi.fn(),
    isVisible: mockIsVisible,
  }),
}));

const mockGroupDetailData = {
  channels: [
    {
      slug: "meta-ads",
      name: "Meta Ads",
      channelType: "paid",
      metrics: [
        { name: "spend", value: 1500, unit: "currency" },
        { name: "impressions", value: 50000 },
        { name: "clicks", value: 2000 },
      ],
      sourceLabel: "Meta",
      connected: true,
    },
  ],
  totals: { spend: 1500, impressions: 50000, clicks: 2000 },
};

let mockGroupDetailReturn = {
  data: undefined as typeof mockGroupDetailData | undefined,
  isLoading: false,
};
vi.mock("../../../../hooks/use-group-detail", () => ({
  useGroupDetail: () => mockGroupDetailReturn,
}));

// Mock ChannelRow to avoid Shadcn UI dependencies
vi.mock("../ChannelRow", () => ({
  ChannelRow: ({ channel }: { channel: { name: string; slug: string } }) =>
    React.createElement("div", { "data-testid": `channel-row-${channel.slug}` }, channel.name),
}));

// Mock ChannelChip
vi.mock("../ChannelChip", () => ({
  ChannelChip: ({
    channel,
    variant,
  }: {
    channel: { name: string; slug: string };
    variant: string;
  }) =>
    React.createElement(
      "div",
      {
        "data-testid": `channel-chip-${channel.slug}`,
        "data-variant": variant,
      },
      channel.name,
    ),
}));

// Mock Accordion components
vi.mock("@/components/ui/accordion", () => ({
  Accordion: ({ children }: { children: React.ReactNode }) =>
    React.createElement("div", null, children),
  AccordionItem: ({ children }: { children: React.ReactNode }) =>
    React.createElement("div", null, children),
  AccordionTrigger: ({ children }: { children: React.ReactNode }) =>
    React.createElement("div", null, children),
  AccordionContent: ({ children }: { children: React.ReactNode }) =>
    React.createElement("div", null, children),
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { LazyChannelGroup } from "../LazyChannelGroup";

import type { ChannelOverview } from "../../../../types/metrics";

// ── Test data ──────────────────────────────────────────────────────────────────

const connectedWithData: ChannelOverview = {
  slug: "meta-ads",
  name: "Meta Ads",
  channelType: "paid",
  groupKey: "paid",
  connected: true,
  headlineKpi: { name: "spend", value: 1500, unit: "currency" },
  stale: false,
};

const disconnectedChannel: ChannelOverview = {
  slug: "tiktok-organic",
  name: "TikTok Organic",
  channelType: "organic_social",
  groupKey: "paid",
  connected: false,
  headlineKpi: null,
  stale: false,
};

const connectedNoData: ChannelOverview = {
  slug: "ga4-search",
  name: "Google Analytics",
  channelType: "ga4_search",
  groupKey: "paid",
  connected: true,
  headlineKpi: null,
  stale: false,
};

const proximamenteChannel: ChannelOverview = {
  slug: "checkout-lp",
  name: "Checkout Landing",
  channelType: "checkout",
  groupKey: "paid",
  connected: true,
  headlineKpi: { name: "views", value: 100, unit: "count" },
  stale: false,
};

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("LazyChannelGroup", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIsVisible = false;
    mockGroupDetailReturn = { data: undefined, isLoading: false };
  });

  it("renders overview channels when group not in viewport", () => {
    mockIsVisible = false;

    render(
      <LazyChannelGroup
        stage="attraction"
        groupKey="paid"
        title="Paid"
        overviewChannels={[connectedWithData]}
      />,
    );

    expect(screen.getByText("Meta Ads")).toBeDefined();
  });

  it("renders enriched channels when group detail loads", () => {
    mockIsVisible = true;
    mockGroupDetailReturn = { data: mockGroupDetailData, isLoading: false };

    render(
      <LazyChannelGroup
        stage="attraction"
        groupKey="paid"
        title="Paid"
        overviewChannels={[connectedWithData]}
      />,
    );

    expect(screen.getByText("Meta Ads")).toBeDefined();
  });

  it("shows skeleton state when loading group detail", () => {
    mockIsVisible = true;
    mockGroupDetailReturn = { data: undefined, isLoading: true };

    render(
      <LazyChannelGroup
        stage="attraction"
        groupKey="paid"
        title="Paid"
        overviewChannels={[connectedWithData]}
      />,
    );

    expect(screen.getByText("Meta Ads")).toBeDefined();
  });

  // ── New chip tests ──────────────────────────────────────────────────────────

  it("renders disconnected channels as chips, not rows", () => {
    render(
      <LazyChannelGroup
        stage="attraction"
        groupKey="paid"
        title="Paid"
        overviewChannels={[connectedWithData, disconnectedChannel]}
      />,
    );

    // Active channel renders as a row
    expect(screen.getByTestId("channel-row-meta-ads")).toBeInTheDocument();
    // Disconnected channel renders as a chip
    expect(screen.getByTestId("channel-chip-tiktok-organic")).toBeInTheDocument();
    // Disconnected channel does NOT render as a row
    expect(screen.queryByTestId("channel-row-tiktok-organic")).not.toBeInTheDocument();
  });

  it("renders connected-no-data channels as chips", () => {
    render(
      <LazyChannelGroup
        stage="attraction"
        groupKey="paid"
        title="Paid"
        overviewChannels={[connectedWithData, connectedNoData]}
      />,
    );

    expect(screen.getByTestId("channel-row-meta-ads")).toBeInTheDocument();
    expect(screen.getByTestId("channel-chip-ga4-search")).toBeInTheDocument();
    expect(screen.queryByTestId("channel-row-ga4-search")).not.toBeInTheDocument();
  });

  it("applies correct variant to disconnected chips", () => {
    render(
      <LazyChannelGroup
        stage="attraction"
        groupKey="paid"
        title="Paid"
        overviewChannels={[disconnectedChannel]}
      />,
    );

    const chip = screen.getByTestId("channel-chip-tiktok-organic");
    expect(chip.getAttribute("data-variant")).toBe("disconnected");
  });

  it("applies correct variant to no-data chips", () => {
    render(
      <LazyChannelGroup
        stage="attraction"
        groupKey="paid"
        title="Paid"
        overviewChannels={[connectedNoData]}
      />,
    );

    const chip = screen.getByTestId("channel-chip-ga4-search");
    expect(chip.getAttribute("data-variant")).toBe("no-data");
  });

  it('renders "Próximamente" channels as rows (not chips)', () => {
    render(
      <LazyChannelGroup
        stage="attraction"
        groupKey="paid"
        title="Paid"
        overviewChannels={[proximamenteChannel]}
      />,
    );

    expect(screen.getByTestId("channel-row-checkout-lp")).toBeInTheDocument();
    expect(screen.queryByTestId("channel-chip-checkout-lp")).not.toBeInTheDocument();
  });

  it("does not render chips section when all channels are active", () => {
    const { container } = render(
      <LazyChannelGroup
        stage="attraction"
        groupKey="paid"
        title="Paid"
        overviewChannels={[connectedWithData]}
      />,
    );

    expect(container.querySelector('[data-testid^="channel-chip-"]')).toBeNull();
  });

  it("returns null when there are no channels at all", () => {
    const { container } = render(
      <LazyChannelGroup stage="attraction" groupKey="paid" title="Paid" overviewChannels={[]} />,
    );

    expect(container.firstChild).toBeNull();
  });
});
