import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { WebsiteOverviewPanel } from "../WebsiteOverviewPanel";

import type { ChannelDashboardData, ChannelMetric } from "../../../../../types/metrics";

// --- Mocks ---
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("test-token") }),
}));

vi.mock("../../../../../hooks/useSyncChannel", () => ({
  useSyncChannel: () => ({
    sync: vi.fn(),
    isSyncing: false,
    cooldownMinutes: 0,
    result: null,
    error: null,
    reset: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: "test-tenant" }),
  useSearchParams: () => ({ get: vi.fn().mockReturnValue(null) }),
}));

const MOCK_WEBSITE_DATA: ChannelDashboardData = {
  channelSlug: "website-total",
  channelName: "Sitio Web",
  industryCategory: "education",
  period: "30d",
  kpis: [
    {
      metricName: "sessions",
      displayName: "Sesiones",
      currentValue: 12500,
      previousValue: 10200,
      deltaPct: 22.5,
      deltaAbsolute: 2300,
      unit: "count",
      higherIsBetter: true,
      benchmark: null,
    },
    {
      metricName: "engagementRate",
      displayName: "Engagement Rate",
      currentValue: 0.65,
      previousValue: 0.58,
      deltaPct: 12.1,
      deltaAbsolute: 0.07,
      unit: "percentage",
      higherIsBetter: true,
      benchmark: null,
    },
    {
      metricName: "bounceRate",
      displayName: "Tasa de Rebote",
      currentValue: 0.35,
      previousValue: 0.42,
      deltaPct: -16.7,
      deltaAbsolute: -0.07,
      unit: "percentage",
      higherIsBetter: false,
      benchmark: null,
    },
    {
      metricName: "conversions",
      displayName: "Conversiones",
      currentValue: 340,
      previousValue: 280,
      deltaPct: 21.4,
      deltaAbsolute: 60,
      unit: "count",
      higherIsBetter: true,
      benchmark: null,
    },
    {
      metricName: "averageSessionDuration",
      displayName: "Duración Promedio",
      currentValue: 185,
      previousValue: 160,
      deltaPct: 15.6,
      deltaAbsolute: 25,
      unit: "seconds",
      higherIsBetter: true,
      benchmark: null,
    },
    {
      metricName: "users",
      displayName: "Usuarios",
      currentValue: 9800,
      previousValue: 8100,
      deltaPct: 21.0,
      deltaAbsolute: 1700,
      unit: "count",
      higherIsBetter: true,
      benchmark: null,
    },
  ],
  timeSeries: [],
  funnel: {
    steps: [
      { label: "Usuarios", metricName: "users", value: 9800, conversionRate: null },
      { label: "Sesiones", metricName: "sessions", value: 12500, conversionRate: null },
      { label: "Conversiones", metricName: "conversions", value: 340, conversionRate: 2.72 },
    ],
  },
  frequencyAlert: null,
};

let mockData: ChannelDashboardData | undefined = MOCK_WEBSITE_DATA;
let mockIsLoading = false;

vi.mock("../../../../../hooks/useChannelDashboard", () => ({
  useChannelDashboard: () => ({ data: mockData, isLoading: mockIsLoading }),
}));

vi.mock("../../../../../hooks/useMetricCatalog", () => ({
  useMetricCatalog: () => ({
    getTooltipData: () => null,
  }),
}));

// Mock recharts to avoid SVG rendering issues in tests
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

const WEBSITE_CHANNEL: ChannelMetric = {
  slug: "website-total",
  name: "Sitio Web",
  channelType: "website",
  metrics: [],
  sourceLabel: "Google Analytics",
  connected: true,
};

describe("WebsiteOverviewPanel", () => {
  beforeEach(() => {
    mockData = MOCK_WEBSITE_DATA;
    mockIsLoading = false;
  });

  it("renders the channel name in the header", () => {
    render(<WebsiteOverviewPanel channel={WEBSITE_CHANNEL} onClose={vi.fn()} />);
    expect(screen.getByText("Sitio Web")).toBeInTheDocument();
  });

  it("renders KPI display names from data", () => {
    render(<WebsiteOverviewPanel channel={WEBSITE_CHANNEL} onClose={vi.fn()} />);
    expect(screen.getAllByText("Sesiones").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Engagement Rate")).toBeInTheDocument();
    expect(screen.getAllByText("Conversiones").length).toBeGreaterThanOrEqual(1);
  });

  it('renders the "Dashboard completo" button when onExpand is provided', () => {
    render(<WebsiteOverviewPanel channel={WEBSITE_CHANNEL} onClose={vi.fn()} onExpand={vi.fn()} />);
    expect(screen.getByLabelText("Dashboard completo")).toBeInTheDocument();
  });

  it('does not render "Dashboard completo" button when onExpand is absent', () => {
    render(<WebsiteOverviewPanel channel={WEBSITE_CHANNEL} onClose={vi.fn()} />);
    expect(screen.queryByLabelText("Dashboard completo")).not.toBeInTheDocument();
  });

  it("shows loading spinner when isLoading is true", () => {
    mockIsLoading = true;
    mockData = undefined;
    const { container } = render(
      <WebsiteOverviewPanel channel={WEBSITE_CHANNEL} onClose={vi.fn()} />,
    );
    expect(container.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("shows empty state when no data", () => {
    mockData = undefined;
    render(<WebsiteOverviewPanel channel={WEBSITE_CHANNEL} onClose={vi.fn()} />);
    expect(screen.getByText("No hay datos para el periodo seleccionado")).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    render(<WebsiteOverviewPanel channel={WEBSITE_CHANNEL} onClose={onClose} />);
    const closeButton = screen.getByRole("button", { name: /cerrar/i });
    fireEvent.click(closeButton);
    expect(onClose).toHaveBeenCalled();
  });
});
