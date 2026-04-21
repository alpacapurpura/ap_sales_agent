import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it, vi } from "vitest";

import { EditionStatus, EditionVisibility } from "../../../types";
import { TemporalEntry } from "../entries/TemporalEntry";

import type { LaunchEdition } from "../../../types";

function makeTemporal(overrides: Partial<LaunchEdition> = {}): LaunchEdition {
  return {
    id: "ed-1",
    offer_id: "offer-1",
    edition_name: "Edición #1",
    edition_number: 1,
    variant_structure: "temporal_cohort",
    structure_data: {},
    sort_rank: null,
    start_date: "2026-07-15T19:00:00Z",
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
    enrollment_count: 12,
    status: EditionStatus.UPCOMING,
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

describe("TemporalEntry", () => {
  it("renders the edition number", () => {
    render(
      <TemporalEntry
        variant={makeTemporal()}
        tone="next"
        isSelected={false}
        waitlistCount={0}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText("Edición #1")).toBeInTheDocument();
  });

  it("renders status label", () => {
    render(
      <TemporalEntry
        variant={makeTemporal({ status: EditionStatus.ACTIVE })}
        tone="active"
        isSelected={false}
        waitlistCount={0}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/En curso/i)).toBeInTheDocument();
  });

  it("renders start date", () => {
    render(
      <TemporalEntry
        variant={makeTemporal()}
        tone="next"
        isSelected={false}
        waitlistCount={0}
        onClick={vi.fn()}
      />,
    );
    // Any date-like text rendered from start_date
    expect(screen.getByText(/jul|Jul|15/i)).toBeInTheDocument();
  });

  it("renders enrollment/capacity", () => {
    render(
      <TemporalEntry
        variant={makeTemporal({ capacity: 50, enrollment_count: 12 })}
        tone="next"
        isSelected={false}
        waitlistCount={0}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/12\/50/)).toBeInTheDocument();
  });

  it("shows public icon when PUBLIC visibility", () => {
    render(
      <TemporalEntry
        variant={makeTemporal({ visibility: EditionVisibility.PUBLIC })}
        tone="next"
        isSelected={false}
        waitlistCount={0}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/Pública/i)).toBeInTheDocument();
  });

  it("shows private icon when PRIVATE visibility", () => {
    render(
      <TemporalEntry
        variant={makeTemporal({ visibility: EditionVisibility.PRIVATE })}
        tone="draft"
        isSelected={false}
        waitlistCount={0}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/Privada/i)).toBeInTheDocument();
  });

  it("shows waitlist count when > 0", () => {
    render(
      <TemporalEntry
        variant={makeTemporal()}
        tone="draft"
        isSelected={true}
        waitlistCount={5}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/5 en waitlist/i)).toBeInTheDocument();
  });

  it("does not show waitlist section when count is 0", () => {
    render(
      <TemporalEntry
        variant={makeTemporal()}
        tone="next"
        isSelected={false}
        waitlistCount={0}
        onClick={vi.fn()}
      />,
    );
    expect(screen.queryByText(/waitlist/i)).toBeNull();
  });

  it("marks entry as pressed when selected", () => {
    render(
      <TemporalEntry
        variant={makeTemporal()}
        tone="next"
        isSelected={true}
        waitlistCount={0}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "true");
  });
});
