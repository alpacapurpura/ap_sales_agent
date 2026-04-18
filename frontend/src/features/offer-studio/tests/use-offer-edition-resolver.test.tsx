import { renderHook } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { EditionStatus, EditionVisibility } from "../types";

import type { LaunchEdition } from "../types";

const mockUseEditions = vi.fn();

vi.mock("../hooks/use-editions", () => ({
  useEditions: (...args: unknown[]) => mockUseEditions(...args),
}));

// Mock the catalog hook out of the transitive graph so tests don't need
// a live ``@/lib/config`` resolution. The resolver itself never calls
// the catalog — it only imports ``EVERGREEN_CODE`` from this module.
vi.mock("../hooks/use-archetype-catalog", () => ({
  useArchetypeCatalog: () => ({ data: undefined }),
  useArchetypeCapabilities: () => undefined,
}));

const { useOfferEditionResolver } = await import("../hooks/use-offer-edition-resolver");
const { EVERGREEN_CODE } = await import("../hooks/use-visible-sections");

const EDITION_ONE: LaunchEdition = {
  id: "550e8400-e29b-41d4-a716-446655440001",
  offer_id: "offer-1",
  edition_name: "Cohorte #1",
  edition_number: 1,
  status: EditionStatus.UPCOMING,
  visibility: EditionVisibility.PUBLIC,
  start_date: "2026-05-01T00:00:00Z",
  end_date: null,
  registration_start: null,
  registration_end: null,
  pricing_override: null,
  pricing_tiers: [],
  active_tier: null,
  effective_pricing: [],
  currency: "USD",
  capacity: null,
  enrollment_count: 0,
  timezone: "UTC",
  is_placeholder: false,
  location_override: null,
  notes: null,
  cloned_from_edition_id: null,
  created_at: null,
  updated_at: null,
};

const EDITION_THREE: LaunchEdition = {
  ...EDITION_ONE,
  id: "550e8400-e29b-41d4-a716-446655440003",
  edition_name: "Cohorte #3",
  edition_number: 3,
};

describe("useOfferEditionResolver", () => {
  beforeEach(() => {
    mockUseEditions.mockReset();
    mockUseEditions.mockReturnValue({ editions: [EDITION_ONE, EDITION_THREE], loading: false });
  });

  it("resolves evergreen code to offer-level mode with no edition row", () => {
    const { result } = renderHook(() => useOfferEditionResolver("offer-1", EVERGREEN_CODE));
    expect(result.current.status).toBe("ready");
    expect(result.current.mode).toBe("evergreen");
    expect(result.current.edition).toBeNull();
    expect(result.current.editions).toHaveLength(2);
  });

  it("resolves undefined code to evergreen mode (offer-level URL)", () => {
    const { result } = renderHook(() => useOfferEditionResolver("offer-1", undefined));
    expect(result.current.status).toBe("ready");
    expect(result.current.mode).toBe("evergreen");
  });

  it("resolves a matching edition_number", () => {
    const { result } = renderHook(() => useOfferEditionResolver("offer-1", "3"));
    expect(result.current.status).toBe("ready");
    expect(result.current.mode).toBe("edition");
    expect(result.current.edition?.edition_number).toBe(3);
    expect(result.current.edition?.id).toBe(EDITION_THREE.id);
  });

  it("returns not_found when the edition_number is missing", () => {
    const { result } = renderHook(() => useOfferEditionResolver("offer-1", "42"));
    expect(result.current.status).toBe("not_found");
    expect(result.current.edition).toBeNull();
  });

  it("rejects non-numeric codes as not_found (never collapses to evergreen)", () => {
    const { result } = renderHook(() => useOfferEditionResolver("offer-1", "abc"));
    expect(result.current.status).toBe("not_found");
  });

  it("rejects zero and negative codes", () => {
    const { result } = renderHook(() => useOfferEditionResolver("offer-1", "0"));
    expect(result.current.status).toBe("not_found");
  });

  it("rejects decimal codes", () => {
    const { result } = renderHook(() => useOfferEditionResolver("offer-1", "1.5"));
    expect(result.current.status).toBe("not_found");
  });

  it("reports loading while editions fetch is in flight", () => {
    mockUseEditions.mockReturnValue({ editions: [], loading: true });
    const { result } = renderHook(() => useOfferEditionResolver("offer-1", "1"));
    expect(result.current.status).toBe("loading");
  });
});
