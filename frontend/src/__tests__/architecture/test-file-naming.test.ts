/**
 * ARCH TEST: Non-component .ts files must be kebab-case.
 *
 * Rule: .ts(x) files inside hooks/, api/, types/, utils/, config/, lib/,
 * context/, store/, services/ directories must have a kebab-case stem.
 * Uses ignoreMiddleExtensions: true logic (checks only first segment).
 *
 * Ratchet pattern: KNOWN_CAMELCASE_FILES is frozen at 2026-04-15 violations.
 * This set MUST only shrink — never add new entries.
 */
import { describe, it, expect } from "vitest";
import * as path from "path";
import { FEATURES_DIR, walkFiles, relPath, isKebabCase, stemName, isTestFile } from "./helpers";

// ── Ratchet allowlist ─────────────────────────────────────────────────────────
const KNOWN_CAMELCASE_FILES = new Set([
  // audit hooks (1)
  "features/audit/hooks/useAudit.ts",
  // brand hooks (4)
  "features/brand/hooks/useBrandSettings.ts",
  "features/brand/hooks/useBuyerPersona.ts",
  "features/brand/hooks/useBuyerPersonas.ts",
  "features/brand/hooks/useOnboardingWizard.ts",
  // copilot hooks (7)
  "features/copilot/hooks/useCopilotChat.ts",
  "features/copilot/hooks/useCopilotFieldSync.ts",
  "features/copilot/hooks/useCopilotNavigator.ts",
  "features/copilot/hooks/useCopilotUIAction.ts",
  "features/copilot/hooks/useProactiveNudges.ts",
  "features/copilot/hooks/useRouteTracker.ts",
  "features/copilot/hooks/useVoiceRecorder.ts",
  // growth-studio context (3 — 2 PascalCase + 1 camelCase hook file)
  "features/growth-studio/components/metrics-dashboard/context/GrowthStudioContext.tsx",
  "features/growth-studio/components/metrics-dashboard/context/useMetricClickHandler.ts",
  // growth-studio nested hooks (3)
  "features/growth-studio/components/metrics-dashboard/hooks/useStageSummaries.ts",
  "features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/hooks/useMetaAdsOnboardingTrigger.ts",
  "features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/hooks/useResumenViewData.ts",
  // growth-studio hooks (15)
  "features/growth-studio/hooks/useBowtiesSummary.ts",
  "features/growth-studio/hooks/useChannelDashboard.ts",
  "features/growth-studio/hooks/useConnectionHealth.ts",
  "features/growth-studio/hooks/useGroupDetail.ts",
  "features/growth-studio/hooks/useGrowthStudioUrl.ts",
  "features/growth-studio/hooks/useHashScroll.ts",
  "features/growth-studio/hooks/useInitialLoad.ts",
  "features/growth-studio/hooks/useIntersectionObserver.ts",
  "features/growth-studio/hooks/useMailDashboard.ts",
  "features/growth-studio/hooks/useMetricCatalog.ts",
  "features/growth-studio/hooks/useStageDetail.ts",
  "features/growth-studio/hooks/useStageOverview.ts",
  "features/growth-studio/hooks/useSyncAllSources.ts",
  "features/growth-studio/hooks/useSyncChannel.ts",
  "features/growth-studio/hooks/useYoutubeAnalytics.ts",
  // growth-studio lib (4)
  "features/growth-studio/lib/channelIcons.ts",
  "features/growth-studio/lib/channelViewMap.ts",
  "features/growth-studio/lib/classifyChannel.ts",
  "features/growth-studio/lib/providerToConnectionRoute.ts",
  // offer-studio context (1 PascalCase context file)
  "features/offer-studio/components/landing/context/LandingThemeContext.tsx",
  // sales services (2)
  "features/sales/services/dashboardService.ts",
  "features/sales/services/leadService.ts",
  // tenant_domains hooks (1)
  "features/tenant_domains/hooks/useDomains.ts",
]);

// ─────────────────────────────────────────────────────────────────────────────

const SCANNED_DIRS = new Set(["hooks", "api", "types", "utils", "config", "lib", "context", "store", "services"]);

describe("Architecture: File naming (non-components)", () => {
  it("every .ts(x) file in hooks/api/types/utils/config/lib/context/store/services/ must be kebab-case", () => {
    const violations: string[] = [];

    for (const file of walkFiles(FEATURES_DIR)) {
      if (isTestFile(file)) continue;
      if (!file.endsWith(".ts") && !file.endsWith(".tsx")) continue;

      const basename = path.basename(file);
      if (basename === "index.ts" || basename === "index.tsx") continue;

      const parentDir = path.basename(path.dirname(file));
      if (!SCANNED_DIRS.has(parentDir)) continue;

      const stem = stemName(basename);
      if (!isKebabCase(stem)) {
        violations.push(relPath(file));
      }
    }

    const newViolations = violations.filter((v) => !KNOWN_CAMELCASE_FILES.has(v));
    const alreadyFixed = [...KNOWN_CAMELCASE_FILES].filter((v) => !violations.includes(v));

    if (alreadyFixed.length > 0) {
      console.info(
        `[arch] Allowlist can shrink: ${alreadyFixed.length} entries already fixed:\n  ${alreadyFixed.join("\n  ")}`,
      );
    }

    expect(
      newViolations,
      `NEW file naming violations (rename to kebab-case, update imports):\n${newViolations.join("\n")}`,
    ).toEqual([]);
  });
});
