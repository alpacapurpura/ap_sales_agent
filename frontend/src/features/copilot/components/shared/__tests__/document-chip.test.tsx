import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import { DocumentChip } from "../document-chip";

function makeFile(name: string): File {
  return new File(["content"], name, { type: "application/pdf" });
}

describe("DocumentChip", () => {
  it("shows truncated filename", () => {
    const file = makeFile("my-document.pdf");
    render(<DocumentChip file={file} status="pending" />);
    expect(screen.getByText("my-document.pdf")).toBeInTheDocument();
  });

  it("truncates long filenames", () => {
    const file = makeFile("this-is-a-very-long-document-name-that-should-be-truncated.pdf");
    render(<DocumentChip file={file} status="pending" />);
    const nameEl = screen.getByText(
      "this-is-a-very-long-document-name-that-should-be-truncated.pdf",
    );
    expect(nameEl.className).toContain("truncate");
  });

  it("shows spinner and 'Analizando...' when processing", () => {
    const file = makeFile("doc.pdf");
    render(<DocumentChip file={file} status="processing" />);
    expect(screen.getByText("Analizando...")).toBeInTheDocument();
  });

  it("shows green check icon when done", () => {
    const file = makeFile("doc.pdf");
    render(<DocumentChip file={file} status="done" />);
    // CheckCircle2 renders as an SVG; verify no error/processing indicators
    expect(screen.queryByText("Analizando...")).not.toBeInTheDocument();
  });

  it("shows red error icon when error", () => {
    const file = makeFile("doc.pdf");
    render(<DocumentChip file={file} status="error" />);
    expect(screen.queryByText("Analizando...")).not.toBeInTheDocument();
  });

  it("shows remove button when status is pending and onRemove provided", () => {
    const onRemove = vi.fn();
    const file = makeFile("doc.pdf");
    render(<DocumentChip file={file} status="pending" onRemove={onRemove} />);
    expect(screen.getByRole("button", { name: "Eliminar documento" })).toBeInTheDocument();
  });

  it("calls onRemove when remove button is clicked", async () => {
    const user = userEvent.setup();
    const onRemove = vi.fn();
    const file = makeFile("doc.pdf");
    render(<DocumentChip file={file} status="pending" onRemove={onRemove} />);

    await user.click(screen.getByRole("button", { name: "Eliminar documento" }));
    expect(onRemove).toHaveBeenCalledOnce();
  });

  it("hides remove button when status is not pending", () => {
    const onRemove = vi.fn();
    const file = makeFile("doc.pdf");
    render(<DocumentChip file={file} status="processing" onRemove={onRemove} />);
    expect(screen.queryByRole("button", { name: "Eliminar documento" })).not.toBeInTheDocument();
  });

  it("hides remove button when onRemove is not provided", () => {
    const file = makeFile("doc.pdf");
    render(<DocumentChip file={file} status="pending" />);
    expect(screen.queryByRole("button", { name: "Eliminar documento" })).not.toBeInTheDocument();
  });
});
