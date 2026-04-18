import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerIdentitySchema } from "../identity.schema";

describe("offerIdentitySchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerIdentitySchema)).not.toThrow();
  });

  it("declares offer_level scope", () => {
    expect(offerIdentitySchema.scope).toBe("offer_level");
  });

  it("carries the canonical namespaced key", () => {
    expect(offerIdentitySchema.key).toBe("offer.identity");
  });

  it("exposes public_name as a required field", () => {
    const publicName = offerIdentitySchema.fields.find((f) => f.id === "public_name");
    expect(publicName?.required).toBe(true);
  });

  it("has no duplicate field ids", () => {
    const ids = offerIdentitySchema.fields.map((f) => f.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
