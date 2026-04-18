import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerResourcesSchema } from "../resources.schema";

describe("offerResourcesSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerResourcesSchema)).not.toThrow();
  });

  it("declares mixed scope with owner on every field", () => {
    expect(offerResourcesSchema.scope).toBe("mixed");
    for (const field of offerResourcesSchema.fields) {
      expect(field.owner).toBeDefined();
    }
  });

  it("separates base offer-owned resources from per-edition ones", () => {
    const base = offerResourcesSchema.fields.find((f) => f.id === "base_resources");
    const edition = offerResourcesSchema.fields.find((f) => f.id === "edition_resources");
    expect(base?.owner).toBe("offer");
    expect(edition?.owner).toBe("edition");
  });
});
