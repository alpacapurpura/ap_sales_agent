import { describe, expect, it } from "vitest";

import { OfferArchetype } from "@/features/offer-studio/types";

import { archetypeSupportsEditions, getEditionsCopy } from "./editions-copy";

describe("archetypeSupportsEditions", () => {
  it.each([
    [OfferArchetype.PROGRAMA, true],
    [OfferArchetype.EXPERIENCIA, true],
    [OfferArchetype.SERVICIO, true],
    [OfferArchetype.PRODUCTO, false],
    [OfferArchetype.MEMBRESIA, false],
  ])("archetype %s → %s", (archetype, expected) => {
    expect(archetypeSupportsEditions(archetype)).toBe(expected);
  });
});

describe("getEditionsCopy", () => {
  it("returns null for archetypes without editions", () => {
    expect(getEditionsCopy(OfferArchetype.PRODUCTO)).toBeNull();
    expect(getEditionsCopy(OfferArchetype.MEMBRESIA)).toBeNull();
  });

  it("returns programa copy using the word 'cohortes'", () => {
    const copy = getEditionsCopy(OfferArchetype.PROGRAMA);
    expect(copy).not.toBeNull();
    expect(copy!.title.toLowerCase()).toContain("cohorte");
    expect(copy!.yesLabel.toLowerCase()).toContain("cohorte");
  });

  it("returns experiencia copy using 'salidas' terminology", () => {
    const copy = getEditionsCopy(OfferArchetype.EXPERIENCIA);
    expect(copy).not.toBeNull();
    expect(copy!.title.toLowerCase()).toContain("salidas");
    expect(copy!.noLabel.toLowerCase()).toContain("única");
  });

  it("returns servicio copy using 'convocatorias' terminology", () => {
    const copy = getEditionsCopy(OfferArchetype.SERVICIO);
    expect(copy).not.toBeNull();
    expect(copy!.title.toLowerCase()).toContain("convocatorias");
    expect(copy!.yesLabel.toLowerCase()).toContain("convocatorias");
  });

  it("uses Spanish characters with tildes and eñe where appropriate", () => {
    // Rule 11: Spanish user-facing text must use correct accents.
    const programa = getEditionsCopy(OfferArchetype.PROGRAMA)!;
    expect(programa.yesLabel).toContain("Sí");
    const experiencia = getEditionsCopy(OfferArchetype.EXPERIENCIA)!;
    expect(experiencia.noLabel).toContain("única");
  });
});
