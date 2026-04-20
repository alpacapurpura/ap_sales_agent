import { describe, it, expect } from "vitest";

import { inferFieldLayout, layoutToColSpanClass } from "../layout";

import type { FieldSchema } from "../types";

function makeField(type: FieldSchema["type"], layout?: FieldSchema["layout"]): FieldSchema {
  return { id: "x", label: "X", type, path: "x", layout };
}

describe("inferFieldLayout", () => {
  it("honours explicit layout", () => {
    expect(inferFieldLayout(makeField("text", "full"))).toBe("full");
    expect(inferFieldLayout(makeField("textarea", "half"))).toBe("half");
    expect(inferFieldLayout(makeField("enum", "two-thirds"))).toBe("two-thirds");
  });

  it("defaults text/url/email/number/boolean/enum to half", () => {
    const types = ["text", "url", "email", "number", "boolean", "enum"] as const;
    for (const t of types) {
      expect(inferFieldLayout(makeField(t))).toBe("half");
    }
  });

  it("defaults textarea/array/custom to full", () => {
    const types = ["textarea", "array", "custom"] as const;
    for (const t of types) {
      expect(inferFieldLayout(makeField(t))).toBe("full");
    }
  });
});

describe("layoutToColSpanClass", () => {
  it("maps full to col-span-full", () => {
    expect(layoutToColSpanClass("full")).toBe("col-span-full");
  });
  it("maps half to col-span-1", () => {
    expect(layoutToColSpanClass("half")).toBe("col-span-1");
  });
  it("maps two-thirds to responsive span", () => {
    expect(layoutToColSpanClass("two-thirds")).toContain("col-span-2");
    expect(layoutToColSpanClass("two-thirds")).toContain("col-span-full");
  });
});
