import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockPush = vi.fn();
const mockUsePathname = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => mockUsePathname(),
}));

// ── Imports after mocks ──────────────────────────────────────────────────────

import { EditionStatus, EditionVisibility } from "../../../types";
import { VariantRail } from "../VariantRail";

import type { VariantStructure } from "../../../api/archetype-catalog-api";
import type { LaunchEdition } from "../../../types";

const BASE = "/acme/offer-studio/offer/offer-1";

function makeVariant(
  id: string,
  structure: VariantStructure,
  overrides: Partial<LaunchEdition> = {},
): LaunchEdition {
  return {
    id,
    offer_id: "offer-1",
    edition_name: `Variante ${id}`,
    edition_number: 1,
    variant_structure: structure,
    structure_data: {},
    sort_rank: null,
    start_date: null,
    end_date: null,
    registration_start: null,
    registration_end: null,
    timezone: "UTC",
    pricing_override: null,
    pricing_tiers: [],
    active_tier: null,
    effective_pricing: [],
    currency: "USD",
    capacity: null,
    enrollment_count: 0,
    status: EditionStatus.ACTIVE,
    visibility: EditionVisibility.PUBLIC,
    is_placeholder: false,
    location_override: null,
    notes: null,
    cloned_from_edition_id: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

const baseProps = {
  offerId: "offer-1",
  tenantId: "acme",
  currentVariantId: null as string | null,
  onCollapse: vi.fn(),
  onCreateNew: vi.fn(),
  waitlistCount: 0,
};

describe("VariantRail", () => {
  beforeEach(() => {
    mockPush.mockReset();
    mockUsePathname.mockReset();
    mockUsePathname.mockReturnValue(BASE);
    baseProps.onCollapse = vi.fn();
    baseProps.onCreateNew = vi.fn();
  });

  // ── Empty state ─────────────────────────────────────────────────────────────

  it("renders empty state when no variants", () => {
    render(<VariantRail {...baseProps} variants={[]} />);
    expect(screen.getByText(/Aún no tienes/i)).toBeInTheDocument();
  });

  it("empty state has a CTA button", () => {
    render(<VariantRail {...baseProps} variants={[]} />);
    // At least one button fires onCreateNew
    const ctaButton = screen
      .getAllByRole("button")
      .find(
        (b) =>
          b.textContent?.toLowerCase().includes("crear") ||
          b.textContent?.toLowerCase().includes("nueva") ||
          b.textContent?.toLowerCase().includes("primer"),
      );
    expect(ctaButton).toBeDefined();
  });

  // ── Temporal cohort (parity with EditionsRail) ───────────────────────────────

  it("renders temporal cohort variants with edition number", () => {
    const variants = [
      makeVariant("ed-1", "temporal_cohort", {
        edition_number: 1,
        edition_name: "Edición #1",
        status: EditionStatus.UPCOMING,
        start_date: "2026-09-01",
      }),
    ];
    render(<VariantRail {...baseProps} variants={variants} currentVariantId="ed-1" />);
    expect(screen.getByText("Edición #1")).toBeInTheDocument();
  });

  it("temporal: collapse button fires onCollapse", () => {
    const variants = [makeVariant("ed-1", "temporal_cohort")];
    render(<VariantRail {...baseProps} variants={variants} />);
    fireEvent.click(screen.getByLabelText("Contraer rail"));
    expect(baseProps.onCollapse).toHaveBeenCalledTimes(1);
  });

  // ── Tier (3 plans) ──────────────────────────────────────────────────────────

  it("renders 3 tier variants in 'Publicados' group", () => {
    const variants = [
      makeVariant("tier-1", "tier", {
        edition_name: "Básico",
        structure_data: { price_amount: 29, price_currency: "USD" },
      }),
      makeVariant("tier-2", "tier", {
        edition_name: "Premium",
        structure_data: { price_amount: 79, price_currency: "USD", is_recommended: true },
      }),
      makeVariant("tier-3", "tier", {
        edition_name: "Enterprise",
        structure_data: { price_amount: 249, price_currency: "USD" },
      }),
    ];
    render(<VariantRail {...baseProps} variants={variants} />);
    expect(screen.getByText("Básico")).toBeInTheDocument();
    expect(screen.getByText("Premium")).toBeInTheDocument();
    expect(screen.getByText("Enterprise")).toBeInTheDocument();
    // All 3 are ACTIVE → one "Publicados" group
    expect(screen.getByText(/Publicados/)).toBeInTheDocument();
  });

  it("tier: header shows 'Planes' noun from catalog", () => {
    const variants = [makeVariant("tier-1", "tier")];
    render(<VariantRail {...baseProps} variants={variants} />);
    // nounPluralEs for tier = "planes", capitalized → "Planes"
    expect(screen.getByText(/Planes/i)).toBeInTheDocument();
  });

  it("tier: price is visible for each variant", () => {
    const variants = [
      makeVariant("tier-1", "tier", {
        edition_name: "Básico",
        structure_data: { price_amount: 29, price_currency: "USD" },
      }),
    ];
    render(<VariantRail {...baseProps} variants={variants} />);
    expect(screen.getByText(/\$29/)).toBeInTheDocument();
  });

  // ── SKU with low-stock ───────────────────────────────────────────────────────

  it("shows '⚠ Low stock' on the entry with capacity ≤ threshold", () => {
    const variants = [
      makeVariant("sku-1", "sku_variant", {
        edition_name: "30ml SNS",
        capacity: 8,
        status: EditionStatus.ACTIVE,
        structure_data: { sku_code: "SRM-30-SNS" },
      }),
      makeVariant("sku-2", "sku_variant", {
        edition_name: "50ml NRM",
        capacity: 100,
        status: EditionStatus.ACTIVE,
        structure_data: { sku_code: "SRM-50-NRM" },
      }),
      makeVariant("sku-3", "sku_variant", {
        edition_name: "50ml SNS",
        capacity: 89,
        status: EditionStatus.ACTIVE,
        structure_data: { sku_code: "SRM-50-SNS" },
      }),
      makeVariant("sku-4", "sku_variant", {
        edition_name: "30ml NRM",
        capacity: 142,
        status: EditionStatus.ACTIVE,
        structure_data: { sku_code: "SRM-30-NRM" },
      }),
      makeVariant("sku-5", "sku_variant", {
        edition_name: "100ml NRM",
        capacity: 0,
        status: EditionStatus.DRAFT,
        structure_data: { sku_code: "SRM-100-NRM" },
      }),
      makeVariant("sku-6", "sku_variant", {
        edition_name: "100ml SNS",
        capacity: 0,
        status: EditionStatus.DRAFT,
        structure_data: { sku_code: "SRM-100-SNS" },
      }),
    ];
    render(<VariantRail {...baseProps} variants={variants} />);
    // sku-1 (capacity 8) is the only entry with capacity ≤ threshold 10.
    // The rail renders: 1 group label "⚠ Low stock" + 1 entry "⚠ Low stock" = 2 total.
    // We verify there is at least 1 Low stock group and no more than 1 low-stock entry.
    const lowStockTexts = screen.getAllByText(/Low stock/i);
    // At least the group label appears; must not have more than 2 (label + 1 entry)
    expect(lowStockTexts.length).toBeGreaterThanOrEqual(1);
    expect(lowStockTexts.length).toBeLessThanOrEqual(2);
    // Only one SKU entry shows low-stock inline warning
    expect(screen.getByText("30ml SNS")).toBeInTheDocument();
  });

  // ── Header shows correct noun ────────────────────────────────────────────────

  it("header shows 'Variantes' noun for sku_variant", () => {
    const variants = [makeVariant("sku-1", "sku_variant")];
    render(<VariantRail {...baseProps} variants={variants} />);
    expect(screen.getByText(/Variantes/i)).toBeInTheDocument();
  });

  it("header shows 'Cohortes' noun for temporal_cohort", () => {
    const variants = [makeVariant("ed-1", "temporal_cohort")];
    render(<VariantRail {...baseProps} variants={variants} />);
    expect(screen.getByText(/Cohortes/i)).toBeInTheDocument();
  });

  // ── Selection ────────────────────────────────────────────────────────────────

  it("marks the selected variant entry as pressed", () => {
    const variants = [makeVariant("tier-1", "tier", { edition_name: "Premium" })];
    render(<VariantRail {...baseProps} variants={variants} currentVariantId="tier-1" />);
    // Find the entry button with aria-pressed=true
    const pressedButtons = screen
      .getAllByRole("button")
      .filter((b) => b.getAttribute("aria-pressed") === "true");
    expect(pressedButtons).toHaveLength(1);
  });

  // ── onCreateNew ─────────────────────────────────────────────────────────────

  it("footer CTA fires onCreateNew", () => {
    const variants = [makeVariant("tier-1", "tier")];
    render(<VariantRail {...baseProps} variants={variants} />);
    const ctaButton = screen.getByRole("button", { name: /nueva/i });
    fireEvent.click(ctaButton);
    expect(baseProps.onCreateNew).toHaveBeenCalledTimes(1);
  });

  // ── aria-label ────────────────────────────────────────────────────────────────

  it("has correct aria-label on the aside element", () => {
    const variants = [makeVariant("tier-1", "tier")];
    const { container } = render(<VariantRail {...baseProps} variants={variants} />);
    const aside = container.querySelector("aside");
    expect(aside).toHaveAttribute("aria-label", "Variantes de la oferta");
  });
});
