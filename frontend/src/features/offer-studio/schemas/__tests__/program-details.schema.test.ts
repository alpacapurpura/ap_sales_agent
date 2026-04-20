import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerProgramDetailsSchema } from "../program-details.schema";

describe("offerProgramDetailsSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerProgramDetailsSchema)).not.toThrow();
  });

  it("declares mixed scope", () => {
    expect(offerProgramDetailsSchema.scope).toBe("mixed");
  });

  it("splits curriculum (offer) from cohort schedule (edition)", () => {
    const curriculum = offerProgramDetailsSchema.fields.find((f) => f.id === "curriculum");
    const schedule = offerProgramDetailsSchema.fields.find((f) => f.id === "schedule");
    expect(curriculum?.owner).toBe("offer");
    expect(schedule?.owner).toBe("edition");
  });

  it("exposes start_date and capacity on the edition side", () => {
    const startDate = offerProgramDetailsSchema.fields.find((f) => f.id === "start_date");
    const capacity = offerProgramDetailsSchema.fields.find((f) => f.id === "capacity");
    expect(startDate?.owner).toBe("edition");
    expect(capacity?.owner).toBe("edition");
  });
});
