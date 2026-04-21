import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useActiveField } from "../use-active-field";

vi.mock("next/navigation", () => ({
  usePathname: vi.fn(() => "/t/brand-studio/identity"),
  useSearchParams: vi.fn(() => new URLSearchParams()),
}));

const { usePathname, useSearchParams } = await import("next/navigation");

function mockRoute({
  pathname = "/t/brand-studio/identity",
  search = "",
}: {
  pathname?: string;
  search?: string;
} = {}) {
  vi.mocked(usePathname).mockReturnValue(pathname);
  vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams(search) as never);
  window.history.replaceState(null, "", `${pathname}${search ? `?${search}` : ""}`);
}

describe("useActiveField", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRoute();
  });

  it("returns null when ?field= is absent", () => {
    const { result } = renderHook(() => useActiveField());
    expect(result.current.activeFieldId).toBeNull();
  });

  it("reads the initial field from the query param", () => {
    mockRoute({ search: "field=tagline" });
    const { result } = renderHook(() => useActiveField());
    expect(result.current.activeFieldId).toBe("tagline");
  });

  it("builds an href that preserves the current pathname and query string", () => {
    mockRoute({ pathname: "/t/offer-studio/offer/o/editor/identity", search: "edition=2" });
    const { result } = renderHook(() => useActiveField());
    expect(result.current.getFieldHref("frase")).toBe(
      "/t/offer-studio/offer/o/editor/identity?edition=2&field=frase",
    );
    expect(result.current.getFieldHref(null)).toBe(
      "/t/offer-studio/offer/o/editor/identity?edition=2",
    );
  });

  it("setActiveField updates history + notifies subscribers without full navigation", () => {
    const { result } = renderHook(() => useActiveField());
    act(() => {
      result.current.setActiveField("tagline");
    });
    expect(window.location.search).toBe("?field=tagline");
    expect(result.current.activeFieldId).toBe("tagline");
  });

  it("setActiveField(null) clears the query param", () => {
    mockRoute({ search: "field=tagline" });
    const { result } = renderHook(() => useActiveField());
    act(() => {
      result.current.setActiveField(null);
    });
    expect(window.location.search).toBe("");
    expect(result.current.activeFieldId).toBeNull();
  });
});
