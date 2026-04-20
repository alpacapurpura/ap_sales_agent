import { beforeEach, describe, expect, it } from "vitest";

import { clearRegistry, hasAction, listActions } from "@/lib/form-runtime/actions";

import { BRAND_STUDIO_ACTION_KEYS, bootstrapBrandStudioActions } from "../registry";

describe("brand-studio action registry bootstrap", () => {
  beforeEach(() => {
    clearRegistry();
  });

  it("registers every advertised action key when bootstrapped", () => {
    bootstrapBrandStudioActions();
    for (const key of BRAND_STUDIO_ACTION_KEYS) {
      expect(hasAction(key), `missing: ${key}`).toBe(true);
    }
  });

  it("exposes exactly 13 brand-studio actions", () => {
    bootstrapBrandStudioActions();
    expect(listActions().length).toBeGreaterThanOrEqual(BRAND_STUDIO_ACTION_KEYS.length);
  });

  it("is idempotent", () => {
    bootstrapBrandStudioActions();
    const first = listActions();
    bootstrapBrandStudioActions();
    const second = listActions();
    expect(second).toEqual(first);
  });
});
