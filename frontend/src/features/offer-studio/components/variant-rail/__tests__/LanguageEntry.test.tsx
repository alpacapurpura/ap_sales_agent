import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it, vi } from "vitest";

import { EditionStatus, EditionVisibility } from "../../../types";
import { LanguageEntry } from "../entries/LanguageEntry";

import type { LaunchEdition } from "../../../types";

function makeLangVariant(overrides: Partial<LaunchEdition> = {}): LaunchEdition {
  return {
    id: "lang-1",
    offer_id: "offer-1",
    edition_name: "Português",
    edition_number: 1,
    variant_structure: "language",
    structure_data: {
      flag_emoji: "🇧🇷",
      locale: "PT-BR",
      translation_progress: 8,
      translation_total: 14,
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

describe("LanguageEntry", () => {
  it("renders the language name", () => {
    render(
      <LanguageEntry
        variant={makeLangVariant()}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/Português/)).toBeInTheDocument();
  });

  it("renders the flag emoji", () => {
    render(
      <LanguageEntry
        variant={makeLangVariant()}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/🇧🇷/)).toBeInTheDocument();
  });

  it("renders module progress count", () => {
    render(
      <LanguageEntry
        variant={makeLangVariant()}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/8\/14/)).toBeInTheDocument();
  });

  it("shows 'En traducción' status when progress < total", () => {
    render(
      <LanguageEntry
        variant={makeLangVariant()}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/En traducción/i)).toBeInTheDocument();
  });

  it("shows 'Completo' status when progress === total", () => {
    render(
      <LanguageEntry
        variant={makeLangVariant({
          structure_data: {
            flag_emoji: "🇪🇸",
            locale: "ES",
            translation_progress: 14,
            translation_total: 14,
          },
        })}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/Completo/i)).toBeInTheDocument();
  });

  it("renders a progress bar element", () => {
    const { container } = render(
      <LanguageEntry
        variant={makeLangVariant()}
        tone="active"
        isSelected={false}
        onClick={vi.fn()}
      />,
    );
    // Expect a div with role or an element representing the progress bar fill
    const progressBar = container.querySelector("[role='progressbar']");
    expect(progressBar).not.toBeNull();
  });

  it("marks entry as pressed when selected", () => {
    render(
      <LanguageEntry
        variant={makeLangVariant()}
        tone="active"
        isSelected={true}
        onClick={vi.fn()}
      />,
    );
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "true");
  });
});
