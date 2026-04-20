import { describe, it, expect, vi } from "vitest";

import { createFormRuntimeBridge, type FormRuntimeBridge } from "../bridge";

import type { SectionSchema } from "../../schema/types";

const SCHEMA: SectionSchema = {
  key: "brand.identity",
  title: "Identity",
  fields: [
    { id: "name", label: "Name", type: "text", path: "name" },
    { id: "mission", label: "Mission", type: "textarea", path: "mission" },
  ],
};

const noopPatch: (path: string, value: unknown) => Promise<void> = () => Promise.resolve();

function makeBridge(
  initial: Record<string, unknown> = {},
  onPatch: (path: string, value: unknown) => Promise<void> = noopPatch,
): FormRuntimeBridge {
  return createFormRuntimeBridge({
    schema: SCHEMA,
    getValues: () => initial,
    patchFn: onPatch,
  });
}

describe("FormRuntimeBridge", () => {
  it("getSnapshot returns current sectionKey, schema and values", () => {
    const bridge = makeBridge({ name: "Visionarias" });
    const snap = bridge.getSnapshot();
    expect(snap).not.toBeNull();
    expect(snap?.sectionKey).toBe("brand.identity");
    expect(snap?.values).toEqual({ name: "Visionarias" });
    expect(snap?.schema).toBe(SCHEMA);
  });

  it("patchField delegates to the provided patchFn", async () => {
    const patchFn = vi.fn().mockResolvedValue(undefined);
    const bridge = makeBridge({ name: "old" }, patchFn);

    await bridge.patchField("name", "new");
    expect(patchFn).toHaveBeenCalledWith("name", "new");
  });

  it("focusField notifies subscribers with the new focus state", () => {
    const bridge = makeBridge();
    const listener = vi.fn();
    bridge.subscribe(listener);

    bridge.focusField("name");
    expect(listener).toHaveBeenCalled();
    const lastCall = listener.mock.calls.at(-1);
    expect(lastCall).toBeDefined();
    const [lastSnapshot] = lastCall ?? [];
    expect(lastSnapshot?.focusedField).toEqual({
      id: "name",
      label: "Name",
      path: "name",
    });
  });

  it("focusField with unknown id clears focus (null)", () => {
    const bridge = makeBridge();
    bridge.focusField("name");
    bridge.focusField(null);
    const snap = bridge.getSnapshot();
    expect(snap?.focusedField).toBeNull();
  });

  it("subscribe returns an unsubscribe function", () => {
    const bridge = makeBridge();
    const listener = vi.fn();
    const unsubscribe = bridge.subscribe(listener);

    bridge.focusField("name");
    expect(listener).toHaveBeenCalledTimes(1);

    unsubscribe();
    bridge.focusField("mission");
    expect(listener).toHaveBeenCalledTimes(1);
  });

  it("multiple subscribers all receive notifications", () => {
    const bridge = makeBridge();
    const a = vi.fn();
    const b = vi.fn();
    bridge.subscribe(a);
    bridge.subscribe(b);

    bridge.focusField("name");
    expect(a).toHaveBeenCalledTimes(1);
    expect(b).toHaveBeenCalledTimes(1);
  });

  it("notifies subscribers after a successful patchField", async () => {
    let stored: Record<string, unknown> = { name: "old" };
    const bridge = createFormRuntimeBridge({
      schema: SCHEMA,
      getValues: () => stored,
      patchFn: async (p, v) => {
        stored = { ...stored, [p]: v };
      },
    });
    const listener = vi.fn();
    bridge.subscribe(listener);

    await bridge.patchField("name", "new");
    expect(listener).toHaveBeenCalled();
    expect(bridge.getSnapshot()?.values).toEqual({ name: "new" });
  });

  it("propagates patchFn failures without corrupting subscriber state", async () => {
    const bridge = makeBridge({ name: "old" }, async () => {
      throw new Error("api down");
    });
    await expect(bridge.patchField("name", "new")).rejects.toThrow("api down");
  });

  it("looks up field metadata by id on focusField", () => {
    const bridge = makeBridge();
    bridge.focusField("mission");
    const snap = bridge.getSnapshot();
    expect(snap?.focusedField?.label).toBe("Mission");
    expect(snap?.focusedField?.path).toBe("mission");
  });
});
