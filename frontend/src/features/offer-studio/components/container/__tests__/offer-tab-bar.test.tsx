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

// ── Imports after mocks ──────────────────────────────────────────────────────

import { OfferTabBar } from "../OfferTabBar";

const baseProps = {
  tenantId: "acme",
  offerId: "offer-1",
  counts: { assets: 4, campaigns: 2, knowledge: 7, active_campaigns: 2 },
};

describe("OfferTabBar", () => {
  beforeEach(() => {
    mockUsePathname.mockReset();
  });

  it("renders all five tabs (Info, Ventas, Assets, Campañas, Conocimiento)", () => {
    mockUsePathname.mockReturnValue("/acme/offer-studio/offer/offer-1");
    render(<OfferTabBar {...baseProps} />);
    expect(screen.getByRole("link", { name: /Info/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Ventas/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Assets/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Campañas/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Conocimiento/i })).toBeInTheDocument();
  });

  it("marks the Ventas tab active on the ventas sub-route", () => {
    mockUsePathname.mockReturnValue("/acme/offer-studio/offer/offer-1/ventas");
    render(<OfferTabBar {...baseProps} />);
    expect(screen.getByRole("link", { name: /Ventas/i })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("renders count badges for assets, campaigns and knowledge", () => {
    mockUsePathname.mockReturnValue("/acme/offer-studio/offer/offer-1");
    render(<OfferTabBar {...baseProps} />);
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("7")).toBeInTheDocument();
  });

  it("marks Info as active on the base route", () => {
    mockUsePathname.mockReturnValue("/acme/offer-studio/offer/offer-1");
    render(<OfferTabBar {...baseProps} />);
    expect(screen.getByRole("link", { name: /Info/i })).toHaveAttribute("aria-current", "page");
  });

  it("marks Assets as active on the assets sub-route", () => {
    mockUsePathname.mockReturnValue("/acme/offer-studio/offer/offer-1/assets");
    render(<OfferTabBar {...baseProps} />);
    expect(screen.getByRole("link", { name: /Assets/i })).toHaveAttribute("aria-current", "page");
  });

  it("marks Campañas as active on the campaigns sub-route", () => {
    mockUsePathname.mockReturnValue("/acme/offer-studio/offer/offer-1/campaigns");
    render(<OfferTabBar {...baseProps} />);
    expect(screen.getByRole("link", { name: /Campañas/i })).toHaveAttribute("aria-current", "page");
  });
});
