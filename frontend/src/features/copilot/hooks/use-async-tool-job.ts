"use client";

import { useAuth } from "@clerk/nextjs";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useRef } from "react";
import { toast } from "sonner";
import { useShallow } from "zustand/react/shallow";

import { pollJobStatus } from "@/lib/api/ai-actions";

import { JOB_INVALIDATION_MAP } from "../lib/job-invalidation-map";
import { useCopilotStore } from "../store/copilot-store";

import { useTabNotificationPermission } from "./use-tab-notification-permission";

import type { AsyncJobState } from "../store/copilot-store";

// ── Constants ────────────────────────────────────────────────────────────────

/** Initial polling interval in milliseconds (0s–60s: tight loop). */
const POLL_INTERVAL_FAST_MS = 2_000;
/** Medium interval (60s–180s: user still watching, waves land). */
const POLL_INTERVAL_SLOW_MS = 5_000;
/** Idle interval (180s+: long offer extractions, don't burn cycles). */
const POLL_INTERVAL_IDLE_MS = 15_000;
/** After this much elapsed time, switch from fast (2s) to slow (5s). */
const BACKOFF_THRESHOLD_MS = 60_000;
/** After this much elapsed time, switch from slow (5s) to idle (15s). */
const IDLE_THRESHOLD_MS = 180_000;
/**
 * Stop polling entirely after this much time (safety cap for orphan jobs).
 *
 * Raised from 120s → 600s: offer narrative extraction runs 3 waves with
 * 6 LLM calls total and often exceeds 2 min. The loop exits early anyway
 * on terminal status (``completed``/``failed``), so the cap only matters
 * for runaway workers that never write a terminal status to Redis.
 */
const MAX_POLL_DURATION_MS = 600_000;

function pickPollInterval(elapsedMs: number): number {
  if (elapsedMs >= IDLE_THRESHOLD_MS) return POLL_INTERVAL_IDLE_MS;
  if (elapsedMs >= BACKOFF_THRESHOLD_MS) return POLL_INTERVAL_SLOW_MS;
  return POLL_INTERVAL_FAST_MS;
}

// ── Selectors ────────────────────────────────────────────────────────────────

/** Returns the job state for a given job id, or undefined if not tracked. */
export function useAsyncToolJob(jobId: string): AsyncJobState | undefined {
  usePollingForJob(jobId);
  return useCopilotStore((s) => s.activeJobs[jobId]);
}

/**
 * Returns all currently tracked jobs.
 *
 * Uses `useShallow` so the returned array is referentially stable across
 * renders when the underlying `activeJobs` map has not changed — required
 * to prevent React's "getSnapshot should be cached" infinite-render loop.
 */
export function useActiveJobs(): AsyncJobState[] {
  return useCopilotStore(useShallow((s) => Object.values(s.activeJobs)));
}

/**
 * Returns tracked jobs filtered by module.
 *
 * Subscribes with `useShallow` to the raw `activeJobs` map so unchanged
 * references are reused, then filters inside a `useMemo` keyed on that
 * stable reference. Without this, the selector would build a new array on
 * every store snapshot and trigger the infinite-render loop documented in
 * Zustand's FAQ.
 */
export function useActiveJobsForModule(module: string): AsyncJobState[] {
  const jobs = useCopilotStore(useShallow((s) => Object.values(s.activeJobs)));
  return useMemo(() => jobs.filter((j) => j.module === module), [jobs, module]);
}

// ── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Dispatch a ``copilot:field-update`` event for each newly filled field.
 *
 * Mutates ``knownFields`` in place so the next poll only fires for genuinely
 * new ids. ``newValue: null`` is a "field arrived" signal — the form pulls
 * the actual value from a React Query cache invalidated at job terminal.
 */
function dispatchNewFields(filledFields: string[], knownFields: Set<string>): void {
  const fresh = filledFields.filter((f) => !knownFields.has(f));
  for (const fieldId of fresh) {
    knownFields.add(fieldId);
    window.dispatchEvent(
      new CustomEvent("copilot:field-update", {
        detail: { fieldId, newValue: null },
      }),
    );
  }
}

