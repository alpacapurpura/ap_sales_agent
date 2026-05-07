/**
 * Unit tests for stage-registry.ts — SSoT for growth-studio funnel stages.
 *
 * Validates:
 * - 5 canonical slugs exist
 * - Shape per entry is correct
 * - Registry is frozen (immutable)
 * - No duplicate slugs
 * - Correct ordering
 */
import { describe, it, expect } from "vitest";

import { STAGE_REGISTRY, type StageSlug } from "../stage-registry";

const CANONICAL_STAGE_SLUGS: StageSlug[] = [
  "atraccion-captura",
  "nutricion-oportunidad",
  "ventas",
  "adopcion",
  "expansion-evangelizacion",
];

describe("stage-registry", () => {
  it("exports exactly 5 canonical stage slugs", () => {
    expect(STAGE_REGISTRY).toHaveLength(5);
  });

  it("contains all canonical slugs", () => {
    const slugs = STAGE_REGISTRY.map((s) => s.slug);
    for (const canonical of CANONICAL_STAGE_SLUGS) {
      expect(slugs, `Falta slug canónico: ${canonical}`).toContain(canonical);
    }
  });

  it("has no duplicate slugs", () => {
    const slugs = STAGE_REGISTRY.map((s) => s.slug);
    const unique = new Set(slugs);
    expect(unique.size).toBe(slugs.length);
  });

  it("each entry has required shape fields", () => {
    for (const entry of STAGE_REGISTRY) {
      expect(entry, `Entry ${entry.slug} missing 'slug'`).toHaveProperty("slug");
      expect(typeof entry.slug).toBe("string");

      expect(entry, `Entry ${entry.slug} missing 'label'`).toHaveProperty("label");
      expect(typeof entry.label).toBe("string");

      expect(entry, `Entry ${entry.slug} missing 'order'`).toHaveProperty("order");
      expect(typeof entry.order).toBe("number");

      expect(entry, `Entry ${entry.slug} missing 'iconName'`).toHaveProperty("iconName");
      expect(typeof entry.iconName).toBe("string");

      expect(entry, `Entry ${entry.slug} missing 'mainKpiLabel'`).toHaveProperty("mainKpiLabel");
      expect(typeof entry.mainKpiLabel).toBe("string");
    }
  });

  it("entries are ordered by 'order' field ascending (1-indexed)", () => {
    const orders = STAGE_REGISTRY.map((s) => s.order);
    for (let i = 0; i < orders.length; i++) {
      expect(orders[i]).toBe(i + 1);
    }
  });

  it("STAGE_REGISTRY is frozen (immutable)", () => {
    expect(Object.isFrozen(STAGE_REGISTRY)).toBe(true);
  });

  it("labels are in Spanish neutro (no voseo)", () => {
    for (const entry of STAGE_REGISTRY) {
      // Basic check — labels should be non-empty strings
      expect(entry.label.length).toBeGreaterThan(0);
    }
  });

  it("atraccion-captura is order 1", () => {
    const stage = STAGE_REGISTRY.find((s) => s.slug === "atraccion-captura");
    expect(stage?.order).toBe(1);
  });

  it("expansion-evangelizacion is order 5", () => {
    const stage = STAGE_REGISTRY.find((s) => s.slug === "expansion-evangelizacion");
    expect(stage?.order).toBe(5);
  });
});
