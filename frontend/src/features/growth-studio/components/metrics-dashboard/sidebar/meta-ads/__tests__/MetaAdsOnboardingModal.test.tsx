import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { MetaAdsOnboardingModal } from "../MetaAdsOnboardingModal";

const CAMPAIGNS = [
  { externalId: "camp-1", name: "Sales Master", objective: "OUTCOME_SALES" },
  { externalId: "camp-2", name: "Tráfico", objective: "OUTCOME_TRAFFIC" },
];

describe("MetaAdsOnboardingModal", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders Step 1 (best practices) by default when open", () => {
    render(
      <MetaAdsOnboardingModal
        open={true}
        onOpenChange={vi.fn()}
        campaigns={CAMPAIGNS}
        onAssignNow={vi.fn()}
      />,
    );
    expect(screen.getByText(/Cómo organizar tus campañas/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Siguiente/i })).toBeInTheDocument();
  });

  it("advances to Step 2 on Siguiente click and shows campaigns list", () => {
    render(
      <MetaAdsOnboardingModal
        open={true}
        onOpenChange={vi.fn()}
        campaigns={CAMPAIGNS}
        onAssignNow={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Siguiente/i }));
    expect(screen.getByText(/Sales Master/)).toBeInTheDocument();
    // "Tráfico" appears as both the campaign name and the objective badge — both OK.
    expect(screen.getAllByText(/Tráfico/).length).toBeGreaterThan(0);
  });

  it('Step 2 "Asociar ahora" calls onAssignNow and closes', () => {
    const onAssignNow = vi.fn();
    const onOpenChange = vi.fn();
    render(
      <MetaAdsOnboardingModal
        open={true}
        onOpenChange={onOpenChange}
        campaigns={CAMPAIGNS}
        onAssignNow={onAssignNow}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Siguiente/i }));
    fireEvent.click(screen.getByRole("button", { name: /Asociar ahora/i }));
    expect(onAssignNow).toHaveBeenCalled();
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('Step 2 "Más tarde" advances to step 3', () => {
    render(
      <MetaAdsOnboardingModal
        open={true}
        onOpenChange={vi.fn()}
        campaigns={CAMPAIGNS}
        onAssignNow={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Siguiente/i }));
    fireEvent.click(screen.getByRole("button", { name: /Más tarde/i }));
    expect(screen.getByText(/Entendido/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Cerrar/i })).toBeInTheDocument();
  });

  it("closing persists localStorage key", () => {
    const onOpenChange = vi.fn();
    render(
      <MetaAdsOnboardingModal
        open={true}
        onOpenChange={onOpenChange}
        campaigns={CAMPAIGNS}
        onAssignNow={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Siguiente/i }));
    fireEvent.click(screen.getByRole("button", { name: /Más tarde/i }));
    fireEvent.click(screen.getByRole("button", { name: /Cerrar/i }));
    expect(localStorage.getItem("meta-ads-onboarding-dismissed")).toBe("1");
  });

  it("does not render when open=false", () => {
    render(
      <MetaAdsOnboardingModal
        open={false}
        onOpenChange={vi.fn()}
        campaigns={CAMPAIGNS}
        onAssignNow={vi.fn()}
      />,
    );
    expect(screen.queryByText(/Cómo organizar/i)).toBeNull();
  });
});
