/**
 * ARCH TEST: studios mantienen paridad estructural en pages/ (adapter mode).
 *
 * Cada studio define sus archivos canónicos bajo `features/{studio}/pages/`.
 * La forma EXACTA puede diferir por studio (adapter mode per AD6 de
 * growth-studio-folder-parity), pero cada studio DEBE tener la estructura
 * canonical para su dominio.
 *
 * --- Brand-studio + Offer-studio (SECTION pattern) ---
 * Archivos canónicos:
 *   - pages/section-slugs.ts
 *   - pages/SectionDispatcher.tsx
 *   - pages/sections/ (directorio con N *-page.tsx)
 *
 * --- Growth-studio (STAGE + CHANNEL pattern — adapter mode) ---
 * Archivos canónicos:
 *   - pages/stage-slugs.ts         (stage dispatcher thin slug list)
 *   - pages/StageDispatcher.tsx     (factory lazy-loader per stage)
 *   - pages/channel-slugs.ts        (channel dispatcher thin slug list)
 *   - pages/ChannelDispatcher.tsx   (factory lazy-loader per channel)
 *   - pages/tiers/                  (4-tier loading hooks: tier0..tier3)
 *
 * Este test NO enforza que N sea igual entre studios ni los mismos slugs.
 * Solo valida que la *forma* del módulo sea la correcta para su dominio.
 *
 * Adapter mode rationale (AD6): growth-studio tiene 5 etapas × N canales
 * × 4-tier loading, lo cual difiere del pattern section-only de brand/offer.
 * Per-studio canonical config permite verificar FORM no SHAPE.
 */
import * as fs from "fs";
import * as path from "path";

import { describe, it, expect } from "vitest";

import { SRC_DIR } from "./helpers";

// ─── Section-based studios (brand + offer) ───────────────────────────────────

const SECTION_CANONICAL_FILES = ["section-slugs.ts", "SectionDispatcher.tsx"] as const;

const SECTION_STUDIO_PAGE_DIRS: Record<string, string> = {
  brand: path.join(SRC_DIR, "features", "brand-studio", "pages"),
  offer: path.join(SRC_DIR, "features", "offer-studio", "pages"),
};

// ─── Growth-studio canonical config (adapter mode) ────────────────────────────

const GROWTH_STUDIO_PAGES = path.join(SRC_DIR, "features", "growth-studio", "pages");

/**
 * Canonical files + directories that growth-studio/pages/ MUST define.
 * Different from section-based studios — adapter mode per AD6.
 */
const GROWTH_CANONICAL_FILES = [
  "stage-slugs.ts",
  "StageDispatcher.tsx",
  "channel-slugs.ts",
  "ChannelDispatcher.tsx",
] as const;

const GROWTH_CANONICAL_DIRS = [
  "tiers", // 4-tier loading hooks
] as const;

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("Architecture: studio structure parity", () => {
  // ── Section-based studios (brand + offer) ──────────────────────────────

  for (const filename of SECTION_CANONICAL_FILES) {
    it(`brand-studio and offer-studio both define ${filename}`, () => {
      for (const [studio, dir] of Object.entries(SECTION_STUDIO_PAGE_DIRS)) {
        const full = path.join(dir, filename);
        expect(
          fs.existsSync(full),
          `${studio}-studio falta ${filename} — patrón homologado requiere ambos.`,
        ).toBe(true);
      }
    });
  }

  it("brand-studio and offer-studio both have a sections/ directory with at least one *-page.tsx", () => {
    for (const [studio, dir] of Object.entries(SECTION_STUDIO_PAGE_DIRS)) {
      const sectionsDir = path.join(dir, "sections");
      expect(fs.existsSync(sectionsDir), `${studio}-studio falta pages/sections/`).toBe(true);

      const files = fs.readdirSync(sectionsDir).filter((f) => f.endsWith("-page.tsx"));
      expect(files.length, `${studio}-studio/pages/sections/ sin *-page.tsx files`).toBeGreaterThan(
        0,
      );
    }
  });

  // ── Growth-studio (adapter mode — AD6) ────────────────────────────────────

  for (const filename of GROWTH_CANONICAL_FILES) {
    it(`growth-studio defines canonical file: pages/${filename}`, () => {
      const full = path.join(GROWTH_STUDIO_PAGES, filename);
      expect(
        fs.existsSync(full),
        `growth-studio falta pages/${filename} — adapter mode canonical file requerido (AD6).`,
      ).toBe(true);
    });
  }

  for (const dirName of GROWTH_CANONICAL_DIRS) {
    it(`growth-studio has canonical directory: pages/${dirName}/`, () => {
      const full = path.join(GROWTH_STUDIO_PAGES, dirName);
      expect(
        fs.existsSync(full),
        `growth-studio falta pages/${dirName}/ — adapter mode canonical directory (AD6).`,
      ).toBe(true);
    });
  }

  it("growth-studio pages/tiers/ contains all 4 tier files (tier0..tier3)", () => {
    const tiersDir = path.join(GROWTH_STUDIO_PAGES, "tiers");
    expect(
      fs.existsSync(tiersDir),
      "growth-studio falta pages/tiers/ — 4-tier loading hooks requeridos.",
    ).toBe(true);

    const tierFiles = fs
      .readdirSync(tiersDir)
      .filter((f) => f.endsWith(".ts") || f.endsWith(".tsx"));

    // Must have at least 4 tier files
    expect(
      tierFiles.length,
      `growth-studio pages/tiers/ solo tiene ${tierFiles.length} archivo(s) — se esperan 4 (tier0..tier3).`,
    ).toBeGreaterThanOrEqual(4);
  });
});
