import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { CampaignDetailSidebar } from "../CampaignDetailSidebar";

import type { EmailCampaign } from "../../../../../../types/mail-types";

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

describe("CampaignDetailSidebar", () => {
  it("does not render content when campaign is null", () => {
    const { container } = render(<CampaignDetailSidebar campaign={null} onClose={() => {}} />);
    expect(container.textContent).not.toContain("Test subject");
  });

  it("renders campaign subject and name in header", () => {
    const campaign = buildCampaign({
      campaignSubject: "Mi subject line",
      campaignName: "Newsletter #42",
    });
    render(<CampaignDetailSidebar campaign={campaign} onClose={() => {}} />);

    expect(screen.getAllByText("Mi subject line").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Newsletter #42/).length).toBeGreaterThan(0);
  });

  it("falls back to campaign name when subject is null", () => {
    const campaign = buildCampaign({
      campaignSubject: null,
      campaignName: "Unnamed Campaign",
    });
    render(<CampaignDetailSidebar campaign={campaign} onClose={() => {}} />);

    expect(screen.getAllByText("Unnamed Campaign").length).toBeGreaterThan(0);
  });

  it("renders all six metric boxes (enviados, abiertos, clicks, open/click/ctor)", () => {
    const campaign = buildCampaign({
      emailsSent: 500,
      uniqueOpens: 200,
      uniqueClicks: 50,
      openRate: 40,
      clickRate: 10,
      clickToOpenRate: 25,
    });
    render(<CampaignDetailSidebar campaign={campaign} onClose={() => {}} />);

    // raw counts
    expect(screen.getAllByText("500").length).toBeGreaterThan(0);
    expect(screen.getAllByText("200").length).toBeGreaterThan(0);
    expect(screen.getAllByText("50").length).toBeGreaterThan(0);
    // rates
    expect(screen.getAllByText("40.0%").length).toBeGreaterThan(0);
    expect(screen.getAllByText("10.0%").length).toBeGreaterThan(0);
    expect(screen.getAllByText("25.0%").length).toBeGreaterThan(0);
  });

  it('renders "ver email completo" link when previewUrl exists', () => {
    const campaign = buildCampaign({
      previewUrl: "https://preview.example",
    });
    render(<CampaignDetailSidebar campaign={campaign} onClose={() => {}} />);

    const link = screen.getByRole("link", { name: /email completo/i });
    expect(link).toHaveAttribute("href", "https://preview.example");
  });

  it("renders AI diagnosis when campaign has issues", () => {
    const campaign = buildCampaign({
      openRate: 70,
      clickRate: 0.5,
      emailsSent: 100,
    });
    render(<CampaignDetailSidebar campaign={campaign} onClose={() => {}} />);

    expect(screen.getByText(/CTA/i)).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", () => {
    const handler = vi.fn();
    const campaign = buildCampaign();
    render(<CampaignDetailSidebar campaign={campaign} onClose={handler} />);
    const closeBtn = screen.getByRole("button", { name: /cerrar/i });
    closeBtn.click();
    expect(handler).toHaveBeenCalled();
  });
});
