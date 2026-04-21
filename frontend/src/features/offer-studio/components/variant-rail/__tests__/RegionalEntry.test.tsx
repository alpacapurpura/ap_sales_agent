import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it, vi } from "vitest";

import { EditionStatus, EditionVisibility } from "../../../types";
import { RegionalEntry } from "../entries/RegionalEntry";

import type { LaunchEdition } from "../../../types";

function makeRegionalVariant(overrides: Partial<LaunchEdition> = {}): LaunchEdition {
  return {
    id: "regional-1",
    offer_id: "offer-1",
    edition_name: "México",
    edition_number: 1,
    variant_structure: "regional",
    structure_data: {
      flag_emoji: "🇲🇽",
      price_amount: 4900,
      price_currency: "MXN",
      tax_label: "IVA 16%",
      locale: "ES-MX",
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
    currency: "MXN",
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

describe("RegionalEntry", () => {
  it("renders the country name", () => {
    render(
      <RegionalEntry
        variant={makeRegionalVariant()}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/México/)).toBeInTheDocument();
  });

  it("renders the flag emoji", () => {
    render(
      <RegionalEntry
        variant={makeRegionalVariant()}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/🇲🇽/)).toBeInTheDocument();
  });

  it("renders price with currency from structure_data", () => {
    render(
      <RegionalEntry
        variant={makeRegionalVariant()}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    // formatMoney(4900, 'MXN') → "$4,900.00"
    expect(screen.getByText(/4,900/)).toBeInTheDocument();
  });

  it("renders locale chip", () => {
    render(
      <RegionalEntry
        variant={makeRegionalVariant()}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText("ES-MX")).toBeInTheDocument();
  });

  it("renders tax label", () => {
    render(
      <RegionalEntry
        variant={makeRegionalVariant()}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/IVA 16%/)).toBeInTheDocument();
  });

  it("marks entry as pressed when selected", () => {
    render(
      <RegionalEntry
        variant={makeRegionalVariant()}
        tone="active"
        isSelected={true}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "true");
  });
});
