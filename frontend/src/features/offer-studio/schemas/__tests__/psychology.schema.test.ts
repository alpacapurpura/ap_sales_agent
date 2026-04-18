import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerPsychologySchema } from "../psychology.schema";

describe("offerPsychologySchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerPsychologySchema)).not.toThrow();
  });

  it("declares offer_level scope", () => {
    expect(offerPsychologySchema.scope).toBe("offer_level");
  });

  it("carries the canonical namespaced key", () => {
    expect(offerPsychologySchema.key).toBe("offer.psychology");
  });

  it("has no duplicate field ids", () => {
    const ids = offerPsychologySchema.fields.map((f) => f.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
