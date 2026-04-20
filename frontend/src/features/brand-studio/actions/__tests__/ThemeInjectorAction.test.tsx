import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { FormRuntimeProvider } from "@/components/form-runtime";

import { ThemeInjectorAction } from "../ThemeInjectorAction";

import type { SectionSchema } from "@/lib/form-runtime/schema";

const VISUALS_SCHEMA: SectionSchema = {
  key: "brand.visuals",
  title: "Visuales",
  fields: [{ id: "primary_color", label: "Primario", type: "text", path: "primary_color" }],
};

function mountWith(values: Record<string, unknown>) {
  return render(
    <FormRuntimeProvider
      schema={VISUALS_SCHEMA}
      initialValues={values}
      onSave={vi.fn().mockResolvedValue(undefined)}
    >
      <ThemeInjectorAction value={undefined} onChange={vi.fn()} />
    </FormRuntimeProvider>,
  );
}

describe("ThemeInjectorAction", () => {
  it("renders 'sin definir' placeholders when colors are absent", () => {
    mountWith({});
    expect(screen.getAllByText(/sin definir/i).length).toBeGreaterThan(0);
  });

  it("renders swatches for every defined color", () => {
    mountWith({
      primary_color: "#123456",
      secondary_color: "#ABCDEF",
      accent_color: "#FF00AA",
    });
    expect(screen.getByText("#123456")).toBeTruthy();
    expect(screen.getByText("#ABCDEF")).toBeTruthy();
    expect(screen.getByText("#FF00AA")).toBeTruthy();
  });

  it("uses the provided font names for preview headlines and body copy", () => {
    mountWith({ font_heading: "Inter", font_body: "Roboto" });
    expect(screen.getByText(/Inter/)).toBeTruthy();
    expect(screen.getByText(/Roboto/)).toBeTruthy();
  });

  it("falls back to sans-serif when no font family is set", () => {
    mountWith({ primary_color: "#111111" });
    expect(screen.getAllByText(/sans-serif/i).length).toBeGreaterThan(0);
  });
});
