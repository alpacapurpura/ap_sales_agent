import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

// Mock useCopilotNavigator
vi.mock("@/features/copilot/hooks/use-copilot-navigator", () => ({
  useCopilotNavigator: () => ({ navigate: vi.fn() }),
}));

// Mock useRouter (Next.js)
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

// Fase 03 · Block B — ExtractionSummaryCard now consumes the BE section
// catalog via ``useSectionLabelResolver`` (React Query). Tests stub it
// with a plain identity resolver so they remain decoupled from the
// catalog endpoint.
vi.mock("@/features/offer-studio/hooks/use-section-catalog", () => ({
  useSectionLabelResolver: () => (slug: string) => slug,
}));

// Fase 03 · Block D — same pattern for the brand catalog hook.
vi.mock("@/features/brand-studio/hooks/use-brand-section-catalog", () => ({
  useBrandSectionLabelResolver: () => (slug: string) => slug,
}));

import { ExtractionSummaryCard } from "../ExtractionSummaryCard";

import type { ExtractionSummaryData } from "../../../types/message-blocks";

function makeData(overrides: Partial<ExtractionSummaryData> = {}): ExtractionSummaryData {
  return {
    source_kind: "url",
    source_ref: "https://visionarias.pe",
    duration_seconds: 38,
    total_fields: 27,
    total_sections: 6,
    coverage_by_section: [
      { slug: "identity", label: "Identidad", filled: 14, total: 18 },
      { slug: "strategy", label: "Estrategia", filled: 8, total: 15 },
      { slug: "audience", label: "Público", filled: 3, total: 12 },
    ],
    strong_assumptions_count: 4,
    open_questions_count: 6,
    primary_cta_route: "/brand-studio/identity",
    ...overrides,
  };
}

describe("ExtractionSummaryCard", () => {
  it("renders total_fields stat box", () => {
    render(<ExtractionSummaryCard data={makeData()} />);
    expect(screen.getByText("27")).toBeInTheDocument();
    expect(screen.getByText(/campos/i)).toBeInTheDocument();
  });

  it("renders total_sections stat box", () => {
    render(<ExtractionSummaryCard data={makeData()} />);
    // "6" may appear as total_sections stat and in the "Ver preguntas (6)" button; use getAllByText
    expect(screen.getAllByText("6").length).toBeGreaterThan(0);
    expect(screen.getByText(/secciones/i)).toBeInTheDocument();
  });

  it("renders coverage section labels", () => {
    render(<ExtractionSummaryCard data={makeData()} />);
    expect(screen.getByText("Identidad")).toBeInTheDocument();
    expect(screen.getByText("Estrategia")).toBeInTheDocument();
    expect(screen.getByText("Público")).toBeInTheDocument();
  });

  it("applies success color class when coverage >= 70%", () => {
    // identity: 14/18 = 77.7% → bg-success
    const { container } = render(<ExtractionSummaryCard data={makeData()} />);
    const bars = container.querySelectorAll("[data-testid='coverage-bar-fill']");
    expect(bars[0].className).toContain("bg-success");
  });

  it("applies warning color class when coverage >= 40% and < 70%", () => {
    // strategy: 8/15 = 53.3% → bg-warning
    const { container } = render(<ExtractionSummaryCard data={makeData()} />);
    const bars = container.querySelectorAll("[data-testid='coverage-bar-fill']");
    expect(bars[1].className).toContain("bg-warning");
  });

  it("applies destructive color class when coverage < 40%", () => {
    // audience: 3/12 = 25% → bg-destructive
    const { container } = render(<ExtractionSummaryCard data={makeData()} />);
    const bars = container.querySelectorAll("[data-testid='coverage-bar-fill']");
    expect(bars[2].className).toContain("bg-destructive");
  });

  it("renders source_ref in header", () => {
    render(<ExtractionSummaryCard data={makeData()} />);
    expect(screen.getByText(/visionarias\.pe/i)).toBeInTheDocument();
  });

  it("renders duration_seconds", () => {
    render(<ExtractionSummaryCard data={makeData()} />);
    expect(screen.getByText(/38s/)).toBeInTheDocument();
  });

  it("renders open_questions_count CTA", () => {
    render(<ExtractionSummaryCard data={makeData()} />);
    // The "Ver preguntas (6)" button contains both text fragments
    expect(screen.getByRole("button", { name: /preguntas.*6|6.*preguntas/i })).toBeInTheDocument();
  });

  it("renders strong_assumptions_count", () => {
    render(<ExtractionSummaryCard data={makeData()} />);
    // "Supuestos: 4" appears in the body; "Ver supuestos" also renders as a CTA
    expect(screen.getAllByText(/supuestos/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("renders primary CTA button for review", () => {
    render(<ExtractionSummaryCard data={makeData()} />);
    expect(screen.getByRole("button", { name: /revisar/i })).toBeInTheDocument();
  });

  it("primary CTA is clickable without throwing", () => {
    const { getByRole } = render(<ExtractionSummaryCard data={makeData()} />);
    expect(() => fireEvent.click(getByRole("button", { name: /revisar/i }))).not.toThrow();
  });

  it("has accessible group role", () => {
    render(<ExtractionSummaryCard data={makeData()} />);
    expect(screen.getByRole("group")).toBeInTheDocument();
  });

  it("renders with doc source_kind label", () => {
    render(
      <ExtractionSummaryCard data={makeData({ source_kind: "doc", source_ref: "doc-123" })} />,
    );
    expect(screen.getByText(/doc-123/i)).toBeInTheDocument();
  });
});
