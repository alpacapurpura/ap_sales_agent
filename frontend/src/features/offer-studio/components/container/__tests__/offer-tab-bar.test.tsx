import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockUsePathname = vi.fn();

vi.mock("next/navigation", () => ({
  usePathname: () => mockUsePathname(),
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
    ...props
  }: {
    children: React.ReactNode;
    href: string;
  } & React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

// The landing action button uses the useLandingStatus hook which in turn calls
// the Clerk auth hook + React Query. Stub the whole component so the TabBar
// test can stay focused on tab rendering and routing behaviour.
vi.mock("../LandingActionButton", () => ({
  LandingActionButton: ({ offerId, tenantId }: { offerId: string; tenantId: string }) => (
    <button
      type="button"
      data-testid="landing-action-button"
      data-offer-id={offerId}
      data-tenant-id={tenantId}
    >
      Landing
    </button>
  ),
}));

// ── Imports after mocks ──────────────────────────────────────────────────────

import { OfferTabBar } from "../OfferTabBar";

const BASE_PATH = "/acme/offer-studio/offer/offer-1";
const ARIA_CURRENT = "aria-current";
const ARIA_PAGE = "page";

const baseProps = {
  tenantId: "acme",
  offerId: "offer-1",
  counts: { assets: 4, campaigns: 2, knowledge: 7, active_campaigns: 2 },
};

describe("OfferTabBar", () => {
  beforeEach(() => {
    mockUsePathname.mockReset();
  });

  it("renders exactly four tabs (Info, Ventas, Assets, Campañas) — no Conocimiento tab", () => {
    mockUsePathname.mockReturnValue(BASE_PATH);
    render(<OfferTabBar {...baseProps} />);
    const tabs = screen.getAllByRole("link");
    expect(tabs).toHaveLength(4);
    expect(screen.getByRole("link", { name: /Info/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Ventas/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Assets/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Campañas/i })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Conocimiento/i })).toBeNull();
  });

  it("marks the Ventas tab active on the ventas sub-route", () => {
    mockUsePathname.mockReturnValue("/acme/offer-studio/offer/offer-1/ventas");
    render(<OfferTabBar {...baseProps} />);
    expect(screen.getByRole("link", { name: /Ventas/i })).toHaveAttribute(ARIA_CURRENT, ARIA_PAGE);
  });

  it("renders count badges only for assets and campaigns (knowledge count ignored)", () => {
    mockUsePathname.mockReturnValue(BASE_PATH);
    render(<OfferTabBar {...baseProps} />);
    expect(screen.getByText("4")).toBeInTheDocument(); // assets
    expect(screen.getByText("2")).toBeInTheDocument(); // campaigns
    expect(screen.queryByText("7")).toBeNull(); // knowledge count must not render
  });

  it("marks Info as active on the base route", () => {
    mockUsePathname.mockReturnValue(BASE_PATH);
    render(<OfferTabBar {...baseProps} />);
    expect(screen.getByRole("link", { name: /Info/i })).toHaveAttribute(ARIA_CURRENT, ARIA_PAGE);
  });

  it("marks Assets as active on the assets sub-route", () => {
    mockUsePathname.mockReturnValue("/acme/offer-studio/offer/offer-1/assets");
    render(<OfferTabBar {...baseProps} />);
    expect(screen.getByRole("link", { name: /Assets/i })).toHaveAttribute(ARIA_CURRENT, ARIA_PAGE);
  });

  it("marks Campañas as active on the campaigns sub-route", () => {
    mockUsePathname.mockReturnValue("/acme/offer-studio/offer/offer-1/campaigns");
    render(<OfferTabBar {...baseProps} />);
    expect(screen.getByRole("link", { name: /Campañas/i })).toHaveAttribute(
      ARIA_CURRENT,
      ARIA_PAGE,
    );
  });

  it("renders the LandingActionButton on the right side of the bar", () => {
    mockUsePathname.mockReturnValue(BASE_PATH);
    render(<OfferTabBar {...baseProps} />);
    const landingButton = screen.getByTestId("landing-action-button");
    expect(landingButton).toBeInTheDocument();
    expect(landingButton).toHaveAttribute("data-offer-id", "offer-1");
    expect(landingButton).toHaveAttribute("data-tenant-id", "acme");
  });
});
