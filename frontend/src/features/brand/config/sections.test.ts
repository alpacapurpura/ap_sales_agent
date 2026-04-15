import { describe, it, expect } from "vitest";

import {
  BRAND_SECTIONS,
  BRAND_SECTION_ORDER,
  EDIT_MODE_META,
  computeNavItemHealth,
  buildSectionNavItems,
  type BrandSectionId,
} from "./sections";

import type { BrandSettings } from "../types";

describe("Brand Section Config", () => {
  describe("BRAND_SECTIONS", () => {
    it("should have all 4 sections", () => {
      expect(Object.keys(BRAND_SECTIONS)).toHaveLength(4);
      expect(BRAND_SECTIONS.esencia).toBeDefined();
      expect(BRAND_SECTIONS.estrategia).toBeDefined();
      expect(BRAND_SECTIONS.publico).toBeDefined();
      expect(BRAND_SECTIONS["identidad-creativa"]).toBeDefined();
    });

    it("each section should have navItems", () => {
      for (const section of Object.values(BRAND_SECTIONS)) {
        expect(section.navItems.length).toBeGreaterThan(0);
        for (const item of section.navItems) {
          expect(item.id).toBeTruthy();
          expect(item.label).toBeTruthy();
          expect(item.scrollTo).toBeTruthy();
          // validators may be empty for UI-only nav items (e.g., voice-personality)
        }
      }
    });
  });

  describe("BRAND_SECTION_ORDER", () => {
    it("should list all sections in order", () => {
      expect(BRAND_SECTION_ORDER).toEqual([
        "esencia",
        "estrategia",
        "publico",
        "identidad-creativa",
      ]);
    });
  });

  describe("EDIT_MODE_META", () => {
    it("should have metadata for all edit modes", () => {
      const modes = [
        "none",
        "identity",
        "voice",
        "legal",
        "authority",
        "team",
        "testimonials",
        "avatars",
        "contact",
        "visuals",
        "visuals-wizard",
        "logos",
        "story",
        "methodology",
        "positioning",
        "values-essence",
        "storybrand",
        "communication-assets",
      ];
      for (const mode of modes) {
        const meta = EDIT_MODE_META[mode as keyof typeof EDIT_MODE_META];
        expect(meta).toBeDefined();
        expect(meta.title).toBeTruthy();
        expect(meta.desc).toBeTruthy();
      }
    });
  });

  describe("computeNavItemHealth", () => {
    it("should return empty for missing data", () => {
      const item = BRAND_SECTIONS.esencia.navItems[0]; // origin
      const emptySettings = {} as BrandSettings;
      const health = computeNavItemHealth(item, emptySettings);
      expect(health.status).toBe("empty");
      expect(health.score).toBe(0);
    });

    it("should return complete for full data", () => {
      // Find credibility by id — avoids index fragility when nav items shift
      const item = BRAND_SECTIONS.esencia.navItems.find((i) => i.id === "credibility");
      expect(item).toBeDefined();
      const settings = {
        authority_vault: [{ id: "1", entity_name: "Press" }],
      } as unknown as BrandSettings;
      const health = computeNavItemHealth(item!, settings);
      expect(health.status).toBe("complete");
      expect(health.score).toBe(100);
    });
  });

  describe("buildSectionNavItems", () => {
    it("should return items with computed health", () => {
      const items = buildSectionNavItems("esencia", {} as BrandSettings);
      expect(items.length).toBe(BRAND_SECTIONS.esencia.navItems.length);
      for (const item of items) {
        expect(item).toHaveProperty("score");
        expect(item).toHaveProperty("status");
        expect(item).toHaveProperty("missingFields");
      }
    });
  });
});
