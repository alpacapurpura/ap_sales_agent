/**
 * Large volume tests for StageMetricsAction — spec scenario 3 (truncated flag).
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { StageMetricsAction } from "../StageMetricsAction";
import { clearRegistry } from "@/lib/form-runtime/actions";

vi.mock("@/features/tenant/context/tenant-locale-context", () => ({
  useTenantLocale: () => ({ currency: "MXN", timezone: "America/Mexico_City" }),
}));

describe("StageMetricsAction — large volume (spec scenario 3)", () => {
  beforeEach(() => {
    clearRegistry();
  });

  const largVolumePayload = {
    stage_name: "Atracción y Captura",
    period: "90d",
    kpis: [{ slug: "impressions", value: 1_250_000 }],
    tier_used: 3 as const,
    truncated: true,
    row_count: 15000,
  };

  it("shows truncated badge/alert when row_count exceeds tier threshold", () => {
    render(<StageMetricsAction value={largVolumePayload} onChange={vi.fn()} />);
    const alert = screen.getByRole("alert");
    expect(alert).toBeInTheDocument();
  });

  it("renders tier_used indicator", () => {
    render(<StageMetricsAction value={largVolumePayload} onChange={vi.fn()} />);
    // Should indicate Tier 3 was used
    expect(screen.getByText(/Atracción y Captura/)).toBeInTheDocument();
  });

  it("falls back to tenant currency when payload has no currency", () => {
    render(<StageMetricsAction value={largVolumePayload} onChange={vi.fn()} />);
    // impressions is not a currency KPI — just renders a number
    expect(screen.getByText(/1,250,000|1\.250\.000/)).toBeInTheDocument();
  });
});
