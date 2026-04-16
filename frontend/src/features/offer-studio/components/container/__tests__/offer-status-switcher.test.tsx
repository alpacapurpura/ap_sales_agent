import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi } from "vitest";

import { TooltipProvider } from "@/components/ui/tooltip";

import { OfferStatusSwitcher } from "../OfferStatusSwitcher";

function renderWithTooltip(ui: React.ReactElement) {
  return render(<TooltipProvider>{ui}</TooltipProvider>);
}

describe("OfferStatusSwitcher", () => {
  it("renders the three visible lifecycle pills", () => {
    renderWithTooltip(
      <OfferStatusSwitcher currentStatus="draft" onTransitionRequested={vi.fn()} />,
    );
    expect(screen.getByRole("tab", { name: /Borrador/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Activa/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Pausada/i })).toBeInTheDocument();
  });

  it("marks the current status pill as selected", () => {
    renderWithTooltip(
      <OfferStatusSwitcher currentStatus="active" onTransitionRequested={vi.fn()} />,
    );
    expect(screen.getByRole("tab", { name: /Activa/i, selected: true })).toBeInTheDocument();
  });

  it("disables the Pausada pill when transitioning from Borrador (not allowed)", () => {
    renderWithTooltip(
      <OfferStatusSwitcher currentStatus="draft" onTransitionRequested={vi.fn()} />,
    );
    const paused = screen.getByRole("tab", { name: /Pausada/i });
    expect(paused).toBeDisabled();
  });

  it("calls onTransitionRequested when clicking a different status", () => {
    const onTransitionRequested = vi.fn();
    renderWithTooltip(
      <OfferStatusSwitcher currentStatus="draft" onTransitionRequested={onTransitionRequested} />,
    );
    fireEvent.click(screen.getByRole("tab", { name: /Activa/i }));
    expect(onTransitionRequested).toHaveBeenCalledWith("active");
  });

  it("does not call onTransitionRequested when clicking the current status", () => {
    const onTransitionRequested = vi.fn();
    renderWithTooltip(
      <OfferStatusSwitcher currentStatus="active" onTransitionRequested={onTransitionRequested} />,
    );
    fireEvent.click(screen.getByRole("tab", { name: /Activa/i }));
    expect(onTransitionRequested).not.toHaveBeenCalled();
  });

  it("disables all pills when the offer is archived", () => {
    renderWithTooltip(
      <OfferStatusSwitcher currentStatus="archived" onTransitionRequested={vi.fn()} />,
    );
    expect(screen.getByRole("tab", { name: /Borrador/i })).toBeDisabled();
    expect(screen.getByRole("tab", { name: /Activa/i })).toBeDisabled();
    expect(screen.getByRole("tab", { name: /Pausada/i })).toBeDisabled();
  });
});
