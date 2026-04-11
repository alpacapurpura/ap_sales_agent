import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { OfferStatusChangeModal } from "../offer-status-change-modal";

describe("OfferStatusChangeModal", () => {
  const baseProps = {
    open: true,
    fromStatus: "draft" as const,
    toStatus: "active" as const,
    offerName: "Programa Insignia",
    isSubmitting: false,
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
  };

  it("renders the offer name in the modal body", () => {
    render(<OfferStatusChangeModal {...baseProps} />);
    expect(screen.getByText(/Programa Insignia/)).toBeInTheDocument();
  });

  it("renders consequences for draft → active", () => {
    render(<OfferStatusChangeModal {...baseProps} />);
    // 3 bullets for draft → active
    expect(
      screen.getByText(
        /Sales Agent empezará a proponerla en conversaciones/i,
      ),
    ).toBeInTheDocument();
  });

  it("renders consequences for active → paused", () => {
    render(
      <OfferStatusChangeModal
        {...baseProps}
        fromStatus="active"
        toStatus="paused"
      />,
    );
    expect(
      screen.getByText(/Sales Agent dejará de proponerla/i),
    ).toBeInTheDocument();
  });

  it("calls onConfirm when the confirm button is clicked", () => {
    const onConfirm = vi.fn();
    render(<OfferStatusChangeModal {...baseProps} onConfirm={onConfirm} />);
    fireEvent.click(
      screen.getByRole("button", { name: /Activar|Confirmar/i }),
    );
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("calls onCancel when the cancel button is clicked", () => {
    const onCancel = vi.fn();
    render(<OfferStatusChangeModal {...baseProps} onCancel={onCancel} />);
    fireEvent.click(screen.getByRole("button", { name: /Cancelar/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("disables the confirm button while submitting", () => {
    render(<OfferStatusChangeModal {...baseProps} isSubmitting={true} />);
    expect(
      screen.getByRole("button", { name: /Activar|Confirmar/i }),
    ).toBeDisabled();
  });
});
