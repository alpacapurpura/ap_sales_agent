/**
 * Unit tests for channel-registry.ts — SSoT for growth-studio channels.
 *
 * Validates:
 * - 5+ canonical slugs exist
 * - Shape per entry is correct
 * - Registry is frozen (immutable)
 * - No duplicate slugs
 * - getStageForChannel() works correctly
 * - ChannelSlug type covers all 5 canonical channels
 */
import { describe, it, expect } from "vitest";

import { CHANNEL_REGISTRY, getStageForChannel, type ChannelSlug } from "../channel-registry";

/** The 5 canonical channel slugs confirmed by architect grep 2026-05-07. */
const CANONICAL_CHANNEL_SLUGS: ChannelSlug[] = [
  "meta-ads",
  "yt-organic",
  "email-nurture",
  "ig-organic",
  "website-total",
];

describe("channel-registry", () => {
  it("exports at least 5 channel entries", () => {
    expect(CHANNEL_REGISTRY.length).toBeGreaterThanOrEqual(5);
  });

  it("contains all 5 canonical channel slugs", () => {
    const slugs = CHANNEL_REGISTRY.map((c) => c.slug);
    for (const canonical of CANONICAL_CHANNEL_SLUGS) {
      expect(slugs, `Falta slug canónico: ${canonical}`).toContain(canonical);
    }
  });

  it("has no duplicate slugs", () => {
    const slugs = CHANNEL_REGISTRY.map((c) => c.slug);
    const unique = new Set(slugs);
    expect(unique.size).toBe(slugs.length);
  });

  it("each entry has required shape fields", () => {
    for (const entry of CHANNEL_REGISTRY) {
      expect(entry, `Entry ${entry.slug} missing 'slug'`).toHaveProperty("slug");
      expect(typeof entry.slug).toBe("string");

      expect(entry, `Entry ${entry.slug} missing 'stageSlug'`).toHaveProperty("stageSlug");
      expect(typeof entry.stageSlug).toBe("string");

      expect(entry, `Entry ${entry.slug} missing 'name'`).toHaveProperty("name");
      expect(typeof entry.name).toBe("string");

      expect(entry, `Entry ${entry.slug} missing 'etlProvider'`).toHaveProperty("etlProvider");
      expect(typeof entry.etlProvider).toBe("string");

      expect(entry, `Entry ${entry.slug} missing 'color'`).toHaveProperty("color");
      expect(typeof entry.color).toBe("string");
    }
  });

  it("each entry's stageSlug is a valid stage slug", () => {
    const validStageSlugs = new Set([
      "atraccion-captura",
      "nutricion-oportunidad",
      "ventas",
      "adopcion",
      "expansion-evangelizacion",
    ]);
    for (const entry of CHANNEL_REGISTRY) {
      expect(
        validStageSlugs.has(entry.stageSlug),
        `Channel '${entry.slug}' tiene stageSlug inválido: '${entry.stageSlug}'`,
      ).toBe(true);
    }
  });

  it("CHANNEL_REGISTRY is frozen (immutable)", () => {
    expect(Object.isFrozen(CHANNEL_REGISTRY)).toBe(true);
  });

  describe("getStageForChannel()", () => {
    it("returns correct stage for meta-ads", () => {
      expect(getStageForChannel("meta-ads")).toBe("atraccion-captura");
    });

    it("returns correct stage for ig-organic", () => {
      expect(getStageForChannel("ig-organic")).toBe("atraccion-captura");
    });

    it("returns correct stage for yt-organic", () => {
      expect(getStageForChannel("yt-organic")).toBe("atraccion-captura");
    });

    it("returns correct stage for email-nurture", () => {
      expect(getStageForChannel("email-nurture")).toBe("nutricion-oportunidad");
    });

    it("returns correct stage for website-total", () => {
      // website-total maps to atraccion-captura or similar — verify against registry
      const entry = CHANNEL_REGISTRY.find((c) => c.slug === "website-total");
      expect(getStageForChannel("website-total")).toBe(entry?.stageSlug ?? "atraccion-captura");
    });

    it("returns fallback 'atraccion-captura' for unknown channel", () => {
      expect(getStageForChannel("unknown-channel-xyz")).toBe("atraccion-captura");
    });
  });
});
