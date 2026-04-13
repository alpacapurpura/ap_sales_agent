/**
 * Legacy tests for the backward-compatible API surface of the preview registry.
 *
 * NOTE: registerPreview() and clearPreviewRegistry() are now no-ops — the registry
 * is static. These tests verify that the backward-compatible functions still
 * behave consistently with their documented contracts under the new design.
 */
import { describe, it, expect } from "vitest";
import {
  registerPreview,
  getPreview,
  clearPreviewRegistry,
  type PreviewConfig,
} from "../interview-preview-registry";

const mockConfig: PreviewConfig = {
  summaryComponent: (() => null) as any,
  sectionsComponent: (() => null) as any,
  emptyStateMessage: "No hay datos todavía",
};

describe("interview-preview-registry (backward-compat)", () => {
  it("clearPreviewRegistry is a no-op and does not throw", () => {
    expect(() => clearPreviewRegistry()).not.toThrow();
  });

  it("registerPreview is a no-op and does not throw", () => {
    expect(() => registerPreview("brand", mockConfig)).not.toThrow();
  });

  it("getPreview returns a config for built-in domains (brand)", () => {
    const result = getPreview("brand");
    expect(result).toBeDefined();
    expect(result.emptyStateMessage).toBeTruthy();
  });

  it("getPreview returns a config for built-in domains (buyer_persona)", () => {
    const result = getPreview("buyer_persona");
    expect(result).toBeDefined();
    expect(result.emptyStateMessage).toBeTruthy();
  });

  it("getPreview throws for a domain that was never registered", () => {
    expect(() => getPreview("nonexistent_xyz")).toThrow(
      "No preview registered for domain: nonexistent_xyz",
    );
  });
});
