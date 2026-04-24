"use client";

import { memo } from "react";

import { useActiveJobs, useAsyncToolJob } from "../hooks/use-async-tool-job";

import { ToolCallChip } from "./messages/ToolCallChip";

/**
 * Headless poller for a single async extraction job.
 *
 * Calls ``useAsyncToolJob`` which mounts the polling effect. Returns null —
 * this component exists only to host the effect. Isolating one hook per
 * ``jobId`` keeps the effect lifecycle keyed to the job, so completed jobs
 * unmount cleanly and new jobs start their own 2s/5s loop.
 */
const SingleJobPoller = memo(function SingleJobPoller({ jobId }: { jobId: string }) {
  useAsyncToolJob(jobId);
  return null;
});
SingleJobPoller.displayName = "SingleJobPoller";

/**
 * Top-level poller that mounts a ``SingleJobPoller`` per non-terminal active
 * job in the Zustand store, and renders a visible chip per pending job.
 *
 * Rationale: polling must survive conversation re-hydration. Previously it
 * was hosted inside ``ToolCallChip``, which renders from ``message.toolCalls``
 * — an ephemeral client-only field. On idle refetch the server transcript
 * (blocks only, no toolCalls) full-replaces local messages and unmounts the
 * chip, killing both the polling loop and the user-visible status.
 *
 * Moving the chip here decouples progress UI from message rendering: as long
 * as ``registerJob`` populated ``activeJobs``, this component keeps the user
 * informed (tool name + progress + stage + counts) until the job reaches
 * terminal status. Then the visible card lands via the nav pills / extraction
 * summary inserted by the worker into the conversation transcript.
 */
export const ActiveJobsPoller = memo(function ActiveJobsPoller() {
  const jobs = useActiveJobs();
  const pending = jobs.filter((j) => j.status !== "completed" && j.status !== "failed");
  if (pending.length === 0) {
    return null;
  }
  return (
    <div
      data-testid="active-jobs-banner"
      className="flex flex-wrap gap-1.5 border-b border-border/40 bg-muted/20 px-4 py-2"
    >
      {pending.map((j) => (
        <div key={j.jobId} className="flex min-w-[240px] flex-col gap-1">
          <SingleJobPoller jobId={j.jobId} />
          <ToolCallChip tool={`extract_from_${j.sourceKind}`} jobId={j.jobId} status="running" />
        </div>
      ))}
    </div>
  );
});
ActiveJobsPoller.displayName = "ActiveJobsPoller";
