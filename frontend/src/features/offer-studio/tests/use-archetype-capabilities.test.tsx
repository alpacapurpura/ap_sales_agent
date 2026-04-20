import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

import { useArchetypeCapabilities } from "../hooks/use-archetype-catalog";
import { OfferArchetype } from "../types";

import { MOCK_ARCHETYPE_CATALOG_RESPONSE } from "./fixtures/archetype-catalog-fixture";

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

  it("returns capabilities with null wizard copy for non-edition archetype", async () => {
    const { result } = renderHook(() => useArchetypeCapabilities(OfferArchetype.PRODUCTO), {
      wrapper,
    });
    await waitFor(() => expect(result.current).toBeDefined());
    expect(result.current?.supports_editions).toBe(false);
    expect(result.current?.editions_wizard_copy).toBeNull();
  });

  it("returns undefined for undefined archetype", () => {
    const { result } = renderHook(() => useArchetypeCapabilities(undefined), { wrapper });
    expect(result.current).toBeUndefined();
  });
});
