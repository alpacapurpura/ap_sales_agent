import { describe, expect, it } from "vitest";

import { getSectionsForOffer, SECTION_REGISTRY } from "../config/offer-builder-config";
import { OfferArchetype } from "../types";

describe("getSectionsForOffer — v3 section ownership", () => {
  // ── Editions are owned by the rail, not by an inline Info section ─────────

  it("never includes 'editions' — the rail owns edition management", () => {
    for (const archetype of Object.values(OfferArchetype)) {
      const withEditions = getSectionsForOffer({ archetype, has_editions: true });
      const withoutEditions = getSectionsForOffer({ archetype, has_editions: false });
      expect(withEditions).not.toContain("editions");
      expect(withoutEditions).not.toContain("editions");
    }
  });

  // ── Gallery moved from Info to Assets tab ─────────────────────────────────

  it("never includes 'gallery' — lives in the Assets tab, not in Info", () => {
    for (const archetype of Object.values(OfferArchetype)) {
      const sections = getSectionsForOffer({ archetype, has_editions: true });
      expect(sections).not.toContain("gallery");
    }
  });

  // ── Knowledge migrated from dedicated tab to a section inside Info ─────────

  it("always includes 'knowledge' as a section of Info (replaces the retired tab)", () => {
    for (const archetype of Object.values(OfferArchetype)) {
      const sections = getSectionsForOffer({ archetype, has_editions: true });
      expect(sections).toContain("knowledge");
    }
  });

  it("registers 'knowledge' in the SECTION_REGISTRY so it can be rendered", () => {
    expect(SECTION_REGISTRY.knowledge).toBeDefined();
    expect(SECTION_REGISTRY.knowledge.id).toBe("knowledge");
    expect(typeof SECTION_REGISTRY.knowledge.title).toBe("string");
  });

  // ── Core archetype-scoped sections still render ───────────────────────────

  it("keeps archetype-specific detail sections", () => {
    expect(getSectionsForOffer({ archetype: OfferArchetype.PROGRAMA })).toContain(
      "program_details",
    );
    expect(getSectionsForOffer({ archetype: OfferArchetype.SERVICIO })).toContain(
      "service_details",
    );
    expect(getSectionsForOffer({ archetype: OfferArchetype.EXPERIENCIA })).toContain(
      "event_details",
    );
    expect(getSectionsForOffer({ archetype: OfferArchetype.PRODUCTO })).toContain(
      "product_details",
    );
    expect(getSectionsForOffer({ archetype: OfferArchetype.MEMBRESIA })).toContain(
      "subscription_details",
    );
  });

  it("keeps pricing and closing in every archetype", () => {
    for (const archetype of Object.values(OfferArchetype)) {
      const sections = getSectionsForOffer({ archetype });
      expect(sections).toContain("pricing");
      expect(sections).toContain("closing");
    }
  });
});
