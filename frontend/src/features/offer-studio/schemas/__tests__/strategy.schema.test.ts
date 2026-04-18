import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerStrategySchema } from "../strategy.schema";

describe("offerStrategySchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerStrategySchema)).not.toThrow();
  });

  it("declares offer_level scope", () => {
    expect(offerStrategySchema.scope).toBe("offer_level");
  });

  it("carries the canonical namespaced key", () => {
    expect(offerStrategySchema.key).toBe("offer.strategy");
  });

  it("has no duplicate field ids", () => {
    const ids = offerStrategySchema.fields.map((f) => f.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
