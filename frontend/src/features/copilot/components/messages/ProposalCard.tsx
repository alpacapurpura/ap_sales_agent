"use client";

import { useAuth } from "@clerk/nextjs";
import { Check, X, Pencil, AlertTriangle, ChevronDown, ChevronRight } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";

import {
  applyCopilotMutations,
  fetchAppliedMutations,
  reportCopilotEvent,
  type ApplyMutationsResult,
} from "../../api/copilot-api";
import { useCopilotStore } from "../../store/copilot-store";

import { ProposalValuePreview } from "./ProposalValuePreview";

import type { ProposalUpdate } from "../../store/copilot-store";

interface ProposalCardProps {
  updates: ProposalUpdate[];
  /**
   * Assistant message id that emitted this proposal. Used as the
   * idempotency natural key in the ``/mutations/apply`` fallback so
   * repeated clicks do not insert duplicate journal rows.
   */
  messageId?: string;
}

type FieldStatus = "pending" | "applying" | "applied" | "rejected" | "failed";

interface FieldState {
  status: FieldStatus;
  errorMsg: string | null;
}

const COLLAPSE_THRESHOLD = 2;

interface ContainerColorInput {
  allApplied: boolean;
  allRejected: boolean;
  failedCount: number;
}

function pickContainerColor(input: ContainerColorInput): string {
  if (input.allApplied) {
    return "border-green-200 bg-green-50/50 dark:border-green-800 dark:bg-green-900/20";
  }
  if (input.allRejected) {
    return "border-slate-200 bg-slate-50/50 opacity-70 dark:border-slate-700 dark:bg-slate-800/40";
  }
  if (input.failedCount > 0) {
    return "border-red-300 bg-red-50/60 dark:border-red-800 dark:bg-red-900/20";
  }
  return "border-purple-200 bg-purple-50/50 dark:border-purple-800 dark:bg-purple-900/20";
}

function pickPrimaryButtonLabel(failedCount: number, totalUpdates: number): string {
  if (failedCount > 0) return "Reintentar";
  if (totalUpdates === 1) return "Aceptar";
  return "Aceptar todos";
}

/**
 * Sprint 1 (Opción C) — collapsable hybrid + per-field + batch.
 *
 * Renders a proposal of N field changes. For N >= 2 the list defaults
 * to collapsed (header + counts + batch buttons) and exposes a "Ver
 * detalles" toggle to reveal per-field rows with individual Aceptar /
 * Rechazar affordances. Footer always shows "Aceptar todos" / "Rechazar
 * todos".
 *
 * Persistence: each accepted update is routed through the active
 * form-runtime bridge (so the mounted section sees the patch and
 * autosaves) or, when no bridge is connected, falls back to the
 * backend ``/mutations/apply`` endpoint (FP1). Behaviour matches the
 * canonical ``propose_field_updates`` shape so this component is
 * reusable across all tools that emit ``ui_action.type='proposal'``.
 */
