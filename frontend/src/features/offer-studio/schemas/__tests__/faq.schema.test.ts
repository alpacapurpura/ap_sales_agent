import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerFaqSchema } from "../faq.schema";

describe("offerFaqSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerFaqSchema)).not.toThrow();
  });

  it("declares offer_level scope and the canonical key", () => {
    expect(offerFaqSchema.scope).toBe("offer_level");
    expect(offerFaqSchema.key).toBe("offer.faq");
  });

  it("exposes a single ``questions`` array field with a valid item schema", () => {
    expect(offerFaqSchema.fields).toHaveLength(1);
    const field = offerFaqSchema.fields[0];
    expect(field.id).toBe("questions");
    expect(field.type).toBe("array");
    expect(field.itemSchema?.fields.length).toBeGreaterThan(0);
  });

  it("item schema declares the Latam category enum", () => {
    const itemFields = offerFaqSchema.fields[0].itemSchema?.fields ?? [];
    const category = itemFields.find((f) => f.id === "category");
    expect(category?.type).toBe("enum");
    const values = new Set((category?.options ?? []).map((o) => o.value));
    expect(values.has("pagos")).toBe(true);
    expect(values.has("envios")).toBe(true);
    expect(values.has("devoluciones")).toBe(true);
  });

  it("has no duplicate field ids", () => {
    const ids = offerFaqSchema.fields.map((f) => f.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
