import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerTestimonialsSchema } from "../testimonials.schema";

describe("offerTestimonialsSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerTestimonialsSchema)).not.toThrow();
  });

  it("declares offer_level scope and the canonical key", () => {
    expect(offerTestimonialsSchema.scope).toBe("offer_level");
    expect(offerTestimonialsSchema.key).toBe("offer.testimonials");
  });

  it("supports video, text, audio, before/after and screenshot testimonial types", () => {
    const itemFields = offerTestimonialsSchema.fields[0].itemSchema?.fields ?? [];
    const type = itemFields.find((f) => f.id === "type");
    const values = new Set((type?.options ?? []).map((o) => o.value));
    expect(values.has("text")).toBe(true);
    expect(values.has("video")).toBe(true);
    expect(values.has("audio")).toBe(true);
    expect(values.has("before_after")).toBe(true);
    expect(values.has("screenshot")).toBe(true);
  });

  it("exposes Latam country picker covering >= 10 countries", () => {
    const itemFields = offerTestimonialsSchema.fields[0].itemSchema?.fields ?? [];
    const country = itemFields.find((f) => f.id === "author_country");
    expect(country?.type).toBe("enum");
    expect((country?.options ?? []).length).toBeGreaterThanOrEqual(10);
  });

  it("has no duplicate field ids", () => {
    const ids = offerTestimonialsSchema.fields.map((f) => f.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
