import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MetricInfoPopover } from "../MetricInfoPopover";

describe("MetricInfoPopover", () => {
  it("renders children and info button", () => {
    render(
      <MetricInfoPopover
        displayName="Tasa de Apertura"
        description="Porcentaje de emails abiertos vs enviados"
      >
        <span>Open Rate</span>
      </MetricInfoPopover>,
    );
    expect(screen.getByRole("button", { name: /info/i })).toBeInTheDocument();
    expect(screen.getByText("Open Rate")).toBeInTheDocument();
  });

  it("shows popover content on click", async () => {
    render(
      <MetricInfoPopover
        displayName="Tasa de Apertura"
        description="Porcentaje de emails abiertos vs enviados"
        formula="unique_opens / emails_sent × 100"
        benchmark={{ value: 21.5, source: "Campaign Monitor 2022" }}
      >
        <span>Open Rate</span>
      </MetricInfoPopover>,
    );
    fireEvent.click(screen.getByRole("button", { name: /info/i }));
    expect(await screen.findByText("Tasa de Apertura")).toBeInTheDocument();
    expect(screen.getByText(/unique_opens/)).toBeInTheDocument();
    expect(screen.getByText("21.5")).toBeInTheDocument();
    expect(screen.getByText(/Campaign Monitor 2022/)).toBeInTheDocument();
  });

  it("does not render popover content before click", () => {
    render(
      <MetricInfoPopover displayName="Click Rate" description="Porcentaje de clicks">
        <span>Click Rate</span>
      </MetricInfoPopover>,
    );
    expect(screen.queryByText("Porcentaje de clicks")).not.toBeInTheDocument();
  });

  it("renders interpretation text when provided", async () => {
    render(
      <MetricInfoPopover
        displayName="CTR"
        description="Click-through rate"
        interpretation="Valores altos indican buena relevancia del contenido"
      >
        <span>CTR</span>
      </MetricInfoPopover>,
    );
    fireEvent.click(screen.getByRole("button", { name: /info/i }));
    expect(
      await screen.findByText("Valores altos indican buena relevancia del contenido"),
    ).toBeInTheDocument();
  });

  it("renders benchmark without source when source is omitted", async () => {
    render(
      <MetricInfoPopover
        displayName="CPM"
        description="Costo por mil impresiones"
        benchmark={{ value: 8.5 }}
      >
        <span>CPM</span>
      </MetricInfoPopover>,
    );
    fireEvent.click(screen.getByRole("button", { name: /info/i }));
    expect(await screen.findByText("8.5")).toBeInTheDocument();
    expect(screen.queryByText("(")).not.toBeInTheDocument();
  });

  it("does not render formula section when formula is not provided", async () => {
    render(
      <MetricInfoPopover displayName="Gasto Total" description="Total gastado en publicidad">
        <span>Spend</span>
      </MetricInfoPopover>,
    );
    fireEvent.click(screen.getByRole("button", { name: /info/i }));
    expect(await screen.findByText("Total gastado en publicidad")).toBeInTheDocument();
    const codeElements = document.querySelectorAll("code");
    expect(codeElements.length).toBe(0);
  });

  it("applies custom className to wrapper", () => {
    const { container } = render(
      <MetricInfoPopover displayName="Test" description="Test desc" className="my-custom-class">
        <span>Test</span>
      </MetricInfoPopover>,
    );
    const wrapper = container.firstElementChild;
    expect(wrapper?.classList.contains("my-custom-class")).toBe(true);
  });
});
