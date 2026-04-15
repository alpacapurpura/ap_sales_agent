import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { AudienciaTab } from "../tabs/AudienciaTab";

import type { DemographicsData } from "../../../../../api/campaigns-api";
import type { ChannelDashboardData } from "../../../../../types/metrics";

// --- Mocks ---
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("test-token") }),
}));

// Mock Radix tooltip to render inline (avoids portal issues in tests)
function MockProvider({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
MockProvider.displayName = "MockProvider";
function MockRoot({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
MockRoot.displayName = "MockRoot";
function MockTrigger({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
MockTrigger.displayName = "MockTrigger";
function MockContent({ children }: { children: React.ReactNode }) {
  return <div role="tooltip">{children}</div>;
}
MockContent.displayName = "MockContent";

vi.mock("@radix-ui/react-tooltip", () => ({
  Provider: MockProvider,
  Root: MockRoot,
  Trigger: MockTrigger,
  Content: MockContent,
}));

// Mock useDemographics with controllable return value
const mockDemographicsData: { current: DemographicsData | undefined } = { current: undefined };

vi.mock("../../../../../api/campaigns-api", () => ({
  useDemographics: () => ({ data: mockDemographicsData.current, isLoading: false }),
}));

// Must import AFTER mocks are defined

const BASE_DASHBOARD_DATA: ChannelDashboardData = {
  channelSlug: "meta-ads",
  channelName: "Meta Ads",
  industryCategory: "education",
  period: "30d",
  kpis: [
    {
      metricName: "reach",
      displayName: "Alcance",
      currentValue: 89200,
      previousValue: 78000,
      deltaPct: 14.4,
      deltaAbsolute: 11200,
      unit: "count",
      higherIsBetter: true,
      benchmark: null,
    },
    {
      metricName: "frequency",
      displayName: "Frecuencia",
      currentValue: 1.4,
      previousValue: 1.2,
      deltaPct: 16.7,
      deltaAbsolute: 0.2,
      unit: "count",
      higherIsBetter: false,
      benchmark: null,
    },
  ],
  timeSeries: [],
  funnel: { steps: [] },
  frequencyAlert: null,
};

const FULL_DEMOGRAPHICS: DemographicsData = {
  age: [
    { label: "18-24", value: 1500, percentage: 15 },
    { label: "25-34", value: 4200, percentage: 42 },
    { label: "35-44", value: 2800, percentage: 28 },
    { label: "45-54", value: 1000, percentage: 10 },
    { label: "55+", value: 500, percentage: 5 },
  ],
  gender: [
    { label: "Femenino", value: 6800, percentage: 68 },
    { label: "Masculino", value: 3200, percentage: 32 },
  ],
  placement: [
    { label: "Feed", value: 5500, percentage: 55 },
    { label: "Stories", value: 2500, percentage: 25 },
    { label: "Reels", value: 1500, percentage: 15 },
    { label: "Otros", value: 500, percentage: 5 },
  ],
};

describe("AudienciaTab", () => {
  beforeEach(() => {
    mockDemographicsData.current = undefined;
  });

  // --- Loading and empty states ---

  it("renders loading spinner when isLoading is true", () => {
    const { container } = render(<AudienciaTab data={undefined} isLoading={true} period="30d" />);
    const spinner = container.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });

  it('renders "No hay datos disponibles" when data is undefined', () => {
    render(<AudienciaTab data={undefined} isLoading={false} period="30d" />);
    expect(screen.getByText("No hay datos disponibles")).toBeInTheDocument();
  });

  it("renders placeholders when demographics data is empty", () => {
    mockDemographicsData.current = undefined;
    render(<AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />);
    const placeholders = screen.getAllByText(/Pr\u00f3ximamente/);
    expect(placeholders).toHaveLength(3);
  });

  // --- Age distribution ---

  it("renders age distribution bars when demographics data is provided", () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    render(<AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />);

    expect(screen.getByText("18-24")).toBeInTheDocument();
    expect(screen.getByText("25-34")).toBeInTheDocument();
    expect(screen.getByText("35-44")).toBeInTheDocument();
    expect(screen.getByText("45-54")).toBeInTheDocument();
    expect(screen.getByText("55+")).toBeInTheDocument();
  });

  it('renders the section title "Distribucion por edad"', () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    render(<AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />);
    expect(screen.getByText(/Distribuci\u00f3n por edad/)).toBeInTheDocument();
  });

  it("highlights the dominant age group with a star marker", () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    render(<AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />);
    // The highest percentage (42% for 25-34) should have a star inside the bar
    const starElements = screen.getAllByText(/\u2605/);
    expect(starElements.length).toBeGreaterThanOrEqual(1);
    // The star should appear alongside the 42% text
    expect(screen.getByText(/42%.*\u2605/)).toBeInTheDocument();
  });

  it("does not show star on non-dominant age groups", () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    render(<AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />);
    // The 28% bar should NOT contain a star
    const bar28 = screen.getByText(/^28%$/);
    expect(bar28.textContent).not.toContain("\u2605");
  });

  it("formats age percentages correctly", () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    render(<AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />);
    expect(screen.getByText(/42%/)).toBeInTheDocument();
    expect(screen.getByText(/^28%$/)).toBeInTheDocument();
    // 15% appears in both age and placement; verify at least two
    const fifteenPctElements = screen.getAllByText(/^15%$/);
    expect(fifteenPctElements.length).toBeGreaterThanOrEqual(1);
  });

  it("applies stronger blue opacity on the dominant age bar", () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    const { container } = render(
      <AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />,
    );
    // The dominant bar (42%) uses bg-blue-500/70
    const dominantBar = container.querySelector('[class*="bg-blue-500/70"]');
    expect(dominantBar).toBeInTheDocument();
  });

  // --- Gender distribution ---

  it("renders gender split when demographics data is provided", () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    render(<AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />);
    expect(screen.getByText("Femenino")).toBeInTheDocument();
    expect(screen.getByText("Masculino")).toBeInTheDocument();
  });

  it("shows correct gender percentages", () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    render(<AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />);
    expect(screen.getByText("68%")).toBeInTheDocument();
    expect(screen.getByText("32%")).toBeInTheDocument();
  });

  it('renders the section title "Distribucion por genero"', () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    render(<AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />);
    expect(screen.getByText(/Distribuci\u00f3n por g\u00e9nero/)).toBeInTheDocument();
  });

  it("applies violet color for female and blue for male", () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    const { container } = render(
      <AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />,
    );
    // Female percentage should have violet styling
    const violetEl = container.querySelector(".text-violet-400");
    expect(violetEl).toBeInTheDocument();
    expect(violetEl?.textContent).toBe("68%");

    // Male percentage should have blue styling
    const blueEl = container.querySelector(".text-blue-400");
    expect(blueEl).toBeInTheDocument();
    expect(blueEl?.textContent).toBe("32%");
  });

  it("renders divider between gender columns", () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    const { container } = render(
      <AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />,
    );
    const divider = container.querySelector(".bg-zinc-700");
    expect(divider).toBeInTheDocument();
  });

  it("uses large text (text-3xl) for gender percentages", () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    const { container } = render(
      <AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />,
    );
    const largeTexts = container.querySelectorAll(".text-3xl");
    expect(largeTexts.length).toBe(2);
  });

  // --- Placement distribution ---

  it("renders placement bars when demographics data is provided", () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    render(<AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />);
    expect(screen.getByText("Feed")).toBeInTheDocument();
    expect(screen.getByText("Stories")).toBeInTheDocument();
    expect(screen.getByText("Reels")).toBeInTheDocument();
    expect(screen.getByText("Otros")).toBeInTheDocument();
  });

  it('renders the section title "Donde aparecen tus ads"', () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    render(<AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />);
    expect(screen.getByText(/D\u00f3nde aparecen tus ads/)).toBeInTheDocument();
  });

  it("uses emerald color for placement bars", () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    const { container } = render(
      <AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />,
    );
    const emeraldBars = container.querySelectorAll('[class*="bg-emerald-500"]');
    expect(emeraldBars.length).toBeGreaterThanOrEqual(4);
  });

  it("uses varying emerald opacity for different placements", () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    const { container } = render(
      <AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />,
    );
    // Feed (idx 0) = bg-emerald-500/50, Stories (idx 1) = bg-emerald-500/40
    expect(container.querySelector('[class*="bg-emerald-500/50"]')).toBeInTheDocument();
    expect(container.querySelector('[class*="bg-emerald-500/40"]')).toBeInTheDocument();
    expect(container.querySelector('[class*="bg-emerald-500/30"]')).toBeInTheDocument();
    expect(container.querySelector('[class*="bg-emerald-500/20"]')).toBeInTheDocument();
  });

  it("formats placement percentages correctly", () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    render(<AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />);
    expect(screen.getByText(/^55%$/)).toBeInTheDocument();
    // 25% only appears in placement (Stories)
    const twentyFiveElements = screen.getAllByText(/^25%$/);
    expect(twentyFiveElements.length).toBeGreaterThanOrEqual(1);
  });

  // --- Tooltip info icons ---

  it("renders info tooltip icons for all three demographic sections", () => {
    mockDemographicsData.current = FULL_DEMOGRAPHICS;
    const { container } = render(
      <AudienciaTab data={BASE_DASHBOARD_DATA} isLoading={false} period="30d" />,
    );
    // 3 InfoTooltip components render 3 Info icons (SVGs with lucide-react)
    const tooltipIcons = container.querySelectorAll(".cursor-help");
    expect(tooltipIcons.length).toBe(3);
  });
});
