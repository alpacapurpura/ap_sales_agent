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

  it("references Connections module via payment-provider-picker action (no static payment list)", () => {
    const field = offerPricingSchema.fields.find((f) => f.id === "accepted_payment_providers");
    expect(field?.type).toBe("custom");
    expect(field?.action).toBe("payment-provider-picker");
  });

  it("exposes Latam-critical fields (tax_included, installments, currency)", () => {
    const ids = offerPricingSchema.fields.map((f) => f.id);
    expect(ids).toContain("tax_included");
    expect(ids).toContain("installments_available");
    expect(ids).toContain("currency");
  });
});
