"use client";

import { useMemo } from "react";

import { useActiveJobsForModule } from "./use-async-tool-job";

import type { AsyncJobState } from "../store/copilot-store";

// ── Types ─────────────────────────────────────────────────────────────────────

export type SectionStatus = "idle" | "queued" | "running" | "completed";

export interface SectionStatusEntry {
  /** Extraction lifecycle state for this section. */
  status: SectionStatus;
  /**
   * running → in-flight field count; completed → final count; idle/queued → 0.
   */
  fieldCount: number;
  /** Field ids currently filled (used by hover tooltip). */
  fieldIds?: string[];
}

// ── Helper ────────────────────────────────────────────────────────────────────

/**
 * Derives the status of a single section slug from a list of concurrent jobs.
 * If multiple jobs target the same section, we prefer the highest-priority
 * status (completed > running > queued > idle) and the maximum field count.
 */
function deriveSectionEntry(slug: string, jobs: AsyncJobState[]): SectionStatusEntry {
  let best: SectionStatus = "idle";
  let fieldCount = 0;
  let fieldIds: string[] | undefined;

  const priority: Record<SectionStatus, number> = {
    completed: 3,
    running: 2,
    queued: 1,
    idle: 0,
  };

  for (const job of jobs) {
    const fields = job.filledFieldsBySection[slug] ?? [];
    const isTouched = job.sectionsTouched.includes(slug);
    const isCompleted = job.sectionsCompleted.includes(slug);

    let status: SectionStatus = "idle";
    if (isCompleted) {
      status = "completed";
    } else if (isTouched && fields.length > 0) {
      status = "running";
    } else if (isTouched) {
      status = "queued";
    }

    if (priority[status] > priority[best]) {
      best = status;
    }

    if (fields.length > fieldCount) {
      fieldCount = fields.length;
      fieldIds = fields;
    }
  }

  return {
    status: best,
    fieldCount: best === "idle" || best === "queued" ? 0 : fieldCount,
    fieldIds: best === "running" || best === "completed" ? fieldIds : undefined,
  };
}

// ── Hook ──────────────────────────────────────────────────────────────────────

/**
 * Returns a per-section status map derived from active copilot extraction jobs
 * for the given module. Sections not targeted by any job have status "idle".
 *
 * @param module - The studio module ("brand" | "offer" | "asset" | "persona").
 * @returns A map of section slug → {@link SectionStatusEntry}.
 */
export function useSectionStatus(
  module: "brand" | "offer" | "asset" | "persona",
): Record<string, SectionStatusEntry> {
  const jobs = useActiveJobsForModule(module);

  return useMemo(() => {
    if (jobs.length === 0) return {};

    // Collect every slug mentioned across all jobs
    const allSlugs = new Set<string>();
    for (const job of jobs) {
      for (const slug of job.sectionsTouched) allSlugs.add(slug);
      for (const slug of job.sectionsCompleted) allSlugs.add(slug);
      for (const slug of Object.keys(job.filledFieldsBySection)) allSlugs.add(slug);
    }

    const result: Record<string, SectionStatusEntry> = {};
    for (const slug of allSlugs) {
      result[slug] = deriveSectionEntry(slug, jobs);
    }
    return result;
  }, [jobs]);
}