/**
 * Invalidate caches that must refresh every time a new section completes.
 *
 * Two caches are touched on every newly-completed section:
 *
 *  1. Conversation detail (``["copilot", "conversation", id]``) — the worker
 *     subscriber inserts a nav pill into the conversation; without refetching
 *     here the pill only appears after the terminal invalidation bunches
 *     everything at the end.
 *  2. Module queries (``JOB_INVALIDATION_MAP[module]``, e.g.
 *     ``["brand-settings"]``) — the wave persists its subset to the DB before
 *     announcing, so the studio form must refetch to show the freshly
 *     extracted data when the user clicks the pill mid-extraction.
 */
interface InvalidateOnNewSectionsArgs {
  sectionsCompleted: string[];
  knownSections: Set<string>;
  conversationId: string | null | undefined;
  queryClient: ReturnType<typeof useQueryClient>;
  module: string;
}

function invalidateOnNewSections({
  sectionsCompleted,
  knownSections,
  conversationId,
  queryClient,
  module,
}: InvalidateOnNewSectionsArgs): void {
  const fresh = sectionsCompleted.filter((s) => !knownSections.has(s));
  if (fresh.length === 0 || !conversationId) return;
  for (const s of fresh) knownSections.add(s);
  // ``invalidateQueries`` alone relies on an active observer refetching the
  // stale key. In practice the conversation detail query can be idle for the
  // poll window if the user scrolled away, so ``refetchQueries`` forces the
  // hit regardless of subscriber state — pills need to land as soon as the
  // worker writes them.
  void queryClient.invalidateQueries({
    queryKey: ["copilot", "conversation", conversationId],
    refetchType: "all",
  });
  void queryClient.refetchQueries({
    queryKey: ["copilot", "conversation", conversationId],
    type: "active",
  });
  // Refresh module queries (brand-settings, etc.) so the studio form picks up
  // the section the worker just persisted — without waiting for job terminal.
  const moduleKeys = JOB_INVALIDATION_MAP[module] ?? [];
  for (const queryKey of moduleKeys) {
    void queryClient.invalidateQueries({ queryKey: [...queryKey] });
  }
}

// ── Internal polling hook ────────────────────────────────────────────────────

/**
 * Starts a polling loop for the given job. The loop:
 * - Fires every 2s for the first 60s, 5s for 60s–180s, then 15s up to a
 *   600s (10min) safety cap — offer narrative extraction runs ~3–4 min
 *   across 3 waves and needs coverage beyond the old 120s cap.
 * - On each response, diffs `filled_fields` and dispatches
 *   `copilot:field-update` for each newly arrived field.
 * - On terminal status, invalidates React Query keys per JOB_INVALIDATION_MAP.
 * - On terminal status + `document.hidden`, fires a tab-blur notification.
 * - Stops automatically on unmount or terminal status.
 *
 * Design note: Field values are not available in the poll payload (only field
 * ids are known at poll time). We dispatch the event with `value: null` as a
 * "field arrived" signal. The form's React Query cache will serve fresh data
 * after the keys are invalidated on completion. This is the simplest approach
 * that avoids a second round-trip from the hook.
 */
