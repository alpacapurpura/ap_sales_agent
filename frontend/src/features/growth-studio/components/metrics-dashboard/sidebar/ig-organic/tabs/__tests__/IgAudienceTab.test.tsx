/**
 * Tests for IgAudienceTab — the "Audiencia" tab of the Instagram Organic
 * dashboard. Verifies that the diverging bar chart joins the three follow
 * metrics by date, renders lost values as negative (so the chart reads
 * "above zero = gained, below zero = lost"), and summarizes period totals.
 */
import { render, screen } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ChannelDashboardData } from "../../../../../../types/metrics";

// ---------------------------------------------------------------------------
// Mocks — render recharts + ChartContainer as inspectable stubs
// ---------------------------------------------------------------------------

// Capture what data the BarChart receives so we can assert on the join logic.
const capturedChartData: unknown[][] = [];

vi.mock("recharts", () => {
  const Passthrough = ({ children }: { children?: React.ReactNode }) => <div>{children}</div>;
  return {
    ResponsiveContainer: Passthrough,
    BarChart: ({ children, data }: { children?: React.ReactNode; data?: unknown[] }) => {
      if (data) capturedChartData.push(data);
      return (
        <div
          data-testid="bar-chart"
          data-points={data?.length ?? 0}
          data-payload={JSON.stringify(data ?? [])}
        >
          {children}
        </div>
      );
    },
    Bar: ({ dataKey, stackId }: { dataKey?: string; stackId?: string }) => (
      <div data-testid="bar" data-key={dataKey} data-stack={stackId} />
    ),
    CartesianGrid: () => <div data-testid="grid" />,
    XAxis: () => <div data-testid="x-axis" />,
    YAxis: () => <div data-testid="y-axis" />,
    Tooltip: () => <div data-testid="rechart-tooltip" />,
    Legend: () => <div data-testid="legend" />,
  };
});

vi.mock("@/components/ui/chart", () => ({
  ChartContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="chart-container">{children}</div>
  ),
}));

