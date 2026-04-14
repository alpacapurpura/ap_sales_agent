import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import React from "react";

// Mock Clerk — must be before importing the module under test
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("test-token") }),
}));

import { TenantLocaleProvider, useTenantLocale } from "../context/tenant-locale-context";

describe("useTenantLocale", () => {
  it("returns default values when no provider", () => {
    const { result } = renderHook(() => useTenantLocale());
    expect(result.current.currency).toBe("USD");
    expect(result.current.timezone).toBe("UTC");
  });

  it("returns provided values from context", () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <TenantLocaleProvider initialLocale={{ currency: "PEN", timezone: "America/Lima" }}>
        {children}
      </TenantLocaleProvider>
    );

    const { result } = renderHook(() => useTenantLocale(), { wrapper });
    expect(result.current.currency).toBe("PEN");
    expect(result.current.timezone).toBe("America/Lima");
  });
});
