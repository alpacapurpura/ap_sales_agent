import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

import { useVisibleSections, EVERGREEN_CODE } from "../use-visible-sections";
import { OfferArchetype } from "../../types";

import { MOCK_ARCHETYPE_CATALOG_RESPONSE } from "../../__tests__/fixtures/archetype-catalog-fixture";

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useVisibleSections", () => {
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

  it("hides edition_level sections under the evergreen code", async () => {
    const { result } = renderHook(
      () => useVisibleSections(OfferArchetype.EXPERIENCIA, EVERGREEN_CODE),
      { wrapper },
    );
    await waitFor(() => expect(result.current).toBeDefined());
    const scopes = result.current?.map((s) => s.scope) ?? [];
    expect(scopes).not.toContain("edition_level");
    expect(result.current?.find((s) => s.key === "event_details")).toBeUndefined();
  });

  it("shows every section on a specific edition code", async () => {
    const { result } = renderHook(() => useVisibleSections(OfferArchetype.EXPERIENCIA, "1"), {
      wrapper,
    });
    await waitFor(() => expect(result.current).toBeDefined());
    expect(result.current?.find((s) => s.key === "event_details")).toBeDefined();
  });

  it("returns the full list for archetypes with no edition_level sections even under evergreen", async () => {
    const { result } = renderHook(
      () => useVisibleSections(OfferArchetype.PRODUCTO, EVERGREEN_CODE),
      { wrapper },
    );
    await waitFor(() => expect(result.current).toBeDefined());
    // PRODUCTO has no edition_level sections — filter is a no-op.
    expect(result.current?.length).toBe(10);
  });

  it("returns undefined while the catalog loads", () => {
    const { result } = renderHook(
      () => useVisibleSections(OfferArchetype.EXPERIENCIA, EVERGREEN_CODE),
      { wrapper },
    );
    expect(result.current).toBeUndefined();
  });

  it("memoizes the filtered array across identical renders", async () => {
    const { result, rerender } = renderHook(
      () => useVisibleSections(OfferArchetype.EXPERIENCIA, EVERGREEN_CODE),
      { wrapper },
    );
    await waitFor(() => expect(result.current).toBeDefined());
    const first = result.current;
    rerender();
    expect(result.current).toBe(first);
  });
});
