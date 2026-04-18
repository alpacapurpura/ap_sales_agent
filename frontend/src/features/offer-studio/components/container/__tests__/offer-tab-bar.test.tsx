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
  currentEditionId: null as string | null,
};

describe("OfferTabBar — 4 tabs, drops Conocimiento", () => {
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

  it("renders count badges only for assets and campaigns (knowledge count ignored)", () => {
    mockUsePathname.mockReturnValue(BASE_PATH);
    render(<OfferTabBar {...baseProps} />);
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.queryByText("7")).toBeNull();
  });

  it("renders the LandingActionButton on the right", () => {
    mockUsePathname.mockReturnValue(BASE_PATH);
    render(<OfferTabBar {...baseProps} />);
    expect(screen.getByTestId("landing-action-button")).toBeInTheDocument();
  });
});

describe("OfferTabBar — hrefs depend on edition scope", () => {
  beforeEach(() => {
    mockUsePathname.mockReset();
    mockUsePathname.mockReturnValue(BASE_PATH);
  });

  it("evergreen offer (no currentEditionId) links tabs at the offer root", () => {
    render(<OfferTabBar {...baseProps} currentEditionId={null} />);
    expect(screen.getByRole("link", { name: /Info/i })).toHaveAttribute("href", BASE_PATH);
    expect(screen.getByRole("link", { name: /Ventas/i })).toHaveAttribute(
      "href",
      `${BASE_PATH}/ventas`,
    );
    expect(screen.getByRole("link", { name: /Assets/i })).toHaveAttribute(
      "href",
      `${BASE_PATH}/assets`,
    );
    expect(screen.getByRole("link", { name: /Campañas/i })).toHaveAttribute(
      "href",
      `${BASE_PATH}/campaigns`,
    );
  });

  it("offer with current edition scopes Ventas/Assets/Campañas under /editions/{eid}", () => {
    render(<OfferTabBar {...baseProps} currentEditionId="ed-7" />);
    // Info stays at offer root — it's offer-level.
    expect(screen.getByRole("link", { name: /Info/i })).toHaveAttribute("href", BASE_PATH);
    expect(screen.getByRole("link", { name: /Ventas/i })).toHaveAttribute(
      "href",
      `${BASE_PATH}/editions/ed-7/ventas`,
    );
    expect(screen.getByRole("link", { name: /Assets/i })).toHaveAttribute(
      "href",
      `${BASE_PATH}/editions/ed-7/assets`,
    );
    expect(screen.getByRole("link", { name: /Campañas/i })).toHaveAttribute(
      "href",
      `${BASE_PATH}/editions/ed-7/campaigns`,
    );
  });
});

describe("OfferTabBar — active tab highlighting", () => {
  beforeEach(() => {
    mockUsePathname.mockReset();
  });

  it("marks Info active on the base route", () => {
    mockUsePathname.mockReturnValue(BASE_PATH);
    render(<OfferTabBar {...baseProps} />);
    expect(screen.getByRole("link", { name: /Info/i })).toHaveAttribute(ARIA_CURRENT, ARIA_PAGE);
  });

  it("marks Ventas active on the offer-level ventas route", () => {
    mockUsePathname.mockReturnValue(`${BASE_PATH}/ventas`);
    render(<OfferTabBar {...baseProps} />);
    expect(screen.getByRole("link", { name: /Ventas/i })).toHaveAttribute(ARIA_CURRENT, ARIA_PAGE);
  });

  it("marks Ventas active on the edition-scoped ventas route", () => {
    mockUsePathname.mockReturnValue(`${BASE_PATH}/editions/ed-7/ventas`);
    render(<OfferTabBar {...baseProps} currentEditionId="ed-7" />);
    expect(screen.getByRole("link", { name: /Ventas/i })).toHaveAttribute(ARIA_CURRENT, ARIA_PAGE);
  });

  it("marks Assets active on the edition-scoped assets route", () => {
    mockUsePathname.mockReturnValue(`${BASE_PATH}/editions/ed-7/assets`);
    render(<OfferTabBar {...baseProps} currentEditionId="ed-7" />);
    expect(screen.getByRole("link", { name: /Assets/i })).toHaveAttribute(ARIA_CURRENT, ARIA_PAGE);
  });

  it("marks Campañas active on the edition-scoped campaigns route", () => {
    mockUsePathname.mockReturnValue(`${BASE_PATH}/editions/ed-7/campaigns`);
    render(<OfferTabBar {...baseProps} currentEditionId="ed-7" />);
    expect(screen.getByRole("link", { name: /Campañas/i })).toHaveAttribute(
      ARIA_CURRENT,
      ARIA_PAGE,
    );
  });

  it("does not mark Info active on the edition default route", () => {
    mockUsePathname.mockReturnValue(`${BASE_PATH}/editions/ed-7`);
    render(<OfferTabBar {...baseProps} currentEditionId="ed-7" />);
    expect(screen.getByRole("link", { name: /Info/i })).not.toHaveAttribute(
      ARIA_CURRENT,
      ARIA_PAGE,
    );
  });
});
