import { describe, it, expect } from "vitest";
import { getSectionFields, getSectionData } from "../utils/section-helpers";
import { OfferFormValues } from "../types/schema";
import { OfferArchetype, GuaranteeType } from "../types";

// ─── getSectionFields ───

describe("getSectionFields", () => {
  it("returns identity fields", () => {
    const fields = getSectionFields("identity");
    expect(fields).toContain("public_name");
    expect(fields).toContain("archetype");
    expect(fields).toContain("status");
  });

  it("returns strategy fields", () => {
    const fields = getSectionFields("strategy");
    expect(fields).toContain("target_avatar_match");
    expect(fields).toContain("marketing_pain_points");
    expect(fields).toContain("marketing_desires");
  });

  it("returns pricing fields", () => {
    const fields = getSectionFields("pricing");
    expect(fields).toContain("pricing_options");
    expect(fields).toContain("currency");
  });

  it("returns promise fields", () => {
    const fields = getSectionFields("promise");
    expect(fields).toContain("headline_promise");
    expect(fields).toContain("primary_outcome");
    expect(fields).toContain("time_to_value");
  });

  it("returns closing fields", () => {
    const fields = getSectionFields("closing");
    expect(fields).toContain("guarantee_type");
    expect(fields).toContain("guarantee_terms");
  });

  it("returns instructors fields", () => {
    const fields = getSectionFields("instructors");
    expect(fields).toContain("instructors");
  });

  it("returns value_stack fields", () => {
    const fields = getSectionFields("value_stack");
    expect(fields).toContain("deliverables");
    expect(fields).toContain("includes_offers");
  });

  it("returns assets for resources section", () => {
    expect(getSectionFields("resources")).toContain("assets");
  });

  it("returns assets for gallery section", () => {
    expect(getSectionFields("gallery")).toContain("assets");
  });

  it("returns detail fields for all archetype detail sections", () => {
    const detailSections = [
      "program_details",
      "product_details",
      "service_details",
      "event_details",
      "subscription_details",
    ];
    for (const section of detailSections) {
      const fields = getSectionFields(section);
      expect(fields).toContain("specific_details");
      expect(fields).toContain("access_duration");
      expect(fields).toContain("onboarding_action");
    }
  });

  it("returns empty array for unknown section", () => {
    expect(getSectionFields("nonexistent")).toEqual([]);
  });
});

// ─── getSectionData ───

const makeFormValues = (overrides: Partial<OfferFormValues> = {}): OfferFormValues =>
  ({
    public_name: "Test Offer",
    archetype: OfferArchetype.PRODUCTO,
    status: "draft",
    pricing_options: [{ total_amount: 100, label: "Standard" }],
    currency: "USD",
    marketing_pain_points: ["pain1"],
    marketing_desires: ["desire1"],
    deliverables: [{ name: "Module 1", format: "video", quantity: "1", value_stack_price: 50 }],
    assets: [{ type: "IMAGE", name: "Hero", url: "https://example.com/hero.png", is_knowledge_base: false }],
    specific_details: { key: "value" },
    guarantee_type: GuaranteeType.NONE,
    headline_promise: "Transform your life",
    primary_outcome: "Better health",
    time_to_value: "30 days",
    instructors: ["instructor-1"],
    includes_offers: [],
    target_avatar_match: [],
    ...overrides,
  }) as OfferFormValues;

describe("getSectionData", () => {
  it("extracts identity section data", () => {
    const values = makeFormValues();
    const data = getSectionData("identity", values);
    expect(data.public_name).toBe("Test Offer");
    expect(data.archetype).toBe(OfferArchetype.PRODUCTO);
    expect(data.status).toBe("draft");
    // Should NOT include unrelated fields
    expect(data.headline_promise).toBeUndefined();
  });

  it("extracts pricing section data", () => {
    const values = makeFormValues();
    const data = getSectionData("pricing", values);
    expect(data.currency).toBe("USD");
    // pricing_options is NOT in the generic loop (it's not special-handled either),
    // so let's verify behavior
    expect(data.pricing_options).toBeDefined();
  });

  it("extracts promise section data", () => {
    const values = makeFormValues();
    const data = getSectionData("promise", values);
    expect(data.headline_promise).toBe("Transform your life");
    expect(data.primary_outcome).toBe("Better health");
    expect(data.time_to_value).toBe("30 days");
  });

  it("deep-copies specific_details for detail sections", () => {
    const values = makeFormValues({ specific_details: { nested: "data", extra: 42 } });
    const data = getSectionData("program_details", values);
    expect(data.specific_details).toEqual({ nested: "data", extra: 42 });
    // Ensure it's a copy, not the same reference
    expect(data.specific_details).not.toBe(values.specific_details);
  });

  it("returns empty object for specific_details when null", () => {
    const values = makeFormValues({ specific_details: null });
    const data = getSectionData("program_details", values);
    expect(data.specific_details).toEqual({});
  });

  it("deep-copies assets array for resources section", () => {
    const values = makeFormValues();
    const data = getSectionData("resources", values);
    expect(data.assets).toHaveLength(1);
    expect(data.assets).not.toBe(values.assets);
  });

  it("returns empty assets array when null", () => {
    const values = makeFormValues({ assets: undefined });
    const data = getSectionData("resources", values);
    expect(data.assets).toEqual([]);
  });

  it("returns empty object for unknown section", () => {
    const values = makeFormValues();
    const data = getSectionData("nonexistent", values);
    expect(Object.keys(data)).toHaveLength(0);
  });
});
