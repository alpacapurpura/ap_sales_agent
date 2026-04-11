import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useAutoSave } from "../use-auto-save";

/**
 * Flushes microtasks so pending `.then` callbacks (from resolved promises
 * inside the hook) run before the next assertion. Must be awaited inside
 * `act()` to keep React state transitions batched.
 */
async function flushMicrotasks(times = 3): Promise<void> {
  for (let i = 0; i < times; i += 1) {
    await Promise.resolve();
  }
}

describe("useAutoSave", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("starts in idle state with no last saved timestamp", () => {
    const saveFn = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() => useAutoSave({ saveFn }));

    expect(result.current.state).toBe("idle");
    expect(result.current.lastSavedAt).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("debounces trigger calls by 800ms by default", async () => {
    const saveFn = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() => useAutoSave<{ name: string }>({ saveFn }));

    act(() => {
      result.current.trigger({ name: "first" });
    });
    act(() => {
      vi.advanceTimersByTime(500);
    });
    expect(saveFn).not.toHaveBeenCalled();

    act(() => {
      result.current.trigger({ name: "second" });
    });
    act(() => {
      vi.advanceTimersByTime(500);
    });
    expect(saveFn).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(400);
    });
    expect(saveFn).toHaveBeenCalledTimes(1);
    expect(saveFn).toHaveBeenCalledWith({ name: "second" });
  });

  it("transitions idle → saving → saved on a successful save", async () => {
    let resolveSave: (() => void) | undefined;
    const saveFn = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveSave = resolve;
        }),
    );
    const { result } = renderHook(() =>
      useAutoSave<string>({ saveFn, delay: 100 }),
    );

    act(() => {
      result.current.trigger("payload");
    });
    expect(result.current.state).toBe("idle");

    await act(async () => {
      vi.advanceTimersByTime(100);
      await flushMicrotasks();
    });
    expect(saveFn).toHaveBeenCalledWith("payload");
    expect(result.current.state).toBe("saving");

    await act(async () => {
      resolveSave?.();
      await flushMicrotasks();
    });

    expect(result.current.state).toBe("saved");
    expect(result.current.lastSavedAt).not.toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("transitions to error state and exposes the error", async () => {
    const failure = new Error("boom");
    const saveFn = vi.fn().mockRejectedValue(failure);
    const { result } = renderHook(() =>
      useAutoSave<string>({ saveFn, delay: 50 }),
    );

    act(() => {
      result.current.trigger("payload");
    });
    await act(async () => {
      vi.advanceTimersByTime(50);
      await flushMicrotasks();
    });

    expect(result.current.state).toBe("error");
    expect(result.current.error).toBe(failure);
    expect(result.current.lastSavedAt).toBeNull();
  });

  it("retries the last payload and transitions back to saved", async () => {
    const saveFn = vi
      .fn<(payload: string) => Promise<void>>()
      .mockRejectedValueOnce(new Error("first-failure"))
      .mockResolvedValueOnce(undefined);

    const { result } = renderHook(() =>
      useAutoSave<string>({ saveFn, delay: 10 }),
    );

    act(() => {
      result.current.trigger("payload");
    });
    await act(async () => {
      vi.advanceTimersByTime(10);
      await flushMicrotasks();
    });

    expect(result.current.state).toBe("error");
    expect(saveFn).toHaveBeenCalledTimes(1);

    await act(async () => {
      result.current.retry();
      await flushMicrotasks();
    });

    expect(result.current.state).toBe("saved");
    expect(saveFn).toHaveBeenCalledTimes(2);
    expect(saveFn).toHaveBeenLastCalledWith("payload");
  });

  it("cancel clears a pending save without firing saveFn", () => {
    const saveFn = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useAutoSave<string>({ saveFn, delay: 200 }),
    );

    act(() => {
      result.current.trigger("payload");
    });
    act(() => {
      result.current.cancel();
      vi.advanceTimersByTime(500);
    });
    expect(saveFn).not.toHaveBeenCalled();
    expect(result.current.state).toBe("idle");
  });
});
