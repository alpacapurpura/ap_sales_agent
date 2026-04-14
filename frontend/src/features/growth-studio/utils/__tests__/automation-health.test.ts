import { describe, it, expect } from "vitest";

import {
  computeHealthScore,
  computeDropoff,
  diagnoseStep,
  findBestStep,
  findAttentionStep,
} from "../automation-health";
import type { EmailAutomation, AutomationStep } from "../../types/mail-types";

function buildAutomation(overrides: Partial<EmailAutomation> = {}): EmailAutomation {
  return {
    automationId: "a1",
    name: "Test",
    automationType: "welcome",
    status: "active",
    activeSubscribers: 10,
    completed: 5,
    emailsSent: 20,
    openRate: 60,
    clickRate: 10,
    clickToOpenRate: 16.7,
    completionRate: 50,
    unsubscribes: 0,
    steps: [],
    ...overrides,
  };
}

function buildStep(overrides: Partial<AutomationStep> = {}): AutomationStep {
  return {
    stepId: "s1",
    stepNumber: 1,
    type: "email",
    subject: "Test email",
    fromName: "Me",
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

describe("computeHealthScore", () => {
  it("returns 0 when automation has no data", () => {
    const auto = buildAutomation({
      openRate: 0,
      clickRate: 0,
      clickToOpenRate: 0,
      completionRate: 0,
      unsubscribes: 0,
      emailsSent: 0,
    });
    expect(computeHealthScore(auto)).toBe(0);
  });

  it("returns high score (>70) for excellent automation", () => {
    const auto = buildAutomation({
      openRate: 90,
      clickRate: 30,
      clickToOpenRate: 33,
      completionRate: 80,
      unsubscribes: 0,
    });
    expect(computeHealthScore(auto)).toBeGreaterThan(70);
  });

  it("returns low score (<40) for poor automation", () => {
    const auto = buildAutomation({
      openRate: 10,
      clickRate: 0.5,
      clickToOpenRate: 2,
      completionRate: 5,
      unsubscribes: 5,
      emailsSent: 100,
    });
    expect(computeHealthScore(auto)).toBeLessThan(40);
  });

  it("penalizes high unsubscribe rate", () => {
    const baseline = buildAutomation({
      openRate: 60,
      clickRate: 10,
      clickToOpenRate: 16.7,
      completionRate: 50,
      unsubscribes: 0,
      emailsSent: 100,
    });
    const penalized = { ...baseline, unsubscribes: 10 };
    expect(computeHealthScore(penalized)).toBeLessThan(computeHealthScore(baseline));
  });
});

describe("computeDropoff", () => {
  it("returns 0 when both steps have same sent", () => {
    expect(computeDropoff(100, 100)).toBe(0);
  });

  it("returns 50 when half drop off", () => {
    expect(computeDropoff(100, 50)).toBe(50);
  });

  it("returns 0 when previous step had 0 sent (avoid div by zero)", () => {
    expect(computeDropoff(0, 0)).toBe(0);
  });

  it("returns 100 when all drop off", () => {
    expect(computeDropoff(100, 0)).toBe(100);
  });
});

describe("diagnoseStep", () => {
  it("flags high open + low click as weak CTA", () => {
    const step = buildStep({ openRate: 70, clickRate: 1 });
    const insights = diagnoseStep(step);
    expect(insights.some((i) => i.includes("CTA"))).toBe(true);
  });

  it("flags low open rate", () => {
    const step = buildStep({ openRate: 15, clickRate: 2 });
    const insights = diagnoseStep(step);
    expect(insights.some((i) => i.toLowerCase().includes("apertura"))).toBe(true);
  });

  it("flags high unsubscribes", () => {
    const step = buildStep({ unsubscribes: 5, emailsSent: 20 });
    const insights = diagnoseStep(step);
    expect(insights.some((i) => i.toLowerCase().includes("desuscrip"))).toBe(true);
  });

  it("flags steep drop vs previous step", () => {
    const prev = buildStep({ openRate: 90 });
    const current = buildStep({ openRate: 30 });
    const insights = diagnoseStep(current, prev);
    expect(insights.some((i) => i.toLowerCase().includes("caída"))).toBe(true);
  });

  it("returns empty for healthy step", () => {
    const step = buildStep({ openRate: 70, clickRate: 15, unsubscribes: 0 });
    expect(diagnoseStep(step)).toEqual([]);
  });
});

describe("findBestStep", () => {
  it("returns null for empty list", () => {
    expect(findBestStep([])).toBeNull();
  });

  it("picks step with highest open × click product", () => {
    const steps = [
      buildStep({ stepId: "s1", openRate: 80, clickRate: 10 }), // 800
      buildStep({ stepId: "s2", openRate: 60, clickRate: 20 }), // 1200
      buildStep({ stepId: "s3", openRate: 70, clickRate: 5 }), // 350
    ];
    expect(findBestStep(steps)?.stepId).toBe("s2");
  });

  it("ignores non-email steps", () => {
    const steps = [
      buildStep({ stepId: "s1", type: "delay", openRate: 100, clickRate: 100 }),
      buildStep({ stepId: "s2", type: "email", openRate: 50, clickRate: 5 }),
    ];
    expect(findBestStep(steps)?.stepId).toBe("s2");
  });
});

describe("findAttentionStep", () => {
  it("returns null when all emails perform OK", () => {
    const steps = [
      buildStep({ openRate: 60, clickRate: 10 }),
      buildStep({ openRate: 55, clickRate: 8 }),
    ];
    expect(findAttentionStep(steps)).toBeNull();
  });

  it("flags step with 0 click rate", () => {
    const steps = [
      buildStep({ stepId: "s1", openRate: 60, clickRate: 10 }),
      buildStep({ stepId: "s2", openRate: 40, clickRate: 0 }),
    ];
    expect(findAttentionStep(steps)?.stepId).toBe("s2");
  });

  it("flags step with very low open rate", () => {
    const steps = [
      buildStep({ stepId: "s1", openRate: 80, clickRate: 15 }),
      buildStep({ stepId: "s2", openRate: 10, clickRate: 2 }),
    ];
    expect(findAttentionStep(steps)?.stepId).toBe("s2");
  });
});
