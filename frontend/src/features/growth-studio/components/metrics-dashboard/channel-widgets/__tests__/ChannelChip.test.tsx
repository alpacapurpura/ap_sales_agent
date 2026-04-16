import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { ChannelChip } from "../ChannelChip";

import type { ChannelMetric } from "@/features/growth-studio/types/metrics";

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock("../../../../lib/channel-icons", () => ({
  getChannelIcon: (_slug: string) => {
    const MockIcon = (props: React.SVGProps<SVGSVGElement>) => (
      <svg data-testid="chip-icon" {...props} />
    );
    MockIcon.displayName = "MockIcon";
    return MockIcon;
  },
  getChannelColor: (_slug: string) => "#4285F4",
}));

// Mock Tooltip to render content inline for testing
vi.mock("@/components/ui/tooltip", () => {
  const TooltipTrigger = React.forwardRef(
    (
      { children, ...props }: React.PropsWithChildren<{ asChild?: boolean }>,
      _ref: React.Ref<HTMLElement>,
    ) => React.createElement("span", { "data-testid": "tooltip-trigger", ...props }, children),
  );
  TooltipTrigger.displayName = "TooltipTrigger";
  return {
    TooltipProvider: ({ children }: { children: React.ReactNode }) =>
      React.createElement(React.Fragment, null, children),
    Tooltip: ({ children }: { children: React.ReactNode }) =>
      React.createElement(React.Fragment, null, children),
    TooltipTrigger,
    TooltipContent: ({ children }: { children: React.ReactNode }) =>
      React.createElement("span", { "data-testid": "tooltip-content" }, children),
  };
});

// ── Test data ────────────────────────────────────────────────────────────────

const disconnectedChannel: ChannelMetric = {
  slug: "tiktok-organic",
  name: "TikTok Organic",
  channelType: "organic_social",
  metrics: [],
  sourceLabel: "TikTok",
  connected: false,
  providerName: "tiktok",
};

const noDataChannel: ChannelMetric = {
  slug: "ga4-search",
  name: "Google Analytics",
  channelType: "ga4_search",
  metrics: [],
  sourceLabel: "GA4",
  connected: true,
  providerName: "google_analytics",
};

// ── Tests ────────────────────────────────────────────────────────────────────

describe("ChannelChip", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("variant: disconnected", () => {
    it("renders channel name", () => {
      render(<ChannelChip channel={disconnectedChannel} variant="disconnected" />);
      expect(screen.getByText("TikTok Organic")).toBeInTheDocument();
    });

    it("renders channel icon", () => {
      render(<ChannelChip channel={disconnectedChannel} variant="disconnected" />);
      expect(screen.getByTestId("chip-icon")).toBeInTheDocument();
    });

    it("shows disconnected tooltip text", () => {
      render(<ChannelChip channel={disconnectedChannel} variant="disconnected" />);
      expect(screen.getByText("Desconectado, haga clic para conectar")).toBeInTheDocument();
    });

    it("has aria-label for accessibility", () => {
      render(<ChannelChip channel={disconnectedChannel} variant="disconnected" />);
      expect(
        screen.getByRole("button", { name: /TikTok Organic.*desconectado/i }),
      ).toBeInTheDocument();
    });

    it("calls onDisconnectedClick when clicked", async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(
        <ChannelChip
          channel={disconnectedChannel}
          variant="disconnected"
          onDisconnectedClick={handleClick}
        />,
      );

      await user.click(screen.getByRole("button"));
      expect(handleClick).toHaveBeenCalledWith(disconnectedChannel);
    });

    it("applies gray/muted styling", () => {
      render(<ChannelChip channel={disconnectedChannel} variant="disconnected" />);
      const button = screen.getByRole("button");
      expect(button.className).toMatch(/opacity/);
    });
  });

  describe("variant: no-data", () => {
    it("renders channel name", () => {
      render(<ChannelChip channel={noDataChannel} variant="no-data" />);
      expect(screen.getByText("Google Analytics")).toBeInTheDocument();
    });

    it("renders channel icon", () => {
      render(<ChannelChip channel={noDataChannel} variant="no-data" />);
      expect(screen.getByTestId("chip-icon")).toBeInTheDocument();
    });

    it("renders alert icon", () => {
      render(<ChannelChip channel={noDataChannel} variant="no-data" />);
      expect(screen.getByTestId("alert-icon")).toBeInTheDocument();
    });

    it("shows no-data tooltip text", () => {
      render(<ChannelChip channel={noDataChannel} variant="no-data" />);
      expect(
        screen.getByText("Conectado pero sin datos, ¡revisemos cómo podemos usarlo!"),
      ).toBeInTheDocument();
    });

    it("has aria-label for accessibility", () => {
      render(<ChannelChip channel={noDataChannel} variant="no-data" />);
      expect(
        screen.getByRole("button", { name: /Google Analytics.*sin datos/i }),
      ).toBeInTheDocument();
    });

    it("calls onNoDataClick when clicked", async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(<ChannelChip channel={noDataChannel} variant="no-data" onNoDataClick={handleClick} />);

      await user.click(screen.getByRole("button"));
      expect(handleClick).toHaveBeenCalledWith(noDataChannel);
    });

    it("applies amber/warning styling", () => {
      render(<ChannelChip channel={noDataChannel} variant="no-data" />);
      const button = screen.getByRole("button");
      expect(button.className).toMatch(/amber/);
    });
  });
});
