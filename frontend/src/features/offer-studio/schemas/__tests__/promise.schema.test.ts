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

  it("does not duplicate headline_promise or primary_outcome from IDENTITY", () => {
    // Post-consolidation: IDENTITY owns headline_promise + primary_outcome.
    // PROMISE unpacks the transformation arc (before/after/why-now/metrics).
    const ids = offerPromiseSchema.fields.map((f) => f.id);
    expect(ids).not.toContain("headline_promise");
    expect(ids).not.toContain("primary_outcome");
  });

  it("marks before_state and after_state as required (core transformation arc)", () => {
    const before = offerPromiseSchema.fields.find((f) => f.id === "before_state");
    const after = offerPromiseSchema.fields.find((f) => f.id === "after_state");
    expect(before?.required).toBe(true);
    expect(after?.required).toBe(true);
  });

  it("has no duplicate field ids", () => {
    const ids = offerPromiseSchema.fields.map((f) => f.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
