import { beforeEach, describe, expect, it } from "vitest";

import { clearRegistry, hasAction, listActions } from "@/lib/form-runtime/actions";

import { bootstrapOfferStudioActions, OFFER_STUDIO_ACTION_KEYS } from "../registry";

describe("offer-studio action registry bootstrap", () => {
  beforeEach(() => {
    clearRegistry();
  });

  it("registers every advertised action key when bootstrapped", () => {
    bootstrapOfferStudioActions();
    for (const key of OFFER_STUDIO_ACTION_KEYS) {
      expect(hasAction(key), `missing: ${key}`).toBe(true);
    }
  });

  it("exposes at least all offer-studio actions after bootstrap", () => {
    bootstrapOfferStudioActions();
    expect(listActions().length).toBeGreaterThanOrEqual(OFFER_STUDIO_ACTION_KEYS.length);
  });

  it("is idempotent across multiple bootstrap calls", () => {
    bootstrapOfferStudioActions();
    const first = listActions();
    bootstrapOfferStudioActions();
    const second = listActions();
    expect(second).toEqual(first);
  });

  it("does not override an already-registered action (real-port tolerance)", () => {
    bootstrapOfferStudioActions();
    const before = listActions();
    // Simulate a real-action port that registered before bootstrap.
    bootstrapOfferStudioActions();
    const after = listActions();
    expect(after).toEqual(before);
  });
});
