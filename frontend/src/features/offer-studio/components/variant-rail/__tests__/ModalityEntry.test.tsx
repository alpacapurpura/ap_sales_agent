import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it, vi } from "vitest";

import { EditionStatus, EditionVisibility } from "../../../types";
import { ModalityEntry } from "../entries/ModalityEntry";

import type { LaunchEdition } from "../../../types";

function makeModalityVariant(overrides: Partial<LaunchEdition> = {}): LaunchEdition {
  return {
    id: "modality-1",
    offer_id: "offer-1",
    edition_name: "Presencial",
    edition_number: 1,
    variant_structure: "modality",
    structure_data: {
      mode: "presencial",
      price_amount: 129,
      price_currency: "USD",
      venue: "CDMX",
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
    capacity: 20,
    enrollment_count: 12,
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

describe("ModalityEntry", () => {
  it("renders the modality name", () => {
    render(
      <ModalityEntry
        variant={makeModalityVariant()}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/Presencial/)).toBeInTheDocument();
  });

  it("renders 🏢 icon for presencial mode", () => {
    render(
      <ModalityEntry
        variant={makeModalityVariant({ structure_data: { mode: "presencial" } })}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/🏢/)).toBeInTheDocument();
  });

  it("renders 💻 icon for online mode", () => {
    render(
      <ModalityEntry
        variant={makeModalityVariant({
          edition_name: "Online",
          structure_data: { mode: "online" },
        })}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/💻/)).toBeInTheDocument();
  });

  it("renders 🔀 icon for hibrido mode", () => {
    render(
      <ModalityEntry
        variant={makeModalityVariant({
          edition_name: "Híbrido",
          structure_data: { mode: "hibrido" },
        })}
        tone="draft"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/🔀/)).toBeInTheDocument();
  });

  it("renders price from structure_data", () => {
    render(
      <ModalityEntry
        variant={makeModalityVariant()}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/\$129/)).toBeInTheDocument();
  });

  it("renders capacity as cupos when presencial", () => {
    render(
      <ModalityEntry
        variant={makeModalityVariant({ capacity: 20, enrollment_count: 12 })}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/12\/20/)).toBeInTheDocument();
  });

  it("marks entry as pressed when selected", () => {
    render(
      <ModalityEntry
        variant={makeModalityVariant()}
        tone="active"
        isSelected={true}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "true");
  });
});
