import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

import { MOCK_ARCHETYPE_CATALOG_RESPONSE } from "../../__tests__/fixtures/archetype-catalog-fixture";
import { OfferArchetype } from "../../types";
import { useArchetypeCapabilities } from "../use-archetype-catalog";

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useArchetypeCapabilities", () => {
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

  it("returns undefined while catalog is loading", () => {
    const { result } = renderHook(() => useArchetypeCapabilities(OfferArchetype.EXPERIENCIA), {
      wrapper,
    });
    expect(result.current).toBeUndefined();
  });

  it("returns capabilities for an edition-supporting archetype", async () => {
    const { result } = renderHook(() => useArchetypeCapabilities(OfferArchetype.EXPERIENCIA), {
      wrapper,
    });
    await waitFor(() => expect(result.current).toBeDefined());
    expect(result.current?.supports_editions).toBe(true);
    expect(result.current?.editions_wizard_copy).not.toBeNull();
  });

  it("returns sku-variant capabilities for PRODUCTO (Sprint 15.1)", async () => {
    const { result } = renderHook(() => useArchetypeCapabilities(OfferArchetype.PRODUCTO), {
      wrapper,
    });
    await waitFor(() => expect(result.current).toBeDefined());
    expect(result.current?.supports_editions).toBe(true);
    expect(result.current?.default_variant_structure).toBe("sku_variant");
    expect(result.current?.allow_single_variant).toBe(true);
    expect(result.current?.edition_noun_es).toBe("variante");
  });

  it("returns undefined for undefined archetype", () => {
    const { result } = renderHook(() => useArchetypeCapabilities(undefined), { wrapper });
    expect(result.current).toBeUndefined();
  });
});
