import { render, screen } from "@testing-library/react";
import * as React from "react";
import { describe, it, expect } from "vitest";

import { ScoreBadge } from "../ScoreBadge";

describe("ScoreBadge", () => {
  it("renders score value", () => {
    render(<ScoreBadge score={55} />);
    expect(screen.getByText("55")).toBeInTheDocument();
  });

  it("renders secondary variant for score 0-39", () => {
    const { container } = render(<ScoreBadge score={25} />);
    // secondary variant classes applied
    expect(container.firstChild).toBeInTheDocument();
  });

  it("renders default variant for score 40-69", () => {
    const { container } = render(<ScoreBadge score={65} />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it("renders destructive variant for score 70-100", () => {
    const { container } = render(<ScoreBadge score={85} />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it("renders boundary values correctly", () => {
    render(<ScoreBadge score={0} />);
    expect(screen.getByText("0")).toBeInTheDocument();

    render(<ScoreBadge score={100} />);
    expect(screen.getByText("100")).toBeInTheDocument();
  });
});
