import { describe, it, expect } from "vitest";

import { computeItemStatus } from "../array-validation";

import type { FieldSchema } from "@/lib/form-runtime/schema";

type Row = Record<string, unknown>;

const titleField: FieldSchema = {
  id: "title",
  label: "Título",
  type: "text",
  path: "title",
  required: true,
};

const descField: FieldSchema = {
  id: "description",
  label: "Descripción",
  type: "textarea",
  path: "description",
  required: false,
};

const bodyField: FieldSchema = {
  id: "body",
  label: "Cuerpo",
  type: "textarea",
  path: "body",
  required: true,
};

describe("computeItemStatus", () => {
  it("returns required-<field> when required field is empty", () => {
    const item: Row = { title: "", description: "algo" };
    expect(computeItemStatus(item, [titleField, descField])).toBe("required-title");
  });

  it("returns required-<field> when required field is missing", () => {
    const item: Row = {};
    expect(computeItemStatus(item, [titleField, descField])).toBe("required-title");
  });

  it("returns complete when all required filled, optional empty", () => {
    const item: Row = { title: "Hola", description: "" };
    expect(computeItemStatus(item, [titleField, descField])).toBe("complete");
  });

  it("returns complete when all required filled, optional filled", () => {
    const item: Row = { title: "Hola", description: "Mundo" };
    expect(computeItemStatus(item, [titleField, descField])).toBe("complete");
  });

  it("returns complete when only required fields exist and all filled", () => {
    const item: Row = { title: "Hola" };
    expect(computeItemStatus(item, [titleField])).toBe("complete");
  });

  it("returns required for first failing required field when multiple required", () => {
    const item: Row = { title: "", body: "" };
    expect(computeItemStatus(item, [titleField, bodyField])).toBe("required-title");
  });

  it("returns required for second field when first is filled but second is not", () => {
    const item: Row = { title: "Algo", body: "" };
    expect(computeItemStatus(item, [titleField, bodyField])).toBe("required-body");
  });

  it("returns complete for empty item with no required fields", () => {
    const item: Row = {};
    expect(computeItemStatus(item, [descField])).toBe("complete");
  });

  it("handles whitespace-only string as empty", () => {
    const item: Row = { title: "   " };
    expect(computeItemStatus(item, [titleField])).toBe("required-title");
  });
});
