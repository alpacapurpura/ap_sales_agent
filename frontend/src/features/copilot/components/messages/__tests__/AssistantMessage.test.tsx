import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { AssistantMessage } from "../AssistantMessage";

import type { CopilotMessage } from "../../../store/copilot-store";

// AssistantMessage uses Clerk auth internally via cards that may need router — mock it
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/brand",
  useSearchParams: () => new URLSearchParams(),
}));

function makeMessage(overrides: Partial<CopilotMessage> = {}): CopilotMessage {
  return {
    id: "msg-1",
    role: "assistant",
    content: "Aquí tienes algunas opciones:",
    timestamp: Date.now(),
    ...overrides,
  };
}

describe("AssistantMessage — AlternativesCard callbacks", () => {
  it("calls sendCardAction with selected alternative title when Seleccionar clicked", () => {
    const sendCardAction = vi.fn();
    const message = makeMessage({
      uiActions: [
        {
          type: "alternatives_card",
          field_path: "identity.archetype",
          question: "¿Cuál arquetipo?",
          alternatives: [
            {
              id: "a1",
              title: "El Mago",
              description: "Transforma lo complejo",
              recommended: true,
              recommendation_reason: "Se adapta",
            },
            {
              id: "a2",
              title: "El Héroe",
              description: "Empodera a los usuarios",
              recommended: false,
            },
          ],
          allow_custom: false,
          card_status: "pending",
        },
      ],
    });

    render(<AssistantMessage message={message} sendCardAction={sendCardAction} />);

    // Select the alternative
    fireEvent.click(screen.getByText("El Héroe"));
    // Click Seleccionar
    fireEvent.click(screen.getByRole("button", { name: /seleccionar/i }));

    expect(sendCardAction).toHaveBeenCalledOnce();
    expect(sendCardAction).toHaveBeenCalledWith("msg-1", 0, "Selecciono: El Héroe");
  });

  it("calls sendCardAction with custom text when Otro clicked", () => {
    const sendCardAction = vi.fn();
    const message = makeMessage({
      uiActions: [
        {
          type: "alternatives_card",
          field_path: "identity.archetype",
          question: "¿Cuál arquetipo?",
          alternatives: [
            {
              id: "a1",
              title: "El Mago",
              description: "Transforma lo complejo",
              recommended: false,
            },
          ],
          allow_custom: true,
          card_status: "pending",
        },
      ],
    });

    render(<AssistantMessage message={message} sendCardAction={sendCardAction} />);

    fireEvent.click(screen.getByText("Otro"));

    expect(sendCardAction).toHaveBeenCalledOnce();
    expect(sendCardAction).toHaveBeenCalledWith("msg-1", 0, "Prefiero otra opción personalizada");
  });

  it("does not call sendCardAction when sendCardAction is not provided (graceful no-op)", () => {
    const message = makeMessage({
      uiActions: [
        {
          type: "alternatives_card",
          field_path: "identity.archetype",
          question: "¿Cuál arquetipo?",
          alternatives: [
            {
              id: "a1",
              title: "El Mago",
              description: "Transforma lo complejo",
              recommended: false,
            },
          ],
          allow_custom: true,
          card_status: "pending",
        },
      ],
    });

    // Should not throw
    expect(() => {
      render(<AssistantMessage message={message} />);
      fireEvent.click(screen.getByText("Otro"));
    }).not.toThrow();
  });
});

describe("AssistantMessage — ClarifyCard callbacks", () => {
  it("calls sendCardAction with the resolution text when an option is clicked", () => {
    const sendCardAction = vi.fn();
    const message = makeMessage({
      uiActions: [
        {
          type: "clarify_card",
          clarify_items: [
            {
              field_path: "offer.price",
              issue: "El precio no cuadra con el segmento",
              options: ["Precio premium", "Precio accesible"],
            },
          ],
          card_status: "pending",
        },
      ],
    });

    render(<AssistantMessage message={message} sendCardAction={sendCardAction} />);

    fireEvent.click(screen.getByText("Precio accesible"));

    expect(sendCardAction).toHaveBeenCalledOnce();
    expect(sendCardAction).toHaveBeenCalledWith("msg-1", 0, "Precio accesible");
  });
});

