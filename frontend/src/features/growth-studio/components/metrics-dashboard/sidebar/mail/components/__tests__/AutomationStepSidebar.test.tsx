import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { AutomationStepSidebar } from "../AutomationStepSidebar";

import type { AutomationStep } from "../../../../../../types/mail-types";

function buildStep(overrides: Partial<AutomationStep> = {}): AutomationStep {
  return {
    stepId: "s1",
    stepNumber: 1,
    type: "email",
    subject: "Test Subject",
    fromName: "Visionarias",
    emailsSent: 10,
    uniqueOpens: 8,
    openRate: 80,
    uniqueClicks: 4,
    clickRate: 40,
    unsubscribes: 1,
    bounces: 0,
    screenshotUrl: null,
    previewUrl: null,
    delayValue: null,
    delayUnit: null,
    ...overrides,
  };
}

describe("AutomationStepSidebar", () => {
  it("does not render content when step is null", () => {
    const { container } = render(
      <AutomationStepSidebar
        step={null}
        automationName="Test automation"
        totalSteps={3}
        previousStep={null}
        onClose={() => {}}
      />,
    );
    // Panel is closed — no visible step data
    expect(container.textContent).not.toContain("Test Subject");
  });

  it("renders step subject and context in header", () => {
    const step = buildStep({ subject: "Mi email", stepNumber: 2 });
    render(
      <AutomationStepSidebar
        step={step}
        automationName="BIENVENIDA"
        totalSteps={4}
        previousStep={null}
        onClose={() => {}}
      />,
    );
    // Subject is shown in both the header title and the details row,
    // so getAllByText returns multiple matches.
    expect(screen.getAllByText("Mi email").length).toBeGreaterThan(0);
    expect(screen.getByText(/Email 2 de 4/i)).toBeInTheDocument();
    expect(screen.getByText(/BIENVENIDA/)).toBeInTheDocument();
  });

  it("renders all six metric boxes (enviados, abiertos, clicks, open/click/ctor)", () => {
    const step = buildStep({
      emailsSent: 100,
      uniqueOpens: 80,
      uniqueClicks: 20,
      openRate: 80,
      clickRate: 20,
    });
    render(
      <AutomationStepSidebar
        step={step}
        automationName="Test"
        totalSteps={1}
        previousStep={null}
        onClose={() => {}}
      />,
    );
    expect(screen.getByText("100")).toBeInTheDocument(); // enviados
    expect(screen.getByText("80")).toBeInTheDocument(); // abiertos
    expect(screen.getByText("20")).toBeInTheDocument(); // clicks
    // Rates appear in both the metric box and the benchmarks row — use getAllByText.
    expect(screen.getAllByText("80.0%").length).toBeGreaterThan(0); // open rate
    expect(screen.getAllByText("20.0%").length).toBeGreaterThan(0); // click rate
    // CTOR = clicks/opens = 20/80 = 25%
    expect(screen.getAllByText("25.0%").length).toBeGreaterThan(0);
  });

  it('renders "ver email completo" link when previewUrl exists', () => {
    const step = buildStep({ previewUrl: "https://preview.example" });
    render(
      <AutomationStepSidebar
        step={step}
        automationName="Test"
        totalSteps={1}
        previousStep={null}
        onClose={() => {}}
      />,
    );
    const link = screen.getByRole("link", { name: /email completo/i });
    expect(link).toHaveAttribute("href", "https://preview.example");
  });

  it("renders AI diagnosis when step has issues", () => {
    const step = buildStep({ openRate: 70, clickRate: 0.5, emailsSent: 100 });
    render(
      <AutomationStepSidebar
        step={step}
        automationName="Test"
        totalSteps={1}
        previousStep={null}
        onClose={() => {}}
      />,
    );
    expect(screen.getByText(/CTA/i)).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", () => {
    const handler = vi.fn();
    const step = buildStep();
    render(
      <AutomationStepSidebar
        step={step}
        automationName="Test"
        totalSteps={1}
        previousStep={null}
        onClose={handler}
      />,
    );
    const closeBtn = screen.getByRole("button", { name: /cerrar/i });
    closeBtn.click();
    expect(handler).toHaveBeenCalled();
  });
});
