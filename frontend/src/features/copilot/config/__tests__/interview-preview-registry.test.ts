import { describe, it, expect, beforeEach } from "vitest";
import {
  registerPreview,
  getPreview,
  clearPreviewRegistry,
  type PreviewConfig,
} from "../interview-preview-registry";

const mockConfig: PreviewConfig = {
  summaryComponent: () => null,
  sectionsComponent: () => null,
  emptyStateMessage: "No hay datos todavia",
};

const mockConfigWithTabs: PreviewConfig = {
  summaryComponent: () => null,
  sectionsComponent: () => null,
  tabsComponent: () => null,
  emptyStateMessage: "Sin datos",
};

describe("interview-preview-registry", () => {
  beforeEach(() => {
    clearPreviewRegistry();
  });

  it("registers and retrieves a preview config", () => {
    registerPreview("brand", mockConfig);
    const result = getPreview("brand");
    expect(result).toBe(mockConfig);
  });

  it("throws for unregistered domain", () => {
    expect(() => getPreview("nonexistent_xyz")).toThrow(
      "No preview registered for domain: nonexistent_xyz",
    );
  });

  it("registers config with optional tabsComponent", () => {
    registerPreview("brand_with_tabs", mockConfigWithTabs);
    const result = getPreview("brand_with_tabs");
    expect(result.tabsComponent).toBeDefined();
  });

  it("overwrites existing registration for the same domain", () => {
    registerPreview("brand", mockConfig);
    registerPreview("brand", mockConfigWithTabs);
    const result = getPreview("brand");
    expect(result).toBe(mockConfigWithTabs);
  });

  it("supports multiple domains simultaneously", () => {
    registerPreview("brand", mockConfig);
    registerPreview("buyer_persona", mockConfigWithTabs);

    expect(getPreview("brand")).toBe(mockConfig);
    expect(getPreview("buyer_persona")).toBe(mockConfigWithTabs);
  });
});
