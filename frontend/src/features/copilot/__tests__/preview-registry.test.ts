import { describe, it, expect } from "vitest";
import { getPreviewEntry, getSupportedDomains } from "../config/interview-preview-registry";

describe("Preview Registry (lazy)", () => {
  it("returns entry for brand domain", () => {
    const entry = getPreviewEntry("brand");
    expect(entry).not.toBeNull();
    expect(entry!.emptyStateMessage).toBeTruthy();
    expect(typeof entry!.summaryComponent).toBe("function");
    expect(typeof entry!.sectionsComponent).toBe("function");
  });

  it("returns entry for offer domain", () => {
    const entry = getPreviewEntry("offer");
    expect(entry).not.toBeNull();
    expect(entry!.emptyStateMessage).toBeTruthy();
  });

  it("returns entry for buyer_persona domain", () => {
    const entry = getPreviewEntry("buyer_persona");
    expect(entry).not.toBeNull();
  });

  it("returns null for unknown domain", () => {
    const entry = getPreviewEntry("unknown");
    expect(entry).toBeNull();
  });

  it("lists supported domains", () => {
    const domains = getSupportedDomains();
    expect(domains).toContain("brand");
    expect(domains).toContain("offer");
    expect(domains).toContain("buyer_persona");
    expect(domains).toHaveLength(3);
  });
});
