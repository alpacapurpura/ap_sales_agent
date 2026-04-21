import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { useOfferSettings } from "../use-offer-settings";

import type { LaunchEdition } from "../../types";
import type { OfferFormValues } from "../../types/schema";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockSaveSection = vi.fn(async (_section: string, _values: OfferFormValues) => undefined);
const mockSaveOffer = vi.fn();
const mockRefetch = vi.fn();
const mockUseOffer = vi.fn();
const mockUseOfferWithEdition = vi.fn();

vi.mock("../use-offer", () => ({
  useOffer: (...args: unknown[]) => mockUseOffer(...args),
}));

vi.mock("../use-offer-with-edition", () => ({
  useOfferWithEdition: (...args: unknown[]) => mockUseOfferWithEdition(...args),
}));

// ── Imports after mocks ──────────────────────────────────────────────────────

// ── Fixtures ─────────────────────────────────────────────────────────────────

const baseFormValues = {
  public_name: "Mentoría 12 semanas",
  internal_sku: "mentoria-12w",
  archetype: "PROGRAMA",
  status: "DRAFT",
  headline_promise: "Transforma tu negocio",
  currency: "USD",
} as unknown as OfferFormValues;

const mockEdition = {
  id: "ed-1",
  offer_id: "offer-1",
  edition_name: "Default",
  edition_number: 1,
} as LaunchEdition;

function setupMocks(
  overrides: {
    formValues?: OfferFormValues | undefined;
    offer?: unknown;
    loading?: boolean;
  } = {},
) {
  mockSaveSection.mockClear();
  mockSaveOffer.mockClear();
  const resolvedFormValues = "formValues" in overrides ? overrides.formValues : baseFormValues;
  mockUseOffer.mockReturnValue({
    offer: overrides.offer ?? { id: "offer-1" },
    formValues: resolvedFormValues,
    loading: overrides.loading ?? false,
    saving: false,
    error: null,
    saveOffer: mockSaveOffer,
    saveSection: mockSaveSection,
    refetch: mockRefetch,
  });
  mockUseOfferWithEdition.mockReturnValue({
    editions: [mockEdition],
    currentEditionId: "ed-1",
    currentEdition: mockEdition,
    loading: false,
  });
}

describe("useOfferSettings", () => {
  beforeEach(() => {
    setupMocks();
  });

  it("exposes settings sourced from useOffer.formValues", () => {
    const { result } = renderHook(() => useOfferSettings("offer-1"));
    expect(result.current.settings).toEqual(baseFormValues);
  });

  it("surfaces the current edition from useOfferWithEdition", () => {
    const { result } = renderHook(() => useOfferSettings("offer-1"));
    expect(result.current.edition).toBe(mockEdition);
    expect(result.current.editionId).toBe("ed-1");
    expect(result.current.editions).toHaveLength(1);
  });

  it("reports loading when either underlying hook is loading", () => {
    setupMocks({ loading: true });
    const { result } = renderHook(() => useOfferSettings("offer-1"));
    expect(result.current.loading).toBe(true);
  });

  it("updateIdentity calls saveSection with 'identity' + merged values", async () => {
    const { result } = renderHook(() => useOfferSettings("offer-1"));
    await result.current.updateIdentity({ public_name: "New name" } as Partial<OfferFormValues>);

    await waitFor(() => expect(mockSaveSection).toHaveBeenCalledTimes(1));
    expect(mockSaveSection.mock.calls[0][0]).toBe("identity");
    expect(mockSaveSection.mock.calls[0][1]).toMatchObject({
      public_name: "New name",
      internal_sku: "mentoria-12w",
      archetype: "PROGRAMA",
    });
  });

  it("updatePromise routes to saveSection('promise', …) — keyed updaters", async () => {
    const { result } = renderHook(() => useOfferSettings("offer-1"));
    await result.current.updatePromise({
      headline_promise: "New promise",
    } as Partial<OfferFormValues>);
    await waitFor(() => expect(mockSaveSection).toHaveBeenCalledTimes(1));
    expect(mockSaveSection.mock.calls[0][0]).toBe("promise");
    expect(mockSaveSection.mock.calls[0][1]).toMatchObject({
      headline_promise: "New promise",
    });
  });

  it("updatePricing routes to saveSection('pricing', …)", async () => {
    const { result } = renderHook(() => useOfferSettings("offer-1"));
    await result.current.updatePricing({ currency: "MXN" } as Partial<OfferFormValues>);
    await waitFor(() => expect(mockSaveSection).toHaveBeenCalledTimes(1));
    expect(mockSaveSection.mock.calls[0][0]).toBe("pricing");
  });

  it("is a no-op when formValues is undefined (loading or error)", async () => {
    setupMocks({ formValues: undefined });
    const { result } = renderHook(() => useOfferSettings("offer-1"));
    await result.current.updateIdentity({
      public_name: "Whatever",
    } as Partial<OfferFormValues>);
    expect(mockSaveSection).not.toHaveBeenCalled();
  });

  it("exposes typed section updaters for every SectionKey on Offer root", () => {
    const { result } = renderHook(() => useOfferSettings("offer-1"));
    const hook = result.current;
    // Brand-parity surface — one typed updater per singleton section.
    expect(typeof hook.updateIdentity).toBe("function");
    expect(typeof hook.updatePromise).toBe("function");
    expect(typeof hook.updateStrategy).toBe("function");
    expect(typeof hook.updatePsychology).toBe("function");
    expect(typeof hook.updatePricing).toBe("function");
    expect(typeof hook.updateClosing).toBe("function");
    expect(typeof hook.updateValueStack).toBe("function");
    expect(typeof hook.updateProgramDetails).toBe("function");
    expect(typeof hook.updateProductDetails).toBe("function");
    expect(typeof hook.updateServiceDetails).toBe("function");
    expect(typeof hook.updateEventDetails).toBe("function");
    expect(typeof hook.updateSubscriptionDetails).toBe("function");
    expect(typeof hook.updatePlatformDetails).toBe("function");
    expect(typeof hook.updateLocation).toBe("function");
  });
});
