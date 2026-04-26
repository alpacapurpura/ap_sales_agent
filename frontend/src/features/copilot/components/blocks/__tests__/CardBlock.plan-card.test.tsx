import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CardBlock } from "../CardBlock";

import type { CardBlock as CardBlockType } from "../../../types/message-blocks";

/**
 * B18-TP9 — plan_card dispatch + render.
 *
 * Pre-fix: ``card_kind: "plan_card"`` was not in the FE union and fell to
 * the dispatcher's ``default`` case (NavigationCard) which expected a route
 * payload, not the deep-agent ``{todos: [...]}`` shape. Multi-step audit
 * plans never rendered.
 */
describe("CardBlock — plan_card (B18-TP9)", () => {
  it("renders todos with status transitions instead of falling to NavigationCard", () => {
    const block: CardBlockType = {
      id: "block-1",
      type: "card",
      card_kind: "plan_card",
      payload: {
        todos: [
          { content: "Auditar Brand Studio", status: "completed", active_form: "" },
          {
            content: "Auditar Offer Studio",
            status: "in_progress",
            active_form: "Auditando ofertas",
          },
          { content: "Sintetizar 3 recomendaciones", status: "pending", active_form: "" },
        ],
      },
      status: "pending",
    };

    render(<CardBlock block={block} />);

    // Todo content visible — completed shows raw content, in_progress prefers active_form.
    expect(screen.getByText("Auditar Brand Studio")).toBeInTheDocument();
    expect(screen.getByText("Auditando ofertas")).toBeInTheDocument();
    expect(screen.getByText("Sintetizar 3 recomendaciones")).toBeInTheDocument();

    // Status icons rendered (one per todo).
    expect(screen.getByTestId("todo-completed")).toBeInTheDocument();
    expect(screen.getByTestId("todo-in-progress")).toBeInTheDocument();
    expect(screen.getByTestId("todo-pending")).toBeInTheDocument();

    // Counter shows progress.
    expect(screen.getByText("1/3")).toBeInTheDocument();
  });

  it("renders all-pending plan correctly (initial state)", () => {
    const block: CardBlockType = {
      id: "block-2",
      type: "card",
      card_kind: "plan_card",
      payload: {
        todos: [
          { content: "Step A", status: "pending", active_form: "" },
          { content: "Step B", status: "pending", active_form: "" },
        ],
      },
      status: "pending",
    };

    render(<CardBlock block={block} />);

    expect(screen.getByText("Step A")).toBeInTheDocument();
    expect(screen.getByText("Step B")).toBeInTheDocument();
    expect(screen.getByText("0/2")).toBeInTheDocument();
  });

  it("does NOT crash when payload.todos missing (defensive)", () => {
    const block: CardBlockType = {
      id: "block-3",
      type: "card",
      card_kind: "plan_card",
      payload: {},
      status: "pending",
    };

    expect(() => render(<CardBlock block={block} />)).not.toThrow();
    expect(screen.getByText("0/0")).toBeInTheDocument();
  });
});
