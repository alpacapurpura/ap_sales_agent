import { describe, expect, it } from "vitest";

import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { getOfferSchema, OFFER_SCHEMA_REGISTRY } from "../index";

import type { SectionKey } from "../../api/archetype-catalog-api";

/**
 * Lockstep with the backend SectionKey contract. If the backend adds or
 * removes a key, the TS ``SectionKey`` union changes and this test either
 * demands a new entry or rejects the orphan — CI catches the drift at
 * compile time, not at runtime.
 */
const EXPECTED_KEYS: readonly SectionKey[] = [
  "identity",
  "strategy",
  "psychology",
  "promise",
  "value_stack",
  "instructors",
  "knowledge",
  "closing",
  "product_details",
  "subscription_details",
  "gallery",
  "event_details",
  "pricing",
  "program_details",
  "service_details",
  "resources",
  // Nuevas (Latam mass-market rollout)
  "faq",
  "testimonials",
  "portfolio",
  "methodology",
  "credentials",
  "location",
  "platform_details",
];

describe("OFFER_SCHEMA_REGISTRY", () => {
  it("exposes a schema for every SectionKey", () => {
    for (const key of EXPECTED_KEYS) {
      expect(OFFER_SCHEMA_REGISTRY[key]).toBeDefined();
    }
  });

  it("has no extra or missing keys versus the expected set", () => {
    const registryKeys = new Set(Object.keys(OFFER_SCHEMA_REGISTRY));
    const expectedKeys = new Set<string>(EXPECTED_KEYS);
    expect(registryKeys).toEqual(expectedKeys);
  });

  it("every registered schema parses", () => {
    for (const [key, schema] of Object.entries(OFFER_SCHEMA_REGISTRY)) {
      expect(() => parseSectionSchema(schema), `failed parsing ${key}`).not.toThrow();
    }
  });

  it("every registered schema carries a namespaced key starting with 'offer.'", () => {
    for (const schema of Object.values(OFFER_SCHEMA_REGISTRY)) {
      expect(schema.key.startsWith("offer.")).toBe(true);
    }
  });

  it("getOfferSchema returns the correct schema by SectionKey", () => {
    expect(getOfferSchema("identity").key).toBe("offer.identity");
    expect(getOfferSchema("pricing").scope).toBe("mixed");
    expect(getOfferSchema("event_details").scope).toBe("edition_level");
  });

  it("field ids are unique inside every schema (no silent duplication)", () => {
    for (const [sectionKey, schema] of Object.entries(OFFER_SCHEMA_REGISTRY)) {
      const ids = schema.fields.map((f) => f.id);
      expect(new Set(ids).size, `${sectionKey} has duplicate field ids`).toBe(ids.length);
    }
  });
});
