/**
 * Growth-studio action registry bootstrap.
 *
 * Registers every action key produced by the growth-studio copilot module.
 * Keys use the "growth." namespace to avoid collisions with other studios.
 *
 * Side-effect import: features/growth-studio/schemas/index.ts imports this
 * module so every schema consumer also bootstraps actions transitively —
 * no per-page side-effect imports required.
 *
 * Mirrors brand-studio registry pattern (see features/brand-studio/actions/registry.ts).
 */
import { hasAction, registerAction, type ActionComponent } from "@/lib/form-runtime/actions";

import { ChannelOverviewAction } from "./ChannelOverviewAction";
import { ETLConfirmAction } from "./ETLConfirmAction";
import { ETLRateLimitedAction } from "./ETLRateLimitedAction";
import { ETLRefreshAction } from "./ETLRefreshAction";
import { StageMetricsAction } from "./StageMetricsAction";

export const GROWTH_STUDIO_ACTION_KEYS = [
  "growth.stage-metrics",
  "growth.channel-overview",
  "growth.etl-refresh",
  "growth.etl-rate-limited",
  "growth.etl-confirm",
] as const;

export type GrowthStudioActionKey = (typeof GROWTH_STUDIO_ACTION_KEYS)[number];

/**
 * Maps each growth-studio action key to its component.
 *
 * The `as unknown as ActionComponent` cast is required where the action
 * has a narrower TValue than the registry's generic default — TypeScript
 * treats `ActionComponent<SpecificType>` as non-assignable to
 * `ActionComponent<unknown>` due to function-parameter contravariance.
 */
const REGISTRY_ENTRIES: Readonly<Record<GrowthStudioActionKey, ActionComponent>> = {
  "growth.stage-metrics": StageMetricsAction as unknown as ActionComponent,
  "growth.channel-overview": ChannelOverviewAction as unknown as ActionComponent,
  "growth.etl-refresh": ETLRefreshAction as unknown as ActionComponent,
  "growth.etl-rate-limited": ETLRateLimitedAction as unknown as ActionComponent,
  "growth.etl-confirm": ETLConfirmAction as unknown as ActionComponent,
};

/**
 * Registers every growth-studio action. Idempotent — each key is only
 * registered if the registry does not already have it, so it tolerates
 * registry resets (tests) and re-imports.
 */
export function bootstrapGrowthStudioActions(): void {
  for (const key of GROWTH_STUDIO_ACTION_KEYS) {
    if (hasAction(key)) continue;
    registerAction(key, REGISTRY_ENTRIES[key]);
  }
}

// Auto-bootstrap on module load.
bootstrapGrowthStudioActions();
