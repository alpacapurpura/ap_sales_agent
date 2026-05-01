import { render, screen } from "@testing-library/react";
import * as React from "react";
import { describe, it, expect } from "vitest";

import { LifecycleStageChip } from "../LifecycleStageChip";

import type { LifecycleStage } from "../../types";

const STAGES: { stage: LifecycleStage; label: string }[] = [
  { stage: "subscriber", label: "Suscriptor" },
  { stage: "lead", label: "Lead" },
  { stage: "mql", label: "MQL" },
  { stage: "sql", label: "SQL" },
  { stage: "opportunity", label: "Oportunidad" },
  { stage: "customer", label: "Cliente" },
  { stage: "evangelist", label: "Evangelista" },
  { stage: "churned", label: "Churn" },
];

describe("LifecycleStageChip", () => {
  STAGES.forEach(({ stage, label }) => {
    it(`renders label "${label}" for stage "${stage}"`, () => {
      render(<LifecycleStageChip stage={stage} />);
      expect(screen.getByText(label)).toBeInTheDocument();
    });
  });

  it("accepts additional className", () => {
    const { container } = render(<LifecycleStageChip stage="lead" className="custom-class" />);
    expect(container.firstChild).toHaveClass("custom-class");
  });
});
