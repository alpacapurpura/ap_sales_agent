import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it, vi } from "vitest";

import type { MetricKpiData, MetricTimeSeries } from "../../../../../types/metrics";

// Mock useMetricCatalog (used by MetricInfoCard)
vi.mock("../../../../../hooks/useMetricCatalog", () => ({
  useMetricCatalog: () => ({
    getTooltipData: () => null,
  }),
}));

// Mock recharts — spread the real module so chart.tsx re-exports still work,
// but replace heavy SVG components with lightweight stubs.
vi.mock("recharts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("recharts")>();
  return {
    ...actual,
    Area: () => null,
    AreaChart: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="area-chart">{children}</div>
    ),
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  };
});

import { HeroKpiGrid } from "../HeroKpiGrid";

// ---------------------------------------------------------------------------
// Test data
// ---------------------------------------------------------------------------

const BASE_KPI = {
  previousValue: 100,
  deltaPct: 10.0,
  deltaAbsolute: 10,
  higherIsBetter: true,
  benchmark: null,
} satisfies Partial<MetricKpiData>;

const KPIS: MetricKpiData[] = [
  {
    ...BASE_KPI,
    metricName: "metric_a",
    displayName: "Metric A",
    currentValue: 2450,
    unit: "count",
  },
  {
    ...BASE_KPI,
    metricName: "metric_b",
    displayName: "Metric B",
    currentValue: 485000,
    unit: "count",
  },
  {
    ...BASE_KPI,
    metricName: "metric_c",
    displayName: "Metric C",
    currentValue: 127,
    unit: "count",
  },
  {
    ...BASE_KPI,
    metricName: "metric_d",
    displayName: "Metric D",
    currentValue: 0.51,
    unit: "percentage",
  },
];

const HERO_METRICS = ["metric_a", "metric_b", "metric_c", "metric_d"] as const;

