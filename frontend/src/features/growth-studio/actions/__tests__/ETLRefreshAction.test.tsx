/**
 * Tests for ETLRefreshAction component — queued/success state render.
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { ETLRefreshAction } from "../ETLRefreshAction";
import { clearRegistry } from "@/lib/form-runtime/actions";

vi.mock("@/features/tenant/context/tenant-locale-context", () => ({
  useTenantLocale: () => ({ currency: "USD", timezone: "America/Lima" }),
}));

describe("ETLRefreshAction", () => {
  beforeEach(() => {
    clearRegistry();
  });

  it("renders queued status", () => {
    render(
      <ETLRefreshAction value={{ status: "queued", channel: "meta-ads" }} onChange={vi.fn()} />,
    );
    expect(screen.getByText(/meta-ads/i)).toBeInTheDocument();
    // Should show some indication of queued state
    expect(screen.getByText(/en cola|procesando|iniciada|actualización/i)).toBeInTheDocument();
  });

  it("renders channel name in the status", () => {
    render(
      <ETLRefreshAction
        value={{ status: "queued", channel: "email-nurture", run_id: "run-123" }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText(/email-nurture/i)).toBeInTheDocument();
  });

  it("renders run_id when provided", () => {
    render(
      <ETLRefreshAction
        value={{ status: "queued", channel: "meta-ads", run_id: "abc-123" }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText(/abc-123/)).toBeInTheDocument();
  });

  it("has accessible region", () => {
    render(
      <ETLRefreshAction value={{ status: "queued", channel: "meta-ads" }} onChange={vi.fn()} />,
    );
    expect(screen.getByRole("region")).toBeInTheDocument();
  });
});
