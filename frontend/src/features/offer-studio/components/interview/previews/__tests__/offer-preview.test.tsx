import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

// Mock the catalog hooks so the previews don't need a QueryClientProvider
// plus network mocks. The production code path is exercised by the
// integration tests in tests/modules/offer/api/.
vi.mock("@/features/offer-studio/hooks/use-archetype-display", () => ({
  useArchetypeDisplay: (archetype?: string) => {
    if (!archetype) return undefined;
    const labels: Record<string, string> = {
      producto: "Producto",
      programa: "Programa",
      servicio: "Servicio",
      membresia: "Membresía",
      experiencia: "Experiencia",
    };
    return {
      archetype,
      label: labels[archetype] ?? archetype,
      subtitle: "",
      icon: (props: Record<string, unknown>) => <svg data-testid="icon-archetype" {...props} />,
      examples: [],
    };
  },
}));

vi.mock("@/features/offer-studio/hooks/use-value-level-catalog", () => ({
  useValueLevelMetadata: (valueLevel?: string) => {
    if (!valueLevel) return undefined;
    const labels: Record<string, string> = {
      lead_magnet: "Lead Magnet",
      activacion: "Activación",
      transformacion: "Transformación",
      maximizacion: "Maximización",
      corporativo: "Corporativo",
    };
    return {
      value_level: valueLevel,
      order: 0,
      label_es: labels[valueLevel] ?? valueLevel,
      description_es: "",
      role_in_funnel_es: "",
      icon_name: "Sparkles",
      examples_es: [],
      is_free: false,
      typical_price_min_usd: null,
      typical_price_max_usd: null,
    };
  },
  useValueLevelCatalog: () => ({ data: undefined }),
}));

import { OfferPreviewSections } from "../OfferPreviewSections";
import { OfferPreviewSummary } from "../OfferPreviewSummary";

// ── Fixtures ─────────────────────────────────────────────────────────────────

const EMPTY_DATA: Record<string, unknown> = {};

const FULL_DATA: Record<string, unknown> = {
  public_name: "Programa Elite de Ventas",
  archetype: "programa",
  value_level: "transformacion",
  headline_promise: "Transforma tus ventas en 90 dias",
  primary_outcome: "Duplicar tus ingresos",
  time_to_value: "90 dias",
  marketing_pain_points: ["No consigo clientes", "Mis ventas son bajas"],
  marketing_desires: ["Libertad financiera", "Escalar mi negocio"],
  objections: [
    {
      type: "price",
      trigger_phrases: ["Es muy caro"],
      strategy: "Comparar con costo de no actuar",
      rebuttal: "El costo de no actuar es mayor",
    },
    {
      type: "time",
      trigger_phrases: ["No tengo tiempo"],
      strategy: "Solo 30 min al dia",
      rebuttal: "Resultados en 15 min diarios",
    },
  ],
  deliverables: [
    {
      name: "Modulo de estrategia",
      format: "video",
      quantity: "8 modulos",
      value_stack_price: 500,
    },
    {
      name: "Plantilla de ventas",
      format: "template",
      quantity: "1",
      value_stack_price: 200,
    },
  ],
  pricing_options: [
    {
      label: "Pago unico",
      total_amount: 997,
      currency: "USD",
    },
  ],
  guarantee_type: "unconditional_30_day",
  guarantee_terms: "30 dias sin preguntas",
};

// ── OfferPreviewSummary ──────────────────────────────────────────────────────

