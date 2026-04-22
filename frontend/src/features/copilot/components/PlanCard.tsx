"use client";

import { CheckCircle, XCircle } from "lucide-react";
import { forwardRef } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

import { TierChip } from "./TierChip";

// ── Types ────────────────────────────────────────────────────────────

interface PlanStep {
  order: number;
  label: string;
  toolName: string;
  estimatedTokens: number;
}

interface PlanCardProps extends React.HTMLAttributes<HTMLDivElement> {
  msgId: string;
  steps: PlanStep[];
  estimatedCostUsd: number;
  status: "pending" | "approved" | "rejected";
  onApprove: () => void;
  onReject: () => void;
}

// ── Component ────────────────────────────────────────────────────────

/**
 * Card rendered when the copilot proposes a multi-step plan.
 * Appears after SSE event `plan_proposed`.
 */
export const PlanCard = forwardRef<HTMLDivElement, PlanCardProps>(
  (
    { msgId: _msgId, steps, estimatedCostUsd, status, onApprove, onReject, className, ...props },
    ref,
  ) => {
    return (
      <Card ref={ref} className={cn("w-full border-border", className)} {...props}>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-semibold">Plan propuesto</CardTitle>
          <TierChip tier="heavy" size="xs" />
        </CardHeader>

        <CardContent className="pb-3">
          <ol className="space-y-1">
            {steps.map((step) => (
              <li key={step.order} className="flex items-start gap-2 text-sm text-muted-foreground">
                <span className="font-mono text-[10px] mt-0.5 text-muted-foreground/60 w-4 shrink-0">
                  {step.order}.
                </span>
                <span>{step.label}</span>
              </li>
            ))}
          </ol>

          <p className="mt-3 text-xs text-muted-foreground">
            Costo estimado:{" "}
            <span className="font-medium text-foreground">~${estimatedCostUsd.toFixed(2)}</span>
          </p>
        </CardContent>

        <CardFooter className="flex gap-2 pt-0">
          {status === "pending" && (
            <>
              <Button variant="outline" size="sm" onClick={onReject} className="flex-1">
                <XCircle className="mr-1.5 h-3.5 w-3.5" />
                Rechazar
              </Button>
              <Button size="sm" onClick={onApprove} className="flex-1">
                <CheckCircle className="mr-1.5 h-3.5 w-3.5" />
                Aplicar
              </Button>
            </>
          )}

          {status === "approved" && (
            <div className="flex items-center gap-1.5 text-sm text-green-700">
              <CheckCircle className="h-4 w-4" />
              <span>Aplicado</span>
            </div>
          )}

          {status === "rejected" && (
            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <XCircle className="h-4 w-4" />
              <span>Rechazado</span>
            </div>
          )}
        </CardFooter>
      </Card>
    );
  },
);
PlanCard.displayName = "PlanCard";
