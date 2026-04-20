import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerInstructorsSchema } from "../instructors.schema";

describe("offerInstructorsSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerInstructorsSchema)).not.toThrow();
  });

  it("declares offer_level scope and the canonical key", () => {
    expect(offerInstructorsSchema.scope).toBe("offer_level");
    expect(offerInstructorsSchema.key).toBe("offer.instructors");
  });

  it("delegates picking to a registered custom action (brand-studio team source)", () => {
    const instructors = offerInstructorsSchema.fields.find((f) => f.id === "instructors");
    expect(instructors?.type).toBe("custom");
    expect(instructors?.action).toBe("offer-instructors-picker");
  });
});
