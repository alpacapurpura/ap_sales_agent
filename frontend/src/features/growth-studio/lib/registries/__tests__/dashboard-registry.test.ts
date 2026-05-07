/**
 * Unit tests for dashboard-registry.ts — per-channel lazy-loaded component map.
 *
 * Validates:
 * - Keys equal ChannelSlug union (exhaustive)
 * - Each value is a function (lazy import factory)
 * - All 5 canonical channel slugs are covered
 */
import { describe, it, expect } from "vitest";

import { DASHBOARD_COMPONENT_MAP } from "../dashboard-registry";

const CANONICAL_CHANNEL_SLUGS = [
  "meta-ads",
  "yt-organic",
  "email-nurture",
  "ig-organic",
  "website-total",
] as const;

describe("dashboard-registry", () => {
  it("contains all 5 canonical channel slugs as keys", () => {
    for (const slug of CANONICAL_CHANNEL_SLUGS) {
      expect(
        Object.prototype.hasOwnProperty.call(DASHBOARD_COMPONENT_MAP, slug),
        `Falta entrada en dashboard-registry para slug: ${slug}`,
      ).toBe(true);
    }
  });

  it("each value is a function (lazy import factory)", () => {
    for (const slug of CANONICAL_CHANNEL_SLUGS) {
      const factory = DASHBOARD_COMPONENT_MAP[slug];
      expect(
        typeof factory,
        `dashboard-registry['${slug}'] debe ser una función, es: ${typeof factory}`,
      ).toBe("function");
    }
  });

  it("has no extra keys beyond canonical channels", () => {
    const keys = Object.keys(DASHBOARD_COMPONENT_MAP);
    const canonicalSet = new Set<string>(CANONICAL_CHANNEL_SLUGS);
    for (const key of keys) {
      expect(
        canonicalSet.has(key),
        `dashboard-registry tiene clave inesperada: ${key}. Solo slugs canónicos permitidos.`,
      ).toBe(true);
    }
  });

  it("keys count equals canonical channel count (exhaustive union)", () => {
    const keys = Object.keys(DASHBOARD_COMPONENT_MAP);
    expect(keys.length).toBe(CANONICAL_CHANNEL_SLUGS.length);
  });
});
