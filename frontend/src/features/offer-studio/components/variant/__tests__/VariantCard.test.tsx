import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EditionStatus, EditionVisibility } from "../../../types";
import { VariantCard } from "../VariantCard";

import type { LaunchEdition, PricingStructure } from "../../../types";

function buildVariant(partial: Partial<LaunchEdition> = {}): LaunchEdition {
  return {
    id: "variant-1",
    offer_id: "offer-1",
    edition_name: "Test",
    edition_number: 1,
    variant_structure: "temporal_cohort",
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
    status: EditionStatus.DRAFT,
    visibility: EditionVisibility.PRIVATE,
    is_placeholder: false,
    location_override: null,
    notes: null,
    cloned_from_edition_id: null,
    created_at: null,
    updated_at: null,
    ...partial,
  };
}

describe("VariantCard polymorphic dispatch", () => {
  const noop = vi.fn();

  it("renders the tier template for TIER variants", () => {
    const variant = buildVariant({
      edition_name: "Plan Platinum",
      variant_structure: "tier",
      structure_data: {
        features: ["10 sesiones", "WhatsApp directo", "Labs incluidos"],
        price_amount: 1497,
        price_currency: "USD",
      },
    });
    render(
      <VariantCard variant={variant} onEdit={noop} onDuplicate={noop} onDelete={noop} />,
    );
    expect(screen.getByText("Plan Platinum")).toBeInTheDocument();
    expect(screen.getByText("10 sesiones")).toBeInTheDocument();
    expect(screen.getByText("WhatsApp directo")).toBeInTheDocument();
    // price rendered
    expect(screen.getByText(/1,?497/u)).toBeInTheDocument();
  });

  it("renders the SKU template for SKU_VARIANT variants", () => {
    const variant = buildVariant({
      edition_name: "Talla M · Negro",
      variant_structure: "sku_variant",
      structure_data: {
        sku_code: "TSHIRT-M-BLACK",
        attributes: { talla: "M", color: "negro" },
      },
      capacity: 42,
    });
    render(
      <VariantCard variant={variant} onEdit={noop} onDuplicate={noop} onDelete={noop} />,
    );
    expect(screen.getByText(/TSHIRT-M-BLACK/)).toBeInTheDocument();
    expect(screen.getByText(/talla: M/)).toBeInTheDocument();
    expect(screen.getByText(/color: negro/)).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("renders the regional template with country chips + currency", () => {
    const variant = buildVariant({
      edition_name: "LATAM Andina",
      variant_structure: "regional",
      structure_data: { country_codes: ["pe", "co", "ec"], currency: "USD" },
    });
    render(
      <VariantCard variant={variant} onEdit={noop} onDuplicate={noop} onDelete={noop} />,
    );
    expect(screen.getByText("PE")).toBeInTheDocument();
    expect(screen.getByText("CO")).toBeInTheDocument();
    expect(screen.getByText("EC")).toBeInTheDocument();
    expect(screen.getByText(/USD/)).toBeInTheDocument();
  });

  it("renders the modality template with mode pill", () => {
    const variant = buildVariant({
      edition_name: "Presencial",
      variant_structure: "modality",
      structure_data: { mode: "presencial" },
    });
    render(
      <VariantCard variant={variant} onEdit={noop} onDuplicate={noop} onDelete={noop} />,
    );
    expect(screen.getByText("presencial")).toBeInTheDocument();
  });

  it("renders the language template with locale pill", () => {
    const variant = buildVariant({
      edition_name: "Español LATAM",
      variant_structure: "language",
      structure_data: { locale: "es-419" },
    });
    render(
      <VariantCard variant={variant} onEdit={noop} onDuplicate={noop} onDelete={noop} />,
    );
    expect(screen.getByText(/ES-419/i)).toBeInTheDocument();
  });

  it("falls back to TemporalVariantCard (EditionCard) for temporal structures", () => {
    const variant = buildVariant({
      edition_name: "Cohorte Q2-2026",
      variant_structure: "temporal_cohort",
      start_date: "2026-05-06T00:00:00Z",
      capacity: 40,
    });
    render(
      <VariantCard variant={variant} onEdit={noop} onDuplicate={noop} onDelete={noop} />,
    );
    expect(screen.getByText("Cohorte Q2-2026")).toBeInTheDocument();
  });

  it("renders price override when structure_data lacks price fields (TIER)", () => {
    const override: PricingStructure = { label: "Gold", total_amount: 997, currency: "USD" };
    const variant = buildVariant({
      edition_name: "Plan Gold",
      variant_structure: "tier",
      structure_data: {}, // no price_amount / features
      pricing_override: [override],
    });
    render(
      <VariantCard variant={variant} onEdit={noop} onDuplicate={noop} onDelete={noop} />,
    );
    expect(screen.getByText("Plan Gold")).toBeInTheDocument();
    expect(screen.getByText(/997/)).toBeInTheDocument();
  });
});
