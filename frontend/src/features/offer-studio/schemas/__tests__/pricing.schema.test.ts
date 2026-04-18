import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerPricingSchema } from "../pricing.schema";

describe("offerPricingSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerPricingSchema)).not.toThrow();
  });

  it("declares mixed scope with owner on every field", () => {
    expect(offerPricingSchema.scope).toBe("mixed");
    for (const field of offerPricingSchema.fields) {
      expect(field.owner).toBeDefined();
    }
  });

  it("routes pricing_options to the offer and pricing_tiers to the edition", () => {
    const options = offerPricingSchema.fields.find((f) => f.id === "pricing_options");
    const tiers = offerPricingSchema.fields.find((f) => f.id === "pricing_tiers");
    expect(options?.owner).toBe("offer");
    expect(tiers?.owner).toBe("edition");
  });

  it("carries the canonical namespaced key", () => {
    expect(offerPricingSchema.key).toBe("offer.pricing");
  });
});
