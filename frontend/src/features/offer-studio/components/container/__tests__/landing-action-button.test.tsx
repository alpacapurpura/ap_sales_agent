import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi } from "vitest";

import { TooltipProvider } from "@/components/ui/tooltip";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockUseLandingStatus = vi.fn();

vi.mock("../../../hooks/use-landing-status", async () => {
  const actual = await vi.importActual<typeof import("../../../hooks/use-landing-status")>(
    "../../../hooks/use-landing-status",
  );
  return {
    ...actual,
    useLandingStatus: (...args: unknown[]) => mockUseLandingStatus(...args),
  };
});

// ── Imports after mocks ──────────────────────────────────────────────────────

import { LandingActionButton } from "../landing-action-button";

import type { LandingStatusResponse } from "../../../types/landing-status";

function renderWithTooltip(ui: React.ReactElement) {
  return render(<TooltipProvider>{ui}</TooltipProvider>);
}

function mockStatus(
  uiState: "disabled" | "ready-to-generate" | "in-sync" | "outdated",
  overrides: Partial<LandingStatusResponse> = {},
) {
  const base: LandingStatusResponse = {
    offer_id: "offer-1",
    landing_page_id: null,
    is_generated: false,
    is_published: false,
    is_outdated: false,
    generated_at: null,
    offer_snapshot_version: null,
    offer_updated_at: "2026-04-10T00:00:00Z",
    job_id: null,
    job_status: "idle",
    landing_url: null,
    editor_url: null,
    completion_percentage: 50,
    ...overrides,
  };
  mockUseLandingStatus.mockReturnValue({
    data: base,
    uiState,
    isLoading: false,
    isError: false,
    generate: { mutate: vi.fn(), isPending: false },
    regenerate: { mutate: vi.fn(), isPending: false },
    publish: { mutate: vi.fn(), isPending: false },
    unpublish: { mutate: vi.fn(), isPending: false },
  });
}

describe("LandingActionButton", () => {
  it("renders a disabled 'Generar landing' button when state is 'disabled'", () => {
    mockStatus("disabled", { completion_percentage: 45 });
    renderWithTooltip(<LandingActionButton offerId="offer-1" tenantId="acme" />);
    const btn = screen.getByRole("button", { name: /Generar landing/i });
    expect(btn).toBeDisabled();
    // Shows progress percentage badge
    expect(screen.getByText(/45%/)).toBeInTheDocument();
  });

  it("renders 'Generar landing con IA' when state is 'ready-to-generate'", () => {
    mockStatus("ready-to-generate", { completion_percentage: 95 });
    renderWithTooltip(<LandingActionButton offerId="offer-1" tenantId="acme" />);
    expect(screen.getByRole("button", { name: /Generar landing con IA/i })).toBeInTheDocument();
  });

  it("renders 'Abrir landing' when state is 'in-sync'", () => {
    mockStatus("in-sync", {
      is_generated: true,
      is_outdated: false,
      landing_url: "https://example.com/l/foo",
      completion_percentage: 100,
    });
    renderWithTooltip(<LandingActionButton offerId="offer-1" tenantId="acme" />);
    expect(screen.getByRole("button", { name: /Abrir landing/i })).toBeInTheDocument();
  });

  it("renders 'Abrir landing' with outdated indicator when state is 'outdated'", () => {
    mockStatus("outdated", {
      is_generated: true,
      is_outdated: true,
      landing_url: "https://example.com/l/foo",
      completion_percentage: 100,
    });
    renderWithTooltip(<LandingActionButton offerId="offer-1" tenantId="acme" />);
    expect(screen.getByRole("button", { name: /Abrir landing/i })).toBeInTheDocument();
    // Outdated shows a warning indicator
    expect(screen.getByTestId("landing-outdated-dot")).toBeInTheDocument();
  });

  it("renders nothing while loading", () => {
    mockUseLandingStatus.mockReturnValue({
      data: undefined,
      uiState: null,
      isLoading: true,
      isError: false,
      generate: { mutate: vi.fn(), isPending: false },
      regenerate: { mutate: vi.fn(), isPending: false },
      publish: { mutate: vi.fn(), isPending: false },
      unpublish: { mutate: vi.fn(), isPending: false },
    });
    const { container } = renderWithTooltip(
      <LandingActionButton offerId="offer-1" tenantId="acme" />,
    );
    // Loading skeleton or empty
    expect(container.querySelector("[data-testid='landing-loading']")).toBeTruthy();
  });
});
