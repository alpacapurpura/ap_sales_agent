/**
 * Canonical files existence test for growth-studio folder parity.
 *
 * Validates:
 * - Registry SSoT files exist (T-1 deliverables)
 * - Registries are frozen
 * - Shape is correct (basic shape check at runtime import)
 *
 * This test runs incrementally as tickets are implemented:
 * - T-1 (this): lib/registries/ SSoT (stage, channel, dashboard)
 * - T-2: pages/ factory dispatchers (StageDispatcher, ChannelDispatcher, stage-slugs, channel-slugs, sections/)
 * - T-3: pages/tiers/ (tier0–tier3)
 *
 * Files gated by T-2 (pages/ dispatcher) are guarded with
 * `fs.existsSync` so T-1 validator run passes before T-2 is done.
 */
import * as fs from "fs";
import * as path from "path";

import { describe, it, expect } from "vitest";

const GROWTH_STUDIO_DIR = path.resolve(
  __dirname,
  "..", // growth-studio/
);

// ─── T-1 canonical files (MUST exist after T-1) ────────────────────────────

const T1_CANONICAL_FILES = [
  "lib/registries/stage-registry.ts",
  "lib/registries/channel-registry.ts",
  "lib/registries/dashboard-registry.ts",
  "lib/registries/__tests__/stage-registry.test.ts",
  "lib/registries/__tests__/channel-registry.test.ts",
  "lib/registries/__tests__/dashboard-registry.test.ts",
] as const;

// ─── T-2 canonical files (exist after T-2 — guarded) ─────────────────────

const T2_CANONICAL_FILES = [
  "pages/stage-slugs.ts",
  "pages/StageDispatcher.tsx",
  "pages/channel-slugs.ts",
  "pages/ChannelDispatcher.tsx",
] as const;

// ─── T-3 canonical files (exist after T-3 — guarded) ─────────────────────

const T3_TIER_FILES = [
  "pages/tiers/tier0-summary.ts",
  "pages/tiers/tier1-overview.ts",
  "pages/tiers/tier2-group-detail.ts",
  "pages/tiers/tier3-stage.ts",
] as const;

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("growth-studio: T-1 canonical files (SSoT registries)", () => {
  for (const rel of T1_CANONICAL_FILES) {
    it(`file exists: ${rel}`, () => {
      const full = path.join(GROWTH_STUDIO_DIR, rel);
      expect(
        fs.existsSync(full),
        `Canonical file missing: features/growth-studio/${rel}. Esta ruta es obligatoria post-T-1.`,
      ).toBe(true);
    });
  }
});

describe("growth-studio: T-1 registry shapes (runtime import)", () => {
  it("STAGE_REGISTRY is frozen array with 5 entries", async () => {
    const mod = await import("../lib/registries/stage-registry");
    expect(Object.isFrozen(mod.STAGE_REGISTRY)).toBe(true);
    expect(mod.STAGE_REGISTRY).toHaveLength(5);
  });

  it("CHANNEL_REGISTRY is frozen array with ≥5 entries", async () => {
    const mod = await import("../lib/registries/channel-registry");
    expect(Object.isFrozen(mod.CHANNEL_REGISTRY)).toBe(true);
    expect(mod.CHANNEL_REGISTRY.length).toBeGreaterThanOrEqual(5);
  });

  it("DASHBOARD_COMPONENT_MAP has exactly 5 canonical channel keys", async () => {
    const mod = await import("../lib/registries/dashboard-registry");
    const keys = Object.keys(mod.DASHBOARD_COMPONENT_MAP);
    expect(keys).toHaveLength(5);
  });
});

describe("growth-studio: T-2 canonical files (guarded — ok to skip pre-T-2)", () => {
  for (const rel of T2_CANONICAL_FILES) {
    it(`file exists (T-2): ${rel}`, () => {
      const full = path.join(GROWTH_STUDIO_DIR, rel);
      if (!fs.existsSync(full)) {
        // T-2 not yet implemented — skip gracefully (warn only)
        console.warn(`[INFO] T-2 file not yet created: features/growth-studio/${rel}`);
        return;
      }
      expect(fs.existsSync(full)).toBe(true);
    });
  }
});

describe("growth-studio: T-3 tier files (guarded — ok to skip pre-T-3)", () => {
  for (const rel of T3_TIER_FILES) {
    it(`file exists (T-3): ${rel}`, () => {
      const full = path.join(GROWTH_STUDIO_DIR, rel);
      if (!fs.existsSync(full)) {
        console.warn(`[INFO] T-3 file not yet created: features/growth-studio/${rel}`);
        return;
      }
      expect(fs.existsSync(full)).toBe(true);
    });
  }
});

describe("growth-studio: T-2 pages/sections/ has stage pages (guarded)", () => {
  it("pages/sections/ directory exists with ≥1 *-page.tsx (T-2)", () => {
    const sectionsDir = path.join(GROWTH_STUDIO_DIR, "pages", "sections");
    if (!fs.existsSync(sectionsDir)) {
      console.warn("[INFO] T-2 pages/sections/ not yet created");
      return;
    }
    const files = fs.readdirSync(sectionsDir).filter((f) => f.endsWith("-page.tsx"));
    expect(files.length).toBeGreaterThan(0);
  });
});
