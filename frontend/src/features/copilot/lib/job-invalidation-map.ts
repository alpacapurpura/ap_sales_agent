/**
 * Maps copilot async job modules to React Query keys to invalidate on completion.
 * SSoT for cache invalidation — referenced by useAsyncToolJob.
 * See FLOW-SPEC.md §3.5.
 */
export const JOB_INVALIDATION_MAP: Record<string, readonly (readonly string[])[]> = {
  brand: [["brand-settings"], ["brand-sections"]],
  offer: [["offer"]],
  asset: [["assets"]],
  persona: [["personas"]],
} as const;