function usePollingForJob(jobId: string): void {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const { requestIfNeeded, isGranted } = useTabNotificationPermission();

  const stopRef = useRef(false);
  const startedAtRef = useRef<number>(Date.now());
  const knownFieldsRef = useRef<Set<string>>(new Set());
  const knownSectionsRef = useRef<Set<string>>(new Set());
  const titleRestoredRef = useRef(false);

  // Read job state directly from the store (without subscribing — we're
  // managing the loop ourselves, not re-rendering on every poll).
  const getJob = (): AsyncJobState | undefined => useCopilotStore.getState().activeJobs[jobId];

  useEffect(() => {
    const job = getJob();
    if (!job) return;

    // Don't start polling if already in a terminal state
    const isTerminal = (s: string) => s === "completed" || s === "failed";
    if (isTerminal(job.status)) return;

    stopRef.current = false;
    startedAtRef.current = Date.now();
    knownFieldsRef.current = new Set(job.filledFields);
    knownSectionsRef.current = new Set(job.sectionsCompleted);
    titleRestoredRef.current = false;

    // Request notification permission on first job start (non-blocking)
    void requestIfNeeded();

    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    const scheduleNextPoll = (): void => {
      const elapsed = Date.now() - startedAtRef.current;

      if (elapsed >= MAX_POLL_DURATION_MS) {
        // Safety cap — stop polling
        return;
      }

      const interval = pickPollInterval(elapsed);

      timeoutId = setTimeout(() => {
        void runPoll();
      }, interval);
    };

    const runPoll = async (): Promise<void> => {
      if (stopRef.current) return;

      const currentJob = getJob();
      if (!currentJob) return;
      if (isTerminal(currentJob.status)) return;

      let token: string | null = null;
      try {
        token = await getToken();
      } catch {
        // Auth failure — reschedule and try again
        scheduleNextPoll();
        return;
      }
      if (!token) {
        scheduleNextPoll();
        return;
      }

      let statusData;
      try {
        statusData = await pollJobStatus(currentJob.pollEndpoint, token);
      } catch {
        // Network error — reschedule
        if (!stopRef.current) scheduleNextPoll();
        return;
      }

      if (stopRef.current) return;

      const {
        status,
        progress = 0,
        stage = "",
        filled_fields: filledFields = [],
        filled_fields_by_section: filledFieldsBySection = {},
        sections_touched: sectionsTouched = [],
        sections_completed: sectionsCompleted = [],
        finished_at: finishedAtIso,
        error,
      } = statusData;

      dispatchNewFields(filledFields, knownFieldsRef.current);
      invalidateOnNewSections({
        sectionsCompleted,
        knownSections: knownSectionsRef.current,
        conversationId: currentJob.conversationId,
        queryClient,
        module: currentJob.module,
      });

      const patch: Partial<AsyncJobState> = {
        status: status as AsyncJobState["status"],
        progress,
        stage,
        filledFields,
        filledFieldsBySection,
        sectionsTouched,
        sectionsCompleted,
        ...(error ? { error: String(error) } : {}),
        ...(finishedAtIso ? { finishedAt: new Date(finishedAtIso).getTime() } : {}),
      };

      if (isTerminal(status)) {
        handleTerminal(status, patch, currentJob);
        return;
      }

      useCopilotStore.getState().updateJob(jobId, patch);

      if (!stopRef.current) scheduleNextPoll();
    };

    const handleTerminal = (
      status: string,
      patch: Partial<AsyncJobState>,
      currentJob: AsyncJobState,
    ): void => {
      useCopilotStore.getState().completeJob(jobId, patch);
      // Safety-net refresh: mid-extraction section completions already invalidate
      // module queries via ``invalidateOnNewSections``. This terminal call covers
      // the tail case where the final poll returns terminal status with no prior
      // section delta — without it, the last extracted section could miss a
      // refresh.
      invalidateModuleQueries(currentJob.module);
      // The worker inserts summary + navigation cards into the conversation
      // as the last step of the job. Refetch the conversation detail so the
      // chat renders them.
      if (currentJob.conversationId) {
        void queryClient.invalidateQueries({
          queryKey: ["copilot", "conversation", currentJob.conversationId],
        });
      }
      if (document.hidden) fireTabBlurNotification(status, currentJob.sourceRef);
      stopRef.current = true;
    };

    const invalidateModuleQueries = (module: string): void => {
      const keysToInvalidate = JOB_INVALIDATION_MAP[module] ?? [];
      for (const queryKey of keysToInvalidate) {
        void queryClient.invalidateQueries({ queryKey: [...queryKey] });
      }
    };

    const fireTabBlurNotification = (status: string, sourceRef: string): void => {
      const label = status === "completed" ? "Extracción lista" : "Extracción fallida";
      const body =
        status === "completed"
          ? `Se completó el análisis de ${sourceRef}`
          : `Ocurrió un error al analizar ${sourceRef}`;

      toast.success(`Nicolify — ${label}`, {
        description: body,
        duration: Infinity,
        dismissible: true,
      });

      if (isGranted()) {
        try {
          new Notification(`Nicolify — ${label}`, { body });
        } catch {
          // Notification can throw if permission revoked between check and fire
        }
      }

      if (!titleRestoredRef.current) {
        const originalTitle = document.title;
        document.title = `(1) Nicolify — ${label}`;
        const restoreTitle = (): void => {
          if (document.visibilityState === "visible") {
            document.title = originalTitle;
            titleRestoredRef.current = true;
            document.removeEventListener("visibilitychange", restoreTitle);
          }
        };
        document.addEventListener("visibilitychange", restoreTitle);
      }
    };

    // Kick off
    scheduleNextPoll();

    return () => {
      stopRef.current = true;
      if (timeoutId !== null) clearTimeout(timeoutId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Intentionally stable: jobId controls the loop lifecycle
  }, [jobId]);
}

// Re-export the type so consumers don't need to import from the store
export type { AsyncJobState };
