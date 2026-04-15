import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { OfferCard } from "../components/dashboard/offer-card";

import { MOCK_OFFER_NORMALIZED } from "./fixtures";

import type { Offer } from "../types";

// Mock Next.js router
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: "visionarias" }),
}));

// Mock NavigationProvider context
vi.mock("@/components/shared/navigation", () => ({
  useNavigation: () => ({
    navigate: vi.fn(),
    isNavigating: false,
    navigateReplace: vi.fn(),
    pendingHref: null,
  }),
}));

// Default tenant locale — PEN so fallback assertions work without extra wiring
vi.mock("@/features/tenant/context/tenant-locale-context", () => ({
  useTenantLocale: () => ({ currency: "PEN", timezone: "America/Lima" }),
}));

describe("OfferCard Component", () => {
  it("renders the offer name correctly", () => {
    render(<OfferCard offer={MOCK_OFFER_NORMALIZED} />);

    // The most critical check: Is the name visible?
    expect(screen.getByText("Guía: Liberar la Mente")).toBeInTheDocument();
  });

  it("renders the correct archetype label", () => {
    render(<OfferCard offer={MOCK_OFFER_NORMALIZED} />);

    // Should map archetype "producto" -> "Producto" via ARCHETYPE_METADATA
    expect(screen.getByText("Producto")).toBeInTheDocument();
  });

  it("renders the correct delivery badge", () => {
    render(<OfferCard offer={MOCK_OFFER_NORMALIZED} />);
    expect(screen.getByText("DIY")).toBeInTheDocument();
  });

  it("respects the pricing currency (PEN) over tenant default", () => {
    const offer: Offer = {
      ...MOCK_OFFER_NORMALIZED,
      currency: "PEN",
      pricing: [
        {
          label: "Standard",
          total_amount: 1500,
          currency: "PEN",
          deposit_required: 0,
          number_of_installments: 1,
          installment_amount: 0,
        },
      ],
    };
    render(<OfferCard offer={offer} />);
    // Intl.NumberFormat('en-US', { currency: 'PEN' }) → "PEN 1,500"
    const priceNode = screen.getByText(/PEN/);
    expect(priceNode).toBeInTheDocument();
    expect(priceNode.textContent).toContain("1,500");
  });

  it("falls back to tenant currency when pricing has no currency", () => {
    const offer: Offer = {
      ...MOCK_OFFER_NORMALIZED,
      currency: undefined,
      pricing: [
        {
          label: "Standard",
          total_amount: 500,
          currency: undefined,
          deposit_required: 0,
          number_of_installments: 1,
          installment_amount: 0,
        },
      ],
    };
    render(<OfferCard offer={offer} />);
    const priceNode = screen.getByText(/PEN/);
    expect(priceNode).toBeInTheDocument();
    expect(priceNode.textContent).toContain("500");
  });
});
