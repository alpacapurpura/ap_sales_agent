import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerPlatformDetailsSchema } from "../platform-details.schema";

describe("offerPlatformDetailsSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerPlatformDetailsSchema)).not.toThrow();
  });

  it("declares offer_level scope and the canonical key", () => {
    expect(offerPlatformDetailsSchema.scope).toBe("offer_level");
    expect(offerPlatformDetailsSchema.key).toBe("offer.platform_details");
  });

  it("exposes core_features and integrations as arrays with item schemas", () => {
    const features = offerPlatformDetailsSchema.fields.find((f) => f.id === "core_features");
    const integrations = offerPlatformDetailsSchema.fields.find((f) => f.id === "integrations");
    expect(features?.type).toBe("array");
    expect(integrations?.type).toBe("array");
    expect(features?.itemSchema?.fields.length).toBeGreaterThan(0);
    expect(integrations?.itemSchema?.fields.length).toBeGreaterThan(0);
  });

  it("has no duplicate field ids", () => {
    const ids = offerPlatformDetailsSchema.fields.map((f) => f.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
