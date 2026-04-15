import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent, within } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ResumenTab } from "../tabs/ResumenTab";

import type { ChannelDashboardData, CampaignPerformanceData } from "../../../../../types/metrics";
import type {
  BrandingAggregate,
  MetaHealthCheck,
  MetricsByOffer,
  OfferMetrics,
  UnassignedAggregate,
} from "../../../../../types/offer-association";

// ---------------------------------------------------------------------------
// Mocks — must be declared before component import
// ---------------------------------------------------------------------------

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("test-token") }),
}));

vi.mock("@/lib/config", () => ({
  config: { api: { baseUrl: "https://api.test.com" } },
}));

vi.mock("@/lib/http-client", () => ({
  fetchClient: vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
  }),
}));

// Mock the tenant locale hook — it talks to Clerk internally.
vi.mock("@/features/tenant/context/tenant-locale-context", () => ({
  useTenantLocale: () => ({ currency: "PEN", timezone: "America/Lima" }),
}));

// Mock the data hooks so we can drive the tab directly from fixtures instead
// of wiring the full fetchClient pipeline. The underlying API is already
// covered by offer-association-api.test.ts.
const mockHealthCheck = vi.fn<() => { data: MetaHealthCheck | undefined; isLoading: boolean }>();
const mockMetricsByOffer = vi.fn<() => { data: MetricsByOffer | undefined; isLoading: boolean }>();

vi.mock("../../../../../api/offer-association-api", () => ({
  useMetaHealthCheck: () => mockHealthCheck(),
  useMetricsByOffer: () => mockMetricsByOffer(),
}));

// Mock recharts so the chart renders without SVG measurement issues.
vi.mock("recharts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("recharts")>();
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="responsive-container">{children}</div>
    ),
  };
});

// Must import AFTER mocks

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------

function renderWithQuery(ui: React.ReactElement) {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false, refetchOnWindowFocus: false },
      mutations: { retry: false },
    },
  });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

function makeOffer(overrides: Partial<OfferMetrics> = {}): OfferMetrics {
  return {
    offerId: "off-1",
    offerName: "Curso Core",
    archetype: "PROGRAMA",
    expectedMetric: "lead",
    expectedMetricLabelEs: "Leads",
    totalSpend: 500,
    currency: "PEN",
    primaryResultCount: 47,
    primaryCostPerResult: 10.64,
    primaryMetricName: "Leads",
    primaryMetricUnit: "count",
    roas: 2.4,
    impressions: 12_340,
    clicks: 518,
    ctr: 4.2,
    cpm: 5.5,
    cpc: 0.96,
    reach: null,
    frequency: null,
    funnel: [
      {
        label: "Impresiones",
        metricName: "impressions",
        value: 12_340,
        conversionRateFromPrevious: null,
      },
      { label: "Clics", metricName: "clicks", value: 518, conversionRateFromPrevious: 4.2 },
    ],
    timeseries: [
      { date: "2026-04-01", spend: 50, primaryResult: 5 },
      { date: "2026-04-02", spend: 60, primaryResult: 7 },
    ],
    metricUnavailableReason: null,
    ...overrides,
  };
}

function makeBranding(overrides: Partial<BrandingAggregate> = {}): BrandingAggregate {
  return {
    targetCount: 2,
    totalSpend: 200,
    impressions: 30_000,
    clicks: 60,
    ctr: 0.2,
    cpm: 6.7,
    cpc: 3.3,
    reach: null,
    frequency: null,
    funnel: [
      {
        label: "Impresiones",
        metricName: "impressions",
        value: 30_000,
        conversionRateFromPrevious: null,
      },
    ],
    ...overrides,
  };
}

function makeUnassigned(overrides: Partial<UnassignedAggregate> = {}): UnassignedAggregate {
  return {
    targetCount: 1,
    totalSpend: 80,
    impressions: 5_000,
    clicks: 40,
    ctr: 0.8,
    cpm: 16,
    cpc: 2,
    reach: null,
    funnel: [
      {
        label: "Impresiones",
        metricName: "impressions",
        value: 5_000,
        conversionRateFromPrevious: null,
      },
    ],
    ...overrides,
  };
}

