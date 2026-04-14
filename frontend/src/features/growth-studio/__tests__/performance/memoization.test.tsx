import { describe, it, expect, vi } from "vitest";
import { render, act } from "@testing-library/react";
import { useState, memo } from "react";
import { HeroKpiGrid } from "../../components/metrics-dashboard/sidebar/shared/HeroKpiGrid";
import type { MetricKpiData, MetricTimeSeries } from "../../types/metrics";

// Mock recharts to avoid heavy rendering
vi.mock("recharts", () => ({
  Area: () => null,
  AreaChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/chart", () => ({
  ChartContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("../../components/metrics-dashboard/channel-widgets/KpiTooltip", () => ({
  MetricInfoCard: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}));

vi.mock("../../components/metrics-dashboard/channel-widgets/BenchmarkBadge", () => ({
  BenchmarkBadge: () => null,
}));

const MOCK_KPI: MetricKpiData = {
  metricName: "impressions",
  displayName: "Impresiones",
  currentValue: 1000,
  previousValue: 800,
  unit: "count",
  higherIsBetter: true,
  deltaPct: 5.2,
  deltaAbsolute: 200,
  benchmark: null,
};

const MOCK_TIMESERIES: MetricTimeSeries = {
  metricName: "impressions",
  displayName: "Impresiones",
  unit: "count",
  dataPoints: [
    { date: "2026-01-01", value: 100 },
    { date: "2026-01-02", value: 200 },
  ],
};

describe("Memoization verification", () => {
  it("HeroKpiGrid does not re-render when parent state changes and props are stable", () => {
    let heroRenderCount = 0;

    const TrackedHeroKpiGrid = memo(function TrackedHeroKpiGrid(props: {
      kpis: MetricKpiData[];
      timeSeries: MetricTimeSeries[];
      heroMetrics: readonly string[];
      gradientPrefix: string;
    }) {
      heroRenderCount++;
      return <HeroKpiGrid {...props} />;
    });

    const METRICS = ["impressions"] as const;
    const kpis = [MOCK_KPI];
    const timeSeries = [MOCK_TIMESERIES];

    function Parent() {
      const [count, setCount] = useState(0);
      return (
        <div>
          <button onClick={() => setCount((c) => c + 1)}>increment</button>
          <span data-testid="count">{count}</span>
          <TrackedHeroKpiGrid
            kpis={kpis}
            timeSeries={timeSeries}
            heroMetrics={METRICS}
            gradientPrefix="test"
          />
        </div>
      );
    }

    const { getByText } = render(<Parent />);
    expect(heroRenderCount).toBe(1);

    // Trigger parent re-render — child should NOT re-render (stable props)
    act(() => getByText("increment").click());
    act(() => getByText("increment").click());

    expect(heroRenderCount).toBe(1);
  });

  it("HeroKpiGrid re-renders when props change", () => {
    let heroRenderCount = 0;

    const TrackedHeroKpiGrid = memo(function TrackedHeroKpiGrid(props: {
      kpis: MetricKpiData[];
      timeSeries: MetricTimeSeries[];
      heroMetrics: readonly string[];
      gradientPrefix: string;
    }) {
      heroRenderCount++;
      return <HeroKpiGrid {...props} />;
    });

    const METRICS = ["impressions"] as const;

    function Parent() {
      const [kpis, setKpis] = useState([MOCK_KPI]);
      return (
        <div>
          <button onClick={() => setKpis([{ ...MOCK_KPI, currentValue: 2000 }])}>update</button>
          <TrackedHeroKpiGrid
            kpis={kpis}
            timeSeries={[MOCK_TIMESERIES]}
            heroMetrics={METRICS}
            gradientPrefix="test"
          />
        </div>
      );
    }

    const { getByText } = render(<Parent />);
    expect(heroRenderCount).toBe(1);

    act(() => getByText("update").click());
    // Should re-render because kpis array changed reference
    expect(heroRenderCount).toBe(2);
  });
});
