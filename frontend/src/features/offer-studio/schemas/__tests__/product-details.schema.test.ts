import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerProductDetailsSchema } from "../product-details.schema";

describe("offerProductDetailsSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerProductDetailsSchema)).not.toThrow();
  });

  it("declares offer_level scope and the canonical key", () => {
    expect(offerProductDetailsSchema.scope).toBe("offer_level");
    expect(offerProductDetailsSchema.key).toBe("offer.product_details");
  });

  it("uses specific_details as the path prefix for detail fields", () => {
    const fulfillmentType = offerProductDetailsSchema.fields.find(
      (f) => f.id === "fulfillment_type",
    );
    expect(fulfillmentType?.path).toBe("specific_details.fulfillment_type");
  });
});
