/**
 * OfferShellHeader — flat, context-free header row for the offer shell.
 *
 * Replaces the legacy container/OfferShellHeaderRow1 (deleted in F4). Accepts
 * offer + tenantId as props — no context dependency.
 */
import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi } from "vitest";

import type { Offer } from "../../types";

const mockUseChangeOfferStatus = vi.fn<() => { mutate: () => void; isPending: boolean }>(() => ({
  mutate: vi.fn(),
  isPending: false,
}));
vi.mock("../../hooks/use-status-mutation", () => ({
  useChangeOfferStatus: () => mockUseChangeOfferStatus(),
}));

vi.mock("../OfferStatusSwitcher", () => ({
  OfferStatusSwitcher: ({ currentStatus }: { currentStatus: string }) => (
    <div data-testid="status-switcher">{currentStatus}</div>
  ),
}));

vi.mock("../OfferStatusChangeModal", () => ({
  OfferStatusChangeModal: () => <div data-testid="status-modal" />,
}));

vi.mock("../OfferAutoSaveIndicator", () => ({
  OfferAutoSaveIndicator: ({ state }: { state: string }) => (
    <div data-testid="autosave-indicator" data-state={state} />
  ),
}));

import { OfferShellHeader } from "../OfferShellHeader";

function buildOffer(overrides: Record<string, unknown> = {}): Offer {
  return {
    id: "offer-1",
    tenant_id: "tenant-1",
    name: "Programa Flagship",
    status: "draft",
    has_editions: true,
    archetype: "programa",
    format_hint: "cohorte",
    pricing: { amount: 0, currency: "USD" },
    currency: "USD",
    ...overrides,
  } as unknown as Offer;
}

describe("OfferShellHeader", () => {
  it("renders offer name + format badge", () => {
    render(<OfferShellHeader offer={buildOffer({ name: "MasterClass" })} tenantId="t-1" />);
    expect(screen.getByText("MasterClass")).toBeInTheDocument();
    expect(screen.getByText(/programa/i)).toBeInTheDocument();
  });

  it("renders back-button link to /{tenantId}/offer-studio", () => {
    render(<OfferShellHeader offer={buildOffer()} tenantId="acme" />);
    const back = screen.getByLabelText(/volver al offer studio/i);
    expect(back.closest("a")).toHaveAttribute("href", "/acme/offer-studio");
  });

  it("forwards current status to OfferStatusSwitcher", () => {
    render(<OfferShellHeader offer={buildOffer({ status: "active" })} tenantId="t-1" />);
    expect(screen.getByTestId("status-switcher")).toHaveTextContent("active");
  });

  it("renders OfferAutoSaveIndicator in idle state (non-invasive)", () => {
    render(<OfferShellHeader offer={buildOffer()} tenantId="t-1" />);
    expect(screen.getByTestId("autosave-indicator")).toHaveAttribute("data-state", "idle");
  });

  it("falls back to archetype label when format_hint missing", () => {
    render(
      <OfferShellHeader
        offer={buildOffer({ archetype: "servicio", format_hint: undefined })}
        tenantId="t-1"
      />,
    );
    expect(screen.getByText(/servicio/i)).toBeInTheDocument();
  });

  it("omits badge when neither archetype nor format_hint exist", () => {
    const { container } = render(
      <OfferShellHeader
        offer={buildOffer({
          name: "Oferta sin metadata",
          archetype: undefined,
          format_hint: undefined,
        })}
        tenantId="t-1"
      />,
    );
    expect(container.querySelector('[class*="uppercase tracking-wider"]')).toBeNull();
  });
});
