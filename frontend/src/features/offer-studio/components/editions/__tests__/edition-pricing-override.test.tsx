import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { EditionPricingOverride } from "../EditionPricingOverride";

import type { PricingStructure } from "../../../types";

const samplePricing: PricingStructure[] = [
  {
    label: "Pago único",
    plan_type: "one_time",
    total_amount: 300,
    is_default: true,
  } as PricingStructure,
];

describe("EditionPricingOverride", () => {
  it("renders without crashing when offerPricing is undefined", () => {
    render(
      <EditionPricingOverride
        offerPricing={undefined as unknown as PricingStructure[]}
        currency="PEN"
        value={null}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText(/Precio especial para esta edición/i)).toBeInTheDocument();
  });

  it("renders empty-state copy when offerPricing is an empty array", () => {
    render(
      <EditionPricingOverride offerPricing={[]} currency="PEN" value={null} onChange={vi.fn()} />,
    );
    expect(screen.getByText(/La oferta aún no tiene precio base configurado/i)).toBeInTheDocument();
  });

  it("renders inherited pricing summary when offerPricing has items and override is off", () => {
    render(
      <EditionPricingOverride
        offerPricing={samplePricing}
        currency="PEN"
        value={null}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText(/Precio heredado de la oferta/i)).toBeInTheDocument();
  });

  it("renders the override editor when value is provided", () => {
    render(
      <EditionPricingOverride
        offerPricing={samplePricing}
        currency="PEN"
        value={samplePricing}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText(/Precio especial activado/i)).toBeInTheDocument();
  });
});