export function ProposalCard({ updates, messageId }: ProposalCardProps) {
  const initialStates = useMemo<Record<string, FieldState>>(
    () =>
      Object.fromEntries(updates.map((u) => [u.field_id, { status: "pending", errorMsg: null }])),
    [updates],
  );
  const [fieldStates, setFieldStates] = useState<Record<string, FieldState>>(initialStates);
  const [expanded, setExpanded] = useState<boolean>(updates.length < COLLAPSE_THRESHOLD);
  const [batchError, setBatchError] = useState<string | null>(null);
  const { getToken } = useAuth();
  const hasRehydratedRef = useRef(false);

  // Rehydrate per-field "applied" state from the mutation journal when the
  // card mounts. Without this the card always re-renders ``pending`` after
  // a refresh — even though the underlying field had been persisted —
  // because React useState does not survive a reload. We only run this
  // once (per messageId) so user clicks afterwards win against any
  // late-arriving journal data.
  useEffect(() => {
    if (hasRehydratedRef.current || !messageId) return;
    hasRehydratedRef.current = true;
    const { conversationId } = useCopilotStore.getState();
    if (!conversationId) return;
    const fieldIds = new Set(updates.map((u) => u.field_id));
    void getToken().then((token) => {
      if (!token) return;
      void fetchAppliedMutations(conversationId, messageId, token).then((entries) => {
        if (!entries || entries.length === 0) return;
        setFieldStates((prev) => {
          const next = { ...prev };
          for (const entry of entries) {
            if (!fieldIds.has(entry.field_path)) continue;
            // Do not stomp on an active rejection or an in-flight click.
            if (next[entry.field_path]?.status !== "pending") continue;
            next[entry.field_path] = { status: "applied", errorMsg: null };
          }
          return next;
        });
      });
    });
  }, [messageId, updates, getToken]);

  const pendingUpdates = updates.filter((u) => fieldStates[u.field_id]?.status === "pending");
  const retryableUpdates = updates.filter((u) => {
    const s = fieldStates[u.field_id]?.status;
    return s === "pending" || s === "failed";
  });
  const appliedCount = Object.values(fieldStates).filter((s) => s.status === "applied").length;
  const rejectedCount = Object.values(fieldStates).filter((s) => s.status === "rejected").length;
  const failedCount = Object.values(fieldStates).filter((s) => s.status === "failed").length;

  const allDone = appliedCount + rejectedCount + failedCount === updates.length;
  const allApplied = appliedCount === updates.length;

  const setStatus = (fieldId: string, status: FieldStatus, errorMsg: string | null = null) => {
    setFieldStates((prev) => ({
      ...prev,
      [fieldId]: { status, errorMsg },
    }));
  };

  interface ApplyOneResult {
    applied: boolean;
    mutationId: string | null;
    path: "bridge" | "fallback";
  }

  const errMsg = (err: unknown): string =>
    err instanceof Error ? err.message : "No se pudo aplicar la propuesta. Reintenta.";

  const applyViaBridge = async (update: ProposalUpdate): Promise<ApplyOneResult | null> => {
    const bridge = useCopilotStore.getState().activeBridge;
    const snap = bridge?.getSnapshot();
    if (!bridge || !snap) return null;

    // Backend tools (extract_document_to_fields, propose_field_updates)
    // emit ``field_id`` as the canonical dot-notation path matching the
    // schema's ``path`` (e.g. "demographics.age_range"). The schema's
    // ``id`` is the short last-segment label ("age_range"), so matching
    // by ``id`` only worked when both happened to be equal (brand). For
    // buyer_persona / offer the two diverge — match by ``path`` is the
    // canonical key, with ``id`` as a legacy compat fallback.
    const target = update.field_id;
    const field =
      snap.schema.fields.find((f) => f.path === target) ??
      snap.schema.fields.find((f) => f.id === target);
    if (!field) return null;

    try {
      await bridge.patchField(field.path, update.new_value);
      setStatus(update.field_id, "applied");
      // Best-effort journal echo so the next refresh repaints "applied"
      // for this field. The bridge already drove the form-runtime save,
      // so the per-domain handler will be a no-op for buyer_persona /
      // offer (no handler) and an idempotent re-write for brand.
      void echoJournal(update);
      return { applied: true, mutationId: null, path: "bridge" };
    } catch (err) {
      setStatus(update.field_id, "failed", errMsg(err));
      return { applied: false, mutationId: null, path: "bridge" };
    }
  };

  const echoJournal = async (update: ProposalUpdate): Promise<void> => {
    const { conversationId } = useCopilotStore.getState();
    if (!conversationId || !messageId) return;
    try {
      const token = await getToken();
      if (!token) return;
      await applyCopilotMutations(
        conversationId,
        messageId,
        [{ field_id: update.field_id, new_value: update.new_value, reason: update.reason }],
        token,
      );
    } catch {
      // Journal echo is best-effort. A failure here would only mean the
      // next refresh cannot rehydrate "applied" for this field — the
      // user-facing write already succeeded via the bridge.
    }
  };

  const applyViaFallback = async (update: ProposalUpdate): Promise<ApplyOneResult> => {
    setStatus(update.field_id, "applying");
    try {
      const token = await getToken();
      if (!token) throw new Error("missing_token");
      const { conversationId } = useCopilotStore.getState();
      if (!conversationId) throw new Error("missing_conversation");
      if (!messageId) throw new Error("missing_message_id");

      const result: ApplyMutationsResult = await applyCopilotMutations(
        conversationId,
        messageId,
        [{ field_id: update.field_id, new_value: update.new_value, reason: update.reason }],
        token,
      );

      if (result.rejected.length > 0 || result.applied.length === 0) {
        setStatus(
          update.field_id,
          "failed",
          result.rejected[0]?.reason ?? "No se pudo aplicar la propuesta. Reintenta.",
        );
        return { applied: false, mutationId: null, path: "fallback" };
      }
      setStatus(update.field_id, "applied");
      return {
        applied: true,
        mutationId: result.applied[0]?.id ?? null,
        path: "fallback",
      };
    } catch (err) {
      setStatus(update.field_id, "failed", errMsg(err));
      return { applied: false, mutationId: null, path: "fallback" };
    }
  };

  const applyOne = async (update: ProposalUpdate): Promise<ApplyOneResult> => {
    const viaBridge = await applyViaBridge(update);
    if (viaBridge) return viaBridge;
    return applyViaFallback(update);
  };

  interface AcceptEventPayload {
    field_count: number;
    field_ids: string[];
    path: "bridge" | "fallback" | "mixed";
    mutation_ids?: string[];
  }

  const reportAccept = (payload: AcceptEventPayload) => {
    void getToken().then((token) => {
      if (token) {
        reportCopilotEvent(
          "proposal_accepted",
          payload as unknown as Record<string, unknown>,
          token,
        );
      }
    });
  };

  const accumulateBatch = async (targets: ProposalUpdate[]) => {
    const acceptedFieldIds: string[] = [];
    const mutationIds: string[] = [];
    const pathsUsed = new Set<"bridge" | "fallback">();
    for (const update of targets) {
      const res = await applyOne(update);
      if (res.applied) {
        acceptedFieldIds.push(update.field_id);
        if (res.mutationId) mutationIds.push(res.mutationId);
      }
      pathsUsed.add(res.path);
    }
    return { acceptedFieldIds, mutationIds, pathsUsed };
  };

  const inferAggregatePath = (
    pathsUsed: Set<"bridge" | "fallback">,
  ): "bridge" | "fallback" | "mixed" => {
    if (pathsUsed.size > 1) return "mixed";
    return pathsUsed.has("bridge") ? "bridge" : "fallback";
  };

  const handleAcceptAll = async () => {
    setBatchError(null);
    // Retry semantics: include both pending and previously failed updates
    // so the same button serves "Aceptar todos" and "Reintentar".
    const targets = updates.filter((u) => {
      const s = fieldStates[u.field_id]?.status;
      return s === "pending" || s === "failed";
    });
    if (targets.length === 0) return;

    const { acceptedFieldIds, mutationIds, pathsUsed } = await accumulateBatch(targets);
    if (acceptedFieldIds.length === 0) return;

    const payload: AcceptEventPayload = {
      field_count: acceptedFieldIds.length,
      field_ids: acceptedFieldIds,
      path: inferAggregatePath(pathsUsed),
    };
    if (mutationIds.length > 0) payload.mutation_ids = mutationIds;
    reportAccept(payload);
  };

  const handleAcceptOne = async (update: ProposalUpdate) => {
    const res = await applyOne(update);
    if (!res.applied) return;
    const payload: AcceptEventPayload = {
      field_count: 1,
      field_ids: [update.field_id],
      path: res.path,
    };
    if (res.mutationId) payload.mutation_ids = [res.mutationId];
    reportAccept(payload);
  };

  const handleRejectOne = (update: ProposalUpdate) => {
    setStatus(update.field_id, "rejected");
    void getToken().then((token) => {
      if (token) {
        reportCopilotEvent(
          "proposal_rejected",
          { field_count: 1, field_ids: [update.field_id] },
          token,
        );
      }
    });
  };

  const handleRejectAll = () => {
    const targets = pendingUpdates.map((u) => u.field_id);
    if (targets.length === 0) return;
    setFieldStates((prev) => {
      const next = { ...prev };
      for (const id of targets) {
        next[id] = { status: "rejected", errorMsg: null };
      }
      return next;
    });
    void getToken().then((token) => {
      if (token) {
        reportCopilotEvent(
          "proposal_rejected_batch",
          { field_count: targets.length, field_ids: targets },
          token,
        );
      }
    });
  };

  const containerColor = pickContainerColor({
    allApplied,
    allRejected: allDone && rejectedCount === updates.length,
    failedCount,
  });

  return (
    <div className={`my-1 rounded-xl border p-3 text-sm transition-colors ${containerColor}`}>
      <div className="mb-2 flex items-center gap-1.5">
        <Pencil className="h-3.5 w-3.5 text-purple-500" />
        <span className="font-medium text-slate-700 dark:text-slate-200">
          Propuesta — {updates.length} {updates.length === 1 ? "campo" : "campos"}
        </span>
        <span className="ml-auto flex items-center gap-2 text-xs text-slate-500">
          {appliedCount > 0 && (
            <span className="text-green-600">
              Aplicado{appliedCount > 1 ? `s (${appliedCount})` : ""}
            </span>
          )}
          {rejectedCount > 0 && (
            <span className="text-slate-400">
              Rechazado{rejectedCount > 1 ? `s (${rejectedCount})` : ""}
            </span>
          )}
          {failedCount > 0 && (
            <span className="flex items-center gap-1 text-red-600">
              <AlertTriangle className="h-3 w-3" />
              No se pudo aplicar
            </span>
          )}
          {!allDone &&
            pendingUpdates.length > 0 &&
            appliedCount === 0 &&
            rejectedCount === 0 &&
            failedCount === 0 &&
            updates.length > 1 && <span>{pendingUpdates.length} pendientes</span>}
        </span>
      </div>

      {updates.length >= COLLAPSE_THRESHOLD && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="mb-2 flex items-center gap-1 text-xs text-purple-600 hover:underline dark:text-purple-300"
          aria-expanded={expanded}
        >
          {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          {expanded ? "Ocultar detalles" : "Ver detalles"}
        </button>
      )}

      {expanded && (
        <div className="space-y-1.5">
          {updates.map((update) => {
            const state = fieldStates[update.field_id] ?? { status: "pending", errorMsg: null };
            return (
              <div
                key={update.field_id}
                className={`rounded-lg bg-white/60 px-2.5 py-1.5 dark:bg-slate-900/40 ${
                  state.status === "applied" ? "ring-1 ring-green-300" : ""
                } ${state.status === "rejected" ? "opacity-60" : ""} ${
                  state.status === "failed" ? "ring-1 ring-red-300" : ""
                }`}
              >
                <div className="flex items-start gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
                      {update.field_id}
                    </div>
                    <div className="mt-0.5 text-slate-800 dark:text-slate-200">
                      <ProposalValuePreview value={update.new_value} />
                    </div>
                    {update.reason && (
                      <div className="mt-0.5 text-[11px] italic text-slate-400">
                        {update.reason}
                      </div>
                    )}
                    {state.status === "failed" && state.errorMsg && (
                      <div
                        role="alert"
                        className="mt-1 rounded-md border border-red-200 bg-red-50 px-2 py-1 text-[11px] text-red-700 dark:border-red-700 dark:bg-red-900/30 dark:text-red-200"
                      >
                        {state.errorMsg}
                      </div>
                    )}
                  </div>
                  {updates.length >= COLLAPSE_THRESHOLD &&
                    (state.status === "pending" || state.status === "failed") && (
                      <div className="flex shrink-0 gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            void handleAcceptOne(update);
                          }}
                          className="h-6 px-2 text-[11px] text-green-700 hover:bg-green-100 dark:text-green-300 dark:hover:bg-green-900/30"
                        >
                          <Check className="mr-0.5 h-3 w-3" />
                          Aceptar
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleRejectOne(update)}
                          className="h-6 px-2 text-[11px] text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                        >
                          <X className="mr-0.5 h-3 w-3" />
                          Rechazar
                        </Button>
                      </div>
                    )}
                  {updates.length >= COLLAPSE_THRESHOLD && state.status === "applied" && (
                    <span className="shrink-0 text-[11px] text-green-600">Aplicado</span>
                  )}
                  {updates.length >= COLLAPSE_THRESHOLD && state.status === "rejected" && (
                    <span className="shrink-0 text-[11px] text-slate-400">Rechazado</span>
                  )}
                  {updates.length >= COLLAPSE_THRESHOLD && state.status === "applying" && (
                    <span className="shrink-0 text-[11px] text-purple-500">Aplicando…</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {batchError && (
        <div
          role="alert"
          className="mt-2 rounded-md border border-red-200 bg-red-50 px-2 py-1.5 text-xs text-red-700 dark:border-red-700 dark:bg-red-900/30 dark:text-red-200"
        >
          {batchError}
        </div>
      )}

      {retryableUpdates.length > 0 && (
        <div className="mt-2.5 flex flex-wrap gap-2">
          <Button
            size="sm"
            onClick={() => {
              void handleAcceptAll();
            }}
            disabled={retryableUpdates.length === 0}
            className="h-7 bg-purple-600 px-3 text-xs text-white hover:bg-purple-700"
          >
            <Check className="mr-1 h-3 w-3" />
            {pickPrimaryButtonLabel(failedCount, updates.length)}
          </Button>
          {pendingUpdates.length > 0 && (
            <Button
              size="sm"
              variant="ghost"
              onClick={handleRejectAll}
              className="h-7 px-3 text-xs text-slate-500 hover:text-slate-700"
            >
              <X className="mr-1 h-3 w-3" />
              {updates.length === 1 ? "Rechazar" : "Rechazar todos"}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
