import { describe, expect, it } from "vitest";

import { findNextEmpty } from "../NextEmptyFieldCta";

import type { FieldSchema } from "@/lib/form-runtime/schema";

const fields: FieldSchema[] = [
  { id: "a", label: "A", type: "text", path: "a" },
  { id: "b", label: "B", type: "text", path: "b" },
  { id: "c", label: "C", type: "textarea", path: "c" },
];

describe("findNextEmpty", () => {
  it("returns the first empty field", () => {
    const next = findNextEmpty(fields, { a: "hi", b: "", c: "x" });
    expect(next?.id).toBe("b");
  });

  it("returns null when every field is filled", () => {
    const next = findNextEmpty(fields, { a: "1", b: "2", c: "3" });
    expect(next).toBeNull();
  });

  it("treats whitespace-only strings as empty", () => {
    const next = findNextEmpty(fields, { a: "   ", b: "1", c: "1" });
    expect(next?.id).toBe("a");
  });

  it("treats empty arrays as empty", () => {
    const arr: FieldSchema[] = [
      {
        id: "x",
        label: "X",
        type: "array",
        path: "x",
        itemSchema: { fields: [{ id: "y", label: "Y", type: "text", path: "y" }] },
      },
    ];
    expect(findNextEmpty(arr, { x: [] })?.id).toBe("x");
    expect(findNextEmpty(arr, { x: [{}] })).toBeNull();
  });
});
