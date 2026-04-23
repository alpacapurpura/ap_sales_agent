import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import type { SectionStatusEntry } from "@/features/copilot/hooks/use-section-status";

// ── Mocks (must appear before any imports that use the mocked modules) ────────

vi.mock("next/navigation", () => ({
  useParams: vi.fn(),
  usePathname: vi.fn(),
}));

vi.mock("../../hooks/use-offer", () => ({
  useOffer: vi.fn().mockReturnValue({ offer: null }),
}));

vi.mock("../../hooks/use-sections-for-archetype", () => ({
  useSectionsForArchetype: vi.fn().mockReturnValue([]),
}));

const mockSectionStatus = vi.fn(() => ({}) as Record<string, SectionStatusEntry>);

vi.mock("@/features/copilot/hooks/use-section-status", () => ({
  useSectionStatus: (_module: string) => mockSectionStatus(),
}));

// ── Lazy import after mocks are registered ────────────────────────────────────

const { useParams, usePathname } = await import("next/navigation");
const { OfferStudioNavRail, extractActiveSectionSlug } = await import("../OfferStudioNavRail");

// ── Helpers ───────────────────────────────────────────────────────────────────

function setOfferRoute(path: string, tenantId = "t-demo", offerId = "offer-1") {
  vi.mocked(useParams).mockReturnValue({ tenantId, id: offerId } as never);
  vi.mocked(usePathname).mockReturnValue(path);
}

// ── Unit tests for extractActiveSectionSlug (pre-existing) ────────────────────

describe("OfferStudioNavRail · extractActiveSectionSlug", () => {
  const offerId = "o-1";

  it("returns null when the path does not contain the offer id", () => {
    expect(extractActiveSectionSlug("/t-1/offer-studio", offerId)).toBeNull();
    expect(
      extractActiveSectionSlug("/t-1/offer-studio/offer/different-id/editor", offerId),
    ).toBeNull();
  });

  it("returns null when the path ends at /offer/{id}", () => {
    expect(extractActiveSectionSlug("/t-1/offer-studio/offer/o-1", offerId)).toBeNull();
  });

  it("extracts the section slug from the target URL /offer/{id}/editor/{section}", () => {
    expect(extractActiveSectionSlug("/t-1/offer-studio/offer/o-1/editor/promise", offerId)).toBe(
      "promise",
    );
  });

  it("extracts the section slug from the target URL /offer/{id}/editor/{section}/{fieldId}", () => {
    expect(
      extractActiveSectionSlug("/t-1/offer-studio/offer/o-1/editor/pricing/currency", offerId),
    ).toBe("pricing");
  });

  it("extracts the section slug from the legacy URL /offer/{id}/edition/{code}/{section}", () => {
    expect(
      extractActiveSectionSlug("/t-1/offer-studio/offer/o-1/edition/default/promise", offerId),
    ).toBe("promise");
  });

  it("extracts the section slug from the legacy URL with a field id", () => {
    expect(
      extractActiveSectionSlug(
        "/t-1/offer-studio/offer/o-1/edition/default/pricing/currency",
        offerId,
      ),
    ).toBe("pricing");
  });

  it("returns null for editor root (no section selected yet)", () => {
    expect(extractActiveSectionSlug("/t-1/offer-studio/offer/o-1/editor", offerId)).toBeNull();
  });

  it("returns null for sibling tabs that are not editor/edition", () => {
    expect(extractActiveSectionSlug("/t-1/offer-studio/offer/o-1/assets", offerId)).toBeNull();
    expect(extractActiveSectionSlug("/t-1/offer-studio/offer/o-1/editions", offerId)).toBeNull();
  });
});

// ── Component tests with badge status ─────────────────────────────────────────

describe("OfferStudioNavRail · section badges", () => {
  beforeEach(() => {
    mockSectionStatus.mockReturnValue({});
  });

  it("idle state — no badges rendered", () => {
    setOfferRoute("/t-demo/offer-studio/offer/offer-1/editor/promise");
    render(<OfferStudioNavRail />);
    expect(screen.queryByText(/entrando/)).toBeNull();
    expect(screen.queryByText(/sugeridos/)).toBeNull();
    expect(screen.queryAllByLabelText("En cola")).toHaveLength(0);
  });

  it("running state — promise row shows spinner and '3 entrando'", () => {
    setOfferRoute("/t-demo/offer-studio/offer/offer-1/editor/promise");
    mockSectionStatus.mockReturnValue({
      promise: { status: "running", fieldCount: 3, fieldIds: ["headline", "subheadline", "cta"] },
    });
    render(<OfferStudioNavRail />);
    expect(screen.getByText("3 entrando")).toBeTruthy();
    const spinners = document.querySelectorAll(".animate-spin");
    expect(spinners.length).toBeGreaterThanOrEqual(1);
  });

  it("completed state — promise row shows check and '4 sugeridos'", () => {
    setOfferRoute("/t-demo/offer-studio/offer/offer-1/editor/promise");
    mockSectionStatus.mockReturnValue({
      promise: {
        status: "completed",
        fieldCount: 4,
        fieldIds: ["headline", "subheadline", "cta", "offer_name"],
      },
    });
    render(<OfferStudioNavRail />);
    expect(screen.getByText("4 sugeridos")).toBeTruthy();
  });
});
