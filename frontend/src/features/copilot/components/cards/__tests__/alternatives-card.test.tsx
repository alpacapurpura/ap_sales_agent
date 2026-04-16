import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { AlternativesCard } from "../AlternativesCard";

const mockAlternatives = [
  {
    id: "a",
    title: "The Magician",
    description: "Transforms complex",
    recommended: true,
    recommendationReason: "Matches your brand",
  },
  {
    id: "b",
    title: "The Hero",
    description: "Empowers users",
    recommended: false,
  },
  {
    id: "c",
    title: "The Caregiver",
    description: "Protects and guides",
    recommended: false,
  },
];

describe("AlternativesCard", () => {
  it("renders all alternatives", () => {
    render(
      <AlternativesCard
        fieldPath="identity.archetype"
        question="Which archetype fits?"
        alternatives={mockAlternatives}
        allowCustom={true}
        onSelect={vi.fn()}
        onCustom={vi.fn()}
        status="pending"
      />,
    );
    expect(screen.getByText("The Magician")).toBeInTheDocument();
    expect(screen.getByText("The Hero")).toBeInTheDocument();
    expect(screen.getByText("The Caregiver")).toBeInTheDocument();
  });

  it("shows recommendation badge", () => {
    render(
      <AlternativesCard
        fieldPath="identity.archetype"
        question="Which archetype fits?"
        alternatives={mockAlternatives}
        allowCustom={true}
        onSelect={vi.fn()}
        onCustom={vi.fn()}
        status="pending"
      />,
    );
    expect(screen.getByText(/Matches your brand/)).toBeInTheDocument();
  });

  it("calls onSelect when option clicked and confirmed", () => {
    const onSelect = vi.fn();
    render(
      <AlternativesCard
        fieldPath="identity.archetype"
        question="Pick one"
        alternatives={mockAlternatives}
        allowCustom={true}
        onSelect={onSelect}
        onCustom={vi.fn()}
        status="pending"
      />,
    );
    fireEvent.click(screen.getByText("The Hero"));
    fireEvent.click(screen.getByRole("button", { name: /seleccionar/i }));
    expect(onSelect).toHaveBeenCalledWith("b");
  });

  it("disables interaction when resolved", () => {
    render(
      <AlternativesCard
        fieldPath="identity.archetype"
        question="Pick one"
        alternatives={mockAlternatives}
        allowCustom={true}
        onSelect={vi.fn()}
        onCustom={vi.fn()}
        status="resolved"
      />,
    );
    expect(screen.getByRole("button", { name: /seleccionar/i })).toBeDisabled();
  });

  it("shows Otro button when allowCustom is true", () => {
    render(
      <AlternativesCard
        fieldPath="identity.archetype"
        question="Pick one"
        alternatives={mockAlternatives}
        allowCustom={true}
        onSelect={vi.fn()}
        onCustom={vi.fn()}
        status="pending"
      />,
    );
    expect(screen.getByText("Otro")).toBeInTheDocument();
  });

  it("hides Otro button when allowCustom is false", () => {
    render(
      <AlternativesCard
        fieldPath="identity.archetype"
        question="Pick one"
        alternatives={mockAlternatives}
        allowCustom={false}
        onSelect={vi.fn()}
        onCustom={vi.fn()}
        status="pending"
      />,
    );
    expect(screen.queryByText("Otro")).not.toBeInTheDocument();
  });

  it("calls onCustom when Otro button clicked", () => {
    const onCustom = vi.fn();
    render(
      <AlternativesCard
        fieldPath="identity.archetype"
        question="Pick one"
        alternatives={mockAlternatives}
        allowCustom={true}
        onSelect={vi.fn()}
        onCustom={onCustom}
        status="pending"
      />,
    );
    fireEvent.click(screen.getByText("Otro"));
    expect(onCustom).toHaveBeenCalled();
  });

  it("Seleccionar button starts disabled until an option is selected", () => {
    render(
      <AlternativesCard
        fieldPath="identity.archetype"
        question="Pick one"
        alternatives={mockAlternatives}
        allowCustom={false}
        onSelect={vi.fn()}
        onCustom={vi.fn()}
        status="pending"
      />,
    );
    expect(screen.getByRole("button", { name: /seleccionar/i })).toBeDisabled();
    fireEvent.click(screen.getByText("The Magician"));
    expect(screen.getByRole("button", { name: /seleccionar/i })).not.toBeDisabled();
  });
});
