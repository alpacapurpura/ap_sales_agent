import { describe, it, expect } from "vitest";

import {
  SETTINGS_SECTIONS,
  SETTINGS_GROUP_LABELS,
  SETTINGS_DEFAULT_SECTION,
  getSettingsSection,
  getSettingsSectionLabel,
  type SettingsGroup,
} from "./section-catalog";

describe("settings section-catalog", () => {
  it("has exactly 8 sections", () => {
    expect(SETTINGS_SECTIONS).toHaveLength(8);
  });

  it("has exactly 3 groups", () => {
    const groups = new Set(SETTINGS_SECTIONS.map((s) => s.group));
    expect(groups.size).toBe(3);
  });

  it("all groups have labels", () => {
    const groups: SettingsGroup[] = ["principal", "ventas", "desarrolladores"];
    for (const g of groups) {
      expect(SETTINGS_GROUP_LABELS[g]).toBeDefined();
      expect(SETTINGS_GROUP_LABELS[g].length).toBeGreaterThan(0);
    }
  });

  it("all slugs are unique", () => {
    const slugs = SETTINGS_SECTIONS.map((s) => s.slug);
    expect(new Set(slugs).size).toBe(slugs.length);
  });

  it("all sections have icons", () => {
    for (const section of SETTINGS_SECTIONS) {
      // Lucide icons are forwardRef objects (typeof === 'object'), not plain functions
      expect(section.icon).toBeDefined();
      expect(section.icon).not.toBeNull();
    }
  });

  it("default section is 'general'", () => {
    expect(SETTINGS_DEFAULT_SECTION).toBe("general");
  });

  it("getSettingsSection returns correct meta for known slug", () => {
    const meta = getSettingsSection("general");
    expect(meta?.label).toBe("General");
    expect(meta?.group).toBe("principal");
  });

  it("getSettingsSection returns undefined for unknown slug", () => {
    expect(getSettingsSection("does-not-exist")).toBeUndefined();
  });

  it("getSettingsSectionLabel falls back to slug for unknown", () => {
    expect(getSettingsSectionLabel("unknown-slug")).toBe("unknown-slug");
  });

  it("contains perfil-negocio section in principal group", () => {
    const section = getSettingsSection("perfil-negocio");
    expect(section).toBeDefined();
    expect(section?.group).toBe("principal");
    expect(section?.label).toBe("Perfil de negocio");
  });

  it("sections have no voseo copy in labels", () => {
    // Spanish rule 11: no voseo
    const voseoPattern = /\b(tenés|podés|hacés|sos|venís|querés)\b/;
    for (const section of SETTINGS_SECTIONS) {
      expect(section.label).not.toMatch(voseoPattern);
    }
  });
});
