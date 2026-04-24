"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useRef } from "react";

import { fetchActiveJobs } from "../api/copilot-api";
import { useCopilotStore } from "../store/copilot-store";

import type { ActiveJobProgressDTO } from "../api/copilot-api";
import type { AsyncJobState } from "../store/copilot-store";

// ── Helpers ──────────────────────────────────────────────────────────────────

const TERMINAL_STATUSES = new Set(["completed", "failed"]);

/**
 * Narrow a raw module string to the union accepted by AsyncJobState.
 * Falls back to "brand" when the backend returns an unrecognised module.
 */
function toKnownModule(raw: string): AsyncJobState["module"] {
  if (raw === "brand" || raw === "offer" || raw === "asset" || raw === "persona") return raw;
  return "brand";
}

/**
 * Narrow a raw scope string to the union accepted by AsyncJobState.
 */
function toKnownScope(raw: string): AsyncJobState["scope"] {
  if (raw === "full" || raw === "section" || raw === "field" || raw === "visuals") return raw;
  return "full";
}

/**
 * Narrow a raw mode string to the union accepted by AsyncJobState.
 */
function toKnownMode(raw: string): AsyncJobState["mode"] {
  if (raw === "initial" || raw === "update" || raw === "suggest") return raw;
  return "initial";
}

/**
 * Narrow a raw source_kind string to the union accepted by AsyncJobState.
 */
function toKnownSourceKind(raw: string): AsyncJobState["sourceKind"] {
  if (raw === "url" || raw === "doc" || raw === "media") return raw;
  return "url";
}

/**
 * Narrow a raw status string to the union accepted by AsyncJobState.
 * Returns null when the raw value is null/undefined (Redis key expired).
 */
function toKnownStatus(raw: string | null): AsyncJobState["status"] | null {
  if (raw === "queued" || raw === "running" || raw === "completed" || raw === "failed") return raw;
  return null;
}

/**
 * Map an ActiveJobProgressDTO (snake_case, from API) to AsyncJobState
 * (camelCase, for the Zustand store).
 */
function mapDtoToJobState(dto: ActiveJobProgressDTO, conversationId: string): AsyncJobState {
  const status = toKnownStatus(dto.status) ?? "running";
  return {
    jobId: dto.job_id,
    module: toKnownModule(dto.module),
    entityId: dto.entity_id,
    scope: toKnownScope(dto.scope),
    mode: toKnownMode(dto.mode),
    section: null,
    targetLabel: dto.source_ref,
    sourceKind: toKnownSourceKind(dto.source_kind),
    sourceRef: dto.source_ref,
    pollEndpoint: dto.poll_endpoint,
    conversationId,
    status,
    progress: dto.progress ?? 0,
    stage: dto.stage ?? "",
    filledFields: dto.filled_fields,
    filledFieldsBySection: dto.filled_fields_by_section,
    sectionsTouched: dto.sections_touched,
    sectionsCompleted: dto.sections_completed,
    startedAt: new Date(dto.started_at).getTime(),
    finishedAt: dto.finished_at ? new Date(dto.finished_at).getTime() : undefined,
  };
}

// ── Hook ─────────────────────────────────────────────────────────────────────

/**
 * On mount, fetches the conversation's active extraction jobs from the
 * backend and registers each one in the zustand store so that
 * ``ActiveJobsPoller`` resumes its polling loop transparently after a
 * page reload.
 *
 * Idempotent: if the store already tracks a job for the conversation,
 * we skip re-registering it (the local copy is the freshest one).
 *
 * Runs once per ``conversationId`` change. Best-effort — a fetch failure
 * is logged and silently ignored; the user still sees the chat, just
 * without a progress indicator until the job finishes.
 */
export function useHydrateActiveJobs(conversationId: string | null | undefined): void {
  const { getToken } = useAuth();
  // Track per-conversationId whether we already fetched to avoid double-fires
  const hydratedRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!conversationId) return;
    if (hydratedRef.current.has(conversationId)) return;

    hydratedRef.current.add(conversationId);

    const fetchAndRegister = async (): Promise<void> => {
      let token: string | null = null;
      try {
        token = await getToken();
      } catch {
        return;
      }
      if (!token) return;

      const jobs = await fetchActiveJobs(conversationId, token);
      if (!jobs) return;

      const { registerJob, activeJobs } = useCopilotStore.getState();

      for (const dto of jobs) {
        // Skip terminal jobs — they don't need polling
        if (dto.status !== null && TERMINAL_STATUSES.has(dto.status)) continue;

        // Skip jobs already tracked in the store (local state is source of truth)
        if (activeJobs[dto.job_id]) continue;

        registerJob(mapDtoToJobState(dto, conversationId));
      }
    };

    void fetchAndRegister();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Intentional: conversationId controls when to re-fetch; getToken is stable
  }, [conversationId]);
}
