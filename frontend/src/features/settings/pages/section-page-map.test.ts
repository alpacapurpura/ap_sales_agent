import * as fs from "node:fs";
import * as path from "node:path";

import { describe, it, expect } from "vitest";

import { SETTINGS_SECTIONS } from "../lib/section-catalog";

import { SETTINGS_SECTION_MAP, type SettingsSectionSlug } from "./section-page-map";

describe("settings section-page-map", () => {
  it("every catalog slug has a corresponding page component", () => {
    for (const section of SETTINGS_SECTIONS) {
      expect(
        SETTINGS_SECTION_MAP[section.slug as SettingsSectionSlug],
        `Missing page for slug: ${section.slug}`,
      ).toBeDefined();
    }
  });

  it("no orphan entries in map not present in catalog", () => {
    const catalogSlugs = new Set(SETTINGS_SECTIONS.map((s) => s.slug));
    for (const slug of Object.keys(SETTINGS_SECTION_MAP)) {
      expect(catalogSlugs.has(slug), `Orphan entry in map: ${slug}`).toBe(true);
    }
  });

  it("all map values are functions (components)", () => {
    for (const [slug, Component] of Object.entries(SETTINGS_SECTION_MAP)) {
      expect(typeof Component, `${slug} is not a function`).toBe("function");
    }
  });

  it("section-page-map.ts does NOT have 'use client' directive (server-safe)", () => {
    const filePath = path.join(__dirname, "section-page-map.ts");
    const content = fs.readFileSync(filePath, "utf-8");
    // Must not start with "use client" at top of file
    const firstLines = content.split("\n").slice(0, 5).join("\n");
    expect(firstLines).not.toContain('"use client"');
    expect(firstLines).not.toContain("'use client'");
  });
});
