import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { AttachmentButton } from "../attachment-button";

describe("AttachmentButton", () => {
  it("renders with correct aria-label", () => {
    render(<AttachmentButton onFilesSelected={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Adjuntar documento" })).toBeInTheDocument();
  });

  it("renders as disabled when disabled prop is true", () => {
    render(<AttachmentButton onFilesSelected={vi.fn()} disabled />);
    expect(screen.getByRole("button", { name: "Adjuntar documento" })).toBeDisabled();
  });

  it("calls onFilesSelected when files are chosen", () => {
    const onFilesSelected = vi.fn();
    render(<AttachmentButton onFilesSelected={onFilesSelected} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toBeTruthy();

    const file = new File(["content"], "test.pdf", {
      type: "application/pdf",
    });
    fireEvent.change(input, { target: { files: [file] } });

    expect(onFilesSelected).toHaveBeenCalledWith([file]);
  });

  it("uses default accept attribute for file types", () => {
    render(<AttachmentButton onFilesSelected={vi.fn()} />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input.accept).toBe(".pdf,.docx,.txt,.md,.pptx");
  });

  it("uses custom accept attribute when provided", () => {
    render(<AttachmentButton onFilesSelected={vi.fn()} accept=".pdf,.txt" />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input.accept).toBe(".pdf,.txt");
  });

  it("supports multiple file selection", () => {
    const onFilesSelected = vi.fn();
    render(<AttachmentButton onFilesSelected={onFilesSelected} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file1 = new File(["a"], "doc1.pdf", { type: "application/pdf" });
    const file2 = new File(["b"], "doc2.txt", { type: "text/plain" });
    fireEvent.change(input, { target: { files: [file1, file2] } });

    expect(onFilesSelected).toHaveBeenCalledWith([file1, file2]);
  });

  it("resets input value after file selection for re-selection of same file", () => {
    const onFilesSelected = vi.fn();
    render(<AttachmentButton onFilesSelected={onFilesSelected} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["content"], "test.pdf", {
      type: "application/pdf",
    });
    fireEvent.change(input, { target: { files: [file] } });

    expect(input.value).toBe("");
  });
});
