import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerSubscriptionDetailsSchema } from "../subscription-details.schema";

describe("offerSubscriptionDetailsSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerSubscriptionDetailsSchema)).not.toThrow();
  });

  it("declares offer_level scope and the canonical key", () => {
    expect(offerSubscriptionDetailsSchema.scope).toBe("offer_level");
    expect(offerSubscriptionDetailsSchema.key).toBe("offer.subscription_details");
  });

  it("exposes billing_frequency as an enum", () => {
    const billing = offerSubscriptionDetailsSchema.fields.find((f) => f.id === "billing_frequency");
    expect(billing?.type).toBe("enum");
    expect(billing?.options?.length).toBeGreaterThan(0);
  });
});
