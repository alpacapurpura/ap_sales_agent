import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, it, expect } from "vitest";

import { ScoreRing } from "../ScoreRing";

describe("ScoreRing", () => {
  it("renders the score as text", () => {
    render(<ScoreRing score={75} />);
    expect(screen.getByText("75")).toBeInTheDocument();
  });

  it("renders gray color class for score 0", () => {
    const { container } = render(<ScoreRing score={0} />);
    const progressCircle = container.querySelector("circle.transition-all");
    expect(progressCircle?.className).toContain("text-gray-400");
  });

  it("renders red color class for score between 1 and 49", () => {
    const { container } = render(<ScoreRing score={30} />);
    const progressCircle = container.querySelector("circle.transition-all");
    expect(progressCircle?.className).toContain("text-red-500");
  });

  it("renders yellow color class for score between 50 and 79", () => {
    const { container } = render(<ScoreRing score={50} />);
    const progressCircle = container.querySelector("circle.transition-all");
    expect(progressCircle?.className).toContain("text-yellow-500");
  });

  it("renders green color class for score 80 and above", () => {
    const { container } = render(<ScoreRing score={80} />);
    const progressCircle = container.querySelector("circle.transition-all");
    expect(progressCircle?.className).toContain("text-green-500");
  });

  it("renders green color class for score 100", () => {
    const { container } = render(<ScoreRing score={100} />);
    const progressCircle = container.querySelector("circle.transition-all");
    expect(progressCircle?.className).toContain("text-green-500");
    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("renders an SVG with correct dimensions", () => {
    const { container } = render(<ScoreRing score={60} size={48} />);
    const svg = container.querySelector("svg");
    expect(svg).toBeDefined();
    expect(svg?.getAttribute("width")).toBe("48");
    expect(svg?.getAttribute("height")).toBe("48");
  });

  it("applies custom className to the wrapper", () => {
    const { container } = render(<ScoreRing score={50} className="my-custom-class" />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain("my-custom-class");
  });

  it("clamps negative scores to gray (score=0 behavior)", () => {
    const { container } = render(<ScoreRing score={-10} />);
    const progressCircle = container.querySelector("circle.transition-all");
    // score < 0 → colorClass = text-gray-400 (score is not > 0)
    expect(progressCircle?.className).toContain("text-gray-400");
  });
});
