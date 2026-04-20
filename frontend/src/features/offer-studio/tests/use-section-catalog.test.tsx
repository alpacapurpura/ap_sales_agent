import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

import { useSectionCatalog, useSectionMetadata } from "../hooks/use-section-catalog";

import { MOCK_ARCHETYPE_CATALOG_RESPONSE } from "./fixtures/archetype-catalog-fixture";

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useSectionCatalog", () => {
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

  it("returns undefined while loading", () => {
    const { result } = renderHook(() => useSectionCatalog(), { wrapper });
    expect(result.current).toBeUndefined();
  });

  it("returns a readonly Map keyed by SectionKey", async () => {
    const { result } = renderHook(() => useSectionCatalog(), { wrapper });
    await waitFor(() => expect(result.current).toBeDefined());
    expect(result.current).toBeInstanceOf(Map);
    expect(result.current?.get("identity")?.label_es).toBeTruthy();
    expect(result.current?.get("pricing")?.scope).toBe("mixed");
    expect(result.current?.get("event_details")?.scope).toBe("edition_level");
  });

  it("memoizes the map across renders against the same payload", async () => {
    const { result, rerender } = renderHook(() => useSectionCatalog(), { wrapper });
    await waitFor(() => expect(result.current).toBeDefined());
    const first = result.current;
    rerender();
    expect(result.current).toBe(first);
  });
});

describe("useSectionMetadata", () => {
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

  it("returns metadata for a known key", async () => {
    const { result } = renderHook(() => useSectionMetadata("promise"), { wrapper });
    await waitFor(() => expect(result.current).toBeDefined());
    expect(result.current?.key).toBe("promise");
    expect(result.current?.scope).toBe("offer_level");
  });

  it("returns undefined when key is undefined", () => {
    const { result } = renderHook(() => useSectionMetadata(undefined), { wrapper });
    expect(result.current).toBeUndefined();
  });
});