describe("AssistantMessage — CheckpointCard callbacks", () => {
  it("calls sendCardAction with confirm text when Perfecto button clicked", () => {
    const sendCardAction = vi.fn();
    const message = makeMessage({
      uiActions: [
        {
          type: "checkpoint_card",
          block_id: "block-1",
          block_label: "Identidad de Marca",
          summary: { "brand.name": "Nicolify" },
          health_score: 80,
          blocks_progress: { completed: 1, total: 3 },
          card_status: "pending",
        },
      ],
    });

    render(<AssistantMessage message={message} sendCardAction={sendCardAction} />);

    fireEvent.click(screen.getByRole("button", { name: /perfecto, sigamos/i }));

    expect(sendCardAction).toHaveBeenCalledOnce();
    expect(sendCardAction).toHaveBeenCalledWith(
      "msg-1",
      0,
      "Confirmo, sigamos al siguiente bloque",
    );
  });

  it("calls sendCardAction with revise text when Ajustar button clicked", () => {
    const sendCardAction = vi.fn();
    const message = makeMessage({
      uiActions: [
        {
          type: "checkpoint_card",
          block_id: "block-1",
          block_label: "Identidad de Marca",
          summary: { "brand.name": "Nicolify" },
          health_score: 80,
          blocks_progress: { completed: 1, total: 3 },
          card_status: "pending",
        },
      ],
    });

    render(<AssistantMessage message={message} sendCardAction={sendCardAction} />);

    fireEvent.click(screen.getByRole("button", { name: /ajustar algo/i }));

    expect(sendCardAction).toHaveBeenCalledOnce();
    expect(sendCardAction).toHaveBeenCalledWith("msg-1", 0, "Quiero ajustar algo en este bloque");
  });

  it("does not call sendCardAction when card is already confirmed", () => {
    const sendCardAction = vi.fn();
    const message = makeMessage({
      uiActions: [
        {
          type: "checkpoint_card",
          block_id: "block-1",
          block_label: "Identidad de Marca",
          summary: {},
          health_score: 90,
          blocks_progress: { completed: 2, total: 3 },
          card_status: "confirmed",
        },
      ],
    });

    render(<AssistantMessage message={message} sendCardAction={sendCardAction} />);

    // Both buttons should be disabled when confirmed
    expect(screen.getByRole("button", { name: /perfecto, sigamos/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /ajustar algo/i })).toBeDisabled();
    expect(sendCardAction).not.toHaveBeenCalled();
  });
});

describe("AssistantMessage — uiAction index correctness", () => {
  it("passes the correct actionIndex when there are multiple uiActions", () => {
    const sendCardAction = vi.fn();
    const message = makeMessage({
      uiActions: [
        {
          type: "clarify_card",
          clarify_items: [
            {
              field_path: "brand.name",
              issue: "El nombre no cuadra",
              options: ["Opción A"],
            },
          ],
          card_status: "pending",
        },
        {
          type: "checkpoint_card",
          block_id: "block-2",
          block_label: "Oferta",
          summary: {},
          health_score: 70,
          blocks_progress: { completed: 0, total: 2 },
          card_status: "pending",
        },
      ],
    });

    render(<AssistantMessage message={message} sendCardAction={sendCardAction} />);

    // Click Perfecto on the CheckpointCard (second action, index 1)
    fireEvent.click(screen.getByRole("button", { name: /perfecto, sigamos/i }));

    expect(sendCardAction).toHaveBeenCalledWith(
      "msg-1",
      1,
      "Confirmo, sigamos al siguiente bloque",
    );
  });
});
