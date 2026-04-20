import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FieldContextPanel } from "../FieldContextPanel";
import { FormRuntimeProvider } from "../FormRuntimeProvider";

import type { SectionSchema } from "@/lib/form-runtime/schema";

function wrap(schema: SectionSchema, initialValues: Record<string, unknown>) {
  return function wrapped(ui: React.ReactElement) {
    return (
      <FormRuntimeProvider schema={schema} initialValues={initialValues} onSave={vi.fn()}>
        {ui}
      </FormRuntimeProvider>
    );
  };
}

const SCHEMA: SectionSchema = {
  key: "brand.positioning",
  fields: [
    {
      id: "uvp",
      label: "Propuesta de valor",
      type: "textarea",
      path: "uvp",
      formula: {
        template:
          "<b>Solo nosotros</b> + <span class='reco-slot'>{X}</span> + <span class='reco-slot'>{Y}</span>",
      },
      examples: [{ brand: "Notion", text: "Un solo espacio para cada equipo." }],
      downstreamUses: [{ label: "Landing · Hero" }],
      relatedFields: [{ id: "discriminator", label: "Discriminador" }],
      lengthHint: { ideal: [60, 140] },
    },
  ],
};

afterEach(() => {
  window.localStorage.clear();
});

describe("FieldContextPanel", () => {
  it("renders collapsed by default with the badge + toggle + count", () => {
    const Wrapped = wrap(SCHEMA, { uvp: "hola" });
    render(Wrapped(<FieldContextPanel activeFieldId="uvp" />));
    expect(screen.getByText(/Recomendaciones/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Mostrar/i })).toBeTruthy();
  });

  it("expands and shows blocks when the header is clicked", () => {
    const Wrapped = wrap(SCHEMA, { uvp: "hola" });
    render(Wrapped(<FieldContextPanel activeFieldId="uvp" />));

    act(() => {
      fireEvent.click(screen.getByRole("button", { name: /Mostrar/i }));
    });

    expect(screen.getByText(/Fórmula/i)).toBeTruthy();
    expect(screen.getByText(/Ejemplos de referencia/i)).toBeTruthy();
    expect(screen.getByText(/Dónde se usa/i)).toBeTruthy();
    expect(screen.getByText(/Campos relacionados/i)).toBeTruthy();
    expect(screen.getByText(/Metadata/i)).toBeTruthy();
  });

  it("persists expanded state in localStorage between mounts", () => {
    const Wrapped = wrap(SCHEMA, { uvp: "hola" });
    const { unmount } = render(Wrapped(<FieldContextPanel activeFieldId="uvp" />));
    act(() => {
      fireEvent.click(screen.getByRole("button", { name: /Mostrar/i }));
    });
    unmount();

    render(Wrapped(<FieldContextPanel activeFieldId="uvp" />));
    expect(screen.getByRole("button", { name: /Ocultar/i })).toBeTruthy();
  });

  it("shows an empty-state when no active field", () => {
    const Wrapped = wrap(SCHEMA, { uvp: "hola" });
    render(Wrapped(<FieldContextPanel activeFieldId={null} />));
    // Header still rendered, but body when expanded should have no blocks.
    act(() => {
      fireEvent.click(screen.getByRole("button", { name: /Mostrar/i }));
    });
    expect(screen.queryByText(/Fórmula/i)).toBeNull();
  });
});
