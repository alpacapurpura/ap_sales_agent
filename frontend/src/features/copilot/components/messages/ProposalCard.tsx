"use client";

import { useAuth } from "@clerk/nextjs";
import { Check, X, Pencil } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

import { reportCopilotEvent } from "../../api/copilot-api";

import type { ProposalUpdate } from "../../store/copilot-store";

interface ProposalCardProps {
  updates: ProposalUpdate[];
}

type ProposalStatus = "pending" | "applied" | "rejected";

/**
 * Renders a proposal from the AI with field changes.
 * The user can apply or reject the entire proposal.
 * "Aplicar" dispatches copilot:field-update CustomEvents for each field.
 */
export function ProposalCard({ updates }: ProposalCardProps) {
  const [status, setStatus] = useState<ProposalStatus>("pending");
  const { getToken } = useAuth();

  const fieldIds = updates.map((u) => u.field_id);

  const handleApply = () => {
    for (const update of updates) {
      window.dispatchEvent(
        new CustomEvent("copilot:field-update", {
          detail: { fieldId: update.field_id, newValue: update.new_value },
        }),
      );
    }
    setStatus("applied");
    void getToken().then((token) => {
      if (token) {
        reportCopilotEvent(
          "proposal_accepted",
          { field_count: updates.length, field_ids: fieldIds },
          token,
        );
      }
    });
  };

  const handleReject = () => {
    setStatus("rejected");
    void getToken().then((token) => {
      if (token) {
        reportCopilotEvent(
          "proposal_rejected",
          { field_count: updates.length, field_ids: fieldIds },
          token,
        );
      }
    });
  };

  return (
    <div
      className={[
        "my-1 rounded-xl border p-3 text-sm transition-colors",
        status === "applied"
          ? "border-green-200 bg-green-50/50 dark:border-green-800 dark:bg-green-900/20"
          : status === "rejected"
            ? "border-slate-200 bg-slate-50/50 opacity-60 dark:border-slate-700 dark:bg-slate-800/40"
            : "border-purple-200 bg-purple-50/50 dark:border-purple-800 dark:bg-purple-900/20",
      ].join(" ")}
    >
      <div className="mb-2 flex items-center gap-1.5">
        <Pencil className="h-3.5 w-3.5 text-purple-500" />
        <span className="font-medium text-slate-700 dark:text-slate-200">Propuesta de cambios</span>
        {status === "applied" && <span className="ml-auto text-xs text-green-600">Aplicado</span>}
        {status === "rejected" && <span className="ml-auto text-xs text-slate-400">Rechazado</span>}
      </div>

      <div className="space-y-1.5">
        {updates.map((update) => (
          <div
            key={update.field_id}
            className="rounded-lg bg-white/60 px-2.5 py-1.5 dark:bg-slate-900/40"
          >
            <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
              {update.field_id}
            </div>
            <div className="mt-0.5 text-slate-800 dark:text-slate-200">{update.new_value}</div>
            {update.reason && (
              <div className="mt-0.5 text-[11px] italic text-slate-400">{update.reason}</div>
            )}
          </div>
        ))}
      </div>

      {status === "pending" && (
        <div className="mt-2.5 flex gap-2">
          <Button
            size="sm"
            onClick={handleApply}
            className="h-7 bg-purple-600 px-3 text-xs text-white hover:bg-purple-700"
          >
            <Check className="mr-1 h-3 w-3" />
            Aplicar
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={handleReject}
            className="h-7 px-3 text-xs text-slate-500 hover:text-slate-700"
          >
            <X className="mr-1 h-3 w-3" />
            Rechazar
          </Button>
        </div>
      )}
    </div>
  );
}
