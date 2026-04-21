import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it, vi } from "vitest";

import { EditionStatus, EditionVisibility } from "../../../types";
import { SkuEntry } from "../entries/SkuEntry";

import type { LaunchEdition } from "../../../types";

function makeSkuVariant(overrides: Partial<LaunchEdition> = {}): LaunchEdition {
  return {
    id: "sku-1",
    offer_id: "offer-1",
    edition_name: "30ml · Piel sensible",
    edition_number: 1,
    variant_structure: "sku_variant",
    structure_data: {
      sku_code: "SRM-30-SNS",
      low_stock_threshold: 10,
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
    capacity: 50,
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

describe("SkuEntry", () => {
  it("renders the variant name", () => {
    render(
      <SkuEntry variant={makeSkuVariant()} tone="active" isSelected={false} onClick={vi.fn()} />,
    );
    expect(screen.getByText("30ml · Piel sensible")).toBeInTheDocument();
  });

  it("renders the SKU code in monospace", () => {
    render(
      <SkuEntry variant={makeSkuVariant()} tone="active" isSelected={false} onClick={vi.fn()} />,
    );
    expect(screen.getByText("SRM-30-SNS")).toBeInTheDocument();
  });

  it("renders capacity count", () => {
    render(
      <SkuEntry
        variant={makeSkuVariant({ capacity: 50 })}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/50/)).toBeInTheDocument();
  });

  it("shows low-stock warning when capacity ≤ threshold (10)", () => {
    render(
      <SkuEntry
        variant={makeSkuVariant({ capacity: 8 })}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/Low stock/i)).toBeInTheDocument();
  });

  it("does not show low-stock warning when capacity > threshold", () => {
    render(
      <SkuEntry
        variant={makeSkuVariant({ capacity: 100 })}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.queryByText(/Low stock/i)).toBeNull();
  });

  it("uses custom low_stock_threshold from structure_data", () => {
    render(
      <SkuEntry
        variant={makeSkuVariant({
          capacity: 15,
          structure_data: { sku_code: "ABC", low_stock_threshold: 20 },
        })}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/Low stock/i)).toBeInTheDocument();
  });

  it("renders status label", () => {
    render(
      <SkuEntry
        variant={makeSkuVariant({ status: EditionStatus.DRAFT })}
        tone="draft"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/Borrador/i)).toBeInTheDocument();
  });

  it("marks entry as pressed when selected", () => {
    render(
      <SkuEntry variant={makeSkuVariant()} tone="active" isSelected={true} onClick={vi.fn()} />,
    );
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "true");
  });
});
