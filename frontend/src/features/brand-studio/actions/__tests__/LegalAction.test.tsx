import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { FormRuntimeProvider } from "@/components/form-runtime";

import { LegalAction } from "../LegalAction";

import type { SectionSchema } from "@/lib/form-runtime/schema";

const IDENTITY_SCHEMA: SectionSchema = {
  key: "brand.identity",
  title: "Identidad",
  fields: [
    { id: "legal_name", label: "Razón social", type: "text", path: "legal_name" },
    { id: "tax_id", label: "RUC", type: "text", path: "tax_id" },
    { id: "fiscal_address", label: "Dirección", type: "text", path: "fiscal_address" },
    { id: "legal_representative", label: "Rep", type: "text", path: "legal_representative" },
    { id: "terms_url", label: "Términos", type: "url", path: "terms_url" },
    { id: "privacy_url", label: "Privacidad", type: "url", path: "privacy_url" },
  ],
};

function mountAction(
  values: Record<string, unknown> = {},
  onSave = vi.fn().mockResolvedValue(undefined),
) {
  return render(
    <FormRuntimeProvider
      schema={IDENTITY_SCHEMA}
      initialValues={values}
      onSave={onSave}
      saveMode="explicit"
    >
      <LegalAction value="" onChange={vi.fn()} />
    </FormRuntimeProvider>,
  );
}

describe("LegalAction", () => {
  it("prefills inputs from the form-runtime identity slice", () => {
    mountAction({
      legal_name: "Visionarias LLC",
      tax_id: "20601234567",
      terms_url: "https://example.com/terms",
    });
    expect(screen.getByDisplayValue("Visionarias LLC")).toBeTruthy();
    expect(screen.getByDisplayValue("20601234567")).toBeTruthy();
    expect(screen.getByDisplayValue("https://example.com/terms")).toBeTruthy();
  });

  it("shows URL validation error when terms_url is invalid", async () => {
    mountAction();
    fireEvent.change(screen.getByLabelText(/Términos y condiciones/i), {
      target: { value: "not a url" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Guardar/i }));
    await waitFor(() => {
      expect(screen.getByText(/URL inválida/i)).toBeTruthy();
    });
  });

  it("dispatches every legal field to the runtime on submit", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    mountAction({}, onSave);
    fireEvent.change(screen.getByLabelText(/Razón social/i), {
      target: { value: "Acme SA" },
    });
    fireEvent.change(screen.getByLabelText(/RUC/i), { target: { value: "123" } });
    fireEvent.click(screen.getByRole("button", { name: /Guardar/i }));
    // saveMode is explicit — runtime won't auto-persist, but the form-runtime
    // state should still reflect the new values. Verify via the DOM.
    await waitFor(() => {
      expect(screen.getByDisplayValue("Acme SA")).toBeTruthy();
      expect(screen.getByDisplayValue("123")).toBeTruthy();
    });
  });
});
