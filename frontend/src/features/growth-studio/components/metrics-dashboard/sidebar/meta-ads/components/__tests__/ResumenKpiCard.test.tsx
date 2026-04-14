import React from "react";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TooltipProvider } from "@/components/ui/tooltip";

// The card uses formatMoney, which pulls from tenant context transitively via
// lib/format-money. format-money is a pure function — no mock needed.

import { ResumenKpiCard } from "../ResumenKpiCard";
import type { ResumenKpiCard as ResumenKpiCardData } from "../../hooks/useResumenViewData";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeCard(overrides: Partial<ResumenKpiCardData> = {}): ResumenKpiCardData {
  return {
    key: "spend",
    label: "Inversión",
    tooltipKey: "spend",
    unavailableTooltipKey: null,
    value: 1234.56,
    currency: "PEN",
    unit: "currency",
    higherIsBetter: null,
    deltaPct: null,
    kind: "value",
    ...overrides,
  };
}

function renderCard(card: ResumenKpiCardData, onCtaClick = vi.fn()) {
  return render(
    <TooltipProvider delayDuration={0}>
      <ResumenKpiCard card={card} onCtaClick={onCtaClick} />
    </TooltipProvider>,
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("ResumenKpiCard", () => {
  it("renders label and a formatted currency value", () => {
    renderCard(makeCard());
    expect(screen.getByText("Inversión")).toBeInTheDocument();
    // formatMoney('PEN') uses es locale — just assert the number is rendered
    expect(screen.getByText(/1[.,]234[.,]56/)).toBeInTheDocument();
  });

  it("renders a positive delta with the upward trend for higher-is-better metrics", () => {
    renderCard(
      makeCard({
        key: "roas",
        label: "ROAS",
        tooltipKey: "roas",
        unit: "ratio",
        value: 2.4,
        higherIsBetter: true,
        deltaPct: 12.3,
      }),
    );
    expect(screen.getByText(/12\.3% vs ant\./)).toBeInTheDocument();
    // tabular-nums value
    expect(screen.getByText(/2\.40x/)).toBeInTheDocument();
  });

  it('renders a negative delta with downward trend for lower-is-better metrics as "good"', () => {
    renderCard(
      makeCard({
        key: "cpa",
        label: "CPA",
        tooltipKey: "cpa",
        unit: "currency",
        value: 10,
        higherIsBetter: false,
        deltaPct: -5.5,
      }),
    );
    const deltaEl = screen.getByText(/5\.5% vs ant\./);
    expect(deltaEl).toBeInTheDocument();
    // lower-is-better + negative delta → emerald tone class present
    expect(deltaEl.className).toMatch(/emerald/);
  });

  it('renders "—" with Info icon for unavailable cards and omits the delta', () => {
    renderCard(
      makeCard({
        key: "reach",
        label: "Alcance",
        tooltipKey: "reach_all",
        unavailableTooltipKey: "unavailable_generic",
        value: null,
        unit: "count",
        higherIsBetter: true,
        deltaPct: 10, // should be suppressed
        kind: "unavailable",
      }),
    );
    const group = screen.getByRole("group");
    expect(within(group).getByText("—")).toBeInTheDocument();
    expect(screen.getByTestId("kpi-unavailable-icon")).toBeInTheDocument();
    expect(within(group).queryByText(/vs ant\./)).toBeNull();
  });

  it('uses the "dato no disponible" aria-label for the unavailable state', () => {
    renderCard(
      makeCard({
        key: "reach",
        label: "Alcance",
        tooltipKey: "reach_all",
        unavailableTooltipKey: null,
        value: null,
        unit: "count",
        higherIsBetter: true,
        deltaPct: null,
        kind: "unavailable",
      }),
    );
    const group = screen.getByRole("group");
    expect(group.getAttribute("aria-label")).toMatch(/Alcance: dato no disponible/);
  });

  it("embeds the spoken value in the aria-label for a normal card", () => {
    renderCard(
      makeCard({
        key: "ctr",
        label: "CTR",
        tooltipKey: "ctr",
        unit: "percentage",
        value: 2.45,
        higherIsBetter: true,
        deltaPct: 0.6,
      }),
    );
    const group = screen.getByRole("group");
    const label = group.getAttribute("aria-label") ?? "";
    expect(label).toMatch(/CTR: 2\.45 por ciento/);
    expect(label).toMatch(/variación 0\.6% respecto al período anterior/);
  });

  it("shows tooltip content on hover", async () => {
    const user = userEvent.setup();
    renderCard(
      makeCard({
        key: "ctr",
        label: "CTR",
        tooltipKey: "ctr",
        unit: "percentage",
        value: 2.4,
        higherIsBetter: true,
      }),
    );
    const trigger = screen.getByRole("group");
    await user.hover(trigger);
    const tooltip = await screen.findByRole("tooltip");
    expect(tooltip).toBeInTheDocument();
    // Shadcn tooltip has title + body — verify the title is rendered
    expect(within(tooltip).getByText(/CTR/)).toBeInTheDocument();
  });

  it('renders the CTA variant with an "Asignar ahora" button that fires the callback', async () => {
    const onCtaClick = vi.fn();
    const user = userEvent.setup();
    renderCard(
      makeCard({
        key: "action",
        label: "",
        tooltipKey: "",
        unavailableTooltipKey: null,
        value: null,
        unit: "count",
        higherIsBetter: null,
        deltaPct: null,
        kind: "cta",
      }),
      onCtaClick,
    );
    expect(screen.getByText("Acción requerida")).toBeInTheDocument();
    const btn = screen.getByRole("button", { name: /Asignar ahora/i });
    await user.click(btn);
    expect(onCtaClick).toHaveBeenCalledTimes(1);
  });
});
