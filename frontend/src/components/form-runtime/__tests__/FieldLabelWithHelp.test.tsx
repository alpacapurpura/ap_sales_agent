import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FieldLabelWithHelp } from "../FieldLabelWithHelp";

import type { FieldSchema } from "@/lib/form-runtime/schema";

const BASE_FIELD: FieldSchema = {
  id: "test_field",
  label: "Tono de voz",
  type: "text",
  path: "voice_tone",
  hint: "Cómo habla tu marca en cada canal.",
};

describe("FieldLabelWithHelp", () => {
  it("renders the label text", () => {
    render(<FieldLabelWithHelp field={BASE_FIELD} htmlFor="test_field" />);
    expect(screen.getByText("Tono de voz")).toBeTruthy();
  });

  it("renders a HelpCircle trigger button when hint is present", () => {
    render(<FieldLabelWithHelp field={BASE_FIELD} htmlFor="test_field" />);
    const trigger = screen.getByRole("button", { name: /ayuda sobre/i });
    expect(trigger).toBeTruthy();
  });

  it("does NOT render a trigger button when no hint, no examples, no formula, no downstreamUses", () => {
    const fieldWithoutHelp: FieldSchema = {
      id: "bare",
      label: "Campo sin ayuda",
      type: "text",
      path: "bare",
    };
    render(<FieldLabelWithHelp field={fieldWithoutHelp} htmlFor="bare" />);
    const trigger = screen.queryByRole("button", { name: /ayuda sobre/i });
    expect(trigger).toBeNull();
  });

  it("shows hint content in popover when trigger is clicked", async () => {
    render(<FieldLabelWithHelp field={BASE_FIELD} htmlFor="test_field" />);
    const trigger = screen.getByRole("button", { name: /ayuda sobre/i });
    fireEvent.click(trigger);
    expect(screen.getByText("Cómo habla tu marca en cada canal.")).toBeTruthy();
  });

  it("shows examples section when field has examples", () => {
    const fieldWithExamples: FieldSchema = {
      ...BASE_FIELD,
      examples: [
        { brand: "Coach ejecutiva (CDMX)", text: "Directo, cálido, con metáforas de liderazgo." },
        { brand: "Nutricionista (Lima, PE)", text: "Educativo, empático, sin culpa." },
      ],
    };
    render(<FieldLabelWithHelp field={fieldWithExamples} htmlFor="test_field" />);
    const trigger = screen.getByRole("button", { name: /ayuda sobre/i });
    fireEvent.click(trigger);
    expect(screen.getByText("Coach ejecutiva (CDMX)")).toBeTruthy();
    expect(screen.getByText("Directo, cálido, con metáforas de liderazgo.")).toBeTruthy();
  });

  it("shows formula section when field has formula", () => {
    const fieldWithFormula: FieldSchema = {
      ...BASE_FIELD,
      formula: {
        template: "Resultado en <slot>tiempo</slot> sin <slot>obstáculo</slot>",
      },
    };
    render(<FieldLabelWithHelp field={fieldWithFormula} htmlFor="test_field" />);
    const trigger = screen.getByRole("button", { name: /ayuda sobre/i });
    fireEvent.click(trigger);
    expect(screen.getByText("Fórmula sugerida")).toBeTruthy();
  });

  it("shows downstreamUses section when field has downstream uses", () => {
    const fieldWithUses: FieldSchema = {
      ...BASE_FIELD,
      downstreamUses: [{ label: "Landing hero" }, { label: "Email de bienvenida" }],
    };
    render(<FieldLabelWithHelp field={fieldWithUses} htmlFor="test_field" />);
    const trigger = screen.getByRole("button", { name: /ayuda sobre/i });
    fireEvent.click(trigger);
    expect(screen.getByText("Dónde se usa")).toBeTruthy();
    expect(screen.getByText("Landing hero")).toBeTruthy();
    expect(screen.getByText("Email de bienvenida")).toBeTruthy();
  });

  it("renders required asterisk when field is required", () => {
    const requiredField: FieldSchema = { ...BASE_FIELD, required: true };
    render(<FieldLabelWithHelp field={requiredField} htmlFor="test_field" />);
    expect(screen.getByText("*")).toBeTruthy();
  });

  it("accepts custom className on the wrapper", () => {
    const { container } = render(
      <FieldLabelWithHelp field={BASE_FIELD} htmlFor="test_field" className="text-xs" />,
    );
    expect(container.firstElementChild?.className).toContain("text-xs");
  });

  it("renders trigger even when there is only examples (no hint)", () => {
    const fieldExamplesOnly: FieldSchema = {
      id: "no_hint",
      label: "Solo ejemplos",
      type: "text",
      path: "no_hint",
      examples: [{ brand: "Marca X", text: "Texto ejemplo." }],
    };
    render(<FieldLabelWithHelp field={fieldExamplesOnly} htmlFor="no_hint" />);
    const trigger = screen.queryByRole("button", { name: /ayuda sobre/i });
    expect(trigger).toBeTruthy();
  });
});
