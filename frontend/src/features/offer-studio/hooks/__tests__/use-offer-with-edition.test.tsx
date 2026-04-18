import { renderHook } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import type { LaunchEdition } from "../../types";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockUseParams = vi.fn();
const mockUseEditions = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => mockUseParams(),
}));

vi.mock("../use-editions", () => ({
  useEditions: (...args: unknown[]) => mockUseEditions(...args),
}));

// ── Imports after mocks ──────────────────────────────────────────────────────

import { useOfferWithEdition } from "../use-offer-with-edition";
import { EditionStatus, EditionVisibility } from "../../types";

// ── Fixtures ─────────────────────────────────────────────────────────────────

function buildEdition(overrides: Partial<LaunchEdition> = {}): LaunchEdition {
  return {
    id: "ed-default",
    offer_id: "offer-1",
    edition_name: "",
    edition_number: 1,
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

const editionActive = buildEdition({
  id: "ed-active",
  edition_number: 3,
  status: EditionStatus.ACTIVE,
  start_date: "2026-03-01T12:00:00Z",
});
const editionUpcoming = buildEdition({
  id: "ed-upcoming",
  edition_number: 4,
  status: EditionStatus.UPCOMING,
  start_date: "2026-07-15T12:00:00Z",
  visibility: EditionVisibility.PUBLIC,
});
const editionCompleted = buildEdition({
  id: "ed-completed",
  edition_number: 2,
  status: EditionStatus.COMPLETED,
  start_date: "2026-01-15T12:00:00Z",
});

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("useOfferWithEdition — reads editionId from route params", () => {
  beforeEach(() => {
    mockUseParams.mockReset();
    mockUseEditions.mockReset();
  });

  it("returns the edition matching route param editionId", () => {
    mockUseParams.mockReturnValue({ tenantId: "acme", id: "offer-1", editionId: "ed-upcoming" });
    mockUseEditions.mockReturnValue({
      editions: [editionActive, editionUpcoming, editionCompleted],
      loading: false,
    });

    const { result } = renderHook(() => useOfferWithEdition("offer-1"));
    expect(result.current.currentEditionId).toBe("ed-upcoming");
    expect(result.current.currentEdition).toBe(editionUpcoming);
  });

  it("falls back to ACTIVE edition when route param is absent", () => {
    mockUseParams.mockReturnValue({ tenantId: "acme", id: "offer-1" });
    mockUseEditions.mockReturnValue({
      editions: [editionActive, editionUpcoming, editionCompleted],
      loading: false,
    });

    const { result } = renderHook(() => useOfferWithEdition("offer-1"));
    expect(result.current.currentEditionId).toBe("ed-active");
  });

  it("falls back to soonest UPCOMING when no ACTIVE exists", () => {
    mockUseParams.mockReturnValue({ tenantId: "acme", id: "offer-1" });
    mockUseEditions.mockReturnValue({
      editions: [editionUpcoming, editionCompleted],
      loading: false,
    });

    const { result } = renderHook(() => useOfferWithEdition("offer-1"));
    expect(result.current.currentEditionId).toBe("ed-upcoming");
  });

  it("falls back to latest COMPLETED when no ACTIVE/UPCOMING exist", () => {
    mockUseParams.mockReturnValue({ tenantId: "acme", id: "offer-1" });
    mockUseEditions.mockReturnValue({
      editions: [editionCompleted],
      loading: false,
    });

    const { result } = renderHook(() => useOfferWithEdition("offer-1"));
    expect(result.current.currentEditionId).toBe("ed-completed");
  });

  it("returns null when the editions list is empty", () => {
    mockUseParams.mockReturnValue({ tenantId: "acme", id: "offer-1" });
    mockUseEditions.mockReturnValue({ editions: [], loading: false });

    const { result } = renderHook(() => useOfferWithEdition("offer-1"));
    expect(result.current.currentEditionId).toBeNull();
    expect(result.current.currentEdition).toBeNull();
  });

  it("ignores a stale/deleted editionId from params and falls back", () => {
    mockUseParams.mockReturnValue({ tenantId: "acme", id: "offer-1", editionId: "ed-ghost" });
    mockUseEditions.mockReturnValue({
      editions: [editionActive, editionUpcoming],
      loading: false,
    });

    const { result } = renderHook(() => useOfferWithEdition("offer-1"));
    expect(result.current.currentEditionId).toBe("ed-active");
  });

  it("ignores array-shaped editionId values (defensive against catch-all segments)", () => {
    mockUseParams.mockReturnValue({ tenantId: "acme", id: "offer-1", editionId: ["ed-upcoming"] });
    mockUseEditions.mockReturnValue({
      editions: [editionActive, editionUpcoming],
      loading: false,
    });

    const { result } = renderHook(() => useOfferWithEdition("offer-1"));
    // String arrays are ignored → falls back to ACTIVE.
    expect(result.current.currentEditionId).toBe("ed-active");
  });

  it("forwards loading state from useEditions", () => {
    mockUseParams.mockReturnValue({ tenantId: "acme", id: "offer-1" });
    mockUseEditions.mockReturnValue({ editions: [], loading: true });

    const { result } = renderHook(() => useOfferWithEdition("offer-1"));
    expect(result.current.loading).toBe(true);
  });
});
