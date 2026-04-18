import { describe, it, expect } from "vitest";

import { getPreviewEntry, getSupportedDomains } from "../config/interview-preview-registry";

describe("Preview Registry (lazy)", () => {
  it("returns entry for offer domain", () => {
    const entry = getPreviewEntry("offer");
    expect(entry).not.toBeNull();
    expect(entry!.emptyStateMessage).toBeTruthy();
    expect(typeof entry!.summaryComponent).toBe("function");
    expect(typeof entry!.sectionsComponent).toBe("function");
  });

  it("returns null for brand domain (removed with features/brand/ in Sprint 5)", () => {
    expect(getPreviewEntry("brand")).toBeNull();
  });

  it("returns null for buyer_persona domain (removed with features/brand/ in Sprint 5)", () => {
    expect(getPreviewEntry("buyer_persona")).toBeNull();
  });

  it("returns null for unknown domain", () => {
    const entry = getPreviewEntry("unknown");
    expect(entry).toBeNull();
  });

  it("lists supported domains", () => {
    const domains = getSupportedDomains();
    expect(domains).toEqual(["offer"]);
  });
});
