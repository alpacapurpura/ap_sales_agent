import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EditableField } from "../EditableField";
import { FormRuntimeProvider } from "../FormRuntimeProvider";

import type { SectionSchema } from "@/lib/form-runtime/schema";

vi.mock("next/navigation", () => ({
  usePathname: vi.fn(() => "/t/brand-studio/positioning"),
  useSearchParams: vi.fn(() => new URLSearchParams("field=technical_enemy")),
}));

const SCHEMA: SectionSchema = {
  key: "brand.positioning",
  title: "Positioning",
  fields: [
    { id: "technical_enemy", label: "Technical enemy", type: "text", path: "technical_enemy" },
    { id: "tagline", label: "Tagline", type: "text", path: "tagline" },
  ],
};

function renderField() {
  return render(
    <FormRuntimeProvider
      schema={SCHEMA}
      initialValues={{ technical_enemy: "jargon", tagline: "" }}
      onSave={vi.fn().mockResolvedValue(undefined)}
    >
      <EditableField field={SCHEMA.fields[0]} />
    </FormRuntimeProvider>,
  );
}

describe("EditableField — URL ownership", () => {
  beforeEach(() => {
    window.history.replaceState(null, "", "/t/brand-studio/positioning?field=technical_enemy");
  });

  it("does NOT clear ?field= when the input blurs to outside the wrapper", () => {
    // Regression: previously a blur to anywhere outside the field wrapper fired
    // setActiveField(null), wiping the URL selection every time the user clicked
    // on empty space. URL is the SSoT — blur is not a selection gesture.
    renderField();

    const input = screen.getByDisplayValue("jargon");
    input.focus();
    expect(document.activeElement).toBe(input);

    fireEvent.blur(input, { relatedTarget: document.body });

    expect(window.location.search).toBe("?field=technical_enemy");
  });

  it("does NOT clear ?field= when focus moves to an element outside the wrapper", () => {
    renderField();

    const input = screen.getByDisplayValue("jargon");
    input.focus();

    // Simulate focus moving to a sibling outside the wrapper (e.g. sidebar button).
    const outsideButton = document.createElement("button");
    document.body.append(outsideButton);
    fireEvent.blur(input, { relatedTarget: outsideButton });

    expect(window.location.search).toBe("?field=technical_enemy");
    outsideButton.remove();
  });

  it("still writes ?field= when the user focuses the input (explicit gesture)", () => {
    window.history.replaceState(null, "", "/t/brand-studio/positioning");
    renderField();

    const input = screen.getByDisplayValue("jargon");
    fireEvent.focus(input);

    expect(window.location.search).toBe("?field=technical_enemy");
  });
});
