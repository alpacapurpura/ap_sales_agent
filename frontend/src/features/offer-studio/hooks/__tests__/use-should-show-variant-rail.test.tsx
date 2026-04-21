// @vitest-environment happy-dom
import { renderHook } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { EditionStatus, EditionVisibility } from "../../types";

import type { ArchetypeCapabilities } from "../../api/archetype-catalog-api";
import type { LaunchEdition, OfferArchetype } from "../../types";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockUseArchetypeCapabilities = vi.fn();

vi.mock("../use-archetype-catalog", () => ({
  useArchetypeCapabilities: (...args: unknown[]) => mockUseArchetypeCapabilities(...args),
}));

// ── Imports after mocks ──────────────────────────────────────────────────────

import { buildNoVariantRedirect, useShouldShowVariantRail } from "../use-should-show-variant-rail";

// ── Fixtures ─────────────────────────────────────────────────────────────────

function buildVariant(overrides: Partial<LaunchEdition> = {}): LaunchEdition {
  return {
    id: "v-1",
    offer_id: "o-1",
    edition_name: "Default",
    edition_number: 1,
    variant_structure: "temporal_cohort",
    structure_data: {},
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
    status: EditionStatus.DRAFT,
    visibility: EditionVisibility.PRIVATE,
    is_placeholder: false,
    location_override: null,
    notes: null,
    cloned_from_edition_id: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

function caps(allow_single_variant: boolean): ArchetypeCapabilities {
  return {
    archetype: "PROGRAMA" as OfferArchetype,
    label: "Programa",
    description: "",
    default_delivery: "DWY",
    default_fulfillment: "HYBRID",
    base_sections: [],
    allow_single_variant,
    has_editions: true,
    supports_editions: true,
    supported_variant_structures: [],
  } as unknown as ArchetypeCapabilities;
}

describe("useShouldShowVariantRail", () => {
  beforeEach(() => {
    mockUseArchetypeCapabilities.mockReset();
  });

  it("returns catalog-loading when capabilities not yet resolved", () => {
    mockUseArchetypeCapabilities.mockReturnValue(undefined);
    const { result } = renderHook(() =>
      useShouldShowVariantRail({ archetype: "PROGRAMA" as OfferArchetype, variants: [] }),
    );
    expect(result.current).toEqual({ shouldShow: false, reason: "catalog-loading" });
  });

  it("hides rail when zero variants (rare but defensive)", () => {
    mockUseArchetypeCapabilities.mockReturnValue(caps(false));
    const { result } = renderHook(() =>
      useShouldShowVariantRail({ archetype: "PROGRAMA" as OfferArchetype, variants: [] }),
    );
    expect(result.current).toEqual({ shouldShow: false, reason: "no-variants" });
  });

  it("shows rail for a single variant when archetype forbids single-variant-only", () => {
    mockUseArchetypeCapabilities.mockReturnValue(caps(false));
    const { result } = renderHook(() =>
      useShouldShowVariantRail({
        archetype: "PROGRAMA" as OfferArchetype,
        variants: [buildVariant()],
      }),
    );
    expect(result.current).toEqual({ shouldShow: true, reason: "archetype-forbids-single" });
  });

  it("hides rail for a single variant when archetype allows single-variant-only", () => {
    mockUseArchetypeCapabilities.mockReturnValue(caps(true));
    const { result } = renderHook(() =>
      useShouldShowVariantRail({
        archetype: "LEAD_MAGNET" as OfferArchetype,
        variants: [buildVariant()],
      }),
    );
    expect(result.current).toEqual({ shouldShow: false, reason: "single-variant-allowed" });
  });

  it("shows rail for multiple variants regardless of archetype default", () => {
    mockUseArchetypeCapabilities.mockReturnValue(caps(true));
    const { result } = renderHook(() =>
      useShouldShowVariantRail({
        archetype: "MEMBRESIA" as OfferArchetype,
        variants: [buildVariant({ id: "v-1" }), buildVariant({ id: "v-2" })],
      }),
    );
    expect(result.current).toEqual({ shouldShow: true, reason: "multiple-variants" });
  });
});

describe("buildNoVariantRedirect", () => {
  it("returns the editor path for /offer/{id}/editions", () => {
    expect(buildNoVariantRedirect("/t-1/offer-studio/offer/o-1/editions")).toBe(
      "/t-1/offer-studio/offer/o-1/editor",
    );
  });

  it("returns the editor path for /offer/{id}/editions/{editionId}", () => {
    expect(buildNoVariantRedirect("/t-1/offer-studio/offer/o-1/editions/ed-123")).toBe(
      "/t-1/offer-studio/offer/o-1/editor",
    );
  });

  it("returns null for non-editions paths", () => {
    expect(buildNoVariantRedirect("/t-1/offer-studio/offer/o-1/editor")).toBeNull();
    expect(buildNoVariantRedirect("/t-1/offer-studio/offer/o-1")).toBeNull();
    expect(buildNoVariantRedirect("/t-1/brand-studio/identity")).toBeNull();
  });

  it("preserves custom tenant segments (uuid-style)", () => {
    const tenant = "a1b2c3d4-e5f6-7890-abcd-ef1234567890";
    expect(buildNoVariantRedirect(`/${tenant}/offer-studio/offer/o-9/editions`)).toBe(
      `/${tenant}/offer-studio/offer/o-9/editor`,
    );
  });
});
