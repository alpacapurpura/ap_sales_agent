/**
 * Tests for ETLRateLimitedAction component.
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { ETLRateLimitedAction } from "../ETLRateLimitedAction";
import { clearRegistry } from "@/lib/form-runtime/actions";

vi.mock("@/features/tenant/context/tenant-locale-context", () => ({
  useTenantLocale: () => ({ currency: "USD", timezone: "America/Lima" }),
}));

describe("ETLRateLimitedAction", () => {
  beforeEach(() => {
    clearRegistry();
  });

  it("renders rate limit alert with role=alert", () => {
    render(
      <ETLRateLimitedAction
        value={{ channel: "meta-ads", retry_after_seconds: 120 }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("renders channel name", () => {
    render(
      <ETLRateLimitedAction
        value={{ channel: "meta-ads", retry_after_seconds: 120 }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText(/meta-ads/i)).toBeInTheDocument();
  });

  it("renders retry_after_seconds information", () => {
    render(
      <ETLRateLimitedAction
        value={{ channel: "email-nurture", retry_after_seconds: 300 }}
        onChange={vi.fn()}
      />,
    );
    // Should show retry time info somewhere in the alert
    const alert = screen.getByRole("alert");
    expect(alert.textContent).toMatch(/300|5 min|espera|límite/i);
  });

  it("shows Spanish neutro message about rate limit", () => {
    render(
      <ETLRateLimitedAction
        value={{ channel: "meta-ads", retry_after_seconds: 60 }}
        onChange={vi.fn()}
      />,
    );
    const alert = screen.getByRole("alert");
    expect(alert.textContent).toMatch(/límite|tarifa|espera|intentar/i);
  });
});
