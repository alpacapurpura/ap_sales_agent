"use client";

import { useAuth } from "@clerk/nextjs";
import { Check, X, Pencil, AlertTriangle } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

import {
  applyCopilotMutations,
  reportCopilotEvent,
  type ApplyMutationsResult,
} from "../../api/copilot-api";
import { useCopilotStore } from "../../store/copilot-store";

import type { ProposalUpdate } from "../../store/copilot-store";

interface ProposalCardProps {
  updates: ProposalUpdate[];
  /**
   * The assistant message id that emitted this proposal. Used as the
   * idempotency natural key in the ``/mutations/apply`` fallback so
   * repeated clicks do not insert duplicate journal rows.
   */
  messageId?: string;
}

type ProposalStatus = "pending" | "applying" | "applied" | "rejected" | "failed";

/**
 * Renders a proposal from the AI with field changes. The user can apply or
 * reject the entire proposal. "Aplicar" routes each update through the
 * active form-runtime bridge so the mounted section sees the patch and
 * autosaves. When no bridge is connected, the card falls back to the
 * backend ``/mutations/apply`` endpoint so the change is persisted server
 * side and reflected after a page reload (B22-FP1).
 */
export function ProposalCard({ updates, messageId }: ProposalCardProps) {
  const [status, setStatus] = useState<ProposalStatus>("pending");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const { getToken } = useAuth();

  const fieldIds = updates.map((u) => u.field_id);

  const handleApply = async () => {
    setErrorMsg(null);
    const bridge = useCopilotStore.getState().activeBridge;
    const snap = bridge?.getSnapshot();

    if (bridge && snap) {
      // Happy path: section mounted → patch via bridge + feature autosave.
      for (const update of updates) {
        const field = snap.schema.fields.find((f) => f.id === update.field_id);
        if (field) {
          void bridge.patchField(field.path, update.new_value);
        }
      }
      setStatus("applied");
      void getToken().then((token) => {
        if (token) {
          reportCopilotEvent(
            "proposal_accepted",
            {
              field_count: updates.length,
              field_ids: fieldIds,
              path: "bridge",
            },
            token,
          );
        }
      });
      return;
    }

    // Fallback path: no bridge connected → POST to backend.
    setStatus("applying");
    try {
      const token = await getToken();
      if (!token) {
        throw new Error("missing_token");
      }
      const { conversationId } = useCopilotStore.getState();
      if (!conversationId) {
        throw new Error("missing_conversation");
      }
      if (!messageId) {
        throw new Error("missing_message_id");
      }
      const result: ApplyMutationsResult = await applyCopilotMutations(
        conversationId,
        messageId,
        updates.map((u) => ({
          field_id: u.field_id,
          new_value: u.new_value,
          reason: u.reason,
        })),
        token,
      );

      if (result.rejected.length > 0 || result.applied.length === 0) {
        setStatus("failed");
        setErrorMsg(result.rejected[0]?.reason ?? "No se pudo aplicar la propuesta. Reintenta.");
        reportCopilotEvent(
          "proposal_apply_failed",
          {
            field_count: updates.length,
            field_ids: fieldIds,
            rejected: result.rejected,
            path: "fallback",
          },
          token,
        );
        return;
      }

      setStatus("applied");
      reportCopilotEvent(
        "proposal_accepted",
        {
          field_count: updates.length,
          field_ids: fieldIds,
          mutation_ids: result.applied.map((r) => r.id),
          path: "fallback",
        },
        token,
      );
    } catch (err) {
      setStatus("failed");
      setErrorMsg(
        err instanceof Error ? err.message : "No se pudo aplicar la propuesta. Reintenta.",
      );
    }
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
            : status === "failed"
              ? "border-red-300 bg-red-50/60 dark:border-red-800 dark:bg-red-900/20"
              : "border-purple-200 bg-purple-50/50 dark:border-purple-800 dark:bg-purple-900/20",
      ].join(" ")}
    >
      <div className="mb-2 flex items-center gap-1.5">
        <Pencil className="h-3.5 w-3.5 text-purple-500" />
        <span className="font-medium text-slate-700 dark:text-slate-200">Propuesta de cambios</span>
        {status === "applied" && <span className="ml-auto text-xs text-green-600">Aplicado</span>}
        {status === "rejected" && <span className="ml-auto text-xs text-slate-400">Rechazado</span>}
        {status === "applying" && (
          <span className="ml-auto text-xs text-purple-500">Aplicando…</span>
        )}
        {status === "failed" && (
          <span className="ml-auto flex items-center gap-1 text-xs text-red-600">
            <AlertTriangle className="h-3 w-3" />
            No se pudo aplicar
          </span>
        )}
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

      {status === "failed" && errorMsg && (
        <div
          role="alert"
          className="mt-2 rounded-md border border-red-200 bg-red-50 px-2 py-1.5 text-xs text-red-700 dark:border-red-700 dark:bg-red-900/30 dark:text-red-200"
        >
          {errorMsg}
        </div>
      )}

      {(status === "pending" || status === "failed") && (
        <div className="mt-2.5 flex gap-2">
          <Button
            size="sm"
            onClick={() => {
              void handleApply();
            }}
            disabled={status === "failed" && !messageId}
            className="h-7 bg-purple-600 px-3 text-xs text-white hover:bg-purple-700"
          >
            <Check className="mr-1 h-3 w-3" />
            {status === "failed" ? "Reintentar" : "Aplicar"}
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
