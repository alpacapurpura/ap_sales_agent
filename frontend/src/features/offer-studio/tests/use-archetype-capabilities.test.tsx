import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

import { useArchetypeCapabilities } from "../hooks/use-archetype-catalog";
import { OfferArchetype } from "../types";

import type { ArchetypeCatalogResponse } from "../api/archetype-catalog-api";

const MOCK_RESPONSE: ArchetypeCatalogResponse = {
  version: "test-version",
  archetypes: [
    {
      archetype: OfferArchetype.EXPERIENCIA,
      supports_editions: true,
      edition_structure: "single_date",
      edition_noun_es: "salida",
      edition_noun_plural_es: "salidas",
      requires_start_date_on_publish: true,
      requires_end_date_on_publish: false,
      requires_location_on_publish: true,
      supports_capacity: true,
      supports_waitlist: true,
      default_delivery: "dwy",
      default_fulfillment: "manual_provisioning",
      label_es: "Experiencia / Evento",
      subtitle_es: "Un momento único",
      icon_name: "Tent",
      examples_es: ["Retiro", "Taller"],
      editions_wizard_copy: {
        title: "¿Tendrá varias salidas?",
        description: "...",
        yes_label: "Sí",
        no_label: "No",
      },
    },
    {
      archetype: OfferArchetype.PRODUCTO,
      supports_editions: false,
      edition_structure: "none",
      edition_noun_es: "",
      edition_noun_plural_es: "",
      requires_start_date_on_publish: false,
      requires_end_date_on_publish: false,
      requires_location_on_publish: false,
      supports_capacity: false,
      supports_waitlist: false,
      default_delivery: "diy",
      default_fulfillment: "digital_download",
      label_es: "Producto",
      subtitle_es: "Algo que creas",
      icon_name: "Package",
      examples_es: ["Ebook", "Curso"],
      editions_wizard_copy: null,
    },
  ],
};

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
        new Response(JSON.stringify(MOCK_RESPONSE), {
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
