import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BenchmarkBadge } from "../BenchmarkBadge";
import type { BenchmarkRange } from "../../../../types/metrics";

const BENCHMARK: BenchmarkRange = {
  low: 0.9,
  median: 1.5,
  high: 2.19,
  unit: "percentage",
  interpretation: "CTR mide la efectividad de tus anuncios",
};

describe("BenchmarkBadge", () => {
  it('shows "mejor que promedio" for value above high (higher is better)', () => {
    render(<BenchmarkBadge value={3.0} benchmark={BENCHMARK} higherIsBetter={true} />);
    expect(screen.getByText(/mejor que promedio/)).toBeInTheDocument();
  });

  it('shows "En promedio" for value between low and high', () => {
    render(<BenchmarkBadge value={1.5} benchmark={BENCHMARK} higherIsBetter={true} />);
    expect(screen.getByText("En promedio")).toBeInTheDocument();
  });

  it('shows "bajo promedio" for value below low (higher is better)', () => {
    render(<BenchmarkBadge value={0.5} benchmark={BENCHMARK} higherIsBetter={true} />);
    expect(screen.getByText(/bajo promedio/)).toBeInTheDocument();
  });

  it("inverts logic when higherIsBetter is false (lower is better)", () => {
    // For CPC: value below low is "good"
    render(<BenchmarkBadge value={0.5} benchmark={BENCHMARK} higherIsBetter={false} />);
    expect(screen.getByText(/mejor que promedio/)).toBeInTheDocument();
  });

  it('shows "sobre promedio" for high value when lower is better', () => {
    render(<BenchmarkBadge value={3.0} benchmark={BENCHMARK} higherIsBetter={false} />);
    expect(screen.getByText(/sobre promedio/)).toBeInTheDocument();
  });

  it("includes interpretation as title attribute", () => {
    const { container } = render(
      <BenchmarkBadge value={1.5} benchmark={BENCHMARK} higherIsBetter={true} />,
    );
    const badge = container.querySelector("span");
    expect(badge?.getAttribute("title")).toBe("CTR mide la efectividad de tus anuncios");
  });

  it('computes correct percentage for "good" status (higher is better)', () => {
    // value=3.0, median=1.5 -> pct = round((3.0-1.5)/1.5*100) = 100
    render(<BenchmarkBadge value={3.0} benchmark={BENCHMARK} higherIsBetter={true} />);
    expect(screen.getByText("100% mejor que promedio")).toBeInTheDocument();
  });

  it('computes correct percentage for "poor" status (higher is better)', () => {
    // value=0.5, median=1.5 -> pct = round((1.5-0.5)/1.5*100) = 67
    render(<BenchmarkBadge value={0.5} benchmark={BENCHMARK} higherIsBetter={true} />);
    expect(screen.getByText("67% bajo promedio")).toBeInTheDocument();
  });

  it('applies green styling for "good" status', () => {
    const { container } = render(
      <BenchmarkBadge value={3.0} benchmark={BENCHMARK} higherIsBetter={true} />,
    );
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("text-emerald");
  });

  it('applies amber styling for "average" status', () => {
    const { container } = render(
      <BenchmarkBadge value={1.5} benchmark={BENCHMARK} higherIsBetter={true} />,
    );
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("text-amber");
  });

  it('applies red styling for "poor" status', () => {
    const { container } = render(
      <BenchmarkBadge value={0.5} benchmark={BENCHMARK} higherIsBetter={true} />,
    );
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("text-red");
  });
});
