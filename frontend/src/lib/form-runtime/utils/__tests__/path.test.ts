import { describe, expect, it } from "vitest";

import { getNestedPath, setNestedPath } from "../path";

const DEMO_AGE = "demographics.age_range";

describe("getNestedPath", () => {
  it("returns the top-level value when path has no dots", () => {
    expect(getNestedPath({ name: "Valeria" }, "name")).toBe("Valeria");
  });

  it("traverses dot-notation into nested objects", () => {
    const obj = {
      demographics: { age_range: "30-42", location: "Lima" },
      psychographics: { values: "autenticidad" },
    };
    expect(getNestedPath(obj, DEMO_AGE)).toBe("30-42");
    expect(getNestedPath(obj, "psychographics.values")).toBe("autenticidad");
  });

  it("returns undefined when an intermediate segment is missing", () => {
    expect(getNestedPath({ demographics: {} }, DEMO_AGE)).toBeUndefined();
    expect(getNestedPath({}, DEMO_AGE)).toBeUndefined();
  });

  it("returns undefined for non-object intermediates", () => {
    expect(getNestedPath({ demographics: "not-an-object" }, DEMO_AGE)).toBeUndefined();
    expect(getNestedPath({ demographics: null }, DEMO_AGE)).toBeUndefined();
  });

  it("supports list values returned at the leaf", () => {
    const obj = { pain_points: [{ description: "x", severity: 4 }] };
    expect(getNestedPath(obj, "pain_points")).toEqual([{ description: "x", severity: 4 }]);
  });
});

describe("setNestedPath", () => {
  it("sets a top-level key when path has no dots", () => {
    const next = setNestedPath({ a: 1 }, "name", "Valeria");
    expect(next).toEqual({ a: 1, name: "Valeria" });
  });

  it("creates the nested object when missing and writes the leaf", () => {
    const next = setNestedPath({}, DEMO_AGE, "30-42");
    expect(next).toEqual({ demographics: { age_range: "30-42" } });
  });

  it("preserves sibling keys at every level when writing a nested leaf", () => {
    const prev = {
      demographics: { age_range: "20-29", location: "Lima" },
      pain_points: [{ description: "x", severity: 3 }],
    };
    const next = setNestedPath(prev, DEMO_AGE, "30-42");
    expect(next).toEqual({
      demographics: { age_range: "30-42", location: "Lima" },
      pain_points: [{ description: "x", severity: 3 }],
    });
  });

  it("does not mutate the input object", () => {
    const prev = { demographics: { age_range: "20-29" } };
    const next = setNestedPath(prev, DEMO_AGE, "30-42");
    expect(prev.demographics.age_range).toBe("20-29");
    expect(next).not.toBe(prev);
    expect(next.demographics).not.toBe(prev.demographics);
  });

  it("never produces a literal flat key with the dotted path", () => {
    const next = setNestedPath({}, DEMO_AGE, "30-42") as Record<string, unknown>;
    expect(next[DEMO_AGE]).toBeUndefined();
  });

  it("supports three-level nesting", () => {
    const next = setNestedPath({}, "buyer_journey.awareness.copy", "x") as Record<string, unknown>;
    expect(next).toEqual({ buyer_journey: { awareness: { copy: "x" } } });
  });

  it("replaces a non-object intermediate with a fresh dict", () => {
    const next = setNestedPath({ demographics: "scalar-from-legacy-data" }, DEMO_AGE, "30-42");
    expect(next).toEqual({ demographics: { age_range: "30-42" } });
  });
});
