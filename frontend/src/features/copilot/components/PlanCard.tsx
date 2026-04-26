"use client";

import { Check, Circle, Loader2 } from "lucide-react";
import { forwardRef } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

import type { PlanCardData, PlanCardTodo } from "../types/message-blocks";

interface PlanCardProps extends React.HTMLAttributes<HTMLDivElement> {
  data: PlanCardData;
}

function StatusIcon({ status }: { status: PlanCardTodo["status"] }) {
  if (status === "completed") {
    return (
      <Check className="h-3.5 w-3.5 text-green-600 mt-0.5 shrink-0" data-testid="todo-completed" />
    );
  }
  if (status === "in_progress") {
    return (
      <Loader2
        className="h-3.5 w-3.5 text-primary mt-0.5 shrink-0 animate-spin"
        data-testid="todo-in-progress"
      />
    );
  }
  return (
    <Circle
      className="h-3.5 w-3.5 text-muted-foreground/60 mt-0.5 shrink-0"
      data-testid="todo-pending"
    />
  );
}

/**
 * Card emitted by the deep-agent harness when ``write_todos`` runs.
 * Shows a multi-step plan with live status transitions
 * (pending → in_progress → completed). Informational — no user approval.
 *
 * # [COPILOT-PLAN-CARD-B18-TP9] → docs/domains/copilot/testing-2026-04/results/TP9-2026-04-26.md
 */
export const PlanCard = forwardRef<HTMLDivElement, PlanCardProps>(
  ({ data, className, ...props }, ref) => {
    const todos = Array.isArray(data?.todos) ? data.todos : [];
    const completed = todos.filter((t) => t.status === "completed").length;
    const total = todos.length;

    return (
      <Card ref={ref} className={cn("w-full border-border", className)} {...props}>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-semibold">Plan</CardTitle>
          <span className="text-xs text-muted-foreground tabular-nums">
            {completed}/{total}
          </span>
        </CardHeader>

        <CardContent className="pb-3">
          <ul className="space-y-1.5">
            {todos.map((todo, idx) => (
              <li
                key={`${idx}-${todo.content}`}
                className={cn(
                  "flex items-start gap-2 text-sm",
                  todo.status === "completed" && "text-muted-foreground line-through",
                  todo.status === "in_progress" && "text-foreground font-medium",
                  todo.status === "pending" && "text-muted-foreground",
                )}
              >
                <StatusIcon status={todo.status} />
                <span>
                  {todo.status === "in_progress" && todo.active_form
                    ? todo.active_form
                    : todo.content}
                </span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    );
  },
);
PlanCard.displayName = "PlanCard";
