import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { offerPortfolioSchema } from "../portfolio.schema";

describe("offerPortfolioSchema", () => {
  it("parses as a valid SectionSchema", () => {
    expect(() => parseSectionSchema(offerPortfolioSchema)).not.toThrow();
  });

  it("declares offer_level scope and the canonical key", () => {
    expect(offerPortfolioSchema.scope).toBe("offer_level");
    expect(offerPortfolioSchema.key).toBe("offer.portfolio");
  });

  it("exposes cases array with the challenge → solution → results skeleton", () => {
    const cases = offerPortfolioSchema.fields.find((f) => f.id === "cases");
    expect(cases?.type).toBe("array");
    const itemFieldIds = (cases?.itemSchema?.fields ?? []).map((f) => f.id);
    expect(itemFieldIds).toContain("challenge");
    expect(itemFieldIds).toContain("solution");
    expect(itemFieldIds).toContain("results_summary");
  });

  it("has no duplicate field ids at the section level", () => {
    const ids = offerPortfolioSchema.fields.map((f) => f.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
