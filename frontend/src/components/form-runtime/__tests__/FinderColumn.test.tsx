import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { FinderColumn } from "../FinderColumn";

describe("FinderColumn", () => {
  it("renders title, count and children", () => {
    render(
      <FinderColumn title="Secciones" count={12}>
        <div>body</div>
      </FinderColumn>,
    );
    expect(screen.getByRole("heading", { name: /Secciones/i })).toBeTruthy();
    expect(screen.getByText("12")).toBeTruthy();
    expect(screen.getByText("body")).toBeTruthy();
  });

  it("renders without count when omitted", () => {
    render(
      <FinderColumn title="Editor">
        <div>editor body</div>
      </FinderColumn>,
    );
    expect(screen.getByRole("heading", { name: /Editor/i })).toBeTruthy();
    expect(screen.getByText("editor body")).toBeTruthy();
  });

  it("renders custom header trailing slot (e.g. autosave status)", () => {
    render(
      <FinderColumn title="Detalle" headerTrailing={<span>guardado</span>}>
        <div />
      </FinderColumn>,
    );
    expect(screen.getByText("guardado")).toBeTruthy();
  });

  it("applies fixed width class from prop", () => {
    const { container } = render(
      <FinderColumn title="X" widthClass="w-[260px]">
        <div />
      </FinderColumn>,
    );
    const col = container.firstChild as HTMLElement;
    expect(col.className).toContain("w-[260px]");
  });
});
