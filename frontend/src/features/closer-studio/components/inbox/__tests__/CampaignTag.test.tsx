import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { describe, expect, it } from "vitest";

import { CampaignTag } from "../CampaignTag";

// ── Tooltip provider not required by happy-dom: Radix uses IntersectionObserver
// which happy-dom stubs — rendering inside a Portal is fine.

describe("CampaignTag", () => {
  it("renders badge with text 'campaña: {campaignName}'", () => {
    render(<CampaignTag campaignId="abc-123" campaignName="Black Friday" />);
    expect(screen.getByRole("link")).toHaveTextContent("campaña: Black Friday");
  });

  it("link href points to /campanas/{campaignId}", () => {
    render(<CampaignTag campaignId="abc-123" campaignName="Black Friday" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/campanas/abc-123");
  });

  it("truncates campaign name longer than 30 chars", () => {
    const longName = "Campaña de ventas de navidad y año nuevo 2026";
    render(<CampaignTag campaignId="x-1" campaignName={longName} />);
    // The rendered truncated text should be at most 30 chars + "…"
    const link = screen.getByRole("link");
    const text = link.textContent ?? "";
    // "campaña: " is 9 chars; remaining truncated to 30 chars + ellipsis
    expect(text.length).toBeLessThan("campaña: ".length + 30 + 2);
    expect(text).toContain("…");
  });

  it("shows full name in title attribute when truncated (tooltip fallback)", () => {
    const longName = "Campaña de ventas de navidad y año nuevo 2026";
    render(<CampaignTag campaignId="x-1" campaignName={longName} />);
    // The badge element or the link should carry title with full name
    const container = screen.getByRole("link").closest("[title]");
    expect(container).not.toBeNull();
    expect(container?.getAttribute("title")).toBe(longName);
  });

  it("passthrough className applies to root element", () => {
    const { container } = render(
      <CampaignTag campaignId="x-1" campaignName="Test" className="custom-cls" />,
    );
    expect(container.firstChild).toHaveClass("custom-cls");
  });

  it("navigates to /campanas/{id} on click", async () => {
    const user = userEvent.setup();
    render(<CampaignTag campaignId="abc-123" campaignName="Promo" />);
    await user.click(screen.getByRole("link"));
    // next/link renders an anchor; navigation happens via href, no manual push needed.
    expect(screen.getByRole("link")).toHaveAttribute("href", "/campanas/abc-123");
  });

  it("variant='detail' renders without error", () => {
    render(<CampaignTag campaignId="d-1" campaignName="Detalle" variant="detail" />);
    expect(screen.getByRole("link")).toBeInTheDocument();
  });
});
