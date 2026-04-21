import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

import { useSectionsForArchetype } from "../use-sections-for-archetype";
import { OfferArchetype } from "../../types";

import { MOCK_ARCHETYPE_CATALOG_RESPONSE } from "../../__tests__/fixtures/archetype-catalog-fixture";

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useSectionsForArchetype", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = vi.fn(
      async () =>
        new Response(JSON.stringify(MOCK_ARCHETYPE_CATALOG_RESPONSE), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    ) as typeof fetch;
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("returns undefined while the catalog is loading", () => {
    const { result } = renderHook(() => useSectionsForArchetype(OfferArchetype.PROGRAMA), {
      wrapper,
    });
    expect(result.current).toBeUndefined();
  });

  it("returns the ordered section list for an archetype", async () => {
    const { result } = renderHook(() => useSectionsForArchetype(OfferArchetype.PROGRAMA), {
      wrapper,
    });
    await waitFor(() => expect(result.current).toBeDefined());
    const keys = result.current?.map((s) => s.key);
    expect(keys).toEqual([
      "identity",
      "strategy",
      "psychology",
      "promise",
      "program_details",
      "instructors",
      "value_stack",
      "resources",
      "pricing",
      "closing",
      "knowledge",
    ]);
  });

  it("returns section metadata with full labels and icons", async () => {
    const { result } = renderHook(() => useSectionsForArchetype(OfferArchetype.EXPERIENCIA), {
      wrapper,
    });
    await waitFor(() => expect(result.current).toBeDefined());
    const eventDetails = result.current?.find((s) => s.key === "event_details");
    expect(eventDetails?.scope).toBe("edition_level");
    expect(eventDetails?.label_es).toBeTruthy();
    expect(eventDetails?.icon_name).toBeTruthy();
  });

  it("returns undefined when archetype is undefined", () => {
    const { result } = renderHook(() => useSectionsForArchetype(undefined), { wrapper });
    expect(result.current).toBeUndefined();
  });

  it("differentiates between edition-supporting and edition-less archetypes", async () => {
    const { result: resultExp } = renderHook(
      () => useSectionsForArchetype(OfferArchetype.EXPERIENCIA),
      { wrapper },
    );
    const { result: resultProd } = renderHook(
      () => useSectionsForArchetype(OfferArchetype.PRODUCTO),
      { wrapper },
    );
    await waitFor(() => {
      expect(resultExp.current).toBeDefined();
      expect(resultProd.current).toBeDefined();
    });
    const expScopes = resultExp.current?.map((s) => s.scope) ?? [];
    const prodScopes = resultProd.current?.map((s) => s.scope) ?? [];
    expect(expScopes).toContain("edition_level");
    expect(prodScopes).not.toContain("edition_level");
  });
});
