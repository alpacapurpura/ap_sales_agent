import { describe, it, expect } from "vitest";

import { summariseItem } from "../array-summary";

import type { FieldSchema } from "@/lib/form-runtime/schema";

type Row = Record<string, unknown>;

const textField: FieldSchema = {
  id: "title",
  label: "Título",
  type: "text",
  path: "title",
};

const textareaField: FieldSchema = {
  id: "description",
  label: "Descripción",
  type: "textarea",
  path: "description",
};

const numberField: FieldSchema = {
  id: "count",
  label: "Cantidad",
  type: "number",
  path: "count",
};

describe("summariseItem", () => {
  it("returns first text field value when present", () => {
    const item: Row = { title: "Mi título", description: "Mi descripción" };
    expect(summariseItem(item, [textField, textareaField])).toBe("Mi título");
  });

  it("truncates to 60 characters", () => {
    const longValue = "A".repeat(80);
    const item: Row = { title: longValue };
    const result = summariseItem(item, [textField]);
    expect(result).toHaveLength(60);
    expect(result).toBe(longValue.slice(0, 60));
  });

  it("returns empty string when no text or textarea fields", () => {
    const item: Row = { count: 5 };
    expect(summariseItem(item, [numberField])).toBe("");
  });

  it("skips empty text field and returns textarea value", () => {
    const item: Row = { title: "", description: "Esta es la descripción" };
    expect(summariseItem(item, [textField, textareaField])).toBe("Esta es la descripción");
  });

  it("returns empty string when all text/textarea fields are empty", () => {
    const item: Row = { title: "", description: "" };
    expect(summariseItem(item, [textField, textareaField])).toBe("");
  });

  it("returns empty string for empty item", () => {
    expect(summariseItem({}, [textField, textareaField])).toBe("");
  });

  it("skips non-text fields before finding text value", () => {
    const item: Row = { count: 5, title: "Título encontrado" };
    expect(summariseItem(item, [numberField, textField])).toBe("Título encontrado");
  });

  it("trims surrounding whitespace before returning", () => {
    const item: Row = { title: "  texto con espacios  " };
    expect(summariseItem(item, [textField])).toBe("texto con espacios");
  });

  it("returns up to 60 chars after trim", () => {
    const item: Row = { title: `  ${"B".repeat(70)}  ` };
    const result = summariseItem(item, [textField]);
    expect(result.length).toBeLessThanOrEqual(60);
  });
});
