import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerEventDetailsSchema } from "../event-details.schema";

describe("offerEventDetailsSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerEventDetailsSchema)).not.toThrow();
  });

  it("declares edition_level scope (every event datum is per-salida)", () => {
    expect(offerEventDetailsSchema.scope).toBe("edition_level");
  });

  it("marks start_date as required (publishing gate)", () => {
    const startDate = offerEventDetailsSchema.fields.find((f) => f.id === "start_date");
    expect(startDate?.required).toBe(true);
  });
});
