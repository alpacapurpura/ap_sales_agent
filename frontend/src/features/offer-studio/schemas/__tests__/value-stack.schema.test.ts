import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerValueStackSchema } from "../value-stack.schema";

describe("offerValueStackSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerValueStackSchema)).not.toThrow();
  });

  it("declares offer_level scope and the canonical key", () => {
    expect(offerValueStackSchema.scope).toBe("offer_level");
    expect(offerValueStackSchema.key).toBe("offer.value_stack");
  });

  it("exposes deliverables as an array with a title-bearing item schema", () => {
    const deliverables = offerValueStackSchema.fields.find((f) => f.id === "deliverables");
    expect(deliverables?.type).toBe("array");
    expect(deliverables?.itemSchema?.fields.some((f) => f.id === "title")).toBe(true);
  });
});
