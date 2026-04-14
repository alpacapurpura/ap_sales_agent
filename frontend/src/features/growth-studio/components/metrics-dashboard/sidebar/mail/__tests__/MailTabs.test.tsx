/**
 * Tests for the 6 new Email Intelligence Hub tabs.
 * Each tab uses its own hook internally, so we mock the hooks.
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  EmailDashboardData,
  EmailCampaignsData,
  EmailAutomationsData,
  EmailAudienceData,
  EmailHealthData,
  EmailGrowthData,
  EmailHealthScore,
} from "../../../../../types/mail-types";
import type { MetricKpiData, MetricTimeSeries, FunnelStep } from "../../../../../types/metrics";

// ---------------------------------------------------------------------------
// Shared mock helpers
// ---------------------------------------------------------------------------

function makeTsPoints(count: number, baseValue: number) {
  return Array.from({ length: count }, (_, i) => ({
    date: `2026-04-${String(i + 1).padStart(2, "0")}`,
    value: baseValue + i * 2,
  }));
}

function makeKpi(overrides: Partial<MetricKpiData> & { metricName: string }): MetricKpiData {
  return {
    displayName: overrides.metricName,
    currentValue: 10,
    previousValue: 8,
    deltaPct: 25,
    deltaAbsolute: 2,
    unit: "count",
    higherIsBetter: true,
    benchmark: null,
    ...overrides,
  };
}

const BASE_KPIS: MetricKpiData[] = [
  makeKpi({ metricName: "emails_sent", displayName: "Emails Enviados", currentValue: 5000 }),
  makeKpi({
    metricName: "open_rate",
    displayName: "Tasa de Apertura",
    currentValue: 22.5,
    unit: "percentage",
  }),
  makeKpi({
    metricName: "click_rate",
    displayName: "Tasa de Clics",
    currentValue: 3.1,
    unit: "percentage",
  }),
  makeKpi({
    metricName: "click_to_open_rate",
    displayName: "CTOR",
    currentValue: 14.1,
    unit: "percentage",
  }),
  makeKpi({
    metricName: "deliverability_rate",
    displayName: "Entregabilidad",
    currentValue: 98.5,
    unit: "percentage",
  }),
  makeKpi({
    metricName: "active_subscribers",
    displayName: "Suscriptores Activos",
    currentValue: 12000,
  }),
  makeKpi({
    metricName: "bounce_rate",
    displayName: "Tasa de Rebote",
    currentValue: 1.2,
    unit: "percentage",
    higherIsBetter: false,
  }),
  makeKpi({
    metricName: "unsubscribe_rate",
    displayName: "Tasa Desuscripción",
    currentValue: 0.15,
    unit: "percentage",
    higherIsBetter: false,
  }),
  makeKpi({
    metricName: "forward_rate",
    displayName: "Tasa de Reenvío",
    currentValue: 0.8,
    unit: "percentage",
  }),
  makeKpi({ metricName: "new_subscribers", displayName: "Nuevos Suscriptores", currentValue: 290 }),
  makeKpi({
    metricName: "unsubscribes",
    displayName: "Bajas",
    currentValue: 30,
    higherIsBetter: false,
  }),
  makeKpi({
    metricName: "list_growth_rate",
    displayName: "Tasa Crecimiento",
    currentValue: 3.2,
    unit: "percentage",
  }),
  makeKpi({
    metricName: "automation_emails_sent",
    displayName: "Emails Automatizados",
    currentValue: 1200,
  }),
  makeKpi({
    metricName: "automation_completion_rate",
    displayName: "Tasa de Completado",
    currentValue: 48.5,
    unit: "percentage",
  }),
  makeKpi({
    metricName: "automation_avg_open_rate",
    displayName: "Open Rate Autos",
    currentValue: 35.0,
    unit: "percentage",
  }),
];

const BASE_TS: MetricTimeSeries[] = [
  {
    metricName: "emails_sent",
    displayName: "Enviados",
    unit: "count",
    dataPoints: makeTsPoints(7, 150),
  },
  {
    metricName: "open_rate",
    displayName: "Apertura",
    unit: "percentage",
    dataPoints: makeTsPoints(7, 18),
  },
  {
    metricName: "active_subscribers",
    displayName: "Activos",
    unit: "count",
    dataPoints: makeTsPoints(7, 11800),
  },
  {
    metricName: "new_subscribers",
    displayName: "Nuevos",
    unit: "count",
    dataPoints: makeTsPoints(7, 20),
  },
  {
    metricName: "unsubscribes",
    displayName: "Bajas",
    unit: "count",
    dataPoints: makeTsPoints(7, 3),
  },
  {
    metricName: "bounce_rate",
    displayName: "Tasa Rebote",
    unit: "percentage",
    dataPoints: makeTsPoints(7, 1),
  },
  {
    metricName: "deliverability_rate",
    displayName: "Entregabilidad",
    unit: "percentage",
    dataPoints: makeTsPoints(7, 97),
  },
];

const BASE_FUNNEL: FunnelStep[] = [
  { label: "Enviados", metricName: "emails_sent", value: 5000, conversionRate: null },
  { label: "Entregados", metricName: "delivered", value: 4900, conversionRate: 98.0 },
  { label: "Abiertos", metricName: "unique_opens", value: 1100, conversionRate: 22.4 },
  { label: "Clics", metricName: "unique_clicks", value: 155, conversionRate: 14.1 },
];

const HEALTH_SCORE: EmailHealthScore = {
  total: 85,
  subScores: [
    { area: "engagement", label: "Engagement", score: 90, color: "green" },
    { area: "entregabilidad", label: "Entregabilidad", score: 80, color: "green" },
    { area: "crecimiento", label: "Crecimiento", score: 75, color: "green" },
    { area: "contenido", label: "Contenido", score: 95, color: "green" },
  ],
};

// ---------------------------------------------------------------------------
// Mock data per tab
// ---------------------------------------------------------------------------

const PANORAMA_DATA: EmailDashboardData = {
  channelSlug: "email-nurture",
  channelName: "Email Marketing",
  providerName: "mailerlite",
  period: "30d",
  healthScore: HEALTH_SCORE,
  kpis: BASE_KPIS,
  timeSeries: BASE_TS,
  funnel: BASE_FUNNEL,
  bestCampaign: {
    campaignName: "Lanzamiento Curso",
    campaignSubject: "Tu oportunidad",
    campaignType: "lanzamiento",
    sentCount: 5000,
    openRate: 45.2,
    clickToOpenRate: 12.8,
    sentDate: "2026-04-01T10:00:00Z",
  },
  worstCampaign: null,
  campaignsVsAutomations: {
    campaignsSent: 4000,
    campaignsOpenRate: 20.0,
    campaignsClickRate: 2.5,
    campaignsCtor: 12.0,
    campaignsUnsubs: 15,
    automationsSent: 1000,
    automationsOpenRate: 35.0,
    automationsClickRate: 5.0,
    automationsCtor: 14.0,
    automationsUnsubs: 3,
  },
};

const CAMPAIGNS_DATA: EmailCampaignsData = {
  period: "30d",
  typePerformance: [
    {
      campaignType: "newsletter",
      campaignCount: 4,
      totalSent: 12000,
      avgOpenRate: 18.5,
      avgCtor: 8.2,
      totalUnsubs: 10,
      rankLabel: "#1",
    },
  ],
  campaigns: [
    {
      campaignId: "c1",
      campaignName: "Newsletter Semanal",
      campaignSubject: "Novedades",
      campaignType: "newsletter",
      sentDate: "2026-04-01T10:00:00Z",
      emailsSent: 3000,
      openRate: 18.5,
      clickRate: 2.3,
      clickToOpenRate: 12.4,
      bounceRate: 1.1,
      unsubscribes: 3,
      uniqueOpens: 555,
      uniqueClicks: 69,
      screenshotUrl: null,
      previewUrl: null,
    },
  ],
  topSubjects: [],
};

const AUTOMATIONS_DATA: EmailAutomationsData = {
  period: "30d",
  kpis: BASE_KPIS,
  automations: [
    {
      automationId: "a1",
      name: "Bienvenida",
      automationType: "welcome",
      status: "active",
      activeSubscribers: 150,
      completed: 120,
      emailsSent: 450,
      openRate: 42.0,
      clickRate: 8.5,
      clickToOpenRate: 20.2,
      completionRate: 80.0,
      unsubscribes: 0,
      steps: [],
    },
  ],
};

const AUDIENCE_DATA: EmailAudienceData = {
  period: "30d",
  segments: [
    {
      segmentName: "champions",
      label: "Champions",
      count: 2000,
      percentage: 16.7,
      openRate: 45.0,
      clickRate: 12.0,
      ctor: 26.7,
      avgDaysInactive: null,
      recommendedAction: "Premiar con contenido exclusivo",
    },
    {
      segmentName: "activos",
      label: "Activos",
      count: 5000,
      percentage: 41.7,
      openRate: 25.0,
      clickRate: 4.0,
      ctor: 16.0,
      avgDaysInactive: null,
      recommendedAction: "Mantener engagement",
    },
  ],
  segmentTypeMatrix: [],
  sources: [
    {
      source: "organic",
      label: "Orgánico",
      subscriberCount: 6000,
      percentage: 50.0,
      openRate: 28.0,
      clickRate: 5.0,
      championsPct: 20.0,
    },
  ],
  engagementDecay: [
    { periodLabel: "0-30d", openRate: 35.0 },
    { periodLabel: "31-60d", openRate: 22.0 },
  ],
  activityHeatmap: [{ dayOfWeek: 0, hourBlock: "9-12", openRate: 12.0 }],
};

const HEALTH_DATA: EmailHealthData = {
  period: "30d",
  campaignsCount: 12,
  healthScore: HEALTH_SCORE,
  kpis: BASE_KPIS,
  bounceBreakdown: {
    hardBounces: 10,
    softBounces: 50,
    hardBounceRate: 0.2,
    softBounceRate: 1.0,
    totalDelivered: 4940,
  },
  timeSeries: BASE_TS,
  alerts: [],
};

const GROWTH_DATA: EmailGrowthData = {
  period: "30d",
  kpis: BASE_KPIS,
  timeSeries: BASE_TS,
  sources: [
    {
      source: "landing",
      label: "Landing Page",
      subscriberCount: 3000,
      percentage: 45.0,
      openRate: 30.0,
      clickRate: 6.0,
      championsPct: 22.0,
    },
  ],
  retentionCurve: [
    { periodLabel: "Mes 1", openRate: 40.0 },
    { periodLabel: "Mes 3", openRate: 25.0 },
  ],
};

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockUseMailDashboard = vi.fn();
const mockUseMailCampaigns = vi.fn();
const mockUseMailAutomations = vi.fn();
const mockUseMailAudience = vi.fn();
const mockUseMailHealth = vi.fn();
const mockUseMailGrowth = vi.fn();

vi.mock("../../../../../hooks/useMailDashboard", () => ({
  useMailDashboard: (...args: unknown[]) => mockUseMailDashboard(...args),
  useMailCampaigns: (...args: unknown[]) => mockUseMailCampaigns(...args),
  useMailAutomations: (...args: unknown[]) => mockUseMailAutomations(...args),
  useMailAudience: (...args: unknown[]) => mockUseMailAudience(...args),
  useMailHealth: (...args: unknown[]) => mockUseMailHealth(...args),
  useMailGrowth: (...args: unknown[]) => mockUseMailGrowth(...args),
}));

// Mock recharts to avoid SVG rendering issues in JSDOM
vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  ComposedChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="composed-chart">{children}</div>
  ),
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="line-chart">{children}</div>
  ),
  AreaChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="area-chart">{children}</div>
  ),
  PieChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Bar: () => null,
  Line: () => null,
  Area: () => null,
  Pie: () => null,
  Cell: () => null,
  CartesianGrid: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  Legend: () => null,
  ReferenceArea: () => null,
  ReferenceLine: () => null,
  LabelList: () => null,
}));

// Mock ChartContainer since it wraps recharts
vi.mock("@/components/ui/chart", () => ({
  ChartContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  ChartTooltipContent: () => null,
}));

// Mock MetricInfoPopover to render children
vi.mock("@/components/shared/MetricInfoPopover", () => ({
  MetricInfoPopover: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Lazy imports after mocks
import { MailPanoramaTab } from "../tabs/MailPanoramaTab";
import { MailCampanasTab } from "../tabs/MailCampanasTab";
import { MailAutomatizacionesTab } from "../tabs/MailAutomatizacionesTab";
import { MailAudienciaTab } from "../tabs/MailAudienciaTab";
import { MailEntregabilidadV2Tab } from "../tabs/MailEntregabilidadV2Tab";
import { MailCrecimientoTab } from "../tabs/MailCrecimientoTab";

// =============================================================================
// Tab 1: Panorama
// =============================================================================
describe("MailPanoramaTab", () => {
  it("shows loading spinner when data is loading", () => {
    mockUseMailDashboard.mockReturnValue({ data: undefined, isLoading: true });
    const { container } = render(<MailPanoramaTab period="30d" />);
    expect(container.querySelector(".animate-spin")).toBeTruthy();
  });

  it("shows empty state when no data", () => {
    mockUseMailDashboard.mockReturnValue({ data: undefined, isLoading: false });
    render(<MailPanoramaTab period="30d" />);
    expect(screen.getByText(/no hay datos disponibles/i)).toBeInTheDocument();
  });

  it("renders KPI cards with correct display names", () => {
    mockUseMailDashboard.mockReturnValue({ data: PANORAMA_DATA, isLoading: false });
    const { container } = render(<MailPanoramaTab period="30d" />);
    expect(container.textContent).toContain("Emails Enviados");
    expect(container.textContent).toContain("Tasa de Apertura");
    expect(container.textContent).toContain("Tasa de Clics");
    expect(container.textContent).toContain("CTOR");
  });

  it("renders funnel steps", () => {
    mockUseMailDashboard.mockReturnValue({ data: PANORAMA_DATA, isLoading: false });
    const { container } = render(<MailPanoramaTab period="30d" />);
    expect(container.textContent).toContain("Enviados");
    expect(container.textContent).toContain("Entregados");
    expect(container.textContent).toContain("Abiertos");
    expect(container.textContent).toContain("Clics");
  });

  it("renders benchmark comparison section", () => {
    mockUseMailDashboard.mockReturnValue({ data: PANORAMA_DATA, isLoading: false });
    const { container } = render(<MailPanoramaTab period="30d" />);
    expect(container.textContent).toContain("Tu Performance vs Industria");
  });

  it("renders campaigns vs automations table when data present", () => {
    mockUseMailDashboard.mockReturnValue({ data: PANORAMA_DATA, isLoading: false });
    const { container } = render(<MailPanoramaTab period="30d" />);
    expect(container.textContent).toContain("Campañas vs Automatizaciones");
  });

  it("renders recent campaigns section", () => {
    mockUseMailDashboard.mockReturnValue({ data: PANORAMA_DATA, isLoading: false });
    render(<MailPanoramaTab period="30d" />);
    expect(screen.getByText("Lanzamiento Curso")).toBeInTheDocument();
  });
});

// =============================================================================
// Tab 2: Campañas
// =============================================================================
describe("MailCampanasTab", () => {
  it("shows loading spinner when data is loading", () => {
    mockUseMailCampaigns.mockReturnValue({ data: undefined, isLoading: true });
    const { container } = render(<MailCampanasTab period="30d" />);
    expect(container.querySelector(".animate-spin")).toBeTruthy();
  });

  it("shows empty state when no data", () => {
    mockUseMailCampaigns.mockReturnValue({ data: undefined, isLoading: false });
    render(<MailCampanasTab period="30d" />);
    expect(screen.getByText(/no hay datos de campañas disponibles/i)).toBeInTheDocument();
  });

  it("renders campaign table with campaign data", () => {
    mockUseMailCampaigns.mockReturnValue({ data: CAMPAIGNS_DATA, isLoading: false });
    render(<MailCampanasTab period="30d" />);
    expect(screen.getByText("Newsletter Semanal")).toBeInTheDocument();
  });

  it("renders type performance cards", () => {
    mockUseMailCampaigns.mockReturnValue({ data: CAMPAIGNS_DATA, isLoading: false });
    const { container } = render(<MailCampanasTab period="30d" />);
    expect(container.textContent).toContain("newsletter");
  });
});

// =============================================================================
// Tab 3: Automatizaciones
// =============================================================================
describe("MailAutomatizacionesTab", () => {
  it("shows loading spinner when data is loading", () => {
    mockUseMailAutomations.mockReturnValue({ data: undefined, isLoading: true });
    const { container } = render(<MailAutomatizacionesTab period="30d" />);
    expect(container.querySelector(".animate-spin")).toBeTruthy();
  });

  it("shows empty state when no automations", () => {
    mockUseMailAutomations.mockReturnValue({
      data: { ...AUTOMATIONS_DATA, automations: [] },
      isLoading: false,
    });
    render(<MailAutomatizacionesTab period="30d" />);
    expect(screen.getByText("Sin automatizaciones")).toBeInTheDocument();
  });

  it("renders automation data when present", () => {
    mockUseMailAutomations.mockReturnValue({ data: AUTOMATIONS_DATA, isLoading: false });
    const { container } = render(<MailAutomatizacionesTab period="30d" />);
    expect(container.textContent).toContain("Bienvenida");
  });

  it("renders KPI cards for automations", () => {
    mockUseMailAutomations.mockReturnValue({ data: AUTOMATIONS_DATA, isLoading: false });
    render(<MailAutomatizacionesTab period="30d" />);
    expect(screen.getByText("Ingresados Totales")).toBeInTheDocument();
    expect(screen.getByText("Salud General")).toBeInTheDocument();
  });
});

describe("MailAutomatizacionesTab — redesigned", () => {
  const REDESIGNED_DATA: EmailAutomationsData = {
    period: "30d",
    kpis: [
      makeKpi({
        metricName: "automation_emails_sent",
        displayName: "Emails Automatizados",
        currentValue: 18,
      }),
    ],
    automations: [
      {
        automationId: "a1",
        name: "BIENVENIDA",
        automationType: "welcome",
        status: "active",
        activeSubscribers: 9,
        completed: 4,
        emailsSent: 18,
        openRate: 100,
        clickRate: 50,
        clickToOpenRate: 50,
        completionRate: 44.4,
        unsubscribes: 0,
        steps: [
          {
            stepId: "s1",
            stepNumber: 1,
            type: "email",
            subject: "Bienvenida hola",
            fromName: "Team",
            emailsSent: 9,
            uniqueOpens: 9,
            openRate: 100,
            uniqueClicks: 4,
            clickRate: 44.4,
            unsubscribes: 0,
            bounces: 0,
            screenshotUrl: null,
            previewUrl: null,
            delayValue: null,
            delayUnit: null,
          },
        ],
      },
    ],
  };

  beforeEach(() => {
    mockUseMailAutomations.mockReturnValue({
      data: REDESIGNED_DATA,
      isLoading: false,
    });
  });

  it("renders new table columns: Ingresados, CTOR, Unsubs, Salud", () => {
    render(<MailAutomatizacionesTab period="30d" />);
    // "Ingresados" also appears in KPI row label, allow multiple matches
    expect(screen.getAllByText(/Ingresados/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/CTOR/i)).toBeInTheDocument();
    expect(screen.getByText(/Unsubs/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Salud/i).length).toBeGreaterThan(0);
  });

  it("renders automation row with activeSubscribers = 9 (ingresados)", () => {
    render(<MailAutomatizacionesTab period="30d" />);
    // Some element should show '9' as the ingresados count
    const nines = screen.getAllByText("9");
    expect(nines.length).toBeGreaterThan(0);
  });

  it("opens accordion when clicking on automation row", async () => {
    render(<MailAutomatizacionesTab period="30d" />);
    const row = screen.getByText("BIENVENIDA").closest("tr");
    expect(row).not.toBeNull();
    fireEvent.click(row!);
    // Email subject from the pipeline becomes visible
    expect(await screen.findByText("Bienvenida hola")).toBeInTheDocument();
  });
});

// =============================================================================
// Tab 4: Audiencia
// =============================================================================
describe("MailAudienciaTab", () => {
  it("shows loading spinner when data is loading", () => {
    mockUseMailAudience.mockReturnValue({ data: undefined, isLoading: true });
    const { container } = render(<MailAudienciaTab period="30d" />);
    expect(container.querySelector(".animate-spin")).toBeTruthy();
  });

  it("shows empty state when no data", () => {
    mockUseMailAudience.mockReturnValue({ data: undefined, isLoading: false });
    render(<MailAudienciaTab period="30d" />);
    expect(screen.getByText("Sin datos de audiencia")).toBeInTheDocument();
  });

  it("renders segment data when present", () => {
    mockUseMailAudience.mockReturnValue({ data: AUDIENCE_DATA, isLoading: false });
    render(<MailAudienciaTab period="30d" />);
    expect(screen.getByText("Champions")).toBeInTheDocument();
    expect(screen.getByText("Activos")).toBeInTheDocument();
  });
});

// =============================================================================
// Tab 5: Entregabilidad (V2)
// =============================================================================
describe("MailEntregabilidadV2Tab", () => {
  it("shows loading spinner when data is loading", () => {
    mockUseMailHealth.mockReturnValue({ data: undefined, isLoading: true });
    const { container } = render(<MailEntregabilidadV2Tab period="30d" />);
    expect(container.querySelector(".animate-spin")).toBeTruthy();
  });

  it("shows empty state when no data", () => {
    mockUseMailHealth.mockReturnValue({ data: undefined, isLoading: false });
    render(<MailEntregabilidadV2Tab period="30d" />);
    expect(screen.getByText("Sin datos de entregabilidad")).toBeInTheDocument();
  });

  it("renders health score when data present", () => {
    mockUseMailHealth.mockReturnValue({ data: HEALTH_DATA, isLoading: false });
    render(<MailEntregabilidadV2Tab period="30d" />);
    // MailHealthScore renders the score heading
    expect(screen.getByText("Salud del Email")).toBeInTheDocument();
  });

  it("renders health KPI cards", () => {
    mockUseMailHealth.mockReturnValue({ data: HEALTH_DATA, isLoading: false });
    const { container } = render(<MailEntregabilidadV2Tab period="30d" />);
    // "Entregabilidad" appears in HealthScore sub-scores and KPI card
    expect(container.textContent).toContain("Entregabilidad");
    expect(container.textContent).toContain("Tasa de Rebote");
  });
});

// =============================================================================
// Tab 6: Crecimiento
// =============================================================================
describe("MailCrecimientoTab", () => {
  it("shows loading spinner when data is loading", () => {
    mockUseMailGrowth.mockReturnValue({ data: undefined, isLoading: true });
    const { container } = render(<MailCrecimientoTab period="30d" />);
    expect(container.querySelector(".animate-spin")).toBeTruthy();
  });

  it("shows empty state when no data", () => {
    mockUseMailGrowth.mockReturnValue({ data: undefined, isLoading: false });
    render(<MailCrecimientoTab period="30d" />);
    expect(screen.getByText("Sin datos de crecimiento")).toBeInTheDocument();
  });

  it("renders KPI cards with growth data", () => {
    mockUseMailGrowth.mockReturnValue({ data: GROWTH_DATA, isLoading: false });
    render(<MailCrecimientoTab period="30d" />);
    expect(screen.getByText("Suscriptores Activos")).toBeInTheDocument();
    expect(screen.getByText("Nuevos Suscriptores")).toBeInTheDocument();
  });

  it("renders sources section when data present", () => {
    mockUseMailGrowth.mockReturnValue({ data: GROWTH_DATA, isLoading: false });
    render(<MailCrecimientoTab period="30d" />);
    expect(screen.getByText("Landing Page")).toBeInTheDocument();
  });
});
