import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StageCard } from "../StageCard";
import type { StageSummary, StageId } from "@/features/growth-studio/types/metrics";

describe("StageCard", () => {
  const baseSummary: StageSummary = {
    id: "ATRACCION" as StageId,
    order: 0,
    label: "Atracción",
    description: "Total visitors attracted to your content",
    mainKpi: { label: "Visitantes", value: 1250 },
    secondaryKpi: { label: "Conversion", value: 18.9, unit: "%" },
    hasDetail: true,
  };

  it("displays the stage label", () => {
    render(<StageCard stage={baseSummary} isActive={false} onClick={() => {}} />);

    expect(screen.getByText(/atracción/i)).toBeInTheDocument();
  });

  it("displays formatted mainKpi value (1250 -> 1.3k)", () => {
    render(<StageCard stage={baseSummary} isActive={false} onClick={() => {}} />);

    // formatKpiValue: 1250 >= 1000 -> (1250/1000).toFixed(1) = "1.3" (JS rounds 1.25 up) -> "1.3k"
    expect(screen.getByText("1.3k")).toBeInTheDocument();
  });

  it("displays the mainKpi label", () => {
    render(<StageCard stage={baseSummary} isActive={false} onClick={() => {}} />);

    expect(screen.getByText("Visitantes")).toBeInTheDocument();
  });

  it("displays currency-formatted mainKpi when unit is $", () => {
    const currencySummary: StageSummary = {
      ...baseSummary,
      mainKpi: { label: "Revenue", value: 1260000, unit: "$" },
    };
    render(<StageCard stage={currencySummary} isActive={false} onClick={() => {}} />);

    // formatKpiValue with unit='$' uses Intl.NumberFormat for MXN
    expect(screen.getByText(/1,260,000/)).toBeInTheDocument();
  });

  it("displays percentage-formatted mainKpi when unit is %", () => {
    const pctSummary: StageSummary = {
      ...baseSummary,
      mainKpi: { label: "Salud", value: 88.9, unit: "%" },
    };
    render(<StageCard stage={pctSummary} isActive={false} onClick={() => {}} />);

    expect(screen.getByText("88.9%")).toBeInTheDocument();
  });

  it("displays string mainKpi values as-is", () => {
    const stringSummary: StageSummary = {
      ...baseSummary,
      mainKpi: { label: "Revenue", value: "$4,200 (~$220 USD)" },
    };
    render(<StageCard stage={stringSummary} isActive={false} onClick={() => {}} />);

    expect(screen.getByText("$4,200 (~$220 USD)")).toBeInTheDocument();
  });

  it("calls onClick when the card is clicked", async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(<StageCard stage={baseSummary} isActive={false} onClick={handleClick} />);

    // The card is the root div with onClick
    const card = screen.getByText(/atracción/i).closest('div[class*="cursor-pointer"]');
    expect(card).toBeTruthy();
    await user.click(card!);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("shows loading skeletons when isLoading is true", () => {
    render(<StageCard stage={baseSummary} isActive={false} onClick={() => {}} isLoading={true} />);

    // When loading, the mainKpi value and label should NOT be visible
    expect(screen.queryByText("1.3k")).not.toBeInTheDocument();
    expect(screen.queryByText("Visitantes")).not.toBeInTheDocument();

    // Stage label is still visible during loading
    expect(screen.getByText(/atracción/i)).toBeInTheDocument();
  });

  it('shows "simulado" badge when isMock is true', () => {
    render(<StageCard stage={baseSummary} isActive={false} onClick={() => {}} isMock={true} />);

    expect(screen.getByText("simulado")).toBeInTheDocument();
  });

  it('does not show "simulado" badge when isMock is false', () => {
    render(<StageCard stage={baseSummary} isActive={false} onClick={() => {}} isMock={false} />);

    expect(screen.queryByText("simulado")).not.toBeInTheDocument();
  });

  it('does not show "simulado" badge when isLoading is true even if isMock is true', () => {
    render(
      <StageCard
        stage={baseSummary}
        isActive={false}
        onClick={() => {}}
        isLoading={true}
        isMock={true}
      />,
    );

    // isMock && !isLoading condition is false when isLoading=true
    expect(screen.queryByText("simulado")).not.toBeInTheDocument();
  });

  it("applies active state styling when isActive is true", () => {
    const { container } = render(
      <StageCard stage={baseSummary} isActive={true} onClick={() => {}} />,
    );

    // Active state adds bg-white/15 class
    const activeDiv = container.querySelector('[class*="bg-white/15"]');
    expect(activeDiv).toBeTruthy();
  });

  it("applies inactive state styling when isActive is false", () => {
    const { container } = render(
      <StageCard stage={baseSummary} isActive={false} onClick={() => {}} />,
    );

    // Inactive state adds bg-slate-900/95 class
    const inactiveDiv = container.querySelector('[class*="bg-slate-900"]');
    expect(inactiveDiv).toBeTruthy();
  });

  it("formats large numbers with M suffix (>= 1,000,000)", () => {
    const largeSummary: StageSummary = {
      ...baseSummary,
      mainKpi: { label: "Impressions", value: 2500000 },
    };
    render(<StageCard stage={largeSummary} isActive={false} onClick={() => {}} />);

    expect(screen.getByText("2.5M")).toBeInTheDocument();
  });
});
