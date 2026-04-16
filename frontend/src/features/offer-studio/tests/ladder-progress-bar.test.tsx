import { render, screen, act } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { LadderProgressBar } from "../components/dashboard/LadderProgressBar";
import { OfferValueLevel } from "../types";

describe("LadderProgressBar", () => {
  it("renders all 5 level segments", () => {
    render(
      <LadderProgressBar filledGroups={new Set<OfferValueLevel>()} score="vacia" percentage={0} />,
    );
    // Each step renders a tooltip with the level label
    expect(screen.getByText("Ladder")).toBeInTheDocument();
    expect(screen.getByText("0/5")).toBeInTheDocument();
  });

  it("shows filled count matching filledGroups size", () => {
    const filled = new Set([OfferValueLevel.LEAD_MAGNET, OfferValueLevel.TRANSFORMACION]);
    render(<LadderProgressBar filledGroups={filled} score="creciendo" percentage={40} />);
    expect(screen.getByText("2/5")).toBeInTheDocument();
    expect(screen.getByText("40")).toBeInTheDocument();
  });

  it("renders with all groups filled", () => {
    const filled = new Set([
      OfferValueLevel.LEAD_MAGNET,
      OfferValueLevel.ACTIVACION,
      OfferValueLevel.TRANSFORMACION,
      OfferValueLevel.MAXIMIZACION,
      OfferValueLevel.CORPORATIVO,
    ]);
    render(<LadderProgressBar filledGroups={filled} score="avanzada" percentage={100} />);
    expect(screen.getByText("5/5")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
  });
});
