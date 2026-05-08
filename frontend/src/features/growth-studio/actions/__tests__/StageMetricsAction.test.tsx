/**
 * Tests for StageMetricsAction component.
 * TDD: written RED before component implementation.
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { StageMetricsAction } from "../StageMetricsAction";
import { clearRegistry } from "@/lib/form-runtime/actions";

// Mock useTenantLocale
vi.mock("@/features/tenant/context/tenant-locale-context", () => ({
  useTenantLocale: () => ({ currency: "USD", timezone: "America/Lima" }),
}));

describe("StageMetricsAction", () => {
  beforeEach(() => {
    clearRegistry();
  });

  const basePayload = {
    stage_name: "Ventas",
    period: "30d",
    kpis: [
      { slug: "revenue", value: 5000, currency: "USD" },
      { slug: "conversion_rate", value: 0.12 },
    ],
    tier_used: 1 as const,
    truncated: false,
  };

  it("renders stage name and period", () => {
    render(<StageMetricsAction value={basePayload} onChange={vi.fn()} />);
    expect(screen.getByText("Ventas")).toBeInTheDocument();
    expect(screen.getByText(/30d/)).toBeInTheDocument();
  });

  it("renders KPI slugs", () => {
    render(<StageMetricsAction value={basePayload} onChange={vi.fn()} />);
    expect(screen.getByText(/revenue/)).toBeInTheDocument();
    expect(screen.getByText(/conversion_rate/)).toBeInTheDocument();
  });

  it("renders formatted currency KPI value", () => {
    render(<StageMetricsAction value={basePayload} onChange={vi.fn()} />);
    // Should format 5000 USD
    expect(screen.getByText(/\$5,000/)).toBeInTheDocument();
  });

  it("does NOT render truncated alert when truncated=false", () => {
    render(<StageMetricsAction value={basePayload} onChange={vi.fn()} />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("renders truncated alert with role=alert when truncated=true", () => {
    render(<StageMetricsAction value={{ ...basePayload, truncated: true }} onChange={vi.fn()} />);
    const alert = screen.getByRole("alert");
    expect(alert).toBeInTheDocument();
    // Spanish neutro copy
    expect(alert.textContent).toMatch(/parcial/i);
  });

  it("renders channel breakdown when provided", () => {
    render(
      <StageMetricsAction
        value={{
          ...basePayload,
          channel_breakdown: [{ channel: "meta-ads", value: 3000 }],
        }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText(/meta-ads/)).toBeInTheDocument();
  });

  it("has accessible aria-label on the card", () => {
    render(<StageMetricsAction value={basePayload} onChange={vi.fn()} />);
    expect(screen.getByRole("region")).toHaveAttribute(
      "aria-label",
      expect.stringContaining("Ventas"),
    );
  });
});
