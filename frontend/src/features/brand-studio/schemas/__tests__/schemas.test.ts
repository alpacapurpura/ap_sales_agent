import { describe, expect, it } from "vitest";

import { BRAND_STUDIO_ACTION_KEYS } from "@/features/brand-studio/actions/registry";
import { parseSectionSchema } from "@/lib/form-runtime/schema";

import { SCHEMA_REGISTRY } from "../index";

describe("brand-studio schemas", () => {
  it("registers every advertised section", () => {
    // 12 brand-studio schemas (removed brand.voice + brand.personality which
    // are now replaced by the top-level "Estilo Comunicacional" section backed
    // by personality_profiles) + buyer-persona + 3 social_proof per-instance
    // schemas (testimonial, authority-item, team-member).
    expect(Object.keys(SCHEMA_REGISTRY)).toHaveLength(15);
  });

  it("every schema parses successfully", () => {
    for (const [key, schema] of Object.entries(SCHEMA_REGISTRY)) {
      expect(() => parseSectionSchema(schema), `parse(${key})`).not.toThrow();
    }
  });

  it("every schema key matches its registry key", () => {
    for (const [key, schema] of Object.entries(SCHEMA_REGISTRY)) {
      expect(schema.key, `entry "${key}" has schema.key=${schema.key}`).toBe(key);
    }
  });

  it("every custom field.action references a known registry key", () => {
    const known = new Set(BRAND_STUDIO_ACTION_KEYS);
    for (const [schemaKey, schema] of Object.entries(SCHEMA_REGISTRY)) {
      walkFields(schema.fields, (field) => {
        if (field.type === "custom" && field.action) {
          expect(
            known.has(field.action as (typeof BRAND_STUDIO_ACTION_KEYS)[number]),
            `${schemaKey}.${field.id} references unknown action "${field.action}"`,
          ).toBe(true);
        }
      });
    }
  });

  it("covers all expected domain keys", () => {
    const expected = [
      "brand.identity",
      "brand.legal",
      "brand.visuals",
      "brand.logos",
      "brand.methodology",
      "brand.story",
      "brand.narrative",
      "brand.positioning",
      "brand.communication-assets",
      "brand.contact",
      "brand.avatars",
      "brand.buyer-persona",
      // social_proof SSoT (per-instance schemas)
      "social-proof.testimonial",
      "social-proof.authority-item",
      "social-proof.team-member",
    ];
    for (const key of expected) {
      expect(SCHEMA_REGISTRY[key], `missing schema: ${key}`).toBeDefined();
    }
  });
});

type Field = Parameters<typeof parseSectionSchema>[0]["fields"][number];

function walkFields(fields: Field[], visit: (f: Field) => void) {
  for (const field of fields) {
    visit(field);
    if (field.type === "array" && field.itemSchema) {
      walkFields(field.itemSchema.fields, visit);
    }
  }
}