function makeMetricsByOffer(overrides: Partial<MetricsByOffer> = {}): MetricsByOffer {
  return {
    period: "30d",
    startDate: "2026-03-11",
    endDate: "2026-04-10",
    currency: "PEN",
    offers: [makeOffer()],
    unassigned: makeUnassigned(),
    brandingOnly: makeBranding(),
    funnelAll: [
      {
        label: "Impresiones",
        metricName: "impressions",
        value: 47_340,
        conversionRateFromPrevious: null,
      },
      { label: "Clics", metricName: "clicks", value: 618, conversionRateFromPrevious: 1.31 },
    ],
    reachAll: 14_200,
    ...overrides,
  };
}

function makeHealthCheck(overrides: Partial<MetaHealthCheck> = {}): MetaHealthCheck {
  return {
    overallStatus: "healthy",
    activeCampaigns: [],
    offersCoverage: [],
    unassignedTargets: [],
    recommendations: [],
    summaryText: "Todo OK",
    ...overrides,
  };
}

function makeDashboardData(): ChannelDashboardData {
  return {
    channelSlug: "meta-ads",
    channelName: "Meta Ads",
    industryCategory: "education",
    period: "30d",
    kpis: [],
    timeSeries: [
      {
        metricName: "spend",
        displayName: "Inversión",
        unit: "currency",
        dataPoints: [
          { date: "2026-04-01", value: 50 },
          { date: "2026-04-02", value: 60 },
        ],
      },
      {
        metricName: "conversions",
        displayName: "Resultados",
        unit: "count",
        dataPoints: [
          { date: "2026-04-01", value: 3 },
          { date: "2026-04-02", value: 5 },
        ],
      },
    ],
    funnel: { steps: [] },
    frequencyAlert: null,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("ResumenTab", () => {
  beforeEach(() => {
    mockHealthCheck.mockReturnValue({ data: makeHealthCheck(), isLoading: false });
    mockMetricsByOffer.mockReturnValue({ data: makeMetricsByOffer(), isLoading: false });
  });

  it("renders loading spinner when isLoading is true", () => {
    const { container } = renderWithQuery(<ResumenTab data={undefined} isLoading={true} />);
    const spinner = container.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });

  it('renders "No hay datos disponibles" when data is undefined', () => {
    renderWithQuery(<ResumenTab data={undefined} isLoading={false} />);
    expect(screen.getByText("No hay datos disponibles")).toBeInTheDocument();
  });

  it('renders 6 KPI cards with the default "all" filter', () => {
    renderWithQuery(<ResumenTab data={makeDashboardData()} isLoading={false} />);
    const grid = screen.getByRole("group", { name: "Resumen de métricas" });
    const cards = within(grid).getAllByRole("group");
    expect(cards).toHaveLength(6);
    // Inversión card shows the Spanish label
    expect(within(grid).getByText("Inversión")).toBeInTheDocument();
    expect(within(grid).getByText("ROAS")).toBeInTheDocument();
    expect(within(grid).getByText("Resultados")).toBeInTheDocument();
    expect(within(grid).getByText("CPA")).toBeInTheDocument();
    expect(within(grid).getByText("CTR")).toBeInTheDocument();
    expect(within(grid).getByText("Alcance")).toBeInTheDocument();
  });

  it("switches to offer-specific KPIs when an offer chip is clicked", () => {
    renderWithQuery(<ResumenTab data={makeDashboardData()} isLoading={false} />);
    const chip = screen.getByRole("button", { name: /Curso Core/i });
    fireEvent.click(chip);
    const grid = screen.getByRole("group", { name: "Resumen de métricas" });
    // Offer with lead primary metric → card #4 is CPL, card #3 is Leads
    expect(within(grid).getByText("CPL")).toBeInTheDocument();
    expect(within(grid).getByText("Leads")).toBeInTheDocument();
  });

  it("switches to branding KPIs when Branding chip is clicked", () => {
    renderWithQuery(<ResumenTab data={makeDashboardData()} isLoading={false} />);
    const chip = screen.getByRole("button", { name: /Branding/i });
    fireEvent.click(chip);
    const grid = screen.getByRole("group", { name: "Resumen de métricas" });
    // Branding exposes CPM and Frecuencia, not ROAS/CPA
    expect(within(grid).getByText("CPM")).toBeInTheDocument();
    expect(within(grid).getByText("Frecuencia")).toBeInTheDocument();
    expect(within(grid).getByText("Campañas activas")).toBeInTheDocument();
    expect(within(grid).queryByText("ROAS")).toBeNull();
  });

  it("shows the unassigned filter CTA when unassigned chip is clicked", () => {
    mockHealthCheck.mockReturnValue({
      data: makeHealthCheck({
        unassignedTargets: [
          {
            targetType: "campaign",
            externalId: "c-1",
            name: "Camp 1",
            objective: null,
            status: null,
          },
        ],
      }),
      isLoading: false,
    });
    renderWithQuery(<ResumenTab data={makeDashboardData()} isLoading={false} />);
    const chip = screen.getByRole("button", { name: /Sin asignar/i });
    fireEvent.click(chip);
    const grid = screen.getByRole("group", { name: "Resumen de métricas" });
    expect(within(grid).getByText("Acción requerida")).toBeInTheDocument();
    expect(within(grid).getByRole("button", { name: /Asignar ahora/i })).toBeInTheDocument();
  });

  it('renders "—" for reach in the default view when reachAll is null', () => {
    mockMetricsByOffer.mockReturnValue({
      data: makeMetricsByOffer({ reachAll: null }),
      isLoading: false,
    });
    renderWithQuery(<ResumenTab data={makeDashboardData()} isLoading={false} />);
    const grid = screen.getByRole("group", { name: "Resumen de métricas" });
    // Find the Alcance card by its aria-label
    const alcanceCard = within(grid)
      .getAllByRole("group")
      .find((el) => el.getAttribute("aria-label")?.startsWith("Alcance"));
    expect(alcanceCard).toBeDefined();
    expect(alcanceCard?.textContent).toContain("—");
  });

  it('renders the celebratory "Todo en orden" state when there are no notices', () => {
    renderWithQuery(<ResumenTab data={makeDashboardData()} isLoading={false} />);
    expect(screen.getByText(/Todo en orden/i)).toBeInTheDocument();
  });

  it('renders the "Tienes N cosas por mejorar" header when a notices summary is passed', () => {
    renderWithQuery(
      <ResumenTab
        data={makeDashboardData()}
        isLoading={false}
        noticesSummary={{
          byTab: {
            campanas: [
              {
                id: "x",
                category: "campaign",
                severity: "warning",
                title: "Aumenta presupuesto",
                body: "Tu CPA es bueno, invertí más.",
                contextLabel: "Campaña: Test",
                targetExternalId: "c1",
              },
            ],
            creativos: [],
            audiencia: [],
            costos: [],
          },
          total: 1,
          perTabCounts: { campanas: 1, creativos: 0, audiencia: 0, costos: 0 },
          severity: { critical: 0, warning: 1, info: 0 },
          severityPerTab: {
            campanas: { critical: 0, warning: 1, info: 0 },
            creativos: { critical: 0, warning: 0, info: 0 },
            audiencia: { critical: 0, warning: 0, info: 0 },
            costos: { critical: 0, warning: 0, info: 0 },
          },
          maxSeverityPerTab: {
            campanas: "warning",
            creativos: null,
            audiencia: null,
            costos: null,
          },
        }}
      />,
    );
    expect(screen.getByText(/Tienes 1 cosa por mejorar/i)).toBeInTheDocument();
  });
});
