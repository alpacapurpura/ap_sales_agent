import { describe, expect, it } from "vitest";

import { buildCrumbs } from "../BrandStudioBreadcrumb";

describe("BrandStudioBreadcrumb · buildCrumbs", () => {
  it("renders the root when path ends at /brand-studio", () => {
    const crumbs = buildCrumbs("/t-demo/brand-studio", "t-demo");
    expect(crumbs).toHaveLength(1);
    expect(crumbs[0]?.label).toBe("Brand Studio");
  });

  it("appends the section when present", () => {
    const crumbs = buildCrumbs("/t/brand-studio/positioning", "t");
    expect(crumbs.map((c) => c.label)).toEqual(["Brand Studio", "Posicionamiento"]);
  });

  it("appends the field id on singleton routes", () => {
    const crumbs = buildCrumbs("/t/brand-studio/positioning/uvp", "t");
    expect(crumbs.map((c) => c.label)).toEqual(["Brand Studio", "Posicionamiento", "uvp"]);
  });

  it("includes instance and field for uniform collection route", () => {
    const crumbs = buildCrumbs("/t/brand-studio/publico/instance/alicia-1234-abcd/dolor", "t");
    expect(crumbs).toHaveLength(4);
    expect(crumbs[0]?.label).toBe("Brand Studio");
    expect(crumbs[1]?.label).toBe("Buyer personas");
    expect(crumbs[2]?.label).toMatch(/Instancia/);
    expect(crumbs[3]?.label).toBe("dolor");
  });

  it("supports legacy publico/persona alias", () => {
    const crumbs = buildCrumbs("/t/brand-studio/publico/persona/p-1234-abcd/pain", "t");
    expect(crumbs).toHaveLength(4);
    expect(crumbs[2]?.label).toMatch(/Persona/);
    expect(crumbs[3]?.label).toBe("pain");
  });

  it("marks the last crumb without href so it renders as active leaf", () => {
    const crumbs = buildCrumbs("/t/brand-studio/positioning/uvp", "t");
    expect(crumbs[crumbs.length - 1]?.href).toBeUndefined();
  });
});