const EMPTY_TIME_SERIES: MetricTimeSeries[] = [];

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("HeroKpiGrid", () => {
  it("renders all hero KPI cards matching the heroMetrics list", () => {
    render(
      <HeroKpiGrid
        kpis={KPIS}
        timeSeries={EMPTY_TIME_SERIES}
        heroMetrics={HERO_METRICS}
        gradientPrefix="test"
      />,
    );
    expect(screen.getByText("Metric A")).toBeInTheDocument();
    expect(screen.getByText("Metric B")).toBeInTheDocument();
    expect(screen.getByText("Metric C")).toBeInTheDocument();
    expect(screen.getByText("Metric D")).toBeInTheDocument();
  });

  it("formats count values using formatMetricValue (k/M abbreviations)", () => {
    render(
      <HeroKpiGrid
        kpis={KPIS}
        timeSeries={EMPTY_TIME_SERIES}
        heroMetrics={HERO_METRICS}
        gradientPrefix="test"
      />,
    );
    // 2450 -> "2.5k", 485000 -> "485k", 127 -> "127"
    expect(screen.getByText("2.5k")).toBeInTheDocument();
    expect(screen.getByText("485k")).toBeInTheDocument();
    expect(screen.getByText("127")).toBeInTheDocument();
  });

  it("formats percentage values with default 2 decimals", () => {
    render(
      <HeroKpiGrid
        kpis={KPIS}
        timeSeries={EMPTY_TIME_SERIES}
        heroMetrics={HERO_METRICS}
        gradientPrefix="test"
      />,
    );
    expect(screen.getByText("0.51%")).toBeInTheDocument();
  });

  it("respects formatOptions.percentDecimals override", () => {
    render(
      <HeroKpiGrid
        kpis={KPIS}
        timeSeries={EMPTY_TIME_SERIES}
        heroMetrics={HERO_METRICS}
        gradientPrefix="test"
        formatOptions={{ percentDecimals: 1 }}
      />,
    );
    // 0.51 with 1 decimal -> "0.5%"
    expect(screen.getByText("0.5%")).toBeInTheDocument();
  });

  it("shows delta percentage badges", () => {
    render(
      <HeroKpiGrid
        kpis={KPIS}
        timeSeries={EMPTY_TIME_SERIES}
        heroMetrics={HERO_METRICS}
        gradientPrefix="test"
      />,
    );
    // All kpis have deltaPct = 10.0
    const deltas = screen.getAllByText("10.0%");
    expect(deltas).toHaveLength(4);
  });

  it("applies correct trend color for positive delta (higherIsBetter=true)", () => {
    render(
      <HeroKpiGrid
        kpis={KPIS}
        timeSeries={EMPTY_TIME_SERIES}
        heroMetrics={HERO_METRICS}
        gradientPrefix="test"
      />,
    );
    const deltas = screen.getAllByText("10.0%");
    deltas.forEach((el) => {
      // The text lives inside the <span> that carries the color class
      const colorSpan = el.closest(".text-emerald-600");
      expect(colorSpan).toBeInTheDocument();
    });
  });

  it("applies red trend color for negative delta", () => {
    const negativeKpis: MetricKpiData[] = [
      {
        ...BASE_KPI,
        metricName: "metric_a",
        displayName: "Metric A",
        currentValue: 90,
        unit: "count",
        deltaPct: -5.0,
        deltaAbsolute: -10,
      },
    ];
    render(
      <HeroKpiGrid
        kpis={negativeKpis}
        timeSeries={EMPTY_TIME_SERIES}
        heroMetrics={["metric_a"]}
        gradientPrefix="test"
      />,
    );
    const delta = screen.getByText("5.0%");
    const colorSpan = delta.closest(".text-red-600");
    expect(colorSpan).toBeInTheDocument();
  });

  it("skips KPIs not found in the kpis array", () => {
    render(
      <HeroKpiGrid
        kpis={[KPIS[0]]}
        timeSeries={EMPTY_TIME_SERIES}
        heroMetrics={["metric_a", "nonexistent_metric"]}
        gradientPrefix="test"
      />,
    );
    const cards = screen.getAllByText(/Metric/);
    expect(cards).toHaveLength(1);
  });

  it("does not render MetricInfoCard when showMetricInfoCard is false", () => {
    const { container } = render(
      <HeroKpiGrid
        kpis={KPIS}
        timeSeries={EMPTY_TIME_SERIES}
        heroMetrics={HERO_METRICS}
        gradientPrefix="test"
        showMetricInfoCard={false}
      />,
    );
    // MetricInfoCard wraps children in a Popover with a span.cursor-help
    const tooltipTriggers = container.querySelectorAll(".cursor-help");
    expect(tooltipTriggers).toHaveLength(0);
  });

  it("renders benchmark badge when benchmark data is present", () => {
    const kpiWithBenchmark: MetricKpiData[] = [
      {
        ...BASE_KPI,
        metricName: "metric_a",
        displayName: "Metric A",
        currentValue: 0.9,
        unit: "percentage",
        benchmark: {
          low: 0.3,
          median: 0.5,
          high: 0.8,
          unit: "percentage",
          interpretation: "Test benchmark",
        },
      },
    ];
    const { container } = render(
      <HeroKpiGrid
        kpis={kpiWithBenchmark}
        timeSeries={EMPTY_TIME_SERIES}
        heroMetrics={["metric_a"]}
        gradientPrefix="test"
      />,
    );
    // BenchmarkBadge renders a span with rounded-full class
    const badge = container.querySelector(".rounded-full");
    expect(badge).toBeInTheDocument();
  });

  it("renders 4 cards in a 2-column grid", () => {
    const { container } = render(
      <HeroKpiGrid
        kpis={KPIS}
        timeSeries={EMPTY_TIME_SERIES}
        heroMetrics={HERO_METRICS}
        gradientPrefix="test"
      />,
    );
    const grid = container.querySelector(".grid.grid-cols-2");
    expect(grid).toBeInTheDocument();
    const cards = container.querySelectorAll(".rounded-lg.border.bg-card");
    expect(cards).toHaveLength(4);
  });
});
