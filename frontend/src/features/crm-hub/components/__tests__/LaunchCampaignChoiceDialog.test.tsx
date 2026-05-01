import { render, screen, fireEvent } from "@testing-library/react";
import * as React from "react";
import { describe, expect, it, vi } from "vitest";

import { LaunchCampaignChoiceDialog } from "../LaunchCampaignChoiceDialog";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, back: vi.fn(), replace: vi.fn() }),
  useParams: () => ({ tenantId: "test-tenant" }),
}));

describe("LaunchCampaignChoiceDialog", () => {
  it("renders segment name in title", () => {
    render(
      <LaunchCampaignChoiceDialog
        open
        onOpenChange={vi.fn()}
        segmentId="seg-123"
        segmentName="Leads Telegram"
      />,
    );

    expect(screen.getByText(/Leads Telegram/)).toBeInTheDocument();
  });

  it("navigates to nuevo campanas route (ASCII, no ñ) when user clicks Sí", () => {
    render(
      <LaunchCampaignChoiceDialog
        open
        onOpenChange={vi.fn()}
        segmentId="seg-abc"
        segmentName="Test Segment"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /sí, crear campaña/i }));

    // Bug #4 fix: route renamed from campañas → campanas (Next.js 16 does not compile ñ in paths)
    expect(mockPush).toHaveBeenCalledWith(
      expect.stringContaining("/test-tenant/sales/campanas/nuevo?segment_id=seg-abc"),
    );
  });

  it("calls onOpenChange(false) when Más tarde clicked", () => {
    const onOpenChange = vi.fn();
    render(
      <LaunchCampaignChoiceDialog
        open
        onOpenChange={onOpenChange}
        segmentId="seg-xyz"
        segmentName="Test"
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /más tarde/i }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
