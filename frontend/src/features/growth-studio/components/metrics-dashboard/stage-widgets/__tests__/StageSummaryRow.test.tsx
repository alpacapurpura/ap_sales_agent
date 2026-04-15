import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import { StageSummaryRow } from "../StageSummaryRow";

import type { StageSummary, StageId } from "@/features/growth-studio/types/metrics";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockNavigate = vi.fn();

vi.mock("next/navigation", () => ({
  usePathname: () => "/test-tenant/growth-studio/atraccion-captura",
}));

vi.mock("@/components/shared/navigation", () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

// ── Test Data ────────────────────────────────────────────────────────────────

function createStages(): StageSummary[] {
  return [
    {
      id: "ATRACCION_CAPTURA" as StageId,
      order: 0,
      label: "Atracción + Captura",
      description: "Attraction and capture",
      mainKpi: { label: "Visitantes", value: 45000 },
      secondaryKpi: { label: "Canales", value: 8 },
      hasDetail: true,
    },
    {
      id: "NUTRICION_OPORTUNIDAD" as StageId,
      order: 1,
      label: "Nutrición + Oportunidad",
      description: "Nurture and opportunity",
      mainKpi: { label: "MQLs", value: 3200 },
      secondaryKpi: { label: "Conversion", value: 37.6, unit: "%" },
      hasDetail: true,
    },
    {
      id: "VENTAS" as StageId,
      order: 2,
      label: "Ventas",
      description: "Sales",
      mainKpi: { label: "Revenue", value: 1260000, unit: "$" },
      secondaryKpi: { label: "Conversion", value: 52.9, unit: "%" },
      hasDetail: true,
    },
    {
      id: "ADOPCION" as StageId,
      order: 3,
      label: "Adopción",
      description: "Adoption health",
      mainKpi: { label: "Salud", value: 88.9, unit: "%" },
      secondaryKpi: { label: "Activos", value: 400 },
      hasDetail: true,
    },
    {
      id: "EXPANSION_EVANGELIZACION" as StageId,
      order: 4,
      label: "Expansión + Evangelización",
      description: "Expansion and evangelization",
      mainKpi: { label: "Net MRR", value: 42000, unit: "$" },
      secondaryKpi: { label: "Churn", value: 2.3, unit: "%" },
      hasDetail: true,
    },
  ];
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe("StageSummaryRow", () => {
  it("renders all 5 stage cards", () => {
    const stages = createStages();
    render(<StageSummaryRow stages={stages} activeStage={null} />);

    expect(screen.getByText(/Atracción \+ Captura/i)).toBeInTheDocument();
    expect(screen.getByText(/Nutrición \+ Oportunidad/i)).toBeInTheDocument();
    expect(screen.getByText(/Ventas/i)).toBeInTheDocument();
    expect(screen.getByText(/Adopción/i)).toBeInTheDocument();
    expect(screen.getByText(/Expansión \+ Evangelización/i)).toBeInTheDocument();
  });

  it("passes isActive=true to the correct stage card based on activeStage", () => {
    const stages = createStages();
    const { container } = render(
      <StageSummaryRow stages={stages} activeStage={"VENTAS" as StageId} />,
    );

    // The active card should have the bg-white/15 styling class
    const activeCards = container.querySelectorAll('[class*="bg-white/15"]');
    expect(activeCards.length).toBe(1);

    // The inactive cards should have bg-slate-900 styling
    const inactiveCards = container.querySelectorAll('[class*="bg-slate-900"]');
    expect(inactiveCards.length).toBe(4);
  });

  it("passes isLoading to the correct stage from loadingMap", () => {
    const stages = createStages();
    render(
      <StageSummaryRow
        stages={stages}
        activeStage={null}
        loadingMap={{ VENTAS: true } as Partial<Record<StageId, boolean>>}
      />,
    );

    // Ventas is loading -> its mainKpi value should not be shown
    expect(screen.queryByText(/1,260,000/)).not.toBeInTheDocument();

    // Other stages' mainKpi values should still be visible
    expect(screen.getByText("45k")).toBeInTheDocument(); // Atraccion
  });

  it("passes isMock to the correct stage from mockMap", () => {
    const stages = createStages();
    render(
      <StageSummaryRow
        stages={stages}
        activeStage={null}
        mockMap={{ ADOPCION: true } as Partial<Record<StageId, boolean>>}
      />,
    );

    // Only one "simulado" badge should be shown (for Adopcion)
    const simuladoBadges = screen.getAllByText("simulado");
    expect(simuladoBadges).toHaveLength(1);
  });

  it("navigates to the correct route when a stage card is clicked", async () => {
    const stages = createStages();
    const user = userEvent.setup();
    render(<StageSummaryRow stages={stages} activeStage={null} />);

    // Click on "Ventas" stage
    const ventasCard = screen.getByText(/Ventas/i).closest('div[class*="cursor-pointer"]');
    expect(ventasCard).toBeTruthy();
    await user.click(ventasCard!);

    // STAGE_TO_SLUG maps VENTAS -> 'ventas'
    // tenantId is derived from pathname: '/test-tenant/...' -> 'test-tenant'
    expect(mockNavigate).toHaveBeenCalledWith("/test-tenant/growth-studio/ventas");
  });

  it("renders mainKpi values for each stage card", () => {
    const stages = createStages();
    render(<StageSummaryRow stages={stages} activeStage={null} />);

    // Atraccion: 45000 -> "45k"
    expect(screen.getByText("45k")).toBeInTheDocument();
    // Nutricion: 3200 -> "3.2k"
    expect(screen.getByText("3.2k")).toBeInTheDocument();
    // Adopcion: 88.9 with unit='%' -> "88.9%"
    expect(screen.getByText("88.9%")).toBeInTheDocument();
  });

  it("renders with no activeStage (null)", () => {
    const stages = createStages();
    const { container } = render(<StageSummaryRow stages={stages} activeStage={null} />);

    // No active cards should have the white glass overlay
    const activeCards = container.querySelectorAll('[class*="bg-white/15"]');
    expect(activeCards.length).toBe(0);
  });
});
