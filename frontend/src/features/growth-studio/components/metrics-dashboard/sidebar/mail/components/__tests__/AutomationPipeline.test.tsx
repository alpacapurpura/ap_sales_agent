import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { AutomationPipeline } from "../AutomationPipeline";

import type { AutomationStep } from "../../../../../../types/mail-types";

function buildEmailStep(overrides: Partial<AutomationStep> = {}): AutomationStep {
  return {
    stepId: "s1",
    stepNumber: 1,
    type: "email",
    subject: "Bienvenida",
    fromName: "Equipo",
    emailsSent: 10,
    uniqueOpens: 8,
    openRate: 80,
    uniqueClicks: 4,
    clickRate: 40,
    unsubscribes: 0,
    bounces: 0,
    screenshotUrl: null,
    previewUrl: null,
    delayValue: null,
    delayUnit: null,
    ...overrides,
  };
}

function buildDelayStep(days = 2): AutomationStep {
  return {
    stepId: `delay-${days}`,
    stepNumber: 2,
    type: "delay",
    subject: null,
    fromName: null,
    emailsSent: 0,
    uniqueOpens: 0,
    openRate: 0,
    uniqueClicks: 0,
    clickRate: 0,
    unsubscribes: 0,
    bounces: 0,
    screenshotUrl: null,
    previewUrl: null,
    delayValue: days,
    delayUnit: "days",
  };
}

describe("AutomationPipeline", () => {
  it("renders a card for each email step with subject and metrics", () => {
    const steps = [
      buildEmailStep({ stepId: "s1", subject: "Hola", openRate: 80, clickRate: 40 }),
      buildEmailStep({ stepId: "s2", subject: "Adiós", openRate: 60, clickRate: 20 }),
    ];
    render(<AutomationPipeline steps={steps} onStepClick={() => {}} />);

    expect(screen.getByText("Hola")).toBeInTheDocument();
    expect(screen.getByText("Adiós")).toBeInTheDocument();
    expect(screen.getByText("80.0%")).toBeInTheDocument();
    expect(screen.getByText("60.0%")).toBeInTheDocument();
  });

  it("shows best performer badge on highest scoring email", () => {
    const steps = [
      buildEmailStep({ stepId: "s1", subject: "A", openRate: 90, clickRate: 20 }),
      buildEmailStep({ stepId: "s2", subject: "B", openRate: 50, clickRate: 5 }),
    ];
    render(<AutomationPipeline steps={steps} onStepClick={() => {}} />);

    const badges = screen.getAllByText(/Mejor/i);
    expect(badges.length).toBeGreaterThanOrEqual(1);
  });

  it("shows attention badge on underperforming email", () => {
    const steps = [
      buildEmailStep({ stepId: "s1", subject: "Good", openRate: 80, clickRate: 25 }),
      buildEmailStep({ stepId: "s2", subject: "Bad", openRate: 10, clickRate: 0 }),
    ];
    render(<AutomationPipeline steps={steps} onStepClick={() => {}} />);

    expect(screen.getByText(/Atención/i)).toBeInTheDocument();
  });

  it("renders delay steps between emails", () => {
    const steps = [
      buildEmailStep({ stepId: "s1" }),
      buildDelayStep(3),
      buildEmailStep({ stepId: "s2" }),
    ];
    render(<AutomationPipeline steps={steps} onStepClick={() => {}} />);

    expect(screen.getByText(/3 días/i)).toBeInTheDocument();
  });

  it("calls onStepClick with the step when an email card is clicked", () => {
    const handler = vi.fn();
    const step = buildEmailStep({ stepId: "s1", subject: "Click me" });
    render(<AutomationPipeline steps={[step]} onStepClick={handler} />);

    fireEvent.click(screen.getByText("Click me"));
    expect(handler).toHaveBeenCalledWith(step);
  });

  it("renders AI insight when sequence has drop-off", () => {
    const steps = [
      buildEmailStep({ stepId: "s1", emailsSent: 10, openRate: 80, clickRate: 30 }),
      buildEmailStep({ stepId: "s2", emailsSent: 2, openRate: 20, clickRate: 0 }),
    ];
    render(<AutomationPipeline steps={steps} onStepClick={() => {}} />);

    expect(screen.getByTestId("automation-ai-insight")).toBeInTheDocument();
  });

  it("renders empty state when there are no email steps", () => {
    render(<AutomationPipeline steps={[]} onStepClick={() => {}} />);
    expect(screen.getByText(/sin pasos/i)).toBeInTheDocument();
  });
});
