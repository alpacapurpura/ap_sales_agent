/**
 * Tier 2 — Group detail cache reader (loads per-group on viewport visibility).
 *
 * Wrapper re-export from the canonical hook location for the 4-tier
 * progressive loading contract. Consumers should import from this
 * canonical path instead of the hook directly.
 *
 * Canonical location: features/growth-studio/pages/tiers/tier2-group-detail.ts
 * Source hook:        features/growth-studio/hooks/use-group-detail.ts
 *
 * @deprecated Import from this canonical path. The source hook at
 * `hooks/use-group-detail.ts` is marked for 1-ciclo deprecation
 * once all group-detail consumers adopt the tier-named import.
 */
export { useGroupDetail as useTier2GroupDetail } from "../../hooks/use-group-detail";
