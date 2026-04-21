import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it, vi } from "vitest";

import { EditionStatus, EditionVisibility } from "../../../types";
import { TierEntry } from "../entries/TierEntry";

import type { LaunchEdition } from "../../../types";

function makeTierVariant(overrides: Partial<LaunchEdition> = {}): LaunchEdition {
  return {
    id: "tier-1",
    offer_id: "offer-1",
    edition_name: "Premium",
    edition_number: 1,
    variant_structure: "tier",
    structure_data: {
      price_amount: 79,
      price_currency: "USD",
      is_recommended: true,
    },
    sort_rank: null,
    start_date: null,
    end_date: null,
    registration_start: null,
    registration_end: null,
    timezone: "UTC",
    pricing_override: null,
    pricing_tiers: [],
    active_tier: null,
    effective_pricing: [],
    currency: "USD",
    capacity: null,
    enrollment_count: 0,
    status: EditionStatus.ACTIVE,
    visibility: EditionVisibility.PUBLIC,
    is_placeholder: false,
    location_override: null,
    notes: null,
    cloned_from_edition_id: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

describe("TierEntry", () => {
  it("renders the plan name", () => {
    render(
      <TierEntry variant={makeTierVariant()} tone="active" isSelected={false} onClick={vi.fn()} />,
    );
    expect(screen.getByText("Premium")).toBeInTheDocument();
  });

  it("renders price from structure_data.price_amount + price_currency", () => {
    render(
      <TierEntry
        variant={makeTierVariant({ structure_data: { price_amount: 79, price_currency: "USD" } })}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    // formatMoney(79, 'USD') → "$79.00"
    expect(screen.getByText(/\$79/)).toBeInTheDocument();
  });

  it("falls back to pricing_override when structure_data has no price", () => {
    const variant = makeTierVariant({
      structure_data: {},
      pricing_override: [{ label: "Base", total_amount: 49, currency: "MXN" }],
    });
    render(<TierEntry variant={variant} tone="draft" isSelected={false} onClick={vi.fn()} />);
    expect(screen.getByText(/49/)).toBeInTheDocument();
  });

  it("shows '★ Recomendado' chip when is_recommended is true", () => {
    render(
      <TierEntry
        variant={makeTierVariant({
          structure_data: { price_amount: 79, price_currency: "USD", is_recommended: true },
        })}
        tone="active"
        isSelected={true}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/Recomendado/)).toBeInTheDocument();
  });

  it("does not show recommended chip when is_recommended is false", () => {
    render(
      <TierEntry
        variant={makeTierVariant({
          structure_data: { price_amount: 29, price_currency: "USD", is_recommended: false },
        })}
        tone="draft"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.queryByText(/Recomendado/)).toBeNull();
  });

  it("renders status label", () => {
    render(
      <TierEntry
        variant={makeTierVariant({ status: EditionStatus.DRAFT })}
        tone="draft"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/Borrador/i)).toBeInTheDocument();
  });

  it("marks entry as pressed when selected", () => {
    render(
      <TierEntry variant={makeTierVariant()} tone="active" isSelected={true} onClick={vi.fn()} />,
    );
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "true");
  });
});
