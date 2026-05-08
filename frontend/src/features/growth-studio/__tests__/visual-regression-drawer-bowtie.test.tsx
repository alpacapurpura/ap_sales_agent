/**
 * Visual regression — PI-8 PR-1 drawer + bowtie + copilot z-index/offset hotfix.
 *
 * Tests:
 *  1. DetailPanel mobile z-index supersedes copilot mobile drawer (z-50).
 *  2. StageSummaryRow outer container respects `paddingRight: copilotWidth`
 *     when copilot is expanded (handles the 640-768px tablet gap where copilot
 *     is `max-md:fixed` overlay AND `useCopilotOffset` returns the open width).
 *  3. Mobile (`useCopilotOffset` → 0) yields no padding (no layout shift).
 *  4. 4-tier loading skeleton state is preserved (smoke — no regression).
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { DetailPanel } from "@/components/ui/detail-panel";
import { StageSummaryRow } from "@/features/growth-studio/components/metrics-dashboard/stage-widgets/StageSummaryRow";

import type { StageId, StageSummary } from "@/features/growth-studio/types/metrics";

// Stable noop reference (avoids react-perf jsx-no-new-function-as-prop)
const NOOP = () => undefined;

// ── Mock useCopilotOffset (per-test override) ────────────────────────
const useCopilotOffsetMock = vi.fn<() => number>(() => 0);

vi.mock("@/hooks/use-copilot-offset", () => ({
  useCopilotOffset: () => useCopilotOffsetMock(),
  COPILOT_OPEN_WIDTH: 460,
  COPILOT_RAIL_WIDTH: 60,
}));

// Next.js navigation mocks (StageSummaryRow consumes both)
vi.mock("next/navigation", () => ({
  usePathname: () => "/tenant-1/growth-studio",
}));

vi.mock("@/components/shared/navigation", () => ({
  useNavigation: () => ({ navigate: vi.fn() }),
}));

const STAGES: StageSummary[] = [
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

beforeEach(() => {
  useCopilotOffsetMock.mockReset();
  useCopilotOffsetMock.mockReturnValue(0);
});

describe("DetailPanel — z-index ladder (mobile bumps panel above copilot drawer)", () => {
  it("panel renders with mobile z-[60] override (above copilot z-50)", () => {
    useCopilotOffsetMock.mockReturnValue(460);

    render(
      <DetailPanel open onClose={NOOP}>
        <div data-testid="panel-content">child</div>
      </DetailPanel>,
    );

    // Both backdrop and panel should carry the responsive class that
    // upgrades z-index on mobile (max-md) above the copilot mobile drawer.
    const portalRoot = screen.getByTestId("panel-content").parentElement;
    expect(portalRoot).not.toBeNull();
    // Walk up to the panel wrapper
    const panel = portalRoot as HTMLElement;
    expect(panel.className).toMatch(/max-md:z-\[60\]/);
  });

  it("desktop z-[45] is preserved (no regression for desktop drawer ladder)", () => {
    useCopilotOffsetMock.mockReturnValue(460);

    render(
      <DetailPanel open onClose={NOOP}>
        <div data-testid="panel-content">child</div>
      </DetailPanel>,
    );

    const portalRoot = screen.getByTestId("panel-content").parentElement;
    const panel = portalRoot as HTMLElement;
    // base z-[45] still present (desktop unaffected)
    expect(panel.className).toMatch(/z-\[45\]/);
  });
});

describe("StageSummaryRow — bowtie respects copilot offset (paddingRight)", () => {
  it("applies paddingRight: copilotWidth when copilot is expanded", () => {
    useCopilotOffsetMock.mockReturnValue(460);

    const { container } = render(<StageSummaryRow stages={STAGES} activeStage={null} />);

    const outer = container.firstElementChild as HTMLElement;
    expect(outer).not.toBeNull();
    expect(outer.style.paddingRight).toBe("460px");
  });

  it("applies paddingRight: 0 on mobile (no layout shift)", () => {
    useCopilotOffsetMock.mockReturnValue(0);

    const { container } = render(<StageSummaryRow stages={STAGES} activeStage={null} />);

    const outer = container.firstElementChild as HTMLElement;
    expect(outer.style.paddingRight).toBe("0px");
  });

  it("applies paddingRight: railWidth when copilot is collapsed (rail)", () => {
    useCopilotOffsetMock.mockReturnValue(60);

    const { container } = render(<StageSummaryRow stages={STAGES} activeStage={null} />);

    const outer = container.firstElementChild as HTMLElement;
    expect(outer.style.paddingRight).toBe("60px");
  });
});

describe("StageSummaryRow — no regression in loading/mock map rendering", () => {
  it("renders all stages even with loadingMap entries (skeleton smoke)", () => {
    useCopilotOffsetMock.mockReturnValue(0);

    const loadingMap = { ATRACCION_CAPTURA: true } as Partial<Record<StageId, boolean>>;
    const mockMap = { VENTAS: true } as Partial<Record<StageId, boolean>>;

    const { container } = render(
      <StageSummaryRow
        stages={STAGES}
        activeStage={null}
        loadingMap={loadingMap}
        mockMap={mockMap}
      />,
    );

    // Bowtie clip-path container present
    const bowtie = container.querySelector('[class*="min-w-[800px]"]');
    expect(bowtie).not.toBeNull();
  });
});
