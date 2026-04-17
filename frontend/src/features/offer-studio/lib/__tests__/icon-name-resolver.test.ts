import { describe, it, expect } from "vitest";

import { resolveIconByName, ICON_BY_NAME } from "../icon-name-resolver";

describe("resolveIconByName", () => {
  it("returns the matching Lucide component for a known name", () => {
    expect(resolveIconByName("Briefcase")).toBe(ICON_BY_NAME.Briefcase);
    expect(resolveIconByName("Rocket")).toBe(ICON_BY_NAME.Rocket);
  });

  it("maps the StrEnum 'Infinity' to the InfinityIcon alias", () => {
    // "Infinity" collides with the JS global, hence the import alias —
    // the map key is still the plain string from the backend catalog.
    expect(resolveIconByName("Infinity")).toBe(ICON_BY_NAME.Infinity);
  });

  it("falls back to Sparkles on unknown names", () => {
    expect(resolveIconByName("NotARealIcon")).toBe(ICON_BY_NAME.Sparkles);
  });

  it("falls back to Sparkles on undefined input", () => {
    expect(resolveIconByName(undefined)).toBe(ICON_BY_NAME.Sparkles);
  });
});