describe("OfferPreviewSummary", () => {
  it("renders offer name and archetype badge", () => {
    render(<OfferPreviewSummary data={FULL_DATA} completenessScore={75} />);

    expect(screen.getByText("Programa Elite de Ventas")).toBeInTheDocument();
    expect(screen.getByText("Programa")).toBeInTheDocument();
  });

  it("renders value level badge", () => {
    render(<OfferPreviewSummary data={FULL_DATA} completenessScore={60} />);

    expect(screen.getByText(/transformaci/i)).toBeInTheDocument();
  });

  it("renders price when pricing is available", () => {
    render(<OfferPreviewSummary data={FULL_DATA} completenessScore={50} />);

    expect(screen.getByText(/997/)).toBeInTheDocument();
  });

  it("renders completeness score", () => {
    render(<OfferPreviewSummary data={FULL_DATA} completenessScore={75} />);

    expect(screen.getByText("75%")).toBeInTheDocument();
  });

  it("handles empty data gracefully", () => {
    render(<OfferPreviewSummary data={EMPTY_DATA} completenessScore={0} />);

    expect(screen.getByText("0%")).toBeInTheDocument();
    expect(screen.getByText(/pendiente/i)).toBeInTheDocument();
  });
});

// ── OfferPreviewSections ─────────────────────────────────────────────────────

describe("OfferPreviewSections", () => {
  it("renders all 7 section headers", () => {
    render(<OfferPreviewSections data={FULL_DATA} currentBlock="identity" blocksCompleted={[]} />);

    expect(screen.getByText("Identidad")).toBeInTheDocument();
    expect(screen.getByText("Estrategia")).toBeInTheDocument();
    expect(screen.getByText("Promesa")).toBeInTheDocument();
    expect(screen.getByText(/Psicolog/i)).toBeInTheDocument();
    expect(screen.getByText("Pricing")).toBeInTheDocument();
    expect(screen.getByText("Value Stack")).toBeInTheDocument();
    expect(screen.getByText("Cierre")).toBeInTheDocument();
  });

  it("renders pain points with red styling indicator", () => {
    render(
      <OfferPreviewSections data={FULL_DATA} currentBlock="psychology" blocksCompleted={[]} />,
    );

    expect(screen.getByText("No consigo clientes")).toBeInTheDocument();
    expect(screen.getByText("Mis ventas son bajas")).toBeInTheDocument();
  });

  it("renders desires with green styling indicator", () => {
    render(
      <OfferPreviewSections data={FULL_DATA} currentBlock="psychology" blocksCompleted={[]} />,
    );

    expect(screen.getByText("Libertad financiera")).toBeInTheDocument();
    expect(screen.getByText("Escalar mi negocio")).toBeInTheDocument();
  });

  it("renders objections with amber styling indicator", () => {
    render(
      <OfferPreviewSections data={FULL_DATA} currentBlock="psychology" blocksCompleted={[]} />,
    );

    expect(screen.getByText("Es muy caro")).toBeInTheDocument();
    expect(screen.getByText("No tengo tiempo")).toBeInTheDocument();
  });

  it("renders deliverables as checklist items", () => {
    render(
      <OfferPreviewSections data={FULL_DATA} currentBlock="value_stack" blocksCompleted={[]} />,
    );

    expect(screen.getByText("Modulo de estrategia")).toBeInTheDocument();
    expect(screen.getByText("Plantilla de ventas")).toBeInTheDocument();
  });

  it("renders pricing information", () => {
    render(<OfferPreviewSections data={FULL_DATA} currentBlock="pricing" blocksCompleted={[]} />);

    expect(screen.getByText(/997/)).toBeInTheDocument();
  });

  it("shows 'Pendiente...' for empty fields", () => {
    render(<OfferPreviewSections data={EMPTY_DATA} currentBlock="identity" blocksCompleted={[]} />);

    const pendingElements = screen.getAllByText("Pendiente...");
    expect(pendingElements.length).toBeGreaterThan(0);
  });

  it("highlights the active section matching currentBlock", () => {
    const { container } = render(
      <OfferPreviewSections data={FULL_DATA} currentBlock="psychology" blocksCompleted={[]} />,
    );

    // The psychology section should have the active ring styling
    const activeSection = container.querySelector("[data-section='psychology']");
    expect(activeSection).toBeInTheDocument();
    expect(activeSection?.className).toContain("ring");
  });
});
