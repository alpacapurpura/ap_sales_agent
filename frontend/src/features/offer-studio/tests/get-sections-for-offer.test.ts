import { describe, expect, it } from "vitest";

import { getSectionsForOffer } from "../config/offer-builder-config";
import { OfferArchetype } from "../types";

describe("getSectionsForOffer — has_editions gating", () => {
  it("keeps 'editions' for PROGRAMA when has_editions is true", () => {
    const sections = getSectionsForOffer({
      archetype: OfferArchetype.PROGRAMA,
      has_editions: true,
    });
    expect(sections).toContain("editions");
  });

  it("hides 'editions' for PROGRAMA when has_editions is false", () => {
    const sections = getSectionsForOffer({
      archetype: OfferArchetype.PROGRAMA,
      has_editions: false,
    });
    expect(sections).not.toContain("editions");
    // Non-editions sections stay
    expect(sections).toContain("program_details");
    expect(sections).toContain("pricing");
  });

  it("hides 'editions' for SERVICIO when has_editions is false", () => {
    const sections = getSectionsForOffer({
      archetype: OfferArchetype.SERVICIO,
      has_editions: false,
    });
    expect(sections).not.toContain("editions");
  });

  it("hides 'editions' for EXPERIENCIA when has_editions is false", () => {
    const sections = getSectionsForOffer({
      archetype: OfferArchetype.EXPERIENCIA,
      has_editions: false,
    });
    expect(sections).not.toContain("editions");
  });

  it("defaults to showing 'editions' for supported archetypes when field is missing", () => {
    // Back-compat: offers loaded before this feature have undefined has_editions
    const sections = getSectionsForOffer({
      archetype: OfferArchetype.PROGRAMA,
    });
    expect(sections).toContain("editions");
  });

  it("ignores has_editions for PRODUCTO (never had editions)", () => {
    const sections = getSectionsForOffer({
      archetype: OfferArchetype.PRODUCTO,
      has_editions: true,
    });
    expect(sections).not.toContain("editions");
  });

  it("ignores has_editions for MEMBRESIA (never had editions)", () => {
    const sections = getSectionsForOffer({
      archetype: OfferArchetype.MEMBRESIA,
      has_editions: true,
    });
    expect(sections).not.toContain("editions");
  });
});
