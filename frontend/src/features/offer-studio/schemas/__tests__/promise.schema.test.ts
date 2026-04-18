import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerPromiseSchema } from "../promise.schema";

describe("offerPromiseSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerPromiseSchema)).not.toThrow();
  });

  it("declares offer_level scope", () => {
    expect(offerPromiseSchema.scope).toBe("offer_level");
  });

  it("marks headline_promise as required", () => {
    const field = offerPromiseSchema.fields.find((f) => f.id === "headline_promise");
    expect(field?.required).toBe(true);
  });

  it("has no duplicate field ids", () => {
    const ids = offerPromiseSchema.fields.map((f) => f.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
