import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi } from "vitest";

import { EditionPreviewCard } from "../EditionPreviewCard";
import { InterviewDateBlock } from "../InterviewDateBlock";

const baseProps = {
  question: "¿Cuándo planeas tu primera cohorte?",
  suggestedDate: "2026-07-15T19:00:00Z",
  editionNoun: "Cohorte",
};

describe("InterviewDateBlock", () => {
  it("renders the question and three quick replies when a suggestion exists", () => {
    render(<InterviewDateBlock {...baseProps} onSubmit={vi.fn()} />);
    expect(screen.getByText(baseProps.question)).toBeInTheDocument();
    expect(screen.getByText(/El \d/i)).toBeInTheDocument();
    expect(screen.getByText(/Elegir fecha/i)).toBeInTheDocument();
    expect(screen.getByText(/Todavía no sé/i)).toBeInTheDocument();
  });

  it("fires onSubmit with the suggested date when user picks it", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<InterviewDateBlock {...baseProps} onSubmit={onSubmit} />);
    fireEvent.click(screen.getByText(/El \d/i));
    expect(onSubmit).toHaveBeenCalledWith({
      start_date: baseProps.suggestedDate,
      skipped: false,
    });
  });

  it("requires confirmation before skipping", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<InterviewDateBlock {...baseProps} onSubmit={onSubmit} />);
    fireEvent.click(screen.getByText(/Todavía no sé/i));
    // Only shows a confirmation UI, onSubmit not called yet.
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText(/sin fecha\?/i)).toBeInTheDocument();
    // After confirming the skip…
    fireEvent.click(screen.getByText(/Sí, crear en borrador/i));
    expect(onSubmit).toHaveBeenCalledWith({ start_date: null, skipped: true });
  });

  it("omits the suggestion button when the backend had no hint", () => {
    render(<InterviewDateBlock {...baseProps} suggestedDate={null} onSubmit={vi.fn()} />);
    // No "El DD..." chip, but the other two options are present.
    expect(screen.queryByText(/El \d/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Elegir fecha/i)).toBeInTheDocument();
  });
});

describe("EditionPreviewCard", () => {
  it("renders the draft state when startDate is null", () => {
    render(<EditionPreviewCard startDate={null} />);
    expect(screen.getByText(/Se publicará/i)).toBeInTheDocument();
    expect(screen.getByText(/Pendiente de confirmar/i)).toBeInTheDocument();
    expect(screen.getByText(/🔒 Privada/)).toBeInTheDocument();
  });

  it("renders the upcoming state when a date is set", () => {
    render(<EditionPreviewCard startDate="2026-07-15T19:00:00Z" />);
    // "Próxima" appears as the status chip at the top-right of the card.
    expect(screen.getAllByText(/Próxima/).length).toBeGreaterThan(0);
    expect(screen.getByText(/🌐 Pública/)).toBeInTheDocument();
  });
});
