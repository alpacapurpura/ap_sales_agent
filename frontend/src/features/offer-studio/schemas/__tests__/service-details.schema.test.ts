import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerServiceDetailsSchema } from "../service-details.schema";

describe("offerServiceDetailsSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerServiceDetailsSchema)).not.toThrow();
  });

  it("declares mixed scope and the canonical key", () => {
    expect(offerServiceDetailsSchema.scope).toBe("mixed");
    expect(offerServiceDetailsSchema.key).toBe("offer.service_details");
  });

  it("routes convocatoria-specific fields (start_date, capacity) to the edition", () => {
    const startDate = offerServiceDetailsSchema.fields.find((f) => f.id === "start_date");
    const capacity = offerServiceDetailsSchema.fields.find((f) => f.id === "capacity");
    expect(startDate?.owner).toBe("edition");
    expect(capacity?.owner).toBe("edition");
  });
});
