/**
 * Tier 1 — Stage overview cache reader (header KPIs + channel list).
 *
 * Wrapper re-export from the canonical hook location for the 4-tier
 * progressive loading contract. Consumers should import from this
 * canonical path instead of the hook directly.
 *
 * Canonical location: features/growth-studio/pages/tiers/tier1-overview.ts
 * Source hook:        features/growth-studio/hooks/use-stage-overview.ts
 *
 * @deprecated Import from this canonical path. The source hook at
 * `hooks/use-stage-overview.ts` is marked for 1-ciclo deprecation
 * once all stage-internal consumers adopt the tier-named import.
 */
export { useStageOverview as useTier1Overview } from "../../hooks/use-stage-overview";
