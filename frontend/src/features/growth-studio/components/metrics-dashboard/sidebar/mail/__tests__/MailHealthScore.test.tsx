import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";

import { MailHealthScore } from "../MailHealthScore";

import type { EmailHealthScore } from "../../../../../types/mail-types";

const HEALTHY_SCORE: EmailHealthScore = {
  total: 85,
  subScores: [
    { area: "engagement", label: "Engagement", score: 90, color: "green" },
    { area: "entregabilidad", label: "Entregabilidad", score: 80, color: "green" },
    { area: "crecimiento", label: "Crecimiento", score: 75, color: "green" },
    { area: "contenido", label: "Contenido", score: 95, color: "green" },
  ],
};

const WARNING_SCORE: EmailHealthScore = {
  total: 55,
  subScores: [
    { area: "engagement", label: "Engagement", score: 60, color: "yellow" },
    { area: "entregabilidad", label: "Entregabilidad", score: 50, color: "yellow" },
    { area: "crecimiento", label: "Crecimiento", score: 45, color: "red" },
    { area: "contenido", label: "Contenido", score: 65, color: "yellow" },
  ],
};

const CRITICAL_SCORE: EmailHealthScore = {
  total: 30,
  subScores: [
    { area: "engagement", label: "Engagement", score: 25, color: "red" },
    { area: "entregabilidad", label: "Entregabilidad", score: 30, color: "red" },
    { area: "crecimiento", label: "Crecimiento", score: 35, color: "red" },
    { area: "contenido", label: "Contenido", score: 30, color: "red" },
  ],
};

describe("MailHealthScore", () => {
  it("renders the total score", () => {
    render(<MailHealthScore healthScore={HEALTHY_SCORE} />);
    expect(screen.getByText("85")).toBeInTheDocument();
  });

  it("renders all sub-score labels", () => {
    render(<MailHealthScore healthScore={HEALTHY_SCORE} />);
    expect(screen.getByText("Engagement")).toBeInTheDocument();
    expect(screen.getByText("Entregabilidad")).toBeInTheDocument();
    expect(screen.getByText("Crecimiento")).toBeInTheDocument();
    expect(screen.getByText("Contenido")).toBeInTheDocument();
  });

  it("applies green color for high scores (>=70)", () => {
    const { container } = render(<MailHealthScore healthScore={HEALTHY_SCORE} />);
    const scoreNumber = screen.getByText("85");
    expect(scoreNumber.className).toContain("emerald");
    // Sub-bars should also have green colors
    const bars = container.querySelectorAll('[role="meter"]');
    expect(bars.length).toBe(4);
  });

  it("applies amber color for medium scores (50-69)", () => {
    render(<MailHealthScore healthScore={WARNING_SCORE} />);
    const scoreNumber = screen.getByText("55");
    expect(scoreNumber.className).toContain("amber");
  });

  it("applies red color for low scores (<50)", () => {
    const { container } = render(<MailHealthScore healthScore={CRITICAL_SCORE} />);
    // The main score is the text-4xl element
    const mainScore = container.querySelector(".text-4xl");
    expect(mainScore).not.toBeNull();
    expect(mainScore!.textContent).toBe("30");
    expect(mainScore!.className).toContain("red");
  });

  it("renders section heading", () => {
    render(<MailHealthScore healthScore={HEALTHY_SCORE} />);
    expect(screen.getByText("Salud del Email")).toBeInTheDocument();
  });
});
