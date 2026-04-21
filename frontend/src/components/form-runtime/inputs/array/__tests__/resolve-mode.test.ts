import { describe, it, expect } from "vitest";

import { resolveMode } from "../../ArrayInput";

import type { FieldSchema } from "@/lib/form-runtime/schema";

function arrayField(fieldCount: number, renderAs?: "cards" | "split" | "accordion"): FieldSchema {
  const fields = Array.from({ length: fieldCount }, (_, i) => ({
    id: `f${i}`,
    label: `Field ${i}`,
    type: "text" as const,
    path: `f${i}`,
  }));

  return {
    id: "arr",
    label: "Array",
    type: "array",
    path: "arr",
    renderAs,
    itemSchema: { fields },
  };
}

describe("resolveMode", () => {
  it("returns cards for 0 fields", () => {
    expect(resolveMode(arrayField(0))).toBe("cards");
  });

  it("returns cards for 1 field", () => {
    expect(resolveMode(arrayField(1))).toBe("cards");
  });

  it("returns cards for 2 fields", () => {
    expect(resolveMode(arrayField(2))).toBe("cards");
  });

  it("returns cards for 3 fields", () => {
    expect(resolveMode(arrayField(3))).toBe("cards");
  });

  it("returns split for 4 fields", () => {
    expect(resolveMode(arrayField(4))).toBe("split");
  });

  it("returns split for 5 fields", () => {
    expect(resolveMode(arrayField(5))).toBe("split");
  });

  it("returns split for 15 fields", () => {
    expect(resolveMode(arrayField(15))).toBe("split");
  });

  it("respects explicit renderAs cards override", () => {
    expect(resolveMode(arrayField(10, "cards"))).toBe("cards");
  });

  it("respects explicit renderAs split override", () => {
    expect(resolveMode(arrayField(2, "split"))).toBe("split");
  });

  it("respects explicit renderAs accordion override", () => {
    expect(resolveMode(arrayField(3, "accordion"))).toBe("accordion");
  });
});
