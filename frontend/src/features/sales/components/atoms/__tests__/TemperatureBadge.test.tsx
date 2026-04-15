import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, it, expect } from "vitest";

import { TemperatureBadge } from "../TemperatureBadge";

describe("TemperatureBadge", () => {
  it('renders "Frío" label with blue classes for cold temperature', () => {
    const { container } = render(<TemperatureBadge temperature="cold" />);
    expect(screen.getByText("Frío")).toBeInTheDocument();
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("bg-blue-100");
    expect(badge.className).toContain("text-blue-700");
  });

  it('renders "Tibio" label with orange classes for warm temperature', () => {
    const { container } = render(<TemperatureBadge temperature="warm" />);
    expect(screen.getByText("Tibio")).toBeInTheDocument();
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("bg-orange-100");
    expect(badge.className).toContain("text-orange-700");
  });

  it('renders "Caliente" label with red classes for hot temperature', () => {
    const { container } = render(<TemperatureBadge temperature="hot" />);
    expect(screen.getByText("Caliente")).toBeInTheDocument();
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("bg-red-100");
    expect(badge.className).toContain("text-red-700");
  });

  it("merges custom className with the badge classes", () => {
    const { container } = render(<TemperatureBadge temperature="hot" className="extra-class" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("extra-class");
    expect(badge.className).toContain("bg-red-100");
  });
});
