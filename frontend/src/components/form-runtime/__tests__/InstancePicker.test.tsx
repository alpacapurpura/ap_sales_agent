import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { computeCompletionTone, initialsOf } from "../instance-display";
import { InstancePicker } from "../InstancePicker";

describe("initialsOf", () => {
  it("uses the first letter of the first word uppercased", () => {
    expect(initialsOf("Alicia")).toBe("A");
    expect(initialsOf("alpaca púrpura")).toBe("A");
  });
  it("falls back to ? on empty", () => {
    expect(initialsOf("")).toBe("?");
  });
});

describe("computeCompletionTone", () => {
  it("returns empty for scores < 34", () => {
    expect(computeCompletionTone(0)).toBe("empty");
    expect(computeCompletionTone(33)).toBe("empty");
  });
  it("returns partial for 34-79", () => {
    expect(computeCompletionTone(50)).toBe("partial");
    expect(computeCompletionTone(79)).toBe("partial");
  });
  it("returns filled for ≥80", () => {
    expect(computeCompletionTone(80)).toBe("filled");
    expect(computeCompletionTone(100)).toBe("filled");
  });
});

describe("InstancePicker", () => {
  it("renders the create CTA and every instance row", () => {
    render(
      <InstancePicker
        title="Personas"
        createLabel="Crear nueva persona"
        onCreate={() => {}}
        activeInstanceId="p1"
        instances={[
          { id: "p1", primary: "Alicia", secondary: "Avatar ideal", completion: 82 },
          { id: "p2", primary: "Bruno", secondary: "Secundario", completion: 54 },
          { id: "p3", primary: "Carla", secondary: "Temprana", completion: 18 },
        ]}
        getInstanceHref={(id) => `/t/brand-studio/publico/instance/${id}`}
      />,
    );
    expect(screen.getByRole("button", { name: /Crear nueva persona/i })).toBeTruthy();
    expect(screen.getByText("Alicia")).toBeTruthy();
    expect(screen.getByText("Bruno")).toBeTruthy();
    expect(screen.getByText("Carla")).toBeTruthy();
  });

  it("marks the active row with aria-current", () => {
    render(
      <InstancePicker
        title="Personas"
        createLabel="Nueva"
        onCreate={() => {}}
        activeInstanceId="p2"
        instances={[
          { id: "p1", primary: "A", completion: 0 },
          { id: "p2", primary: "B", completion: 50 },
        ]}
        getInstanceHref={(id) => `/${id}`}
      />,
    );
    const rows = screen.getAllByRole("link");
    const active = rows.find((r) => r.getAttribute("aria-current") === "page");
    expect(active?.textContent).toContain("B");
  });
});
