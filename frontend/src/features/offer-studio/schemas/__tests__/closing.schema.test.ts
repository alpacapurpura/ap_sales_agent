import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { GuaranteeType } from "../../types";
import { offerClosingSchema } from "../closing.schema";

describe("offerClosingSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerClosingSchema)).not.toThrow();
  });

  it("declares offer_level scope and the canonical key", () => {
    expect(offerClosingSchema.scope).toBe("offer_level");
    expect(offerClosingSchema.key).toBe("offer.closing");
  });

  it("exposes guarantee_type as an enum bound to the backend GuaranteeType enum", () => {
    const guaranteeType = offerClosingSchema.fields.find((f) => f.id === "guarantee_type");
    expect(guaranteeType?.type).toBe("enum");
    const values = guaranteeType?.options?.map((o) => o.value) ?? [];
    expect(values).toContain(GuaranteeType.NONE);
    expect(values).toContain(GuaranteeType.UNCONDITIONAL_30_DAY);
  });
});