// ChartSection / ChartInfoTooltip are pure layout — stub them out so we can
// focus assertions on the data join.
vi.mock("../../../shared/ChartSection", () => ({
  ChartSection: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("../../ChartInfoTooltip", () => ({
  ChartInfoTooltip: ({ title }: { title: string }) => <h3>{title}</h3>,
}));

// Import the component AFTER mocks
import { IgAudienceTab } from "../IgAudienceTab";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeDashboardData(timeSeries: ChannelDashboardData["timeSeries"]): ChannelDashboardData {
  return {
    channelSlug: "ig-organic",
    channelName: "Instagram Orgánico",
    industryCategory: "general",
    period: "30d",
    kpis: [],
    timeSeries,
    funnel: { steps: [] },
    frequencyAlert: null,
  };
}

beforeEach(() => {
  capturedChartData.length = 0;
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("IgAudienceTab", () => {
  it("renders a loader while loading", () => {
    const { container } = render(<IgAudienceTab data={undefined} isLoading={true} />);
    expect(container.querySelector(".animate-spin")).not.toBeNull();
  });

  it("renders an empty state when data is missing", () => {
    render(<IgAudienceTab data={undefined} isLoading={false} />);
    expect(screen.getByText(/No hay datos disponibles/i)).toBeInTheDocument();
  });

  it("joins gained + lost series by date and renders lost as negative", () => {
    const data = makeDashboardData([
      {
        metricName: "ig_follows_gained",
        displayName: "Seguidores Ganados",
        unit: "count",
        dataPoints: [
          { date: "2026-04-01", value: 10 },
          { date: "2026-04-02", value: 15 },
          { date: "2026-04-03", value: 5 },
        ],
      },
      {
        metricName: "ig_follows_lost",
        displayName: "Seguidores Perdidos",
        unit: "count",
        dataPoints: [
          { date: "2026-04-01", value: 2 },
          { date: "2026-04-02", value: 8 },
          { date: "2026-04-03", value: 1 },
        ],
      },
    ]);

    render(<IgAudienceTab data={data} isLoading={false} />);

    expect(capturedChartData.length).toBe(1);
    const rendered = capturedChartData[0] as {
      date: string;
      gained: number;
      lost: number;
      net: number;
    }[];

    // 3 days, sorted ascending by MM-DD
    expect(rendered).toHaveLength(3);
    expect(rendered[0]).toMatchObject({ date: "04-01", gained: 10, lost: -2, net: 8 });
    expect(rendered[1]).toMatchObject({ date: "04-02", gained: 15, lost: -8, net: 7 });
    expect(rendered[2]).toMatchObject({ date: "04-03", gained: 5, lost: -1, net: 4 });
  });

  it("renders period totals summary with signed net", () => {
    const data = makeDashboardData([
      {
        metricName: "ig_follows_gained",
        displayName: "Seguidores Ganados",
        unit: "count",
        dataPoints: [
          { date: "2026-04-01", value: 100 },
          { date: "2026-04-02", value: 50 },
        ],
      },
      {
        metricName: "ig_follows_lost",
        displayName: "Seguidores Perdidos",
        unit: "count",
        dataPoints: [
          { date: "2026-04-01", value: 20 },
          { date: "2026-04-02", value: 10 },
        ],
      },
    ]);

    render(<IgAudienceTab data={data} isLoading={false} />);

    // Total gained = 150, lost = 30, net = +120
    expect(screen.getByText(/\+150 ganados/i)).toBeInTheDocument();
    expect(screen.getByText(/−30 perdidos/i)).toBeInTheDocument();
    expect(screen.getByText(/\+120/)).toBeInTheDocument();
  });

  it("handles dates present in only one series (missing in the other)", () => {
    // lost has an extra date not in gained → should still render, with gained=0
    const data = makeDashboardData([
      {
        metricName: "ig_follows_gained",
        displayName: "Seguidores Ganados",
        unit: "count",
        dataPoints: [{ date: "2026-04-01", value: 10 }],
      },
      {
        metricName: "ig_follows_lost",
        displayName: "Seguidores Perdidos",
        unit: "count",
        dataPoints: [
          { date: "2026-04-01", value: 2 },
          { date: "2026-04-02", value: 5 },
        ],
      },
    ]);

    render(<IgAudienceTab data={data} isLoading={false} />);

    const rendered = capturedChartData[0] as {
      date: string;
      gained: number;
      lost: number;
      net: number;
    }[];
    expect(rendered).toHaveLength(2);
    // 2026-04-01: gained=10, lost=-2, net=8
    // 2026-04-02: gained=0 (missing), lost=-5, net=-5
    const apr1 = rendered.find((p) => p.date === "04-01")!;
    const apr2 = rendered.find((p) => p.date === "04-02")!;
    expect(apr1).toMatchObject({ gained: 10, lost: -2, net: 8 });
    expect(apr2).toMatchObject({ gained: 0, lost: -5, net: -5 });
  });

  it("renders a negative-signed net total when losses outweigh gains", () => {
    const data = makeDashboardData([
      {
        metricName: "ig_follows_gained",
        displayName: "Seguidores Ganados",
        unit: "count",
        dataPoints: [{ date: "2026-04-01", value: 5 }],
      },
      {
        metricName: "ig_follows_lost",
        displayName: "Seguidores Perdidos",
        unit: "count",
        dataPoints: [{ date: "2026-04-01", value: 12 }],
      },
    ]);

    render(<IgAudienceTab data={data} isLoading={false} />);

    // Net = -7, should render with "-" (no "+" prefix)
    // and "−12 perdidos"
    expect(screen.getByText(/−12 perdidos/i)).toBeInTheDocument();
    expect(screen.getByText(/-7/)).toBeInTheDocument();
  });

  it("hides the chart section when there is no follow data at all", () => {
    const data = makeDashboardData([]);
    render(<IgAudienceTab data={data} isLoading={false} />);
    // The chart is not rendered
    expect(screen.queryByTestId("bar-chart")).toBeNull();
    // But the demografia section is still present
    expect(screen.getByText(/Datos demográficos disponibles próximamente/i)).toBeInTheDocument();
  });

  it("renders two stacked bars with the correct data keys", () => {
    const data = makeDashboardData([
      {
        metricName: "ig_follows_gained",
        displayName: "Seguidores Ganados",
        unit: "count",
        dataPoints: [{ date: "2026-04-01", value: 10 }],
      },
      {
        metricName: "ig_follows_lost",
        displayName: "Seguidores Perdidos",
        unit: "count",
        dataPoints: [{ date: "2026-04-01", value: 3 }],
      },
    ]);

    render(<IgAudienceTab data={data} isLoading={false} />);
    const bars = screen.getAllByTestId("bar");
    expect(bars).toHaveLength(2);
    const keys = bars.map((b) => b.getAttribute("data-key")).sort();
    expect(keys).toEqual(["gained", "lost"]);
    // Both bars should share the same stackId so they diverge across the zero axis
    const stacks = bars.map((b) => b.getAttribute("data-stack"));
    expect(stacks[0]).toBe(stacks[1]);
  });
});
