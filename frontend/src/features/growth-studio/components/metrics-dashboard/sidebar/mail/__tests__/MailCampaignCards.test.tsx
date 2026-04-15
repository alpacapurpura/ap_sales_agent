import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";

import { MailCampaignCards } from "../MailCampaignCards";

import type { EmailCampaignSummary } from "../../../../../types/mail-types";

const BEST_CAMPAIGN: EmailCampaignSummary = {
  campaignName: "Lanzamiento Curso Avanzado",
  campaignSubject: "Tu oportunidad de crecer",
  campaignType: "regular",
  sentCount: 5000,
  openRate: 45.2,
  clickToOpenRate: 12.8,
  sentDate: "2026-04-01T10:00:00Z",
};

const WORST_CAMPAIGN: EmailCampaignSummary = {
  campaignName: "Newsletter Semanal #12",
  campaignSubject: null,
  campaignType: "regular",
  sentCount: 3200,
  openRate: 8.5,
  clickToOpenRate: 1.2,
  sentDate: "2026-03-28T14:00:00Z",
};

describe("MailCampaignCards", () => {
  it("renders both campaign cards when data is present", () => {
    render(<MailCampaignCards bestCampaign={BEST_CAMPAIGN} worstCampaign={WORST_CAMPAIGN} />);
    expect(screen.getByText("Mejor Campaña")).toBeInTheDocument();
    expect(screen.getByText("Peor Campaña")).toBeInTheDocument();
    expect(screen.getByText("Lanzamiento Curso Avanzado")).toBeInTheDocument();
    expect(screen.getByText("Newsletter Semanal #12")).toBeInTheDocument();
  });

  it("renders open rate and CTOR for each campaign", () => {
    render(<MailCampaignCards bestCampaign={BEST_CAMPAIGN} worstCampaign={WORST_CAMPAIGN} />);
    expect(screen.getByText("45.2%")).toBeInTheDocument();
    expect(screen.getByText("12.8%")).toBeInTheDocument();
    expect(screen.getByText("8.5%")).toBeInTheDocument();
    expect(screen.getByText("1.2%")).toBeInTheDocument();
  });

  it("renders nothing when both campaigns are null", () => {
    const { container } = render(<MailCampaignCards bestCampaign={null} worstCampaign={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders only the best campaign when worst is null", () => {
    render(<MailCampaignCards bestCampaign={BEST_CAMPAIGN} worstCampaign={null} />);
    expect(screen.getByText("Mejor Campaña")).toBeInTheDocument();
    expect(screen.queryByText("Peor Campaña")).not.toBeInTheDocument();
  });

  it("renders sent count for campaigns", () => {
    render(<MailCampaignCards bestCampaign={BEST_CAMPAIGN} worstCampaign={WORST_CAMPAIGN} />);
    // sentCount is formatted, e.g., "5,000" or "5.0k"
    expect(screen.getByText(/5.*env/i)).toBeInTheDocument();
  });
});
