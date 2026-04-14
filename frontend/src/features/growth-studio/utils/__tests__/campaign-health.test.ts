import { describe, it, expect } from "vitest";

import { computeCampaignHealthScore, diagnoseCampaign } from "../campaign-health";
import type { EmailCampaign } from "../../types/mail-types";

function buildCampaign(overrides: Partial<EmailCampaign> = {}): EmailCampaign {
  return {
    campaignId: "c1",
    campaignName: "Test Campaign",
    campaignSubject: "Test subject",
    campaignType: "newsletter",
    sentDate: "2026-04-09",
    emailsSent: 100,
    openRate: 40,
    clickRate: 5,
    clickToOpenRate: 12.5,
    bounceRate: 0.5,
    unsubscribes: 1,
    uniqueOpens: 40,
    uniqueClicks: 5,
    screenshotUrl: null,
    previewUrl: null,
    ...overrides,
  };
}

describe("computeCampaignHealthScore", () => {
  it("returns 0 when campaign has no emails sent", () => {
    const campaign = buildCampaign({
      emailsSent: 0,
      openRate: 0,
      clickRate: 0,
      clickToOpenRate: 0,
      unsubscribes: 0,
      bounceRate: 0,
    });
    expect(computeCampaignHealthScore(campaign)).toBe(0);
  });

  it("returns high score (>70) for excellent campaign", () => {
    const campaign = buildCampaign({
      openRate: 85,
      clickRate: 20,
      clickToOpenRate: 25,
      unsubscribes: 0,
      bounceRate: 0,
      emailsSent: 500,
    });
    expect(computeCampaignHealthScore(campaign)).toBeGreaterThan(70);
  });

  it("returns low score (<40) for poor campaign", () => {
    const campaign = buildCampaign({
      openRate: 8,
      clickRate: 0.5,
      clickToOpenRate: 2,
      unsubscribes: 10,
      bounceRate: 8,
      emailsSent: 200,
    });
    expect(computeCampaignHealthScore(campaign)).toBeLessThan(40);
  });

  it("penalizes high bounce rate", () => {
    const baseline = buildCampaign({
      openRate: 40,
      clickRate: 5,
      clickToOpenRate: 12,
      unsubscribes: 1,
      bounceRate: 0.5,
      emailsSent: 500,
    });
    const penalized = { ...baseline, bounceRate: 8 };
    expect(computeCampaignHealthScore(penalized)).toBeLessThan(
      computeCampaignHealthScore(baseline),
    );
  });

  it("penalizes high unsubscribe rate", () => {
    const baseline = buildCampaign({
      openRate: 40,
      clickRate: 5,
      clickToOpenRate: 12,
      unsubscribes: 1,
      bounceRate: 0.5,
      emailsSent: 500,
    });
    const penalized = { ...baseline, unsubscribes: 30 };
    expect(computeCampaignHealthScore(penalized)).toBeLessThan(
      computeCampaignHealthScore(baseline),
    );
  });
});

describe("diagnoseCampaign", () => {
  it("flags high open + low click as weak CTA", () => {
    const campaign = buildCampaign({ openRate: 70, clickRate: 1 });
    const insights = diagnoseCampaign(campaign);
    expect(insights.some((i) => i.includes("CTA"))).toBe(true);
  });

  it("flags low open rate", () => {
    const campaign = buildCampaign({ openRate: 12, clickRate: 2 });
    const insights = diagnoseCampaign(campaign);
    expect(insights.some((i) => i.toLowerCase().includes("apertura"))).toBe(true);
  });

  it("flags high unsubscribes", () => {
    const campaign = buildCampaign({
      unsubscribes: 20,
      emailsSent: 100,
      openRate: 40,
      clickRate: 5,
    });
    const insights = diagnoseCampaign(campaign);
    expect(insights.some((i) => i.toLowerCase().includes("desuscrip"))).toBe(true);
  });

  it("flags high bounce rate as list hygiene problem", () => {
    const campaign = buildCampaign({ bounceRate: 6 });
    const insights = diagnoseCampaign(campaign);
    expect(
      insights.some((i) => i.toLowerCase().includes("rebote") || i.toLowerCase().includes("lista")),
    ).toBe(true);
  });

  it("returns empty for healthy campaign", () => {
    const campaign = buildCampaign({
      openRate: 60,
      clickRate: 8,
      clickToOpenRate: 13,
      unsubscribes: 0,
      bounceRate: 0.3,
    });
    expect(diagnoseCampaign(campaign)).toEqual([]);
  });
});
