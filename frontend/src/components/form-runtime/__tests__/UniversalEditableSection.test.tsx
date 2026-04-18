import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { UniversalEditableSection } from "../UniversalEditableSection";

import type { SectionSchema } from "@/lib/form-runtime/schema";

const SCHEMA: SectionSchema = {
  key: "brand.identity",
  title: "Identidad",
  description: "Los cimientos de tu marca.",
  fields: [
    { id: "name", label: "Nombre", type: "text", path: "name", required: true },
    { id: "tagline", label: "Tagline", type: "text", path: "tagline" },
    { id: "mission", label: "Misión", type: "textarea", path: "mission", rows: 3 },
  ],
};

// URL builder used in tests — mimics the real brand-studio route contract.
function sectionHref(fieldId: string | null): string {
  return fieldId === null ? "/t/section" : `/t/section/${fieldId}`;
}

async function flushMicrotasks(): Promise<void> {
  for (let i = 0; i < 3; i += 1) {
    await Promise.resolve();
  }
}

describe("UniversalEditableSection", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders section title, description and all field labels in the list", () => {
    render(
      <UniversalEditableSection
        schema={SCHEMA}
        values={{ name: "Visionarias", tagline: "", mission: "" }}
        onSave={vi.fn().mockResolvedValue(undefined)}
        activeFieldId={null}
        getFieldHref={sectionHref}
      />,
    );
    expect(screen.getByRole("heading", { name: "Identidad" })).toBeTruthy();
    expect(screen.getByText(/cimientos/i)).toBeTruthy();
    expect(screen.getByRole("option", { name: /Nombre/ })).toBeTruthy();
    expect(screen.getByRole("option", { name: /Tagline/ })).toBeTruthy();
    expect(screen.getByRole("option", { name: /Misión/ })).toBeTruthy();
  });

  it("shows completeness chip (filled / total)", () => {
    render(
      <UniversalEditableSection
        schema={SCHEMA}
        values={{ name: "Visionarias", tagline: "hola", mission: "" }}
        onSave={vi.fn().mockResolvedValue(undefined)}
        activeFieldId={null}
        getFieldHref={sectionHref}
      />,
    );
    expect(screen.getByLabelText(/2 de 3 campos completos/i)).toBeTruthy();
  });

  it("renders Cargando… when isLoading or values are missing", () => {
    const { rerender } = render(
      <UniversalEditableSection
        schema={SCHEMA}
        values={undefined}
        onSave={vi.fn()}
        activeFieldId={null}
        getFieldHref={sectionHref}
      />,
    );
    expect(screen.getByText(/Cargando/i)).toBeTruthy();

    rerender(
      <UniversalEditableSection
        schema={SCHEMA}
        values={{}}
        onSave={vi.fn()}
        isLoading
        activeFieldId={null}
        getFieldHref={sectionHref}
      />,
    );
    expect(screen.getByText(/Cargando/i)).toBeTruthy();
  });

  it("renders the field matching activeFieldId in the detail pane", () => {
    render(
      <UniversalEditableSection
        schema={SCHEMA}
        values={{ name: "a", tagline: "b", mission: "c" }}
        onSave={vi.fn().mockResolvedValue(undefined)}
        activeFieldId="tagline"
        getFieldHref={sectionHref}
      />,
    );
    expect(screen.getByDisplayValue("b")).toBeTruthy();
  });

  it("falls back to the first schema field when activeFieldId is null", () => {
    render(
      <UniversalEditableSection
        schema={SCHEMA}
        values={{ name: "a", tagline: "b", mission: "c" }}
        onSave={vi.fn().mockResolvedValue(undefined)}
        activeFieldId={null}
        getFieldHref={sectionHref}
      />,
    );
    expect(screen.getByDisplayValue("a")).toBeTruthy();
  });

  it("renders rows as Next.js Links pointing at the consumer-provided href", () => {
    render(
      <UniversalEditableSection
        schema={SCHEMA}
        values={{ name: "a", tagline: "b", mission: "c" }}
        onSave={vi.fn().mockResolvedValue(undefined)}
        activeFieldId={null}
        getFieldHref={sectionHref}
      />,
    );
    const taglineRow = screen.getByRole("option", { name: /Tagline/ });
    expect(taglineRow.getAttribute("href")).toBe("/t/section/tagline");
  });

  it("autosave triggers after 800ms debounce", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(
      <UniversalEditableSection
        schema={SCHEMA}
        values={{ name: "start", tagline: "t", mission: "m" }}
        onSave={onSave}
        activeFieldId="name"
        getFieldHref={sectionHref}
      />,
    );

    const input = screen.getByDisplayValue("start");
    act(() => {
      fireEvent.change(input, { target: { value: "new" } });
    });

    await act(async () => {
      vi.advanceTimersByTime(850);
      await flushMicrotasks();
    });

    expect(onSave).toHaveBeenCalledWith({ name: "new", tagline: "t", mission: "m" });
  });
});
