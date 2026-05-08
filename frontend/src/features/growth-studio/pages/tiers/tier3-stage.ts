/**
 * Tier 3 — Full stage detail (DB query + cache write, loads on demand).
 *
 * Wrapper re-export from the canonical hook location for the 4-tier
 * progressive loading contract. Consumers should import from this
 * canonical path instead of the hooks directly.
 *
 * Canonical location: features/growth-studio/pages/tiers/tier3-stage.ts
 * Source hook:        features/growth-studio/hooks/use-stage-detail.ts
 *
 * @deprecated Import from this canonical path. The source hooks at
 * `hooks/use-stage-detail.ts` are marked for 1-ciclo deprecation
 * once all stage-detail consumers adopt the tier-named import.
 */
export {
  useAttractionDetail as useTier3AttractionDetail,
  useCaptureDetail as useTier3CaptureDetail,
  useNurtureDetail as useTier3NurtureDetail,
  useOpportunityDetail as useTier3OpportunityDetail,
  useSalesDetail as useTier3SalesDetail,
  useAdoptionDetail as useTier3AdoptionDetail,
  useExpansionDetail as useTier3ExpansionDetail,
  useEvangelizationDetail as useTier3EvangelizationDetail,
  useStageTimeSeries as useTier3StageTimeSeries,
} from "../../hooks/use-stage-detail";
