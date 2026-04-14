import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useIgnoredNotices, __IGNORE_STORAGE_KEY, __IGNORE_TTL_MS } from "../useIgnoredNotices";

describe("useIgnoredNotices", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-04-10T15:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("starts with an empty ignored set when localStorage is empty", () => {
    const { result } = renderHook(() => useIgnoredNotices());
    expect(result.current.ignored.size).toBe(0);
    expect(result.current.isIgnored("meta:foo:1")).toBe(false);
  });

  it("ignores an id and reports it as ignored", () => {
    const { result } = renderHook(() => useIgnoredNotices());

    act(() => {
      result.current.ignore("meta:foo:1");
    });

    expect(result.current.isIgnored("meta:foo:1")).toBe(true);
    expect(result.current.isIgnored("meta:bar:2")).toBe(false);
  });

  it("persists ignored ids in localStorage with a timestamp", () => {
    const { result } = renderHook(() => useIgnoredNotices());

    act(() => {
      result.current.ignore("meta:foo:1");
    });

    const raw = localStorage.getItem(__IGNORE_STORAGE_KEY);
    expect(raw).not.toBeNull();
    const parsed: [string, number][] = JSON.parse(raw!);
    expect(parsed).toHaveLength(1);
    expect(parsed[0][0]).toBe("meta:foo:1");
    expect(typeof parsed[0][1]).toBe("number");
  });

  it("loads previously-ignored ids on mount", () => {
    const now = Date.now();
    localStorage.setItem(__IGNORE_STORAGE_KEY, JSON.stringify([["meta:foo:1", now]]));

    const { result } = renderHook(() => useIgnoredNotices());

    expect(result.current.isIgnored("meta:foo:1")).toBe(true);
  });

  it("purges entries older than the TTL on mount", () => {
    const now = Date.now();
    const stale = now - __IGNORE_TTL_MS - 1;
    localStorage.setItem(
      __IGNORE_STORAGE_KEY,
      JSON.stringify([
        ["meta:fresh:1", now],
        ["meta:stale:2", stale],
      ]),
    );

    const { result } = renderHook(() => useIgnoredNotices());

    expect(result.current.isIgnored("meta:fresh:1")).toBe(true);
    expect(result.current.isIgnored("meta:stale:2")).toBe(false);

    // The purge must also be written back so stale entries don't accumulate.
    const raw = JSON.parse(localStorage.getItem(__IGNORE_STORAGE_KEY)!) as [string, number][];
    expect(raw.map(([id]) => id)).toEqual(["meta:fresh:1"]);
  });

  it("returns the same ignore function across renders (stable reference)", () => {
    const { result, rerender } = renderHook(() => useIgnoredNotices());
    const firstIgnore = result.current.ignore;
    rerender();
    expect(result.current.ignore).toBe(firstIgnore);
  });

  it("handles invalid JSON in localStorage gracefully", () => {
    localStorage.setItem(__IGNORE_STORAGE_KEY, "not-valid-json");
    const { result } = renderHook(() => useIgnoredNotices());
    expect(result.current.ignored.size).toBe(0);
  });
});
