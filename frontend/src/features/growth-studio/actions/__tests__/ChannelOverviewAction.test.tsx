/**
 * Tests for ChannelOverviewAction component.
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { ChannelOverviewAction } from "../ChannelOverviewAction";
import { clearRegistry } from "@/lib/form-runtime/actions";

vi.mock("@/features/tenant/context/tenant-locale-context", () => ({
  useTenantLocale: () => ({ currency: "USD", timezone: "America/Lima" }),
}));

describe("ChannelOverviewAction", () => {
  beforeEach(() => {
    clearRegistry();
  });

  const basePayload = {
    channel_name: "Meta Ads",
    period: "30d",
    dashboard_kpis: [
      { slug: "impressions", value: 45000, label: "Impresiones" },
      { slug: "ctr", value: 0.032, label: "CTR" },
      { slug: "spend", value: 1200, currency: "USD", label: "Inversión" },
    ],
    ui_action: "open-channel-dashboard",
  };

  it("renders channel name", () => {
    render(<ChannelOverviewAction value={basePayload} onChange={vi.fn()} />);
    expect(screen.getByText("Meta Ads")).toBeInTheDocument();
  });

  it("renders KPI labels", () => {
    render(<ChannelOverviewAction value={basePayload} onChange={vi.fn()} />);
    expect(screen.getByText(/Impresiones/)).toBeInTheDocument();
    expect(screen.getByText(/CTR/)).toBeInTheDocument();
    expect(screen.getByText(/Inversión/)).toBeInTheDocument();
  });

  it("has accessible region with aria-label", () => {
    render(<ChannelOverviewAction value={basePayload} onChange={vi.fn()} />);
    expect(screen.getByRole("region")).toHaveAttribute(
      "aria-label",
      expect.stringContaining("Meta Ads"),
    );
  });

  it("renders formatted currency KPI", () => {
    render(<ChannelOverviewAction value={basePayload} onChange={vi.fn()} />);
    expect(screen.getByText(/\$1,200/)).toBeInTheDocument();
  });
});
