import { describe, it, expect } from "vitest";

import { backendToFrontend } from "../adapter";
import { OfferArchetype, OfferStatus } from "../../types";

import { MOCK_BACKEND_RESPONSE } from "../../__tests__/fixtures";

import type { BackendOffer } from "../adapter";

describe("Dashboard Logic & Adapter", () => {
  it('Adapter normalizes "public_name" to "name"', () => {
    const result = backendToFrontend(MOCK_BACKEND_RESPONSE as BackendOffer);
    expect(result.name).toBe("Guía: Liberar la Mente");
  });

  it('Adapter maps backend status "active" to OfferStatus.ACTIVE', () => {
    const result = backendToFrontend(MOCK_BACKEND_RESPONSE as BackendOffer);
    expect(result.status).toBe(OfferStatus.ACTIVE);
  });

  it("Adapter handles unknown archetype gracefully", () => {
    const weirdData = { ...MOCK_BACKEND_RESPONSE, archetype: "UNKNOWN_ARCH_XYZ" } as BackendOffer;
    const result = backendToFrontend(weirdData);

    // Should fallback to default (PRODUCTO) instead of crashing
    expect(result.archetype).toBe(OfferArchetype.PRODUCTO);
  });
});
