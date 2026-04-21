import { describe, expect, it } from "vitest";

import { singulariseES } from "../array-singularise";

describe("singulariseES", () => {
  it.each([
    ["pilares", "pilar"],
    ["canales", "canal"],
    ["testimonios", "testimonio"],
    ["preguntas", "pregunta"],
    ["casos", "caso"],
    ["luces", "luz"],
    ["Pilares", "pilar"],
    ["Testimonios", "testimonio"],
    ["integraciones", "integracion"],
    ["pilar", "pilar"],
    ["caso", "caso"],
    ["item", "item"],
    ["items", "item"],
    ["as", "as"],
    ["", ""],
  ])("%s → %s", (input, expected) => {
    expect(singulariseES(input)).toBe(expected);
  });

  it("trims whitespace", () => {
    expect(singulariseES("  pilares  ")).toBe("pilar");
  });
});
