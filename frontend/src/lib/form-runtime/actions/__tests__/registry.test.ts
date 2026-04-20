/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, beforeEach } from "vitest";

import {
  registerAction,
  getAction,
  hasAction,
  listActions,
  clearRegistry,
  type ActionComponent,
} from "../registry";

const VOICE_KEY = "voice-clone";
const DUP_KEY = "dup";
const StubAction = (() => null) as unknown as ActionComponent;
const AnotherAction = (() => null) as unknown as ActionComponent;

describe("action registry", () => {
  beforeEach(() => {
    clearRegistry();
  });

  it("registers and retrieves an action by key", () => {
    registerAction(VOICE_KEY, StubAction);
    expect(getAction(VOICE_KEY)).toBe(StubAction);
  });

  it("hasAction returns true only for registered keys", () => {
    registerAction(VOICE_KEY, StubAction);
    expect(hasAction(VOICE_KEY)).toBe(true);
    expect(hasAction("missing")).toBe(false);
  });

  it("getAction returns undefined for missing key", () => {
    expect(getAction("missing")).toBeUndefined();
  });

  it("listActions returns all registered keys sorted", () => {
    registerAction("b", StubAction);
    registerAction("a", AnotherAction);
    expect(listActions()).toEqual(["a", "b"]);
  });

  it("re-registering a key throws by default (prevents silent clobbering)", () => {
    registerAction(DUP_KEY, StubAction);
    expect(() => registerAction(DUP_KEY, AnotherAction)).toThrow(/already registered/i);
  });

  it("re-registering with { override: true } replaces the prior entry", () => {
    registerAction(DUP_KEY, StubAction);
    registerAction(DUP_KEY, AnotherAction, { override: true });
    expect(getAction(DUP_KEY)).toBe(AnotherAction);
  });

  it("rejects empty keys", () => {
    expect(() => registerAction("", StubAction)).toThrow(/key/i);
  });

  it("rejects null component", () => {
    expect(() => registerAction("x", null as any)).toThrow(/component/i);
  });

  it("clearRegistry empties the map (used by tests only)", () => {
    registerAction("a", StubAction);
    clearRegistry();
    expect(listActions()).toEqual([]);
  });
});
